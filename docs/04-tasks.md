# 04. Tasks

MVP 를 3개 Phase 로 진행한다. Phase 이름과 개수는 고정이며 바꾸지 않는다.

| Phase | 이름 | 단계 수 |
|---|---|---|
| 1 | 설계 | 10 |
| 2 | 백엔드 | 10 |
| 3 | 프론트 | 8 |

## 진행 규칙

- 순서대로만 진행한다. 병렬로 하지 않는다.
- 단계마다 검증 방법을 실행해 확인한 뒤 완료 열을 `[x]` 로 바꾼다.
- `backend 진행해` = Phase 2 전체. `frontend 진행해` = Phase 3 전체.
- 서버 포트는 **8000** 으로 고정한다.
- pytest 실행 시 httpx2 설치 권고가 떠도 무시한다.

## Phase 1 (설계)

CLAUDE.md + docs/ 6종 작성.

| 단계 | 검증 방법 | 완료 |
|---|---|---|
| 1.1 CLAUDE.md 작성 (역할·스택·절차·절대규칙) | 4개 섹션이 있고 docs 파일명·순서가 일치함 | [x] |
| 1.2 `.env` 작성 (`GEMINI_API_KEY`, `GEMINI_MODEL`) | 키 이름만 있고 값은 사용자가 직접 입력함 | [x] |
| 1.3 `.gitignore` 작성 | `.env` 가 제외 목록에 있음 | [x] |
| 1.4 `docs/` 에 6개 파일 생성 | 이름 6개가 `00`~`05` 와 같고 다른 파일이 없음 | [x] |
| 1.5 `00-overview.md` 작성 | 매핑표·읽는 순서·화면·분리 이유가 있음 | [x] |
| 1.6 `01-product.md` 작성 | 목표·페르소나·MVP·확장·범위 외·성공 기준이 있음 | [x] |
| 1.7 `02-specs.md` 작성 | 모델 8필드·API 7개·오류 코드가 있음 | [x] |
| 1.8 `03-design.md` 작성 | 8행 표와 의존성 정책이 있음 | [x] |
| 1.9 `04-tasks.md` 작성 | Phase 3개, 단계 수 10 / 10 / 8 | [x] |
| 1.10 `05-conventions.md` 작성 + 첫 커밋 | 파일에 내용이 있고, `git log` 에 첫 커밋이 보임 | [x] |

## Phase 2 (백엔드)

`backend/` FastAPI > API 7개 + 받아쓰기 > Swagger 확인.

의존성은 아래 8개로 한정한다. 이 목록 밖은 추가하지 않는다.

`fastapi`, `uvicorn`, `sqlalchemy`, `pytest`, `httpx`, `google-genai`, `python-multipart`, `python-dotenv`

| 단계 | 검증 방법 | 완료 |
|---|---|---|
| 2.1 `backend/` 폴더, 가상환경, 의존성 8개 설치 (`requirements.txt`) | `pip list` 에 8개만 추가됨. Python 3.11 이상 | [x] |
| 2.2 설정 로드 (`.env` 에서 키·모델 읽기) | 코드에 키 문자열이 없음 (`grep`). 키가 비면 명확한 오류 | [x] |
| 2.3 Meeting 모델 (필드 8개, `sqlite_autoincrement`) | 지운 id 가 재사용되지 않음을 테스트로 확인 | [x] |
| 2.4 요청·응답 스키마와 검증 (`extra="forbid"`, 400 핸들러) | 필수 누락 400 / 스펙 외 필드 422 / 없는 id 404 | [x] |
| 2.5 notes CRUD 5개 + 검색 (`q`, `from`, `to`) | 201 / 200 / 200 / 200 / 204, 목록에 `body` 없음, `to` 가 23:59:59 포함 | [x] |
| 2.6 `GET /api/todos` | 필드 `what`·`who`·`when`·`note_id`·`note_title`, 회의 날짜 오래된 순 | [x] |
| 2.7 `POST /api/upload` 와 Gemini 받아쓰기 | mp3·wav 외 415 / 25MB 초과 413 / 외부 호출 실패 502 | [x] |
| 2.8 세 갈래 구분 (프롬프트 + 저장 연동) | 구분 실패 시에도 201 이고 세 필드가 빈 값, 로그만 남김 | [x] |
| 2.9 pytest 전체 실행 | 전부 통과. Gemini 는 실제로 호출하고, 호출 사이를 1초쯤 띄움 (`05-conventions.md`) | [x] |
| 2.10 서버 8000 포트 실행 + Swagger 확인 | `http://localhost:8000/docs` 에서 `/api/` 경로 7개가 보임 | [x] |

## Phase 3 (프론트)

`frontend/` HTML+JS+Tailwind > 화면 4종 > API 연결 > git push.

화면 4종은 `02-specs.md` 화면 명세와 `03-design.md` 표대로 만든다.

| 단계 | 검증 방법 | 완료 |
|---|---|---|
| 3.1 `frontend/index.html` + `app.js` 뼈대, 백엔드가 같은 오리진으로 제공 | `http://localhost:8000/` 으로 열림. `file://` 아님. 파일은 2개뿐 | [x] |
| 3.2 공통 헤더(제목·탭 3개·테마 버튼) + 라이트/다크 토글 | 새로고침해도 테마 유지. 첫 방문은 시스템 설정을 따름 | [x] |
| 3.3 목록 화면 (`q`, `from`, `to`, `cards`) | 카드 2열, 360px 에서 1열. 검색 입력마다 다시 호출 | [x] |
| 3.4 넣기 화면 (`title`, `metAt`, `attendees`, `file`, `body`, `btnUp`, `btnSave`, `result`) | 받아쓰기로 본문이 채워지고, 정리하기로 세 칸이 표시됨 | [x] |
| 3.5 상세 화면 (`modal`, `mTitle`) | 카드 클릭으로 열림, 바깥 클릭으로 닫힘. 삭제는 두 번 눌러야 지워짐 | [x] |
| 3.6 할 일 화면 (`todoBody`) | 담당자·기한·회의가 표로 보임. 좁은 화면에서 표만 가로 스크롤 | [x] |
| 3.7 요소 이름 확인: 화면의 id 가 `03-design.md` 표와 같은지 대조 | `index.html`·`app.js` 의 id 를 표와 하나씩 비교해 불일치 0건 | [x] |
| 3.8 API 연결 최종 확인 + git push | 파일 업로드 후 세 갈래 저장, 새로고침 유지, 검색 동작. `git push` 성공 | [x] |
