from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse, Session, SessionWithMessages, Message
from app.services.chat import ChatService

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a message to Claude and get response"""
    chat_service = ChatService(db)

    # Get or create session
    session_id = request.session_id
    if not session_id:
        # Create new session with default title
        from app.schemas.chat import SessionCreate
        session = chat_service.create_session(SessionCreate())
        session_id = session.id
    else:
        # Verify session exists
        session = chat_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

    # Process chat
    try:
        response = chat_service.process_chat(session_id, request.message)
        return ChatResponse(
            session_id=session_id,
            message=request.message,
            response=response
        )
    except Exception as e:
        # Return mock response instead of error for UI testing
        print(f"Chat API error: {str(e)}. Returning mock response.")
        mock_response = f"""Mock Response (API Error: {str(e)})

This is a simulated response for UI testing since the Claude API is unavailable.

## Sample Code Block
```python
def test_ui():
    print("Testing UI features:")
    print("1. Copy button")
    print("2. Regenerate button")
    print("3. Like/Dislike buttons")
    print("4. Share button")
    return "UI Test Complete"
```

## Test Features
- **Markdown rendering**
- Code syntax highlighting
- Action buttons functionality
- Responsive design

Please check your API configuration in the .env file."""

        return ChatResponse(
            session_id=session_id or "mock-session",
            message=request.message,
            response=mock_response
        )

@router.post("/stream", response_class=StreamingResponse)
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a message to Claude and get streaming response"""
    chat_service = ChatService(db)

    # Get or create session
    session_id = request.session_id
    if not session_id:
        # Create new session with default title
        from app.schemas.chat import SessionCreate
        session = chat_service.create_session(SessionCreate())
        session_id = session.id
    else:
        # Verify session exists
        session = chat_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

    async def stream_generator():
        try:
            for chunk in chat_service.process_chat_stream(session_id, request.message):
                # Format as SSE
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/sessions/{session_id}", response_model=SessionWithMessages)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get a session with all its messages"""
    chat_service = ChatService(db)
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = chat_service.get_messages(session_id)
    return SessionWithMessages(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[Message.from_orm(msg) for msg in messages]
    )

@router.post("/simple-stream")
async def simple_stream():
    async def stream_generator():
        for i in range(5):
            yield f"data: Test message {i}\n\n"
            import asyncio
            await asyncio.sleep(0.5)

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
