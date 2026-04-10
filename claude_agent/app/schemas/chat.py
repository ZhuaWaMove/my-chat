from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Message schemas
class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    session_id: str

class Message(MessageBase):
    id: int
    session_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Session schemas
class SessionBase(BaseModel):
    title: Optional[str] = None

class SessionCreate(SessionBase):
    id: Optional[str] = None  # If not provided, will be generated

class Session(SessionBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Chat request/response schemas
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # If not provided, new session will be created

class ChatResponse(BaseModel):
    session_id: str
    message: str
    response: str

# Session with messages
class SessionWithMessages(Session):
    messages: List[Message] = []
