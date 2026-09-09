# 설계

| 선택 | 대안 | 근거 | 트레이드오프 |
|---|---|---|---|
| 1) 백엔드 - FastAPI | Django, Express | 고정 기술 스택과 Python 기반 API 구현 방향 | Django보다 구성 범위가 작고 Express보다 Python 생태계 활용에 적합하나, 필요한 기능을 직접 구성 |
| 2) 프론트 - Vanilla JS + Tailwind CDN | React, Vue | 고정 기술 스택과 실습 범위에 맞는 최소 구성 | 프레임워크 의존성은 줄지만 컴포넌트 추상화와 상태 관리 기능을 직접 구현. 프론트는 백엔드가 같은 오리진에서 제공하며 `file://`로 직접 열지 않음 |
| 3) DB - SQLite(로컬·테스트) + Neon PostgreSQL(Vercel 운영, SQLAlchemy ORM) | PostgreSQL 단일 환경 | 로컬 실습의 단순성과 Vercel 운영의 영속성 동시 확보 | 환경별 DB가 달라 운영 연결·스키마 검증이 필요 |
| 4) CSS - Tailwind만 | styled-components 금지 | 고정 기술 스택과 일관된 유틸리티 기반 스타일링 | 별도 CSS-in-JS 런타임은 없지만 클래스 조합 관리 필요 |
| 5) 받아쓰기 - Gemini API (gemini-3.1-flash-lite) | Whisper 자체 구동, 브라우저 음성인식 | 지정된 받아쓰기 서비스와 구현 범위 | 외부 API 호출과 네트워크·비용 의존성이 발생하나 자체 음성 모델 운영 부담 감소. 키는 `.env`로만 읽고 저장소에 올리지 않음 |
| 6) 상태관리 - 모듈변수+ DOM 직접갱신 | 별도 상태 관리 라이브러리 | 최소 의존성과 현재 화면 규모 | 구현 구조는 단순하나 화면 규모가 커지면 갱신 흐름 추적 부담 증가 |
| 7) 디자인시스템 - Mac OS UI 톤 | Material, Ant | 제품 문서와 실습 화면의 시각 방향 | 고유한 시각 일관성 확보가 가능하나 범용 컴포넌트 제공 범위는 제한적. 화면 배치와 요소 이름은 `실습소재/화면구성.pdf`를 따름 |
| 8) 테마 - 라이트/다크 토글, `localStorage`, 초기값은 시스템 설정 | 별도 테마 시스템 | 사용자 설정 유지와 시스템 환경 존중 | 브라우저 저장소와 시스템 설정의 우선순위 처리 필요 |

## 의존성 추가 정책

`03-design.md`에 추가 사유를 기록하기 전에는 의존성 도입 불가.

### 사전 승인 목록

- `httpx` - 테스트 구동에 필요
- `google-genai` - 받아쓰기에 필요
- `psycopg[binary]` - Neon PostgreSQL을 SQLAlchemy에서 연결하기 위한 Vercel 운영 드라이버

## 운영 배포

- Vercel은 `api/index.py`를 FastAPI ASGI 진입점으로 사용한다.
- Vercel 운영 환경은 `DATABASE_URL`에 Neon PostgreSQL 연결 문자열을 등록한다.
- 로컬·테스트는 기존 SQLite를 사용하고, Vercel에서는 `DATABASE_URL` 누락 시 실행을 거부한다.
- FastAPI가 API와 `frontend/` 정적 파일을 같은 origin에서 제공해 프론트의 상대 `/api/` 경로를 유지한다.
