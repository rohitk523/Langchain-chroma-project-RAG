from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    chat_id: Optional[str] = None  # If None, creates new chat
    include_sources: bool = True

class ChatResponse(BaseModel):
    response: str
    chat_id: str
    sources: List[Dict[str, Any]] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatHistory(BaseModel):
    id: str
    chat_id: str
    user_id: str
    message: str
    response: str
    message_type: str  # "user" or "assistant"
    sources: List[Dict[str, Any]] = []
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class ChatSession(BaseModel):
    chat_id: str
    user_id: str
    title: str
    created_at: datetime
    last_message_at: datetime
    message_count: int = 0

class DocumentUpload(BaseModel):
    filename: str
    user_id: str
    file_size: int
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    processed: bool = False

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 