from fastapi import APIRouter
from uuid import UUID
from review_service.schemas.review_schema import ReviewCreate
from review_service.controllers import review_controller

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/")
def create_review(data: ReviewCreate):
    return review_controller.create_review_controller(data)

@router.get("/")
def list_reviews(prompt_id: UUID | None = None):
    return review_controller.list_reviews_controller(prompt_id)

@router.get("/{review_id}")
def get_review(review_id: UUID):
    return review_controller.get_review_controller(review_id)

@router.get("/{prompt_id}/summary")
def review_summary(prompt_id: UUID):
    return review_controller.review_summary_controller(prompt_id)