from io import BytesIO

from backend.app.services.gemini_service import normalize_todos


def note_payload() -> dict[str, str]:
    return {
        "title": "기획 회의",
        "met_at": "2026-09-09T10:00:00+09:00",
        "attendees": "홍길동, 김철수",
        "body": "회의 원문",
    }


def test_normalize_todos_from_gemini_array() -> None:
    value = "['목록 화면 및 검색 기능 개발 완료|김대리|다음 주 금요일', '받아쓰기 오류 처리 마무리|이주임|이번 주 내']"
    assert normalize_todos(value) == (
        "목록 화면 및 검색 기능 개발 완료|김대리|다음 주 금요일\\n"
        "받아쓰기 오류 처리 마무리|이주임|이번 주 내"
    )


def test_create_list_detail_update_delete(client):
    response = client.post("/api/notes", json=note_payload())
    assert response.status_code == 201
    note_id = response.json()["id"]
    assert response.json()["summary"] == "회의 요약"

    response = client.get("/api/notes")
    assert response.status_code == 200
    assert "body" not in response.json()[0]

    response = client.get(f"/api/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["body"] == "회의 원문"

    updated = note_payload() | {"title": "수정 회의"}
    assert client.put(f"/api/notes/{note_id}", json=updated).status_code == 200
    assert client.delete(f"/api/notes/{note_id}").status_code == 204
    assert client.get(f"/api/notes/{note_id}").status_code == 404


def test_search_and_todos(client):
    client.post("/api/notes", json=note_payload())
    assert len(client.get("/api/notes?q=기획").json()) == 1
    assert client.get("/api/notes?q=없는회의").json() == []
    todos = client.get("/api/todos")
    assert todos.status_code == 200
    assert todos.json()[0]["who"] == "홍길동"


def test_validation_status_codes(client):
    payload = note_payload()
    payload.pop("title")
    assert client.post("/api/notes", json=payload).status_code == 400
    payload = note_payload() | {"unknown": "value"}
    assert client.post("/api/notes", json=payload).status_code == 422
    payload = note_payload() | {"met_at": "not-a-date"}
    assert client.post("/api/notes", json=payload).status_code == 400
    assert client.get("/api/notes/999").status_code == 404


def test_upload_validation(client):
    response = client.post(
        "/api/upload", files={"file": ("audio.mp3", BytesIO(b"audio"), "audio/mpeg")}
    )
    assert response.status_code == 200
    assert response.json()["text"] == "받아쓴 본문"

    response = client.post(
        "/api/upload", files={"file": ("audio.mp4", BytesIO(b"video"), "video/mp4")}
    )
    assert response.status_code == 415

    response = client.post(
        "/api/upload",
        files={"file": ("audio.wav", BytesIO(b"x" * (25 * 1024 * 1024 + 1)), "audio/wav")},
    )
    assert response.status_code == 413
