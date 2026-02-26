from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Conversation session ID")
    user_input: str = Field(..., description="User input content")


class StreamEvent(BaseModel):
    event: str
    data: str
