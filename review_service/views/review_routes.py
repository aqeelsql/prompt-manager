from uuid import UUID

from fastapi import APIRouter, Request

from review_service.controllers import review_controller
from review_service.schemas.review_schema import ReviewCreate

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/")
async def create_review(data: ReviewCreate, request: Request):
    return await review_controller.create_review_controller(
        data, request.app.state.prompt_client
    )


@router.get("/")
def list_reviews(
    prompt_id: UUID | None = None,
    chat_id: UUID | None = None,
):
    return review_controller.list_reviews_controller(prompt_id, chat_id)


@router.get("/chat/{chat_id}/summary")
def chat_review_summary(chat_id: UUID):
    return review_controller.chat_review_summary_controller(chat_id)


@router.get("/{prompt_id}/summary")
def prompt_review_summary(prompt_id: UUID):
    return review_controller.prompt_review_summary_controller(prompt_id)


@router.get("/{review_id}")
def get_review(review_id: UUID):
    return review_controller.get_review_controller(review_id)


@router.delete("/{review_id}")
def delete_review(review_id: UUID):
    return review_controller.delete_review_controller(review_id)
