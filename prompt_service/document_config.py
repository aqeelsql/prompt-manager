import os

from dotenv import load_dotenv

load_dotenv()

FILE_SERVICE_URL = os.getenv("FILE_SERVICE_URL", "http://localhost:8003")
FILE_CONNECT_TIMEOUT = float(os.getenv("FILE_CONNECT_TIMEOUT", "5"))
FILE_READ_TIMEOUT = float(os.getenv("FILE_READ_TIMEOUT", "30"))
MAX_DOCUMENT_CONTEXT_CHARS = int(
    os.getenv("MAX_DOCUMENT_CONTEXT_CHARS", "100000")
)
