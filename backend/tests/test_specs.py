"""매트릭스 밖에서 02-specs 조항을 확인하는 테스트."""

from google import genai
from sqlalchemy import text

from app import gemini
from app.database import engine
from tests.conftest import FIXTURES, MEETING_BODY, SHORT_BODY, make_note


# 1.1 AUTOINCREMENT 가 실제 테이블에 들어가 있고, 지운 id 를 다시 쓰지 않는다
def test_autoincrement_in_ddl_and_ids_not_reused(client):
    with engine.connect() as conn:
        ddl = conn.execute(text("SELECT sql FROM sqlite_master WHERE name = 'meetings'")).scalar_one()
    assert "AUTOINCREMENT" in ddl
    first = make_note(client)
    client.delete(f"/api/notes/{first['id']}")
    second = make_note(client)
    assert second["id"] > first["id"]


# 4절 body · met_at 누락도 400
def test_missing_body_or_met_at_returns_400(client):
    assert client.post("/api/notes", json={"title": "회의", "met_at": "2026-11-10T01:00:00Z"}).status_code == 400
    assert client.post("/api/notes", json={"title": "회의", "body": "본문"}).status_code == 400


# 5절 met_at 은 UTC 로 저장 - 시간대가 붙은 값은 UTC 로 바꿔 돌려준다
def test_met_at_is_stored_as_utc(client):
    note = make_note(client, met_at="2026-11-10T10:00:00+09:00")
    assert note["met_at"] == "2026-11-10T01:00:00Z"


# 6절 from · to 는 양끝 포함, to 는 그날 23:59:59 까지. 화면의 로컬 날짜 기준
def test_date_range_inclusive_in_local_dates(client):
    # 한국(UTC+9, getTimezoneOffset = -540) 로컬 11/10 00:00 ~ 23:59
    start = make_note(client, title="자정", met_at="2026-11-09T15:00:00Z")  # 로컬 11/10 00:00
    end = make_note(client, title="막판", met_at="2026-11-10T14:59:59Z")  # 로컬 11/10 23:59:59
    make_note(client, title="다음날", met_at="2026-11-10T15:00:00Z")  # 로컬 11/11 00:00
    make_note(client, title="전날", met_at="2026-11-09T14:59:59Z")  # 로컬 11/09 23:59:59
    response = client.get("/api/notes", params={"from": "2026-11-10", "to": "2026-11-10", "tz_offset": -540})
    assert {item["id"] for item in response.json()} == {start["id"], end["id"]}


# 3.1 할 일은 회의 날짜 오래된 순
def test_todos_sorted_by_meeting_date_ascending(client):
    newer = make_note(client, title="나중 회의", met_at="2026-11-12T01:00:00Z")
    older = make_note(client, title="먼저 회의", met_at="2026-11-01T01:00:00Z")
    for note, todo in ((newer, "나중 일 | 김민수 | 모레"), (older, "먼저 일 | 미정 | 내일")):
        client.put(f"/api/notes/{note['id']}", json={
            "title": note["title"], "met_at": note["met_at"], "body": note["body"], "todos": todo})
    titles = [item["note_title"] for item in client.get("/api/todos").json()]
    assert titles == ["먼저 회의", "나중 회의"]


# 7.1 본문이 20자 미만이면 구분하지 않고 세 칸을 비운다
def test_short_body_leaves_three_way_empty(client):
    note = make_note(client, body=SHORT_BODY)
    assert (note["summary"], note["decisions"], note["todos"]) == ("", "", "")


# 7.1 회의 내용이 아니면 세 칸을 비운다 (실제 Gemini)
def test_non_meeting_body_leaves_three_way_empty(client, gemini_pause):
    body = "오늘 저녁 메뉴는 김치찌개와 계란말이입니다. 재료는 김치, 돼지고기, 두부, 계란 네 개가 필요합니다."
    note = make_note(client, body=body)
    assert (note["summary"], note["decisions"], note["todos"]) == ("", "", "")


# 7.1 구분이 실패해도 201 로 저장하고 세 칸을 비운다 - 잘못된 키로 실제 호출을 실패시킨다
def test_classify_failure_still_saves_201(client, monkeypatch, gemini_pause):
    monkeypatch.setattr(gemini, "_client", genai.Client(api_key="invalid-key-for-test"))
    note = make_note(client, body=MEETING_BODY)
    assert (note["summary"], note["decisions"], note["todos"]) == ("", "", "")
    assert client.get(f"/api/notes/{note['id']}").json()["body"] == MEETING_BODY


# 3절 업로드 성공 - 실제 녹취 파일을 실제 Gemini 로 받아쓴다
def test_upload_wav_transcribes(client, gemini_pause):
    audio = (FIXTURES / "meeting.wav").read_bytes()
    response = client.post("/api/upload", files={"file": ("meeting.wav", audio, "audio/wav")})
    assert response.status_code == 200, response.text
    assert "기획" in response.json()["body"]


# 7.2 업로드의 외부 호출이 실패하면 502
def test_upload_external_failure_returns_502(client, monkeypatch, gemini_pause):
    monkeypatch.setattr(gemini, "_client", genai.Client(api_key="invalid-key-for-test"))
    audio = (FIXTURES / "meeting.wav").read_bytes()
    response = client.post("/api/upload", files={"file": ("meeting.wav", audio, "audio/wav")})
    assert response.status_code == 502
