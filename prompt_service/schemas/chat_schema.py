from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PromptExecuteRequest(BaseModel):
    model: Optional[str] = None


class DocumentChatCreate(BaseModel):
    document_id: Optional[UUID] = None
    content: str = Field(min_length=1)


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    model: Optional[str] = None
    document_id: Optional[UUID] = None
