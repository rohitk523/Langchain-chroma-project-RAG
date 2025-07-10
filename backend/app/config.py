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
    
    # OpenSearch settings
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_username: str = "admin"
    opensearch_password: str = "ETHN_hnt523"
    opensearch_use_ssl: bool = True
    opensearch_verify_certs: bool = False
    opensearch_documents_index: str = "rag_documents"
    opensearch_chat_index: str = "chat_history"
    
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