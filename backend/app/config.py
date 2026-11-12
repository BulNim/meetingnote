"""설정값. 키와 모델은 프로젝트 루트의 .env 에서만 읽는다."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"

load_dotenv(PROJECT_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'meetingnote.db'}")

# 업로드 제한 (02-specs 4절)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {".mp3": "audio/mp3", ".wav": "audio/wav"}

# 이보다 짧은 본문은 구분을 부르지 않는다 (02-specs 7.1)
MIN_CLASSIFY_LENGTH = 20
