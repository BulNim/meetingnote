# 04 - Tasks (구현 순서)

MVP 를 3개 Phase 로 진행한다. **Phase 이름과 개수는 고정. 변경 금지.**

진행 규칙 - 1) 순서대로만 2) 병렬 금지 3) 단계별 검증 필수 4) 실패하면 멈춤

이후 `backend 진행해` = Phase 2 전체, `frontend 진행해` = Phase 3 전체.

---

## Phase 1 (설계) - 10단계

CLAUDE.md + docs/ 6종 작성

| 단계 | 검증 방법 | 완료 |
|---|---|---|
| 1.1 작업 폴더와 실습소재 배치 | `docs/화면구성.pdf` 와 `실습소재/회의_녹음.wav` 존재 | [x] |
| 1.2 `.env` + `.gitignore` 에 키 등록 | `.env` 에 `GEMINI_API_KEY`, `.gitignore` 에 `.env` | [x] |
| 1.3 CLAUDE.md 4개 섹션 작성 | 역할 · 스택 · 읽기 순서 · 절대규칙 6개 | [x] |
| 1.4 docs/ 6개 파일 생성 | 파일명 6개가 CLAUDE.md 와 일치 | [x] |
| 1.5 00-overview.md | 매핑표 · 읽는 순서 · 화면 4종 | [x] |
| 1.6 01-product.md (WHY) | 목표 · 페르소나 · 범위 · 범위 외 · 성공 기준 | [x] |
| 1.7 02-specs.md (WHAT) | 필드 8개 · API 7개 · 구분 기준 3종 | [x] |
| 1.8 03-design.md (HOW) | 결정 8행 표 · 의존성 정책 | [x] |
| 1.9 04-tasks.md | Phase 3개 체크리스트 | [x] |
| 1.10 05-conventions.md + 첫 커밋 | 금지 6개 · 매트릭스 13케이스 · `git log` 1건 | [ ] |

---

## Phase 2 (백엔드) - 10단계

`backend/` FastAPI > API 7개 + 받아쓰기 > Swagger 확인

**서버 포트는 8000 으로 고정한다.** 실행은 `backend/` 에서
`uvicorn app.main:app --reload --port 8000`, 주소는 `http://127.0.0.1:8000`,
Swagger 는 `http://127.0.0.1:8000/docs`.

의존성은 아래 8개로 한정한다. 이 목록 밖은 추가하지 않는다.
`fastapi`, `uvicorn`, `sqlalchemy`, `pytest`, `httpx`, `google-genai`,
`python-multipart`, `python-dotenv`.
pytest 실행 시 httpx2 설치 권고가 떠도 무시한다.

| 단계 | 검증 방법 | 완료 |
|---|---|---|
| 2.1 `backend/` 폴더와 가상 환경 | `backend/.venv` 생성, requirements.txt 8개 | [ ] |
| 2.2 Meeting 모델 + SQLite | 필드 8개가 02-specs 와 일치 | [ ] |
| 2.3 `POST /api/notes` | 201, 세 갈래 구분까지 | [ ] |
| 2.4 `GET /api/notes` | 200, body 없음 | [ ] |
| 2.5 `GET /api/notes/{id}` | 200, body 있음 | [ ] |
| 2.6 `PUT` / `DELETE` | 200 / 204 | [ ] |
| 2.7 `GET /api/todos` | 200, `what`/`who`/`when`/`note_id`/`note_title` | [ ] |
| 2.8 `POST /api/upload` | 200, 실제 wav 로 본문 반환 | [ ] |
| 2.9 검색 `q` / `from` / `to` | 제목 · 참석자 부분 일치, 날짜 양끝 포함 | [ ] |
| 2.10 pytest 매트릭스 13건 + Swagger | `13 passed`, `/docs` 에 엔드포인트 7개 | [ ] |

---

## Phase 3 (프론트) - 8단계

`frontend/` HTML+JS+Tailwind > 화면 4종 > API 연결 > git push

화면 4종은 `02-specs` 화면 명세와 `03-design` 표대로 만든다.

| 단계 | 검증 방법 | 완료 |
|---|---|---|
| 3.1 `frontend/` + `index.html` + `app.js` 2개 파일 | 파일이 2개뿐 | [ ] |
| 3.2 Tailwind CDN + 테마 토글 | 다크/라이트 전환, localStorage 유지 | [ ] |
| 3.3 목록 화면 - 카드 + 검색 | `#cards` `#q` `#from` `#to` 동작 | [ ] |
| 3.4 넣기 화면 - 폼 + 업로드 | `#title` `#metAt` `#attendees` `#file` `#body` `#btnUp` `#btnSave` | [ ] |
| 3.5 결과 세 칸 + 상세 창 | `#result` `#modal` `#mTitle` | [ ] |
| 3.6 할 일 화면 | `#todoBody` 표, 담당자 · 기한 | [ ] |
| 3.7 **요소 이름이 03-design 표와 같은지 확인** | id 14개를 표와 1:1 대조 | [ ] |
| 3.8 API 연결 검증 + git push | 엔드포인트 7개 화면 동작, `git push origin main` | [ ] |

Phase 3.8 통과 시 MVP 완성. 확장 작업은 새 작업 문서로 쓰고 여기에 덧붙이지 않는다.
