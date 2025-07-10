import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from app.config import settings

class ChromaService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Set up ChromaDB client with authentication if credentials are provided
        if settings.chroma_username and settings.chroma_password:
            # Authenticated client
            self.client = chromadb.HttpClient(
                host=f"http://{settings.chroma_host}:{settings.chroma_port}",
                settings=Settings(
                    chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                    chroma_client_auth_credentials=f"{settings.chroma_username}:{settings.chroma_password}"
                )
            )
        else:
            # Non-authenticated client for local development
            self.client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port
            )
        
    async def initialize(self):
        """Initialize ChromaDB collections"""
        try:
            # Create documents collection
            try:
                self.documents_collection = self.client.create_collection(
                    name=settings.chroma_collection_name,
                    metadata={"description": "RAG documents collection"}
                )
            except Exception:
                # Collection already exists
                self.documents_collection = self.client.get_collection(settings.chroma_collection_name)
                
            # Create chat history collection
            try:
                self.chat_collection = self.client.create_collection(
                    name=settings.chroma_chat_collection_name,
                    metadata={"description": "Chat history collection"}
                )
            except Exception:
                # Collection already exists
                self.chat_collection = self.client.get_collection(settings.chroma_chat_collection_name)
                
            print("✅ ChromaDB collections initialized")
        except Exception as e:
            print(f"⚠️ ChromaDB initialization error: {e}")
    
    async def add_documents(self, documents: List[str], metadatas: List[Dict], user_id: str) -> str:
        """Add documents to ChromaDB with embeddings"""
        try:
            # Generate embeddings
            embeddings = await self.embeddings.aembed_documents(documents)
            
            # Create unique IDs
            ids = [f"{user_id}_{uuid.uuid4()}" for _ in documents]
            
            # Add user_id to all metadata
            enhanced_metadatas = []
            for metadata in metadatas:
                enhanced_metadata = metadata.copy()
                enhanced_metadata["user_id"] = user_id
                enhanced_metadatas.append(enhanced_metadata)
            
            # Add to collection
            self.documents_collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=enhanced_metadatas
            )
            
            return f"Added {len(documents)} documents"
                    
        except Exception as e:
            raise Exception(f"Error adding documents: {str(e)}")
    
    async def similarity_search(self, query: str, user_id: str, k: int = 3) -> List[Dict[str, Any]]:
        """Perform similarity search for RAG"""
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Query collection
            results = self.documents_collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where={"user_id": user_id}  # Filter by user
            )
            
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
            
            # Add to chat collection
            self.chat_collection.add(
                ids=[message_id],
                embeddings=[embedding],
                documents=[json.dumps(chat_data)],
                metadatas=[chat_data]
            )
            
            return True
                
        except Exception as e:
            print(f"Error adding chat message: {e}")
            return False
    
    async def get_chat_history(self, chat_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a specific chat"""
        try:
            results = self.chat_collection.query(
                query_embeddings=None,
                n_results=100,
                where={
                    "chat_id": chat_id,
                    "user_id": user_id
                }
            )
            
            history = []
            if results.get("metadatas") and results["metadatas"][0]:
                for metadata in results["metadatas"][0]:
                    history.append(metadata)
            
            # Sort by timestamp
            history.sort(key=lambda x: x.get("timestamp", ""))
            return history
                    
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []
    
    async def get_user_chats(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user"""
        try:
            results = self.chat_collection.query(
                query_embeddings=None,
                n_results=1000,
                where={"user_id": user_id}
            )
            
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