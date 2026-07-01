import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(
    dotenv_path=Path(__file__).resolve().parents[1] / ".env",
    override=True,
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-oss-20b")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "openai/gpt-4o-mini")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 8002))
OPENROUTER_CONNECT_TIMEOUT = float(
    os.getenv("OPENROUTER_CONNECT_TIMEOUT", 5)
)
OPENROUTER_READ_TIMEOUT = float(os.getenv("OPENROUTER_READ_TIMEOUT", 50))
