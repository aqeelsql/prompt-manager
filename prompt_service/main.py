from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prompt_service.database import init_db
from prompt_service.views.prompt_routes import router as prompt_router

app = FastAPI(title="Prompt Service")

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

app.include_router(prompt_router)

@app.get("/")
def root():
    return {"message": "Prompt Service is running"}