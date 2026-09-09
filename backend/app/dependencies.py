from collections.abc import Generator

from .database import get_db
from .services.gemini_service import GeminiService


def get_gemini_service() -> Generator[GeminiService, None, None]:
    yield GeminiService()
