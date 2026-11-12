"""Gemini 호출 - 받아쓰기와 세 갈래 구분.

클라이언트는 모듈에 한 번 만들어 재사용한다 (05-conventions 2절).
한 줄로 만들어 바로 부르면 호출 도중 회수되어
"Cannot send a request, as the client has been closed" 가 난다.
"""

import logging
import time

import httpx2  # google-genai 가 통신에 쓰는 라이브러리 (03-design 3.2)
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from app.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = {429, 503}
RETRY_DELAY_SECONDS = 2

_client: genai.Client | None = None


class GeminiError(Exception):
    """Gemini 호출이 끝내 실패했을 때."""


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise GeminiError("GEMINI_API_KEY 가 .env 에 없습니다")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _generate(contents, config: types.GenerateContentConfig | None = None) -> types.GenerateContentResponse:
    """429 · 503 이면 잠시 뒤 1번 다시 부른다 (02-specs 7.3)."""
    client = get_client()
    for attempt in range(2):
        try:
            return client.models.generate_content(model=GEMINI_MODEL, contents=contents, config=config)
        except errors.APIError as exc:
            if attempt == 0 and exc.code in RETRY_STATUS_CODES:
                logger.warning("Gemini %s 응답 - %s초 뒤 다시 부릅니다", exc.code, RETRY_DELAY_SECONDS)
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise GeminiError(f"Gemini 호출 실패: {exc.code} {exc.message}") from exc
        except httpx2.HTTPError as exc:
            raise GeminiError(f"Gemini 연결 실패: {exc}") from exc
    raise GeminiError("Gemini 호출 실패")  # 도달하지 않음


# ---------------------------------------------------------------- 받아쓰기

TRANSCRIBE_PROMPT = (
    "이 녹음을 들리는 그대로 한국어 텍스트로 받아써 주세요. "
    "요약하거나 고치지 말고, 말한 내용만 문장 단위로 줄을 바꿔 적어 주세요. "
    "다른 설명은 붙이지 마세요."
)


def transcribe(audio: bytes, mime_type: str) -> str:
    response = _generate([types.Part.from_bytes(data=audio, mime_type=mime_type), TRANSCRIBE_PROMPT])
    text = (response.text or "").strip()
    if not text:
        raise GeminiError("받아쓰기 결과가 비었습니다")
    return text


# ---------------------------------------------------------------- 세 갈래 구분

# 02-specs 2절의 기준을 그대로 넣는다
CLASSIFY_PROMPT = """다음 회의 본문을 요약 / 결정사항 / 할 일 세 갈래로 나눠 주세요.

[나누는 기준]
- 요약 - 회의 전체를 3~5줄로. 새로운 사실을 지어내지 말 것
- 결정사항 - 「하기로 했다 / 확정 / 승인」 처럼 합의가 끝난 것만. 논의만 하고 안 정한 것은 넣지 말 것
- 할 일 - 담당자와 기한이 드러난 것만. 담당자가 없으면 미정으로 적을 것
- 셋 중 어디에도 안 들어가는 잡담은 버릴 것

[추가 규칙]
- 할 일의 기한은 회의에서 말한 그대로 적을 것 (예: 다음 주 금요일). 날짜로 바꾸지 말 것
- 본문이 회의 내용이 아니면 is_meeting 을 false 로 하고 세 칸을 모두 비울 것
- 해당하는 내용이 없는 칸은 빈 목록으로 둘 것

[본문]
"""


class TodoItem(BaseModel):
    what: str
    who: str
    when: str


class ClassifyResult(BaseModel):
    is_meeting: bool
    summary: list[str]
    decisions: list[str]
    todos: list[TodoItem]


def classify(body: str) -> ClassifyResult:
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ClassifyResult,
    )
    response = _generate(CLASSIFY_PROMPT + body, config)
    try:
        return ClassifyResult.model_validate_json(response.text or "")
    except ValidationError as exc:  # 응답 형식이 깨진 경우
        raise GeminiError(f"구분 결과 형식 오류: {exc}") from exc
