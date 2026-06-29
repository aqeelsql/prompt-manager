from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from review_service.database import init_db
from review_service.views.review_routes import router as review_router

app = FastAPI(title="Review Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(review_router)

@app.get("/")
def root():
    return {"message": "Review Service is running"}