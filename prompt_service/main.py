import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from prompt_service.database import init_db
from prompt_service.document_config import (
    FILE_CONNECT_TIMEOUT,
    FILE_READ_TIMEOUT,
    FILE_SERVICE_URL,
)
from prompt_service.llm_config import (
    LLM_CONNECT_TIMEOUT,
    LLM_READ_TIMEOUT,
    LLM_SERVICE_URL,
)
from prompt_service.views.chat_routes import router as chat_router
from prompt_service.views.prompt_routes import router as prompt_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(init_db)
    llm_timeout = httpx.Timeout(
        connect=LLM_CONNECT_TIMEOUT,
        read=LLM_READ_TIMEOUT,
        write=30.0,
        pool=5.0,
    )
    file_timeout = httpx.Timeout(
        connect=FILE_CONNECT_TIMEOUT,
        read=FILE_READ_TIMEOUT,
        write=30.0,
        pool=5.0,
    )
    app.state.llm_client = httpx.AsyncClient(
        base_url=LLM_SERVICE_URL.rstrip("/"),
        timeout=llm_timeout,
    )
    app.state.file_client = httpx.AsyncClient(
        base_url=FILE_SERVICE_URL.rstrip("/"),
        timeout=file_timeout,
    )
    try:
        yield
    finally:
        await app.state.llm_client.aclose()
        await app.state.file_client.aclose()


app = FastAPI(title="Prompt Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prompt_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "Prompt Service is running"}
