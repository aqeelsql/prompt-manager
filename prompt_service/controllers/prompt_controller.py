from fastapi import HTTPException
from prompt_service.models import prompt_model

def row_to_prompt(row):
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "content": row[3],
        "tags": row[4],
        "model_target": row[5],
        "created_at": row[6],
        "updated_at": row[7]
    }

def create_prompt_controller(data):
    row = prompt_model.create_prompt(data)
    return row_to_prompt(row)

def list_prompts_controller(tag=None, limit=50):
    rows = prompt_model.get_all_prompts(tag, limit)
    return [row_to_prompt(row) for row in rows]

def get_prompt_controller(prompt_id):
    row = prompt_model.get_prompt_by_id(prompt_id)

    if not row:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return row_to_prompt(row)

def update_prompt_controller(prompt_id, data):
    row = prompt_model.update_prompt(prompt_id, data)

    if not row:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return row_to_prompt(row)

def delete_prompt_controller(prompt_id):
    row = prompt_model.delete_prompt(prompt_id)

    if not row:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return {"message": "Prompt deleted successfully"}

def prompt_exists_controller(prompt_id):
    row = prompt_model.get_prompt_by_id(prompt_id)
    return {"exists": row is not None}