from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from backend.app.database import Base, get_db
from backend.app.dependencies import get_gemini_service
from backend.app.main import app
from backend.app.services.gemini_service import AnalysisResult


class FakeGemini:
    def analyze_text(self, body: str) -> AnalysisResult:
        return AnalysisResult(
            summary="회의 요약",
            decisions="일정 확정",
            todos="자료 준비| 홍길동| 2026-09-20",
        )

    def transcribe(self, data: bytes, filename: str) -> str:
        return "받아쓴 본문"


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    def override_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_gemini_service] = lambda: FakeGemini()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
