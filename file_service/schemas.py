from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    id: UUID
    filename: str
    file_type: Literal["pdf", "docx"]
    content_type: str
    size_bytes: int
    character_count: int
    created_at: datetime


class DocumentResponse(DocumentSummary):
    extracted_text: str
