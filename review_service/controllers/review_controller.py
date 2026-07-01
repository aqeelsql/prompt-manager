import asyncio
import json

import httpx
from fastapi import HTTPException

from review_service.models import review_model


def row_to_review(row):
    target_type = row[1]
    stored_snapshot = row[4]
    snapshot = stored_snapshot
    if target_type == "chat":
        try:
            snapshot = json.loads(stored_snapshot)
        except (TypeError, json.JSONDecodeError):
            snapshot = stored_snapshot

    return {
        "id": row[0],
        "target_type": target_type,
        "prompt_id": row[2],
        "chat_id": row[3],
        "snapshot": snapshot,
        "prompt_snapshot": stored_snapshot,
        "reviewer_name": row[5],
        "score": row[6],
        "feedback": row[7],
        "reviewed_at": row[8],
    }


async def _fetch_from_prompt_service(client, path, target_name):
    try:
        response = await client.get(path)
    except httpx.ReadTimeout as exc:
        raise HTTPException(
            status_code=504, detail="Prompt service timed out"
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503, detail="Prompt service is unavailable"
        ) from exc

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"{target_name} not found")
    if response.status_code >= 400:
        raise HTTPException(
            status_code=503, detail="Prompt service returned an error"
        )
    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502, detail="Prompt service returned invalid JSON"
        ) from exc


async def create_review_controller(data, client):
    if data.target_type == "chat":
        chat = await _fetch_from_prompt_service(
            client, f"/chats/{data.chat_id}", "Chat"
        )
        prompt_id = chat["prompt_id"]
        snapshot = chat
    else:
        prompt = await _fetch_from_prompt_service(
            client, f"/prompts/{data.prompt_id}", "Prompt"
        )
        prompt_id = data.prompt_id
        snapshot = prompt["content"]

    row = await asyncio.to_thread(
        review_model.create_review, data, prompt_id, snapshot
    )
    return row_to_review(row)


def list_reviews_controller(prompt_id=None, chat_id=None):
    rows = review_model.get_all_reviews(prompt_id, chat_id)
    return [row_to_review(row) for row in rows]


def get_review_controller(review_id):
    row = review_model.get_review_by_id(review_id)
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
    return row_to_review(row)


def _summary(rows, target_key, target_id):
    if not rows:
        raise HTTPException(
            status_code=404, detail="No reviews found for this target"
        )
    scores = [row[6] for row in rows]
    return {
        target_key: target_id,
        "average_score": round(sum(scores) / len(scores), 2),
        "total_reviews": len(rows),
        "feedback": [row[7] for row in rows],
    }


def prompt_review_summary_controller(prompt_id):
    rows = review_model.get_all_reviews(
        prompt_id=prompt_id, target_type="prompt"
    )
    return _summary(rows, "prompt_id", prompt_id)


def chat_review_summary_controller(chat_id):
    rows = review_model.get_all_reviews(
        chat_id=chat_id, target_type="chat"
    )
    return _summary(rows, "chat_id", chat_id)


def delete_review_controller(review_id):
    if not review_model.delete_review(review_id):
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Review deleted successfully"}
