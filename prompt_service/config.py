import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
PROMPT_SERVICE_PORT = int(os.getenv("PROMPT_SERVICE_PORT", 8000))