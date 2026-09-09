from datetime import datetime, timezone
from io import BytesIO

from backend.app.schemas import format_utc_datetime


def test_utc_datetime_format_is_consistent() -> None:
    value = datetime(2026, 9, 9, 1, 0, 30, 123456, tzinfo=timezone.utc)
    assert format_utc_datetime(value) == "2026-09-09T01:00:30Z"


def test_offset_datetime_formats_as_utc() -> None:
    value = datetime.fromisoformat("2026-09-09T10:00:30+09:00")
    assert format_utc_datetime(value) == "2026-09-09T01:00:30Z"




def payload() -> dict[str, str]:
    return {
        "title": "기획 회의",
        "met_at": "2026-09-09T10:00:00+09:00",
        "attendees": "홍길동, 김철수",
        "body": "기획 회의 본문",
    }


def test_normal_create(client):
    response = client.post("/api/notes", json=payload())
    assert response.status_code == 201


def test_list_excludes_body(client):
    client.post("/api/notes", json=payload())
    response = client.get("/api/notes")
    assert response.status_code == 200
    assert all("body" not in note for note in response.json())


def test_update_all_fields(client):
    created = client.post("/api/notes", json=payload()).json()
    updated = payload() | {"title": "기획 수정 회의", "attendees": "박민수"}
    response = client.put(f"/api/notes/{created['id']}", json=updated)
    assert response.status_code == 200


def test_delete(client):
    created = client.post("/api/notes", json=payload()).json()
    assert client.delete(f"/api/notes/{created['id']}").status_code == 204


def test_search_matches_title_or_attendees(client):
    client.post("/api/notes", json=payload())
    client.post(
        "/api/notes",
        json=payload() | {"title": "개발 회의", "attendees": "이영희"},
    )
    response = client.get("/api/notes", params={"q": "기획"})
    assert response.status_code == 200
    assert all("기획" in item["title"] or "기획" in item["attendees"] for item in response.json())


def test_todos(client):
    response = client.get("/api/todos")
    assert response.status_code == 200


def test_missing_title_is_400(client):
    data = payload()
    del data["title"]
    assert client.post("/api/notes", json=data).status_code == 400


def test_invalid_met_at_is_400(client):
    assert client.post("/api/notes", json=payload() | {"met_at": "invalid"}).status_code == 400


def test_missing_id_is_404(client):
    assert client.get("/api/notes/999999").status_code == 404


def test_extra_field_is_422(client):
    assert client.post("/api/notes", json=payload() | {"extra": True}).status_code == 422


def test_mp4_upload_is_415(client):
    response = client.post(
        "/api/upload",
        files={"file": ("recording.mp4", BytesIO(b"video"), "video/mp4")},
    )
    assert response.status_code == 415


def test_30mb_upload_is_413(client):
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "recording.wav",
                BytesIO(b"x" * (30 * 1024 * 1024)),
                "audio/wav",
            )
        },
    )
    assert response.status_code == 413
