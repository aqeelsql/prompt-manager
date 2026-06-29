import httpx
from fastapi import HTTPException
from review_service.config import PROMPT_SERVICE_URL
from review_service.models import review_model

def row_to_review(row):
    return {
        "id": row[0],
        "prompt_id": row[1],
        "prompt_snapshot": row[2],
        "reviewer_name": row[3],
        "score": row[4],
        "feedback": row[5],
        "reviewed_at": row[6]
    }

def fetch_prompt_from_prompt_service(prompt_id):
    try:
        response = httpx.get(
            f"{PROMPT_SERVICE_URL}/prompts/{prompt_id}",
            timeout=5
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Prompt not found in prompt-service")

        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="Prompt-service returned an error")

        return response.json()

    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Prompt-service is unavailable")

def create_review_controller(data):
    prompt = fetch_prompt_from_prompt_service(data.prompt_id)

    prompt_snapshot = prompt["content"]

    row = review_model.create_review(data, prompt_snapshot)

    return row_to_review(row)

def list_reviews_controller(prompt_id=None):
    rows = review_model.get_all_reviews(prompt_id)
    return [row_to_review(row) for row in rows]

def get_review_controller(review_id):
    row = review_model.get_review_by_id(review_id)

    if not row:
        raise HTTPException(status_code=404, detail="Review not found")

    return row_to_review(row)

def review_summary_controller(prompt_id):
    rows = review_model.get_all_reviews(prompt_id)

    if not rows:
        raise HTTPException(status_code=404, detail="No reviews found for this prompt")

    scores = [row[4] for row in rows]
    feedback_list = [row[5] for row in rows]

    return {
        "prompt_id": prompt_id,
        "average_score": round(sum(scores) / len(scores), 2),
        "total_reviews": len(rows),
        "feedback": feedback_list
    }