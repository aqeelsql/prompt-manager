import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
PROMPT_SERVICE_URL = os.getenv(
    "PROMPT_SERVICE_URL", "http://localhost:8000"
)
REVIEW_SERVICE_PORT = int(os.getenv("REVIEW_SERVICE_PORT", 8001))
PROMPT_CONNECT_TIMEOUT = float(os.getenv("PROMPT_CONNECT_TIMEOUT", 5))
PROMPT_READ_TIMEOUT = float(os.getenv("PROMPT_READ_TIMEOUT", 30))
