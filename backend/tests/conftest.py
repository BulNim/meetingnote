"""테스트 공통 준비. Gemini 는 대역 없이 실제로 부른다 (05-conventions 4.1)."""

import os
import tempfile
import time
from pathlib import Path

# 앱을 불러오기 전에 테스트용 DB 로 돌린다
_TEST_DB = Path(tempfile.gettempdir()) / "meetingnote_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"

GEMINI_PAUSE_SECONDS = 1

MEETING_BODY = (
    "신제품 기획 회의를 시작하겠습니다. 출시일은 다음 달 15일로 확정했습니다. "
    "광고 예산 5천만 원도 승인되었습니다. 김민수 님이 다음 주 금요일까지 상세 기획서를 작성하기로 했습니다. "
    "이수진 님은 이번 주 목요일까지 디자인 시안을 공유해 주세요. 점심은 뭐 먹을까요? 이상으로 회의를 마치겠습니다."
)

# 20자 미만 - 구분을 부르지 않는다
SHORT_BODY = "짧은 메모"


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def gemini_pause():
    """Gemini 를 부르는 테스트 뒤에 1초 띄워 한도에 걸리지 않게 한다."""
    yield
    time.sleep(GEMINI_PAUSE_SECONDS)


def make_note(client: TestClient, **overrides) -> dict:
    payload = {
        "title": "주간 회의",
        "met_at": "2026-11-10T01:00:00Z",
        "attendees": "김민수, 이수진",
        "body": SHORT_BODY,
    }
    payload.update(overrides)
    response = client.post("/api/notes", json=payload)
    assert response.status_code == 201, response.text
    return response.json()
