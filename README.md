# MeetingNote

회의록 자동 정리 풀스택 웹 앱. 녹취 파일을 올리면 받아쓰고,
요약 · 결정사항 · 할 일 세 갈래로 구분해 저장한다.

## 무엇을 하나

- 녹취 파일 업로드 (mp3 · wav, 25MB 이하) 또는 메모 붙여넣기
- 받아쓴 본문을 요약 / 결정사항 / 할 일 세 갈래로 구분
- 회의록 CRUD 4종 (추가 · 목록 · 수정 · 삭제)
- 제목 · 참석자 · 날짜로 검색
- 할 일만 모아 보는 화면 (담당자 · 기한)
- 라이트 / 다크 테마 토글, 360px 반응형

범위 밖 - 실시간 녹음, 화자 자동 구분, 외부 캘린더 연동, 메일 발송.
자세한 것은 `docs/01-product.md`.

## 기술 스택

| 영역 | 스택 |
|---|---|
| 백엔드 `backend/` | FastAPI + Python 3.11 이상 + SQLite (SQLAlchemy) |
| 프론트 `frontend/` | Vanilla JS + Tailwind CDN (`index.html` · `app.js` 2개) |
| 받아쓰기 | Gemini API (`gemini-3.1-flash-lite`) |
| 테스트 | pytest |

선택 근거와 트레이드오프는 `docs/03-design.md`.

## 실행

```powershell
# 1. 키 등록 - 저장소에 올리지 않는다
#    .env 에 GEMINI_API_KEY 와 GEMINI_MODEL 두 줄

# 2. 의존성
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# 3. 서버 - 포트는 8000 고정
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

- 화면 http://127.0.0.1:8000/
- Swagger http://127.0.0.1:8000/docs

프론트는 백엔드가 같은 오리진에서 제공한다. `file://` 로 직접 열지 않는다
(`docs/03-design.md` #2).

## API 7개

| 메서드 · 경로 | 성공 | 하는 일 |
|---|---|---|
| `POST /api/notes` | 201 | 저장하며 세 갈래 구분까지 |
| `GET /api/notes` | 200 | 목록 (`q` · `from` · `to`). body 제외 |
| `GET /api/notes/{id}` | 200 | 단건. body 포함 |
| `PUT /api/notes/{id}` | 200 | 수정 |
| `DELETE /api/notes/{id}` | 204 | 삭제 |
| `GET /api/todos` | 200 | 할 일 모아 보기 |
| `POST /api/upload` | 200 | 녹취 파일을 받아 본문 텍스트로 |

오류 코드 - 검증 실패 400 / 없는 id 404 / 스펙 외 필드 422 /
지원 않는 형식 415 / 25MB 초과 413 / 외부 호출 실패 502.
자세한 것은 `docs/02-specs.md`.

## 테스트

```powershell
cd backend
.\.venv\Scripts\python -m pytest tests -q
```

`docs/05-conventions.md` 의 테스트 매트릭스 13케이스와 1:1로 대응한다.
테스트는 실제 Gemini 를 부른다 (대역으로 바꾸지 않는다).

## 문서

| 파일 | 역할 |
|---|---|
| `CLAUDE.md` | 역할 · 기술 스택 · 읽기 순서 · 절대규칙 6개 |
| `docs/00-overview.md` | 문서 지도와 읽는 순서 |
| `docs/01-product.md` | WHY - 목표 · 페르소나 · 범위 · 성공 기준 |
| `docs/02-specs.md` | WHAT - 모델 · 구분 기준 · API · 검증 |
| `docs/03-design.md` | HOW - 기술 결정 8개 · 화면 요소 이름 · 의존성 정책 |
| `docs/04-tasks.md` | 구현 순서 - Phase 3단계 체크리스트 |
| `docs/05-conventions.md` | 명명 · 금지 6개 · 테스트 매트릭스 · 커밋 규칙 |

화면 배치와 요소 id 는 `docs/화면구성.pdf` 가 근거다.
