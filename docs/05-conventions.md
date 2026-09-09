# 개발 규칙

## 명명

- 백엔드: `snake_case`
- 프론트: `camelCase`
- 컴포넌트: `PascalCase`
- 식별자: 영어
- 주석: 한국어

## 금지 항목

| 금지 | 이유 | 대안 |
|---|---|---|
| `print` 디버깅 | 노이즈 | `logging` 모듈 |
| `bare except` | 예외 삼킴 | `except SpecificError` |
| API 키 하드코딩 | 키 유출 | `.env` + `os.getenv` |
| `any` 타입 (TS) | 의미 상실 | 명시적 타입 |
| `!important` | 우선순위 꼬임 | 셀렉터 개선 |

## `.gitignore` 등록 항목

```gitignore
__pycache__/
.pytest_cache/
.venv/
*.db
*.log
.env
실습소재/
```

## 테스트 매트릭스

| 케이스 | 요청 | 기대응답 |
|---|---|---:|
| 정상 생성 | `POST` title + met_at + body | `201` |
| 목록 | `GET /api/notes` | `200`, body 없음 |
| 수정 | `PUT` 전 필드 | `200` |
| 삭제 | `DELETE` | `204` |
| 검색 | `GET /api/notes?q=기획` | `200`, 제목·참석자 일치만 |
| 할 일 | `GET /api/todos` | `200` |
| title 누락 | 요청 본문에서 title 제외 | `400` |
| met_at 형식 오류 | 잘못된 met_at 형식 전송 | `400` |
| 없는 id | 존재하지 않는 id 요청 | `404` |
| 스펙 외 필드 | 허용되지 않은 필드 포함 | `422` |
| 업로드 mp4 파일 | `POST /api/upload`에 mp4 전송 | `415` |
| 업로드 30MB 파일 | `POST /api/upload`에 30MB 파일 전송 | `413` |

## 운영 배포 규칙

- Vercel 운영 DB는 Neon PostgreSQL을 사용하고 `DATABASE_URL`은 Vercel Environment Variables에만 등록한다.
- `GEMINI_API_KEY`와 `DATABASE_URL`을 코드·Git·문서에 실제 값으로 기록하지 않는다.
- 로컬·테스트는 SQLite를 사용하며 Vercel 환경에서는 `DATABASE_URL` 누락을 허용하지 않는다.
- 배포 후 `/`, `/docs`, `/openapi.json`, 핵심 `/api/` 경로를 smoke test한다.

## Git 커밋 규칙

커밋 유형은 `feat`, `fix`, `docs`, `refactor`, `test`, `chore` 중 하나를 사용하고, 뒤에 한국어 요약을 작성한다.

```text
<type>: <한국어 요약>
```
