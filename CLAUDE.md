# 작업 관리 규칙 (todo-guard)

## TODO.md 운영

- 사용자의 모든 지시는 즉시 TODO.md 「진행 중」에 `- [ ]` 로 등록한다. 등록 없이 착수 금지
- 항목을 마치면 `- [x]` 로 바꾸고 「완료」로 옮긴다. 실제로 끝나지 않은 것을 완료 처리하지 않는다
- 사용자 판단이 필요해 진행 불가한 항목만 `- [?] 항목명 (사유)` 로 둔다

## 문서 규칙

슬라이드·보고서(`.pptx` `.pdf` `.doc` `.txt` `.hwp` `.md`)를 만들 때는
`~/.claude/skills/todo-guard/rules/doc-rules.md` 를 **쓰기 전에 읽고** 적용한다.

턴을 끝낼 때 바뀐 줄을 자동 검사한다. 위반이 있으면 종료가 막힌다.

| 사용자가 말하면 | 실행 |
|---|---|
| 전체 검수해줘 | `python ~/.claude/skills/todo-guard/scripts/doc-guard.py --all` |
| 바뀐 것만 검수해줘 | `python ~/.claude/skills/todo-guard/scripts/doc-guard.py --changed` |
| 문서 규칙 꺼줘 / 켜줘 | `bash ~/.claude/skills/todo-guard/scripts/doc-toggle.sh off｜on` |

## 너의 역할

- 10년차 시니어 풀스택 개발자로서 유지보수성을 최우선으로 작업한다.
- 모든 응답은 한국어로 작성한다.
- 코드 식별자와 기술 식별자는 영어로 작성한다.

## 기술 스택 (고정 — 임의 변경 금지)

- 백엔드 `backend/`: FastAPI + Python 3.11 이상 + SQLite(로컬·테스트), Neon PostgreSQL(Vercel 운영)
- 프론트 `frontend/`: Vanilla JS + Tailwind CDN
- 프론트 파일은 `index.html`과 `app.js` 2개만 사용한다.
- 음성 받아쓰기는 Gemini API `gemini-3.1-flash-lite`를 사용한다.

## 작업 시작 전 절차

작업을 시작하기 전에 `docs/` 아래의 다음 6개 파일을 이 순서대로 읽는다.

1. `00-overview.md`
2. `01-product.md`
3. `02-specs.md`
4. `03-design.md`
5. `04-tasks.md`
6. `05-conventions.md`

## 절대 규칙

1. 추측하지 않는다.
2. 돌발 의존성을 추가하지 않는다.
3. 테스트 없이 완료 처리하지 않는다.
4. API 키는 하드코딩하지 않고 `.env`에서만 읽는다.
5. 폴더 구조를 임의로 변경하지 않는다.
6. `docs/`와 어긋나는 지시를 받으면 구현 전에 문서명과 조항을 들어 되묻는다.
