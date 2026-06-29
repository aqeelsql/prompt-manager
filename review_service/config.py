import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
PROMPT_SERVICE_URL = os.getenv("PROMPT_SERVICE_URL", "http://localhost:8000")
REVIEW_SERVICE_PORT = int(os.getenv("REVIEW_SERVICE_PORT", 8001))