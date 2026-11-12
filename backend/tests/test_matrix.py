"""05-conventions 4절 테스트 매트릭스 15케이스."""

from google import genai
from google.genai import types

from app import gemini

from tests.conftest import FIXTURES, MEETING_BODY, make_note


# 1. 정상 생성 - 실제 Gemini 로 세 갈래까지
def test_01_create_returns_201_with_three_way(client, gemini_pause):
    response = client.post(
        "/api/notes",
        json={"title": "신제품 기획 회의", "met_at": "2026-11-10T01:00:00Z", "attendees": "김민수, 이수진", "body": MEETING_BODY},
    )
    assert response.status_code == 201, response.text
    note = response.json()
    assert note["id"] >= 1
    assert note["summary"].strip()
    assert note["decisions"].strip()
    todo_lines = note["todos"].splitlines()
    assert todo_lines
    assert all(line.count(" | ") == 2 for line in todo_lines)


# 2. 목록 - body 없음
def test_02_list_excludes_body(client):
    make_note(client)
    response = client.get("/api/notes")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert "body" not in items[0]


# 3. 단건 - body 있음
def test_03_get_includes_body(client):
    note = make_note(client)
    response = client.get(f"/api/notes/{note['id']}")
    assert response.status_code == 200
    assert response.json()["body"] == note["body"]


# 4. 수정 - 전 필드
def test_04_update_all_fields(client):
    note = make_note(client)
    payload = {
        "title": "바뀐 제목",
        "met_at": "2026-11-11T02:30:00Z",
        "attendees": "박영희",
        "body": "바뀐 본문",
        "summary": "요약 한 줄",
        "decisions": "결정 한 줄",
        "todos": "자료 정리 | 박영희 | 내일",
    }
    response = client.put(f"/api/notes/{note['id']}", json=payload)
    assert response.status_code == 200, response.text
    updated = response.json()
    for field, value in payload.items():
        if field == "met_at":
            assert updated[field] == "2026-11-11T02:30:00Z"
        else:
            assert updated[field] == value


# 5. 삭제
def test_05_delete_returns_204(client):
    note = make_note(client)
    response = client.delete(f"/api/notes/{note['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/notes/{note['id']}").status_code == 404


# 6. 검색 - 제목 · 참석자 일치만, 본문은 검색하지 않음
def test_06_search_matches_title_and_attendees_only(client):
    by_title = make_note(client, title="기획 회의", attendees="김민수")
    by_attendee = make_note(client, title="주간 회의", attendees="기획팀 이수진")
    make_note(client, title="예산 회의", attendees="박영희", body="기획 이야기만 본문에 있음")
    response = client.get("/api/notes", params={"q": "기획"})
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {by_title["id"], by_attendee["id"]}


# 7. 할 일
def test_07_todos(client):
    note = make_note(client)
    client.put(
        f"/api/notes/{note['id']}",
        json={"title": note["title"], "met_at": note["met_at"], "attendees": note["attendees"], "body": note["body"],
              "todos": "기획서 작성 | 김민수 | 다음 주 금요일"},
    )
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert response.json() == [
        {"what": "기획서 작성", "who": "김민수", "when": "다음 주 금요일", "note_id": note["id"], "note_title": note["title"]}
    ]


# 8. title 누락
def test_08_missing_title_returns_400(client):
    response = client.post("/api/notes", json={"met_at": "2026-11-10T01:00:00Z", "body": "본문"})
    assert response.status_code == 400


# 9. met_at 형식 오류
def test_09_bad_met_at_returns_400(client):
    response = client.post("/api/notes", json={"title": "회의", "met_at": "어제 오후", "body": "본문"})
    assert response.status_code == 400


# 10. 없는 id
def test_10_unknown_id_returns_404(client):
    assert client.get("/api/notes/9999").status_code == 404
    assert client.put("/api/notes/9999", json={"title": "t", "met_at": "2026-11-10T01:00:00Z", "body": "b"}).status_code == 404
    assert client.delete("/api/notes/9999").status_code == 404


# 11. 스펙 외 필드
def test_11_extra_field_returns_422(client):
    response = client.post(
        "/api/notes", json={"title": "회의", "met_at": "2026-11-10T01:00:00Z", "body": "본문", "priority": "high"}
    )
    assert response.status_code == 422


# 12. 업로드 mp4
def test_12_upload_mp4_returns_415(client):
    response = client.post("/api/upload", files={"file": ("meeting.mp4", b"\x00" * 1024, "video/mp4")})
    assert response.status_code == 415


# 13. 업로드 30MB
def test_13_upload_30mb_returns_413(client):
    response = client.post("/api/upload", files={"file": ("big.mp3", b"\x00" * (30 * 1024 * 1024), "audio/mpeg")})
    assert response.status_code == 413


def _unreachable_gemini_client() -> genai.Client:
    """닿지 않는 주소를 가리키는 실제 클라이언트 - 실제로 연결이 실패한다."""
    return genai.Client(api_key="x", http_options=types.HttpOptions(base_url="http://127.0.0.1:9", timeout=3000))


# 14. 업로드 중 Gemini 연결 실패 (02-specs 8.1 결함 1)
def test_14_upload_connection_failure_returns_502(client, monkeypatch):
    monkeypatch.setattr(gemini, "_client", _unreachable_gemini_client())
    audio = (FIXTURES / "meeting.wav").read_bytes()
    response = client.post("/api/upload", files={"file": ("meeting.wav", audio, "audio/wav")})
    assert response.status_code == 502


# 15. 저장 중 Gemini 연결 실패 (02-specs 8.1 결함 1)
def test_15_create_connection_failure_saves_201_empty(client, monkeypatch):
    monkeypatch.setattr(gemini, "_client", _unreachable_gemini_client())
    note = make_note(client, body=MEETING_BODY)
    assert (note["summary"], note["decisions"], note["todos"]) == ("", "", "")
