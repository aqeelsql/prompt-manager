import os

from dotenv import load_dotenv

load_dotenv()

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8002")
LLM_CONNECT_TIMEOUT = float(os.getenv("LLM_CONNECT_TIMEOUT", 5))
LLM_READ_TIMEOUT = float(os.getenv("LLM_READ_TIMEOUT", 120))
