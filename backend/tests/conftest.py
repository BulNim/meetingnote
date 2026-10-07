import sys
import time
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# backend/ 를 import 경로에 넣는다
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
from models import Meeting  # noqa: E402


def gemini_gap() -> None:
    """Gemini 를 부르는 테스트는 한도에 걸리지 않게 호출 사이를 1초쯤 띄운다."""
    time.sleep(1)


@pytest.fixture(scope="session")
def session_factory(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_note(session_factory):
    """Gemini 를 거치지 않고 DB 에 바로 회의록을 넣는다."""

    def _make(**fields) -> Meeting:
        data = {
            "title": "테스트 회의",
            "met_at": datetime(2026, 1, 1, 0, 0, 0),
            "attendees": None,
            "body": "본문",
            "summary": "",
            "decisions": "",
            "todos": "",
        }
        data.update(fields)
        with session_factory() as db:
            meeting = Meeting(**data)
            db.add(meeting)
            db.commit()
            return meeting

    return _make
