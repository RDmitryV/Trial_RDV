"""Chat endpoints."""

from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import (APIRouter, Depends, HTTPException, WebSocket,
                     WebSocketDisconnect, status)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.models.research import Research
from app.models.user import User
from app.services.chat.chat_service import ChatMessage, ChatService
from app.services.chat.websocket_chat_manager import chat_manager

router = APIRouter()


class ChatMessageRequest(BaseModel):
    """Chat message request schema."""

    message: str
    research_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""

    role: str
    content: str
    timestamp: datetime
    tool_uses: Optional[List[dict]] = None


class ChatHistoryRequest(BaseModel):
    """Chat history schema."""

    messages: List[dict]


@router.post("/send", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Send a chat message and get AI response.

    This endpoint allows users to interact with the AI assistant for:
    - Asking questions about research
    - Getting help with research parameters
    - Understanding collected data
    - Requesting analysis suggestions
    """
    # Get research if provided
    research = None
    if request.research_id:
        result = await db.execute(
            select(Research).where(
                Research.id == request.research_id, Research.user_id == current_user.id
            )
        )
        research = result.scalar_one_or_none()

        if not research:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research not found",
            )

    # Create chat service
    chat_service = ChatService(
        db=db,
        llm_provider=settings.default_llm_provider,
    )

    # Get response with tools
    response = await chat_service.chat_with_tools(
        user_message=request.message,
        research=research,
    )

    return ChatMessageResponse(
        role="assistant",
        content=response["content"],
        timestamp=datetime.utcnow(),
        tool_uses=response.get("tool_uses"),
    )


@router.websocket("/ws/{research_id}")
async def chat_websocket(
    websocket: WebSocket,
    research_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    WebSocket endpoint for streaming chat responses.

    Connect to this endpoint to get real-time streaming responses from the AI assistant.
    Send messages in JSON format:
    {
        "message": "Your question here",
        "history": [{"role": "user", "content": "..."}, ...]
    }

    Receive responses in JSON format:
    {
        "type": "chunk|complete|error|tool_use",
        "content": "...",
        ...
    }
    """
    # Connect
    await chat_manager.connect(websocket, research_id)

    try:
        # Get research
        result = await db.execute(select(Research).where(Research.id == research_id))
        research = result.scalar_one_or_none()

        if not research:
            await chat_manager.send_error(research_id, "Research not found")
            await websocket.close()
            return

        # Create chat service
        chat_service = ChatService(
            db=db,
            llm_provider=settings.default_llm_provider,
        )

        # Listen for messages
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message")
            history_data = data.get("history", [])

            if not user_message:
                await chat_manager.send_error(research_id, "Message is required")
                continue

            # Parse history
            history = []
            for msg in history_data:
                history.append(
                    ChatMessage(
                        role=msg["role"],
                        content=msg["content"],
                        timestamp=datetime.fromisoformat(
                            msg.get("timestamp", datetime.utcnow().isoformat())
                        ),
                    )
                )

            # Stream response
            full_response = ""
            try:
                async for chunk in chat_service.chat_stream(
                    user_message=user_message,
                    research=research,
                    history=history,
                ):
                    full_response += chunk
                    await chat_manager.stream_chunk(research_id, chunk)

                # Send completion
                await chat_manager.send_complete(research_id, full_response)

            except Exception as e:
                await chat_manager.send_error(research_id, str(e))

    except WebSocketDisconnect:
        await chat_manager.disconnect(websocket, research_id)
    except Exception as e:
        await chat_manager.send_error(research_id, str(e))
        await chat_manager.disconnect(websocket, research_id)
