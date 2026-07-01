import asyncio

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from file_service.config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from file_service.schemas import DocumentResponse, DocumentSummary
from file_service.storage import (
    DocumentStorageError,
    delete_document,
    get_document,
    initialize_storage,
    list_documents,
    save_document,
    validate_filename,
)

app = FastAPI(title="File Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    initialize_storage()


@app.get("/")
def root():
    return {"message": "File Service is running"}


@app.get("/health")
def health():
    return {
        "status": "ready",
        "supported_extensions": [".pdf", ".docx"],
        "max_file_size_mb": MAX_FILE_SIZE_MB,
    }


@app.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(file: UploadFile = File(...)):
    try:
        validate_filename(file.filename)
    except DocumentStorageError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    content = await file.read(MAX_FILE_SIZE_BYTES + 1)
    await file.close()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Document exceeds the {MAX_FILE_SIZE_MB} MB limit",
        )

    try:
        return await asyncio.to_thread(
            save_document, file.filename, file.content_type, content
        )
    except DocumentStorageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/documents", response_model=list[DocumentSummary])
async def documents():
    return await asyncio.to_thread(list_documents)


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def document(document_id: str):
    try:
        return await asyncio.to_thread(get_document, document_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc


@app.get("/documents/{document_id}/text")
async def document_text(document_id: str):
    try:
        stored = await asyncio.to_thread(get_document, document_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc
    return {
        "id": stored["id"],
        "filename": stored["filename"],
        "extracted_text": stored["extracted_text"],
        "character_count": stored["character_count"],
    }


@app.delete("/documents/{document_id}")
async def remove_document(document_id: str):
    try:
        deleted = await asyncio.to_thread(delete_document, document_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}
