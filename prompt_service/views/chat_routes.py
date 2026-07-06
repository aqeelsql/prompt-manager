from uuid import UUID

from fastapi import APIRouter, Request

from prompt_service.controllers import chat_controller
from prompt_service.schemas.chat_schema import (
    ChatMessageCreate,
    DocumentChatCreate,
    PromptExecuteRequest,
)

router = APIRouter(tags=["Chats"])


@router.post("/document-chats")
async def create_document_chat(data: DocumentChatCreate, request: Request):
    return await chat_controller.create_document_chat_controller(
        data,
        request.app.state.llm_client,
        request.app.state.file_client,
    )

@router.post("/prompts/{prompt_id}/execute")
async def execute_prompt(prompt_id: UUID, data: PromptExecuteRequest):
    return await chat_controller.execute_prompt_controller(prompt_id, data)


@router.get("/chats")
def list_chats(prompt_id: UUID | None = None):
    return chat_controller.list_chats_controller(prompt_id)


@router.get("/chats/{chat_id}")
def get_chat(chat_id: UUID):
    return chat_controller.get_chat_controller(chat_id)


@router.post("/chats/{chat_id}/messages")
async def add_chat_message(
    chat_id: UUID, data: ChatMessageCreate, request: Request
):
    return await chat_controller.add_chat_message_controller(
        chat_id,
        data,
        request.app.state.llm_client,
        request.app.state.file_client,
    )


@router.post("/chats/{chat_id}/summary")
async def summarize_chat(chat_id: UUID, request: Request):
    return await chat_controller.summarize_chat_controller(
        chat_id, request.app.state.llm_client
    )


@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: UUID):
    return chat_controller.delete_chat_controller(chat_id)
