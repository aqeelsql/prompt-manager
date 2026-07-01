import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from review_service.config import (
    PROMPT_CONNECT_TIMEOUT,
    PROMPT_READ_TIMEOUT,
    PROMPT_SERVICE_URL,
)
from review_service.database import init_db
from review_service.views.review_routes import router as review_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(init_db)
    timeout = httpx.Timeout(
        connect=PROMPT_CONNECT_TIMEOUT,
        read=PROMPT_READ_TIMEOUT,
        write=10.0,
        pool=5.0,
    )
    app.state.prompt_client = httpx.AsyncClient(
        base_url=PROMPT_SERVICE_URL.rstrip("/"),
        timeout=timeout,
    )
    try:
        yield
    finally:
        await app.state.prompt_client.aclose()


app = FastAPI(title="Review Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router)


@app.get("/")
def root():
    return {"message": "Review Service is running"}
