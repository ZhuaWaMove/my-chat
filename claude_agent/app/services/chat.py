import json
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.chat import Session as SessionModel, Message as MessageModel
from app.schemas.chat import SessionCreate, MessageCreate
from app.services.claude import claude_service

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, session_data: SessionCreate) -> SessionModel:
        """Create a new chat session"""
        session_id = session_data.id or str(uuid.uuid4())
        db_session = SessionModel(
            id=session_id,
            title=session_data.title
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_session(self, session_id: str) -> Optional[SessionModel]:
        """Get a session by ID"""
        return self.db.query(SessionModel).filter(SessionModel.id == session_id).first()

    def get_all_sessions(self) -> List[SessionModel]:
        """Get all sessions"""
        return self.db.query(SessionModel).order_by(SessionModel.updated_at.desc()).all()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        session = self.get_session(session_id)
        if not session:
            return False

        # Delete all messages in the session
        self.db.query(MessageModel).filter(MessageModel.session_id == session_id).delete()

        # Delete the session
        self.db.delete(session)
        self.db.commit()
        return True

    def add_message(self, message_data: MessageCreate) -> MessageModel:
        """Add a message to a session"""
        # Update session's updated_at timestamp
        session = self.get_session(message_data.session_id)
        if session:
            session.updated_at = datetime.utcnow()

        db_message = MessageModel(
            session_id=message_data.session_id,
            role=message_data.role,
            content=message_data.content
        )
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message

    def get_messages(self, session_id: str) -> List[MessageModel]:
        """Get all messages in a session"""
        return self.db.query(MessageModel).filter(
            MessageModel.session_id == session_id
        ).order_by(MessageModel.timestamp.asc()).all()

    def process_chat(self, session_id: str, user_message: str) -> str:
        """Process a chat message and get response from Claude"""
        # Add user message to database
        self.add_message(MessageCreate(
            session_id=session_id,
            role="user",
            content=user_message
        ))

        # Get conversation history
        messages = self.get_messages(session_id)

        # Format messages for Claude
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Get response from Claude
        claude_response = claude_service.chat(formatted_messages)

        # Add Claude's response to database
        self.add_message(MessageCreate(
            session_id=session_id,
            role="assistant",
            content=claude_response
        ))

        return claude_response

    def process_chat_stream(self, session_id: str, user_message: str):
        """Process a chat message and get streaming response from Claude"""
        # Add user message to database
        self.add_message(MessageCreate(
            session_id=session_id,
            role="user",
            content=user_message
        ))

        # Get conversation history
        messages = self.get_messages(session_id)

        # Format messages for Claude
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # First yield session information
        yield json.dumps({"session_id": session_id})

        # Get streaming response from Claude
        full_response = ""
        for chunk in claude_service.chat_stream(formatted_messages):
            full_response += chunk
            yield chunk

        # Add Claude's response to database after streaming completes
        self.add_message(MessageCreate(
            session_id=session_id,
            role="assistant",
            content=full_response
        ))
