import os
import uuid
import aiofiles
from typing import List, Dict, Any
from datetime import datetime
from fastapi import UploadFile

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from app.services.chroma_service import ChromaService
from app.models.chat import ChatResponse, ChatHistory
from app.config import settings

class ChatService:
    def __init__(self, chroma_service: ChromaService):
        self.chroma_service = chroma_service
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3,
            api_key=settings.openai_api_key
        )
        
        # Custom prompt template for RAG
        self.prompt_template = """You are a helpful AI assistant. Use the following pieces of context to answer the question at the end. 
        If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.
        
        Context:
        {context}
        
        Question: {question}
        
        Helpful Answer:"""
        
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
    
    async def process_chat(self, message: str, chat_id: str, user_id: str) -> ChatResponse:
        """Process a chat message and return RAG response"""
        try:
            # Generate chat_id if not provided
            if not chat_id:
                chat_id = str(uuid.uuid4())
            
            # Get relevant documents from ChromaDB
            relevant_docs = await self.chroma_service.similarity_search(
                query=message,
                user_id=user_id,
                k=3
            )
            
            # Prepare context from relevant documents
            context = ""
            sources = []
            
            if relevant_docs:
                context_parts = []
                for i, doc in enumerate(relevant_docs):
                    context_parts.append(f"Source {i+1}: {doc['content']}")
                    sources.append({
                        "content": doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                        "metadata": doc['metadata'],
                        "similarity_score": 1 - doc.get('distance', 0)
                    })
                context = "\n\n".join(context_parts)
            
            # Generate response using LLM
            if context:
                formatted_prompt = self.prompt.format(context=context, question=message)
            else:
                formatted_prompt = f"Question: {message}\n\nI don't have any relevant documents to answer this question. Please provide a general helpful response."
            
            response = await self.llm.ainvoke(formatted_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Save chat message to history
            await self.chroma_service.add_chat_message(
                chat_id=chat_id,
                user_id=user_id,
                message=message,
                response=response_text,
                message_type="conversation",
                sources=sources
            )
            
            return ChatResponse(
                response=response_text,
                chat_id=chat_id,
                sources=sources,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            # Fallback response
            fallback_response = f"I apologize, but I encountered an error processing your request: {str(e)}"
            
            return ChatResponse(
                response=fallback_response,
                chat_id=chat_id or str(uuid.uuid4()),
                sources=[],
                timestamp=datetime.utcnow()
            )
    
    async def get_chat_history(self, chat_id: str, user_id: str) -> List[ChatHistory]:
        """Get chat history for a specific chat"""
        try:
            history_data = await self.chroma_service.get_chat_history(chat_id, user_id)
            
            history = []
            for item in history_data:
                history.append(ChatHistory(
                    id=f"{chat_id}_{len(history)}",
                    chat_id=chat_id,
                    user_id=user_id,
                    message=item.get("message", ""),
                    response=item.get("response", ""),
                    message_type=item.get("message_type", "conversation"),
                    sources=item.get("sources", []),
                    timestamp=datetime.fromisoformat(item.get("timestamp", datetime.utcnow().isoformat())),
                    metadata=item
                ))
            
            return history
            
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []
    
    async def get_user_chats(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user"""
        try:
            return await self.chroma_service.get_user_chats(user_id)
        except Exception as e:
            print(f"Error getting user chats: {e}")
            return []
    
    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat session"""
        try:
            return await self.chroma_service.delete_chat(chat_id, user_id)
        except Exception as e:
            print(f"Error deleting chat: {e}")
            return False
    
    async def process_uploaded_document(self, file: UploadFile, user_id: str) -> str:
        """Process uploaded PDF document"""
        try:
            # Create unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.upload_dir, unique_filename)
            
            # Save uploaded file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Process the PDF
            result = await self.chroma_service.process_pdf_file(file_path, user_id)
            
            # Clean up uploaded file
            os.remove(file_path)
            
            return result
            
        except Exception as e:
            # Clean up file if it exists
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            
            raise Exception(f"Error processing uploaded document: {str(e)}")
    
    async def search_documents(self, query: str, user_id: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search user's documents"""
        try:
            return await self.chroma_service.similarity_search(query, user_id, k)
        except Exception as e:
            print(f"Error searching documents: {e}")
            return [] 