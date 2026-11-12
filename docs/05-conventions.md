# 05. 코드 규칙

## 1. 명명

| 대상 | 규칙 | 예 |
|---|---|---|
| 백엔드 (Python) | `snake_case` | `met_at`, `classify_body()` |
| 프론트 (JS) | `camelCase` | `metAt`, `loadNotes()` |
| 컴포넌트 · 클래스 | `PascalCase` | `Meeting`, `NoteCreate` |

- **식별자는 영어**, **주석만 한국어**로 쓴다.

## 2. 금지 6개

| 금지 | 이유 | 대안 |
|---|---|---|
| `print` 디버깅 | 노이즈 | `logging` 모듈 |
| bare `except` | 예외 삼킴 | `except SpecificError` |
| API 키 하드코딩 | 키 유출 | `.env` + `os.getenv` |
| `any` 타입 (TS) | 의미 상실 | 명시적 타입 |
| `!important` | 우선순위 꼬임 | 셀렉터 개선 |
| Gemini 클라이언트를 한 줄로 만들어 바로 호출 | 호출 도중 회수되어 `Cannot send a request, as the client has been closed` | 모듈에 한 번 만들어 재사용 |

## 3. .gitignore

다음을 반드시 넣는다.

```
__pycache__/
.pytest_cache/
.venv/
*.db
*.log
.env
.claude/todo-guard/
```

## 4. 테스트 매트릭스

**MVP 기준 13케이스 + 결함 2케이스 = 15케이스.** 뒤에 결함이 나오면 케이스를 늘리고 **이 숫자도 같이 고친다.**

| # | 케이스 | 요청 | 기대 응답 |
|---|---|---|---|
| 1 | 정상 생성 | `POST /api/notes` - `title` + `met_at` + `body` | 201 |
| 2 | 목록 | `GET /api/notes` | 200, `body` 없음 |
| 3 | 단건 | `GET /api/notes/{id}` | 200, `body` 있음 |
| 4 | 수정 | `PUT /api/notes/{id}` - 전 필드 | 200 |
| 5 | 삭제 | `DELETE /api/notes/{id}` | 204 |
| 6 | 검색 | `GET /api/notes?q=기획` | 200, 제목 · 참석자 일치만 |
| 7 | 할 일 | `GET /api/todos` | 200 |
| 8 | title 누락 | `POST /api/notes` - `title` 없음 | 400 |
| 9 | met_at 형식 오류 | `POST /api/notes` - `met_at` 잘못된 형식 | 400 |
| 10 | 없는 id | `GET /api/notes/{없는 id}` | 404 |
| 11 | 스펙 외 필드 | `POST /api/notes` - 모르는 필드 포함 | 422 |
| 12 | 업로드 mp4 파일 | `POST /api/upload` - mp4 | 415 |
| 13 | 업로드 30MB 파일 | `POST /api/upload` - 30MB | 413 |
| 14 | 업로드 중 Gemini 연결 실패 | `POST /api/upload` - Gemini 에 닿지 못함 | 502 (02-specs 8.1 결함 1) |
| 15 | 저장 중 Gemini 연결 실패 | `POST /api/notes` - Gemini 에 닿지 못함 | 201, 세 칸 빈 값 (02-specs 8.1 결함 1) |

### 4.1 실제 Gemini 를 부른다

- 테스트도 **실제 Gemini 를 부른다. 대역(mock · fake)으로 바꾸지 않는다.**
  받아쓰기와 세 갈래 구분이 진짜 되는지는 실제로 불러 봐야 알 수 있다.
- 한도에 걸리지 않게, Gemini 를 부르는 테스트는 **호출 사이를 1초쯤 띄운다.**

## 5. git 커밋 규칙

```
<type>: <한국어 요약>
```

| type | 쓰는 때 |
|---|---|
| `feat` | 새 기능 |
| `fix` | 결함 수정 |
| `docs` | 문서만 바꿈 |
| `refactor` | 동작은 그대로, 구조만 바꿈 |
| `test` | 테스트 추가 · 수정 |
| `chore` | 설정 · 의존성 · 잡무 |

예: `feat: 회의록 저장 API 추가`
