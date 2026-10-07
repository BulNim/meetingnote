from datetime import datetime
from pathlib import Path

import gemini_service
from conftest import gemini_gap

SAMPLE_WAV = Path(__file__).parent / "sample.wav"

MEETING_BODY = (
    "오늘 기획 회의에서 신규 웹사이트를 금요일에 출시하기로 확정했습니다. "
    "디자인 시안은 아직 의견이 갈려서 정하지 못했습니다. "
    "김대리가 다음 주 월요일까지 출시 보고서를 작성합니다."
)


# ---------- 테스트 매트릭스 13케이스 (docs/05-conventions.md) ----------


def test_create_note_real_gemini(client):
    gemini_gap()
    response = client.post(
        "/api/notes",
        json={
            "title": "기획 회의",
            "met_at": "2026-05-01T09:00:00+09:00",
            "attendees": "김대리, 이주임",
            "body": MEETING_BODY,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    # 실제 Gemini 로 세 갈래가 구분되어 저장되었는지 확인한다
    assert data["summary"].strip()
    assert data["decisions"].strip()
    assert "|" in data["todos"]
    # 새로고침(재조회)해도 유지된다
    again = client.get(f"/api/notes/{data['id']}").json()
    assert again["summary"] == data["summary"]
    assert again["todos"] == data["todos"]


def test_list_notes_has_no_body(client, make_note):
    make_note(title="목록 확인용")
    response = client.get("/api/notes")
    assert response.status_code == 200
    items = response.json()
    assert items
    assert all("body" not in item for item in items)


def test_get_note_has_body(client, make_note):
    note = make_note(title="단건 확인용", body="단건 본문")
    response = client.get(f"/api/notes/{note.id}")
    assert response.status_code == 200
    assert response.json()["body"] == "단건 본문"


def test_update_note(client, make_note):
    note = make_note(title="수정 전")
    response = client.put(
        f"/api/notes/{note.id}",
        json={
            "title": "수정 후",
            "met_at": "2026-02-02T10:00:00Z",
            "attendees": "박과장",
            "body": "수정한 본문",
            "summary": "수정한 요약",
            "decisions": "수정한 결정",
            "todos": "할 일 | 박과장 | 내일",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "수정 후"
    assert data["summary"] == "수정한 요약"
    assert client.get(f"/api/notes/{note.id}").json()["title"] == "수정 후"


def test_delete_note(client, make_note):
    note = make_note(title="삭제용")
    response = client.delete(f"/api/notes/{note.id}")
    assert response.status_code == 204
    assert client.get(f"/api/notes/{note.id}").status_code == 404


def test_search_matches_title_and_attendees_only(client, make_note):
    in_title = make_note(title="기획 킥오프", attendees="김대리")
    in_attendees = make_note(title="주간 점검", attendees="박기획, 이주임")
    in_body_only = make_note(title="무관한 회의", attendees="최사원", body="기획 이야기만 본문에 있음")
    response = client.get("/api/notes", params={"q": "기획"})
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert in_title.id in ids
    assert in_attendees.id in ids
    assert in_body_only.id not in ids
    for item in response.json():
        assert "기획" in item["title"] or "기획" in (item["attendees"] or "")


def test_todos_ok(client):
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_missing_title_returns_400(client):
    response = client.post(
        "/api/notes", json={"met_at": "2026-05-01T09:00:00Z", "body": "본문"}
    )
    assert response.status_code == 400


def test_create_bad_met_at_returns_400(client):
    response = client.post(
        "/api/notes", json={"title": "제목", "met_at": "어제쯤", "body": "본문"}
    )
    assert response.status_code == 400


def test_get_unknown_id_returns_404(client):
    assert client.get("/api/notes/999999").status_code == 404


def test_create_extra_field_returns_422(client):
    response = client.post(
        "/api/notes",
        json={
            "title": "제목",
            "met_at": "2026-05-01T09:00:00Z",
            "body": "본문",
            "unknown_field": "x",
        },
    )
    assert response.status_code == 422


def test_upload_mp4_returns_415(client):
    response = client.post("/api/upload", files={"file": ("a.mp4", b"abc", "video/mp4")})
    assert response.status_code == 415


def test_upload_30mb_returns_413(client):
    big = b"\0" * (30 * 1024 * 1024)
    response = client.post("/api/upload", files={"file": ("big.wav", big, "audio/wav")})
    assert response.status_code == 413


# ---------- 추가 검증 (04-tasks.md 각 단계의 검증 방법) ----------


def test_id_is_not_reused_after_delete(client, make_note):
    first = make_note(title="id 재사용 확인")
    client.delete(f"/api/notes/{first.id}")
    second = make_note(title="id 재사용 확인 2")
    assert second.id > first.id


def test_met_at_is_returned_as_utc(client):
    gemini_gap()
    note_id = client.post(
        "/api/notes",
        json={"title": "UTC 확인", "met_at": "2026-05-01T09:00:00+09:00", "body": "짧은 메모"},
    ).json()["id"]
    assert client.get(f"/api/notes/{note_id}").json()["met_at"] == "2026-05-01T00:00:00Z"


def test_date_range_is_inclusive(client, make_note):
    inside_start = make_note(title="범위 시작", met_at=datetime(2026, 3, 10, 0, 0, 0))
    inside_end = make_note(title="범위 끝", met_at=datetime(2026, 3, 10, 23, 59, 59))
    outside = make_note(title="범위 밖", met_at=datetime(2026, 3, 11, 0, 0, 0))
    response = client.get(
        "/api/notes", params={"q": "범위", "from": "2026-03-10", "to": "2026-03-10"}
    )
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert ids == {inside_start.id, inside_end.id}
    assert outside.id not in ids


def test_bad_date_query_returns_400(client):
    assert client.get("/api/notes", params={"from": "2026/03/10"}).status_code == 400


def test_todos_sorted_by_meeting_date_and_missing_who(client, make_note):
    later = make_note(
        title="할일정렬 나중", met_at=datetime(2026, 4, 20), todos="나중 일 | 이주임 | 다음 주 금요일"
    )
    earlier = make_note(
        title="할일정렬 먼저", met_at=datetime(2026, 4, 1), todos="먼저 일 |  | 이번 주 안"
    )
    items = [i for i in client.get("/api/todos").json() if i["note_title"].startswith("할일정렬")]
    assert [i["note_id"] for i in items] == [earlier.id, later.id]
    assert items[0] == {
        "what": "먼저 일",
        "who": "미정",
        "when": "이번 주 안",
        "note_id": earlier.id,
        "note_title": "할일정렬 먼저",
    }
    assert items[1]["when"] == "다음 주 금요일"


def test_split_failure_still_saves_with_201(client, monkeypatch):
    def fail(body):
        raise RuntimeError("구분 실패 시뮬레이션")

    monkeypatch.setattr(gemini_service, "split_note", fail)
    response = client.post(
        "/api/notes",
        json={"title": "구분 실패", "met_at": "2026-05-01T09:00:00Z", "body": "본문"},
    )
    assert response.status_code == 201
    data = response.json()
    assert (data["summary"], data["decisions"], data["todos"]) == ("", "", "")


def test_upload_wav_transcribes_with_real_gemini(client):
    gemini_gap()
    with SAMPLE_WAV.open("rb") as f:
        response = client.post("/api/upload", files={"file": ("sample.wav", f, "audio/wav")})
    assert response.status_code == 200
    text = response.json()["text"]
    assert "금요일" in text or "출시" in text


def test_upload_returns_502_when_gemini_fails(client, monkeypatch):
    def fail(data, mime_type):
        raise RuntimeError("받아쓰기 실패 시뮬레이션")

    monkeypatch.setattr(gemini_service, "transcribe_audio", fail)
    response = client.post("/api/upload", files={"file": ("a.mp3", b"abc", "audio/mpeg")})
    assert response.status_code == 502
