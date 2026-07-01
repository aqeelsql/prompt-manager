from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ReviewCreate(BaseModel):
    target_type: Literal["prompt", "chat"] = "prompt"
    prompt_id: UUID | None = None
    chat_id: UUID | None = None
    reviewer_name: str = Field(min_length=1, max_length=255)
    score: int = Field(ge=1, le=5)
    feedback: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_target_id(self):
        if self.target_type == "prompt" and not self.prompt_id:
            raise ValueError("prompt_id is required for a prompt review")
        if self.target_type == "chat" and not self.chat_id:
            raise ValueError("chat_id is required for a chat review")
        return self
