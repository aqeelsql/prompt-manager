import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_STORAGE = Path(__file__).resolve().parent / "uploads"
FILE_STORAGE_DIR = Path(
    os.getenv("FILE_STORAGE_DIR", str(_DEFAULT_STORAGE))
).resolve()
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "15"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
