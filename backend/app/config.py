from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App settings
    debug: bool = False
    app_name: str = "RAG Chat API"
    
    # Clerk Authentication
    clerk_secret_key: str
    clerk_publishable_key: str = ""
    
    # OpenAI
    openai_api_key: str
    
    # ChromaDB settings
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection_name: str = "rag_documents"
    chroma_chat_collection_name: str = "chat_history"
    # ChromaDB Authentication
    chroma_username: str = ""
    chroma_password: str = ""
    
    # CORS settings
    allowed_origins: List[str] = ["http://localhost:3000", "https://*.railway.app"]
    
    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True) 