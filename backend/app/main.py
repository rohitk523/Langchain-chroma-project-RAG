from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
import uuid

from app.config import settings
from app.auth import verify_clerk_token
from app.services.chroma_service import ChromaService
from app.services.chat_service import ChatService
from app.models.chat import ChatRequest, ChatResponse, ChatHistory

app = FastAPI(title="RAG Chat API", version="1.0.0")

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

# Initialize services
chroma_service = ChromaService()
chat_service = ChatService(chroma_service)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await chroma_service.initialize()
    print("✅ Services initialized successfully")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "RAG Chat API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check for Railway deployment"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Main chat endpoint"""
    try:
        # Verify authentication
        user_data = await verify_clerk_token(credentials.credentials)
        user_id = user_data.get("sub")
        
        # Process chat request
        response = await chat_service.process_chat(
            message=request.message,
            chat_id=request.chat_id,
            user_id=user_id
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/{chat_id}/history", response_model=List[ChatHistory])
async def get_chat_history(
    chat_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get chat history for a specific chat_id"""
    try:
        # Verify authentication
        user_data = await verify_clerk_token(credentials.credentials)
        user_id = user_data.get("sub")
        
        # Get chat history
        history = await chat_service.get_chat_history(chat_id, user_id)
        
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chats", response_model=List[dict])
async def get_user_chats(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all chat sessions for the authenticated user"""
    try:
        # Verify authentication
        user_data = await verify_clerk_token(credentials.credentials)
        user_id = user_data.get("sub")
        
        # Get user's chats
        chats = await chat_service.get_user_chats(user_id)
        
        return chats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload and process a document for RAG"""
    try:
        # Verify authentication
        user_data = await verify_clerk_token(credentials.credentials)
        user_id = user_data.get("sub")
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Process uploaded document
        result = await chat_service.process_uploaded_document(file, user_id)
        
        return {"message": "Document uploaded successfully", "document_id": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/{chat_id}")
async def delete_chat(
    chat_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a chat session"""
    try:
        # Verify authentication
        user_data = await verify_clerk_token(credentials.credentials)
        user_id = user_data.get("sub")
        
        # Delete chat
        await chat_service.delete_chat(chat_id, user_id)
        
        return {"message": "Chat deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.debug
    ) 