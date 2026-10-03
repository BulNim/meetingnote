# 05 - Conventions (규율)

## 명명

- 백엔드 `snake_case`
- 프론트 `camelCase`
- 컴포넌트 `PascalCase`
- 식별자는 영어, 주석만 한국어

## 금지 6개

| 금지 | 이유 | 대안 |
|---|---|---|
| `print` 디버깅 | 노이즈 | `logging` 모듈 |
| bare `except` | 예외 삼킴 | `except SpecificError` |
| API 키 하드코딩 | 키 유출 | `.env` + `os.getenv` |
| `any` 타입 (TS) | 의미 상실 | 명시적 타입 |
| `!important` | 우선순위 꼬임 | 셀렉터 개선 |
| Gemini 클라이언트를 한 줄로 만들어 바로 호출 | 호출 도중 회수되어 `Cannot send a request, as the client has been closed` | 모듈에 한 번 만들어 재사용 |

## .gitignore 에 넣을 것

```
__pycache__/
.pytest_cache/
.venv/
*.db
*.log
.env
실습소재/*.wav
```

## 테스트 매트릭스 (MVP 기준 14케이스)

| # | 케이스 | 요청 | 기대 응답 |
|---|---|---|---|
| 1 | 정상 생성 | POST `title` + `met_at` + `body` | 201 |
| 2 | 목록 | GET `/api/notes` | 200, body 없음 |
| 3 | 단건 | GET `/api/notes/{id}` | 200, body 있음 |
| 4 | 수정 | PUT 전 필드 | 200 |
| 5 | 삭제 | DELETE | 204 |
| 6 | 검색 | GET `/api/notes?q=기획` | 200, 제목 · 참석자 일치만 |
| 7 | 할 일 | GET `/api/todos` | 200 |
| 8 | title 누락 | POST | 400 |
| 9 | met_at 형식 오류 | POST | 400 |
| 10 | 없는 id | GET `/api/notes/99999` | 404 |
| 11 | 스펙 외 필드 | POST | 422 |
| 12 | 업로드 mp4 파일 | POST `/api/upload` | 415 |
| 13 | 업로드 30MB 파일 | POST `/api/upload` | 413 |
| 14 | 중복 저장 막기 | 저장 성공 뒤 넣기 화면 | 입력칸이 비고 `btnSave` 가 잠겨 같은 회의록이 두 번 저장되지 않음 |

뒤에 결함이 나오면 케이스를 늘리고 위 숫자도 같이 고친다.

14번은 화면 계약이라 pytest 가 아니라 브라우저에서 확인한다.
pytest 로 도는 것은 1~13번 13건이다.

## 테스트 원칙

- 테스트도 **실제 Gemini 를 부른다.** 대역(mock)으로 바꾸지 않는다.
  받아쓰기와 3항목 구분이 진짜 되는지는 실제로 불러 봐야 알 수 있다
- 한도에 걸리지 않게 Gemini 를 부르는 테스트는 호출 사이를 1초쯤 띄운다

## git 커밋 규칙

`feat` / `fix` / `docs` / `refactor` / `test` / `chore` + 한국어 요약

예) `feat: Phase 2 백엔드 CRUD API 구현`

## 코드 리뷰 자가 점검 (커밋 전)

- [ ] 명명 규칙을 따랐는가
- [ ] 금지 6개가 없는가
- [ ] 새 의존성은 03-design 에 사유를 적었는가
- [ ] 대응 테스트가 있고 통과하는가
- [ ] 커밋 메시지 규격을 지켰는가
