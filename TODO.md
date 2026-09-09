# TODO

## 진행 중
- [x] Gemini가 반환한 Python 리스트 형태의 할 일을 정상적인 항목으로 파싱하고 화면 표시를 검증한다 (리스트를 줄바꿈 항목으로 정규화, 전체 테스트 19 passed)
- [x] 사용자가 직접 테스트할 수 있도록 FastAPI 서버를 다시 실행한다 (http://127.0.0.1:8011 응답 확인)
- [x] 화면 캡처의 받아쓰기 500 오류와 업로드 endpoint 동작을 확인하고 수정한다 (Gemini SDK Part.from_bytes 적용, 실제 WAV 업로드 200, Playwright 받아쓰기 완료, pytest 18 passed)

## 완료
- [x] Phase 3 프론트 전체 구현 (화면 4종·API 연결·360px 반응형·테마·검증·push)
- [x] 고정 의존성 정책을 지키며 표준 datetime으로 met_at UTC 포맷팅을 개선한다 (02-specs 기준 UTC ISO 8601 `YYYY-MM-DDTHH:MM:SSZ`, 전체 테스트 18 passed)
- [x] 05-conventions.md 테스트 매트릭스 12개 케이스를 실행하고 결과를 기록한다 (12 passed, 전체 회귀 16 passed)
- [x] docs/04-tasks.md의 Phase 2 진행 상태를 확인해 보고한다
- [x] 제공받은 Gemini API 키를 프로젝트 루트 .env에 저장하고 로컬 설정을 검증한다

- [x] Playwright로 Swagger 7개 엔드포인트를 테스트하고 결과를 확인한다 (POST /api/upload은 GEMINI_API_KEY 미설정으로 502 확인)
- [?] localhost:8000/docs 접속 실패 원인을 확인하고 Swagger 접속을 복구한다 (8000 포트를 다른 Node.js server.js가 점유해 localhost 요청이 Node 서버로 전달됨. 해당 프로세스 종료 또는 URL 사용 방식 확인 필요)
- [x] Phase 2 백엔드 전체 구현 (7번째 API로 GET /api/notes/{id} 추가)

- [x] 현재 변경된 프로젝트 파일을 검토하고 커밋해야 할 파일을 모두 커밋·푸시한다

- [x] docs/05-conventions.md에 명명 규칙, 금지 항목, gitignore, 테스트 매트릭스와 커밋 규칙을 작성한다

- [x] docs/04-tasks.md에 3개 Phase별 고정 체크리스트와 진행 규칙을 작성한다

- [x] docs/02-specs.md에 데이터 모델, 분류 기준, 검증 규칙, REST API와 화면 명세 기준을 작성한다
- [x] docs/03-design.md에 고정 기술 선택과 의존성 추가 정책을 8행 표로 작성한다

- [x] docs/01-product.md에 제품 목표, 사용자, MVP 범위와 성공 기준을 작성한다

- [x] docs/에 지정된 6개 문서를 생성하고 00-overview.md에 프로젝트 개요를 작성한다
- [x] CLAUDE.md의 docs 파일명과 읽는 순서를 새 문서 목록과 대조하고 필요하면 수정한다

- [x] CLAUDE.md에 회의록 정리기 프로젝트 규칙 4개 섹션을 추가한다

- [x] 기존 Git 설정을 확인하고 로컬 저장소를 설정한다
- [x] GitHub에 meetingnote 저장소를 생성하거나 기존 저장소를 초기화해 연결한다
- [x] 원격 연결과 push 결과를 검증한다

- [x] todo-guard 문서 규칙 상태 확인


## 보류 (사용자 확인 필요)
