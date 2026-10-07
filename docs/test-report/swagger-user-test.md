# Swagger 사용자 테스트 보고서

- 일시: 2026-10-07
- 대상: `http://localhost:8000/docs` (FastAPI Swagger UI, uvicorn)
- 방법: Playwright(Chromium 153, headless)로 Swagger UI를 실제로 조작 — 오퍼레이션 펼치기 → Try it out → 값 입력 → Execute → 캡처
- 스크립트: 세션 스크래치 폴더의 `swagger_test.py` (프로젝트 의존성에 추가하지 않음)
- 캡처: `docs/test-report/screenshots/`

## 요약

| 항목 | 결과 |
|---|---|
| 시나리오 | 13개 |
| 통과 | **13** |
| 실패 | 0 |

모든 응답 코드가 `02-specs.md`의 기대(201/200/204/400/404/415/422)와 일치했다.

## 결과

| # | 시나리오 | 기대 | 실제 | 판정 | 캡처 |
|---|---|---|---|---|---|
| 0 | Swagger 개요: `/api/` 경로 7개 노출 | 7개 | 7개 | PASS | 00-swagger-overview.png |
| 1 | POST /api/notes 정상 생성 | 201 | 201 | PASS | 01-create-201.png |
| 2 | POST /api/notes `body` 누락 | 400 | 400 | PASS | 02-create-400.png |
| 3 | POST /api/notes 스펙 외 필드(`foo`) | 422 | 422 | PASS | 03-create-422.png |
| 4 | GET /api/notes 전체 목록 | 200 | 200 | PASS | 04-list-200.png |
| 5 | GET /api/notes?q=QA 검색 | 200 | 200 | PASS | 05-list-search.png |
| 6 | GET /api/notes?from&to 기간 검색 | 200 | 200 | PASS | 06-list-range.png |
| 7 | GET /api/notes/{id} 상세 | 200 | 200 | PASS | 07-get-200.png |
| 8 | GET /api/notes/{id} 없는 id | 404 | 404 | PASS | 08-get-404.png |
| 9 | PUT /api/notes/{id} 수정 | 200 | 200 | PASS | 09-update-200.png |
| 10 | GET /api/todos | 200 | 200 | PASS | 10-todos-200.png |
| 11 | POST /api/upload `.txt` | 415 | 415 | PASS | 11-upload-415.png |
| 12 | DELETE /api/notes/{id} | 204 | 204 | PASS | 12-delete-204.png |
| 13 | 삭제 후 재조회 | 404 | 404 | PASS | 13-get-after-delete-404.png |

## 확인한 내용

- **Gemini 세 갈래 구분(시나리오 1)**: 본문에서 요약·결정사항·할 일이 채워져 저장됨 (`todos`: `API 문서 정리 | 김철수 | 10월 10일까지`).
- **검색(5)**: `q=QA`로 제목에 `[QA]`가 든 1건만 반환. 기간(6)은 `to` 당일(23:59:59)까지 포함.
- **할 일 모아보기(10)**: 수정한 두 줄이 `what/who/when`으로 분해됨. 담당자 생략 시 `미정`, 기한 생략 시 빈 문자열.
- **오류 형식**: 400/422/404/415 모두 `detail` 키를 가진 JSON.

## 발견 사항 (결함은 아님, 개선 제안)

1. **Swagger 문서에 400·404·413·415·502가 안 보인다.** 응답 스키마가 201/200과 422만 표시된다(01 캡처 하단). 실제 동작과 문서가 달라 보이므로, `responses=` 로 명시하면 좋다. 사용자 승인 후 처리 권장.
2. **Swagger의 422 예시와 실제 422 본문이 다르다.** 예시는 `input`, `ctx` 필드를 보이지만 커스텀 핸들러는 `loc/msg/type`만 반환한다.
3. **미검증 범위**: 실제 mp3/wav 받아쓰기(성공 200, 25MB 초과 413, Gemini 장애 502)는 외부 API 호출·대용량 파일이 필요해 이번에 하지 않았다.

## 데이터 영향 및 주의

- 테스트 노트(id 6, `[QA] 주간 스프린트 회의`)는 시나리오 12에서 삭제해 남아 있지 않다. 테스트 전용 DB가 아니라 실행 중인 서버의 DB를 썼다.
- 테스트 시작 전 노트는 4건이었으나 종료 후 3건(id 1, 2, 4)이다. 본 테스트가 호출한 DELETE는 id 6 한 번뿐이다. 그 사이 다른 경로(예: 프론트 작업)에서 한 건이 삭제된 것으로 보이나, 원인은 확인하지 못했다.
