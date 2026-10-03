# 03 - Design (HOW)

## 기술 결정 8개

| # 선택 | 대안 | 근거 | 트레이드오프 |
|---|---|---|---|
| 1) 백엔드 - **FastAPI** | Django, Express | 타입 힌트 기반 검증과 Swagger 자동 생성. 작은 API 에 군더더기 없음 | Django 의 admin · ORM 기본 제공은 포기 |
| 2) 프론트 - **Vanilla JS + Tailwind CDN**<br>백엔드가 같은 오리진에서 제공. `file://` 로 직접 열지 않음 | React, Vue | 빌드 0초. 코드가 그대로 보여 검증이 쉬움 | 컴포넌트 재사용과 상태 추상화를 손으로 처리 |
| 3) DB - **SQLite** (SQLAlchemy ORM, 추후 PostgreSQL 전환 고려) | PostgreSQL 즉시 도입 | 파일 하나로 끝. 설치 · 계정 · 포트가 없음 | 동시 쓰기와 다중 인스턴스에 약함 |
| 4) CSS - **Tailwind 만**. styled-components 금지 | CSS-in-JS, 별도 CSS 파일 | 클래스가 마크업에 붙어 화면과 1:1 | 클래스 문자열이 길어짐 |
| 5) 받아쓰기 - **Gemini API (`gemini-3.1-flash-lite`)**<br>키는 `.env` 로만 읽고 저장소에 올리지 않음 | Whisper 자체 구동, 브라우저 음성 인식 | 설치 없이 호출 한 번. 무료 한도로 실습 가능 | 외부 의존 · 네트워크 실패 시 502 처리 필요 |
| 6) 상태관리 - **모듈 변수 + DOM 직접 갱신** | Redux, Zustand | 화면 4종 규모에서 상태 라이브러리는 과함 | 화면이 늘면 갱신 지점을 손으로 추적 |
| 7) 디자인 시스템 - **Mac OS UI 톤** | Material, Ant | 페르소나가 개발자가 아님. 익숙한 톤이 학습 비용 0 | 디자인 토큰을 직접 정의해야 함 |
| 8) 테마 - **라이트/다크 토글**, `localStorage`, 초기값은 시스템 설정 | 라이트 고정 | 01-product 범위 항목. `dark:` 변형으로 비용 작음 | 색 대비를 두 벌 확인해야 함 |

## 디자인 토큰 (Mac OS 톤)

- 모서리 `rounded-xl` (12px) / `rounded-2xl`
- 그림자 `shadow-lg` / `shadow-xl`
- 카드 `backdrop-blur` + 반투명 배경 - 라이트 `bg-white/70`, 다크 `bg-zinc-900/70`
- 폰트 `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- 간격 4px 그리드, 터치 타깃 44px 이상

## 화면 배치와 요소 이름 (한 번 정하면 바꾸지 않음)

근거 자료는 `docs/화면구성.pdf` 5쪽. 배치도는 그 파일에 있고 여기에는 옮겨 적지 않는다.
아래 id 는 그 파일에 적힌 그대로다. **바꿔야 하면 사유를 먼저 적는다.**

| 요소 | id | 자리 |
|---|---|---|
| 검색 입력 | `q` · `from` · `to` | 목록 화면 상단 |
| 목록 칸 | `cards` | 카드 배치 구역 |
| 넣기 폼 | `title` · `metAt` · `attendees` | 제목 · 일시 · 참석자 |
| 파일 · 본문 | `file` · `body` | 녹취 파일과 받아쓴 본문 |
| 버튼 | `btnUp` · `btnSave` | 받아쓰기 · 정리 |
| 결과 세 칸 | `result` | 요약 · 결정사항 · 할 일 |
| 상세 창 | `modal` | 카드를 누르면 뜨는 겹침 창 |
| 제목 수정칸 | `mTitle` | 상세 창 안에서 제목을 고치는 칸 |
| 할 일 표 | `todoBody` | 표의 본문 행 |

공통 - 상단 고정 헤더에 제목과 탭 3개(목록 · 넣기 · 할 일), 테마 버튼.
본문 최대 폭 `max-w-6xl` 가운데 정렬.

## 테마 토글

`dark:` 변형 + `localStorage('theme')`. 초기값은 `prefers-color-scheme` 감지.

## 절대 금지

- styled-components / CSS-in-JS
- Redux / Zustand / Recoil

## 의존성 추가 정책

**03-design 에 사유를 적기 전에는 도입 불가.**

사전 승인 목록

| 패키지 | 사유 |
|---|---|
| `httpx` | 테스트 구동 (FastAPI TestClient) |
| `google-genai` | 받아쓰기 (Gemini API 호출) |
