# 05. Conventions

## 명명

| 대상 | 규칙 |
|---|---|
| 백엔드 (Python) | snake_case |
| 프론트 (JS) | camelCase |
| 컴포넌트 | PascalCase |

식별자는 영어로 쓰고, 주석만 한국어로 쓴다.

## 금지 6개

| 금지 | 이유 | 대안 |
|---|---|---|
| `print` 디버깅 | 노이즈 | `logging` 모듈 |
| bare `except` | 예외를 삼킴 | `except SpecificError` |
| API 키 하드코딩 | 키 유출 | `.env` + `os.getenv` |
| `any` 타입 (TS) | 의미 상실 | 명시적 타입 |
| `!important` | 우선순위가 꼬임 | 셀렉터 개선 |
| Gemini 클라이언트를 한 줄로 만들어 바로 호출 | 호출 도중 회수되어 `Cannot send a request, as the client has been closed` 가 난다 | 모듈에 한 번 만들어 재사용 |

## .gitignore 에 넣을 것

```
__pycache__/
.pytest_cache/
.venv/
*.db
*.log
.env
```

## 테스트 매트릭스

총 21케이스 (MVP 기준 13 + 추가 검증 8). 뒤에 결함이 나오면 케이스를 늘리고 숫자도 같이 고친다.

| 케이스 | 요청 | 기대 응답 |
|---|---|---|
| 정상 생성 | `POST /api/notes` (`title` + `met_at` + `body`) | 201 |
| 목록 | `GET /api/notes` | 200, `body` 없음 |
| 단건 | `GET /api/notes/{id}` | 200, `body` 있음 |
| 수정 | `PUT /api/notes/{id}` (전 필드) | 200 |
| 삭제 | `DELETE /api/notes/{id}` | 204 |
| 검색 | `GET /api/notes?q=기획` | 200, 제목·참석자 일치만 |
| 할 일 | `GET /api/todos` | 200 |
| `title` 누락 | `POST /api/notes` (`title` 없음) | 400 |
| `met_at` 형식 오류 | `POST /api/notes` (`met_at` 형식 틀림) | 400 |
| 없는 id | `GET /api/notes/{없는 id}` | 404 |
| 스펙 외 필드 | `POST /api/notes` (스펙 외 필드 포함) | 422 |
| 업로드 mp4 파일 | `POST /api/upload` (mp4) | 415 |
| 업로드 30MB 파일 | `POST /api/upload` (30MB) | 413 |
| id 재사용 금지 | 회의록 삭제 후 새로 저장 | 새 id 가 지운 id 보다 큼 |
| `met_at` UTC 저장 | `POST /api/notes` (`met_at` = `+09:00` 시각) | 201, 조회 시 UTC(`Z`)로 반환 |
| 날짜 범위 양끝 포함 | `GET /api/notes?from=&to=` (같은 날) | 200, 그날 0시 ~ 23:59:59 포함, 다음 날 0시 제외 |
| 날짜 형식 오류 | `GET /api/notes?from=2026/03/10` | 400 |
| 할 일 정렬·담당자 미정 | `GET /api/todos` | 200, 회의 날짜 오래된 순, 담당자 없으면 `미정` |
| 구분 실패 | `POST /api/notes` (구분 호출이 실패) | 201, `summary`·`decisions`·`todos` 빈 값 |
| wav 받아쓰기 | `POST /api/upload` (wav, 실제 Gemini) | 200, 본문 텍스트 반환 |
| 받아쓰기 실패 | `POST /api/upload` (외부 호출이 실패) | 502 |

### Gemini 테스트 규칙

- 테스트도 실제 Gemini 를 부른다. 대역(mock)으로 바꾸지 않는다. 받아쓰기와 3항목 구분이 진짜 되는지는 실제로 불러 봐야 알 수 있다.
- 예외: 실패 경로(구분 실패 201, 받아쓰기 실패 502)는 Gemini 를 실패시켜야 확인할 수 있어서, 이 2케이스만 실패를 흉내 낸다. 성공 경로는 모두 실제로 부른다.
- 한도에 걸리지 않게, Gemini 를 부르는 테스트는 호출 사이를 1초쯤 띄운다.

## git 커밋 규칙

- 접두사: `feat` / `fix` / `docs` / `refactor` / `test` / `chore`
- 요약은 한국어로 쓴다.
- 예: `docs: CLAUDE.md + docs 6종 작성`
