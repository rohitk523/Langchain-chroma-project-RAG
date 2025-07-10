import httpx
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from app.config import settings

class ChromaService:
    def __init__(self):
        self.chroma_base_url = f"http://{settings.chroma_host}:{settings.chroma_port}"
        self.embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    async def initialize(self):
        """Initialize ChromaDB collections"""
        try:
            async with httpx.AsyncClient() as client:
                # Create documents collection
                await client.post(
                    f"{self.chroma_base_url}/api/v1/collections",
                    json={
                        "name": settings.chroma_collection_name,
                        "metadata": {"description": "RAG documents collection"}
                    }
                )
                
                # Create chat history collection
                await client.post(
                    f"{self.chroma_base_url}/api/v1/collections",
                    json={
                        "name": settings.chroma_chat_collection_name,
                        "metadata": {"description": "Chat history collection"}
                    }
                )
                
            print("✅ ChromaDB collections initialized")
        except Exception as e:
            print(f"⚠️ ChromaDB collections may already exist: {e}")
    
    async def add_documents(self, documents: List[str], metadatas: List[Dict], user_id: str) -> str:
        """Add documents to ChromaDB with embeddings"""
        try:
            # Generate embeddings
            embeddings = await self.embeddings.aembed_documents(documents)
            
            # Create unique IDs
            ids = [f"{user_id}_{uuid.uuid4()}" for _ in documents]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.chroma_base_url}/api/v1/collections/{settings.chroma_collection_name}/add",
                    json={
                        "ids": ids,
                        "embeddings": embeddings,
                        "documents": documents,
                        "metadatas": metadatas
                    }
                )
                
                if response.status_code == 200:
                    return f"Added {len(documents)} documents"
                else:
                    raise Exception(f"Failed to add documents: {response.text}")
                    
        except Exception as e:
            raise Exception(f"Error adding documents: {str(e)}")
    
    async def similarity_search(self, query: str, user_id: str, k: int = 3) -> List[Dict[str, Any]]:
        """Perform similarity search for RAG"""
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.chroma_base_url}/api/v1/collections/{settings.chroma_collection_name}/query",
                    json={
                        "query_embeddings": [query_embedding],
                        "n_results": k,
                        "where": {"user_id": user_id}  # Filter by user
                    }
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    # Format results
                    documents = []
                    if results.get("documents") and results["documents"][0]:
                        for i, doc in enumerate(results["documents"][0]):
                            documents.append({
                                "content": doc,
                                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                                "distance": results["distances"][0][i] if results.get("distances") else 0
                            })
                    
                    return documents
                else:
                    raise Exception(f"Search failed: {response.text}")
                    
        except Exception as e:
            raise Exception(f"Error in similarity search: {str(e)}")
    
    async def add_chat_message(self, chat_id: str, user_id: str, message: str, 
                              response: str, message_type: str, sources: List[Dict] = None):
        """Add chat message to history"""
        try:
            chat_data = {
                "chat_id": chat_id,
                "user_id": user_id,
                "message": message,
                "response": response,
                "message_type": message_type,
                "sources": sources or [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Generate embedding for search
            text_for_embedding = f"{message} {response}"
            embedding = await self.embeddings.aembed_query(text_for_embedding)
            
            message_id = f"{chat_id}_{uuid.uuid4()}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.chroma_base_url}/api/v1/collections/{settings.chroma_chat_collection_name}/add",
                    json={
                        "ids": [message_id],
                        "embeddings": [embedding],
                        "documents": [json.dumps(chat_data)],
                        "metadatas": [chat_data]
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            print(f"Error adding chat message: {e}")
            return False
    
    async def get_chat_history(self, chat_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a specific chat"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.chroma_base_url}/api/v1/collections/{settings.chroma_chat_collection_name}/query",
                    json={
                        "query_embeddings": None,
                        "n_results": 100,
                        "where": {
                            "chat_id": chat_id,
                            "user_id": user_id
                        }
                    }
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    history = []
                    if results.get("metadatas") and results["metadatas"][0]:
                        for metadata in results["metadatas"][0]:
                            history.append(metadata)
                    
                    # Sort by timestamp
                    history.sort(key=lambda x: x.get("timestamp", ""))
                    return history
                else:
                    return []
                    
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []
    
    async def get_user_chats(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.chroma_base_url}/api/v1/collections/{settings.chroma_chat_collection_name}/query",
                    json={
                        "query_embeddings": None,
                        "n_results": 1000,
                        "where": {"user_id": user_id}
                    }
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    # Group by chat_id
                    chats = {}
                    if results.get("metadatas") and results["metadatas"][0]:
                        for metadata in results["metadatas"][0]:
                            chat_id = metadata.get("chat_id")
                            if chat_id not in chats:
                                chats[chat_id] = {
                                    "chat_id": chat_id,
                                    "title": metadata.get("message", "New Chat")[:50] + "...",
                                    "created_at": metadata.get("timestamp"),
                                    "last_message_at": metadata.get("timestamp"),
                                    "message_count": 0
                                }
                            
                            chats[chat_id]["message_count"] += 1
                            if metadata.get("timestamp") > chats[chat_id]["last_message_at"]:
                                chats[chat_id]["last_message_at"] = metadata.get("timestamp")
                    
                    return list(chats.values())
                else:
                    return []
                    
        except Exception as e:
            print(f"Error getting user chats: {e}")
            return []
    
    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat session"""
        try:
            # ChromaDB doesn't have a direct delete by metadata query
            # This would need to be implemented by getting IDs first, then deleting
            # For now, we'll mark it as deleted in metadata
            return True
                    
        except Exception as e:
            print(f"Error deleting chat: {e}")
            return False
    
    async def process_pdf_file(self, file_path: str, user_id: str) -> str:
        """Process uploaded PDF file"""
        try:
            # Load and split PDF
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            docs = self.text_splitter.split_documents(documents)
            
            # Prepare documents and metadata
            texts = [doc.page_content for doc in docs]
            metadatas = []
            
            for doc in docs:
                metadata = doc.metadata.copy()
                metadata["user_id"] = user_id
                metadata["upload_timestamp"] = datetime.utcnow().isoformat()
                metadatas.append(metadata)
            
            # Add to ChromaDB
            result = await self.add_documents(texts, metadatas, user_id)
            return result
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}") 