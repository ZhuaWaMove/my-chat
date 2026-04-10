from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.chat import Session as SessionSchema, SessionCreate
from app.services.chat import ChatService

router = APIRouter()

@router.get("/", response_model=List[SessionSchema])
async def get_sessions(
    db: Session = Depends(get_db)
):
    """Get all chat sessions"""
    chat_service = ChatService(db)
    sessions = chat_service.get_all_sessions()
    return [SessionSchema.from_orm(session) for session in sessions]

@router.post("/", response_model=SessionSchema)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    chat_service = ChatService(db)
    session = chat_service.create_session(session_data)
    return SessionSchema.from_orm(session)

@router.get("/{session_id}", response_model=SessionSchema)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific session"""
    chat_service = ChatService(db)
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionSchema.from_orm(session)

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a session and all its messages"""
    chat_service = ChatService(db)
    success = chat_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully"}
