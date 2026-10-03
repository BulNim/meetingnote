"""05-conventions 테스트 매트릭스 13케이스.

테스트 이름이 곧 매트릭스다. 실제 Gemini 를 부른다 (대역 없음).
"""
import io

BODY = (
    "오늘은 2차 스프린트 계획 회의입니다. 참석자는 김대리, 박과장, 이주임입니다.\n"
    "검색은 제목과 참석자 두 가지만 하기로 했습니다.\n"
    "업로드 용량은 25MB 로 고정합니다.\n"
    "김대리는 목록 화면과 검색을 다음 주 금요일까지 끝내 주세요.\n"
)


def _payload(**over):
    data = {
        "title": "2차 스프린트 기획 회의",
        "met_at": "2026-10-01T10:00:00",
        "attendees": "김대리, 박과장, 이주임",
        "body": BODY,
    }
    data.update(over)
    return data


def test_01_정상_생성은_201(client):
    r = client.post("/api/notes", json=_payload())
    assert r.status_code == 201, r.text
    assert r.json()["id"] > 0


def test_02_목록은_body_없음(client):
    r = client.get("/api/notes")
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert "body" not in r.json()[0]


def test_03_단건은_body_있음(client):
    note_id = client.get("/api/notes").json()[0]["id"]
    r = client.get(f"/api/notes/{note_id}")
    assert r.status_code == 200
    assert "body" in r.json()


def test_04_수정은_200(client):
    note_id = client.get("/api/notes").json()[0]["id"]
    r = client.put(f"/api/notes/{note_id}", json=_payload(title="제목 고침"))
    assert r.status_code == 200
    assert r.json()["title"] == "제목 고침"


def test_05_삭제는_204(client):
    created = client.post("/api/notes", json=_payload(title="지울 회의")).json()
    r = client.delete(f"/api/notes/{created['id']}")
    assert r.status_code == 204
    assert r.content == b""


def test_06_검색은_제목_참석자만(client):
    r = client.get("/api/notes", params={"q": "기획"})
    assert r.status_code == 200
    for row in r.json():
        assert "기획" in row["title"] or "기획" in (row["attendees"] or "")
    # 본문에만 있는 말은 걸리지 않는다
    assert client.get("/api/notes", params={"q": "스프린트 계획 회의입니다"}).json() == []


def test_07_할일_목록은_200(client):
    r = client.get("/api/todos")
    assert r.status_code == 200
    if r.json():
        assert set(r.json()[0]) == {"what", "who", "when", "note_id", "note_title"}


def test_08_title_누락은_400(client):
    data = _payload()
    del data["title"]
    assert client.post("/api/notes", json=data).status_code == 400


def test_09_met_at_형식오류는_400(client):
    assert client.post("/api/notes", json=_payload(met_at="어제쯤")).status_code == 400


def test_10_없는_id_는_404(client):
    assert client.get("/api/notes/99999").status_code == 404


def test_11_스펙외_필드는_422(client):
    assert client.post("/api/notes", json=_payload(owner="나")).status_code == 422


def test_12_mp4_업로드는_415(client):
    files = {"file": ("회의.mp4", io.BytesIO(b"0" * 1024), "video/mp4")}
    assert client.post("/api/upload", files=files).status_code == 415


def test_13_30MB_업로드는_413(client):
    files = {"file": ("회의.wav", io.BytesIO(b"0" * 30 * 1024 * 1024), "audio/wav")}
    assert client.post("/api/upload", files=files).status_code == 413
