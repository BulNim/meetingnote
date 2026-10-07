import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# .env 는 프로젝트 루트에 둔다
load_dotenv(BASE_DIR.parent / ".env")

DATABASE_URL = f"sqlite:///{BASE_DIR / 'meetingnote.db'}"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"


def get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 가 비어 있습니다. .env 에 키를 입력하세요.")
    return key


def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
