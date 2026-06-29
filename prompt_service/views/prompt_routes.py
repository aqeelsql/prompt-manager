from fastapi import APIRouter, Query
from uuid import UUID
from prompt_service.schemas.prompt_schema import PromptCreate, PromptUpdate
from prompt_service.controllers import prompt_controller

router = APIRouter(prefix="/prompts", tags=["Prompts"])

@router.post("/")
def create_prompt(data: PromptCreate):
    return prompt_controller.create_prompt_controller(data)

@router.get("/")
def list_prompts(tag: str | None = None, limit: int = Query(50, ge=1)):
    return prompt_controller.list_prompts_controller(tag, limit)

@router.get("/{prompt_id}")
def get_prompt(prompt_id: UUID):
    return prompt_controller.get_prompt_controller(prompt_id)

@router.put("/{prompt_id}")
def update_prompt(prompt_id: UUID, data: PromptUpdate):
    return prompt_controller.update_prompt_controller(prompt_id, data)

@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: UUID):
    return prompt_controller.delete_prompt_controller(prompt_id)

@router.get("/{prompt_id}/exists")
def prompt_exists(prompt_id: UUID):
    return prompt_controller.prompt_exists_controller(prompt_id)