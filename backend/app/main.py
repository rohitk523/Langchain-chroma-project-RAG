from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import os
from datetime import datetime
import uuid
import logging

from app.config import settings
from app.auth import get_current_user, health_check_auth, require_auth, verify_clerk_token
from app.services.opensearch_service import OpenSearchService
from app.services.chat_service import ChatService
from app.models.chat import ChatRequest, ChatResponse, ChatHistory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
opensearch_service = OpenSearchService()
chat_service = ChatService(opensearch_service)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting up...")
    try:
        await opensearch_service.initialize()
        logger.info("✅ OpenSearch initialized successfully")
        
        # Test auth service
        auth_health = await health_check_auth()
        if auth_health["status"] == "healthy":
            logger.info("✅ Clerk authentication service is accessible")
        else:
            logger.warning(f"⚠️  Clerk authentication service health check failed: {auth_health}")
            
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔥 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A RAG-powered chat application with OpenSearch and Clerk authentication",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "RAG Chat API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check for Railway deployment"""
    try:
        # Check OpenSearch connection
        opensearch_health = await opensearch_service.health_check()
        
        # Check auth service
        auth_health = await health_check_auth()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "opensearch": opensearch_health,
                "auth": auth_health
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@app.post("/api/chat", response_model=ChatResponse)
@require_auth
async def chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Main chat endpoint"""
    try:
        user_id = current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user data")
        
        logger.info(f"Processing chat request for user: {user_id}")
        
        # Process chat request
        response = await chat_service.process_chat(
            message=request.message,
            chat_id=request.chat_id,
            user_id=user_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/api/chat/{chat_id}/history", response_model=List[ChatHistory])
@require_auth
async def get_chat_history(
    chat_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get chat history for a specific chat_id"""
    try:
        user_id = current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user data")
        
        logger.info(f"Getting chat history for chat_id: {chat_id}, user: {user_id}")
        
        # Get chat history
        history = await chat_service.get_chat_history(chat_id, user_id)
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get chat history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

@app.get("/api/chats", response_model=List[dict])
@require_auth
async def get_user_chats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all chat sessions for the authenticated user"""
    try:
        user_id = current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user data")
        
        logger.info(f"Getting chats for user: {user_id}")
        
        # Get user's chats
        chats = await chat_service.get_user_chats(user_id)
        
        return chats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user chats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user chats: {str(e)}")

@app.post("/api/upload")
@require_auth
async def upload_document(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload and process a document for RAG"""
    try:
        user_id = current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user data")
        
        logger.info(f"Processing document upload for user: {user_id}, file: {file.filename}")
        
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Validate file size
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size too large. Maximum allowed: {settings.max_file_size} bytes"
            )
        
        # Process uploaded document
        result = await chat_service.process_uploaded_document(file, user_id)
        
        return {"message": "Document uploaded successfully", "document_id": result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@app.delete("/api/chat/{chat_id}")
@require_auth
async def delete_chat(
    chat_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a chat session"""
    try:
        user_id = current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user data")
        
        logger.info(f"Deleting chat for user: {user_id}, chat_id: {chat_id}")
        
        # Delete chat
        success = await chat_service.delete_chat(chat_id, user_id)
        
        if success:
            return {"message": "Chat deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Chat not found or could not be deleted")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")

@app.get("/api/documents")
@require_auth
async def get_user_documents(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all documents for the authenticated user"""
    try:
        user_id = current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user data")
        
        logger.info(f"Getting documents for user: {user_id}")
        
        # Get user's documents
        documents = await opensearch_service.get_user_documents(user_id)
        
        return {"documents": documents}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user documents error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user documents: {str(e)}")

@app.get("/api/search")
@require_auth
async def search_documents(
    q: str,
    limit: int = 5,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search user's documents"""
    try:
        user_id = current_user.get("user_id") or current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user data")
        
        logger.info(f"Searching documents for user: {user_id}, query: {q}")
        
        # Search documents
        results = await chat_service.search_documents(q, user_id, limit)
        
        return {"results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")

# Add user profile endpoint
@app.get("/api/profile")
@require_auth
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current user's profile"""
    try:
        # Return sanitized user data
        return {
            "user_id": current_user.get("user_id") or current_user.get("sub"),
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "first_name": current_user.get("first_name"),
            "last_name": current_user.get("last_name"),
        }
        
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")

# Debug endpoint for auth testing
@app.get("/api/test-auth")
async def test_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Test authentication without full user dependency - for debugging"""
    try:
        logger.info(f"Testing auth with token: {credentials.credentials[:20]}...")
        
        # Test the token verification
        user_data = await verify_clerk_token(credentials.credentials)
        
        return {
            "status": "success",
            "message": "Authentication successful",
            "user_data": user_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException as e:
        logger.error(f"Auth test failed: {e.detail}")
        return {
            "status": "error",
            "message": f"Authentication failed: {e.detail}",
            "status_code": e.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Auth test error: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.debug
    ) 