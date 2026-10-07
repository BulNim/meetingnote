import io
import logging
import threading

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from config import get_gemini_api_key, get_gemini_model

logger = logging.getLogger(__name__)

# 호출하는 쪽에서 잡아야 하는 Gemini 관련 예외 (ValueError 는 응답 JSON 검증 실패 포함)
GEMINI_ERRORS = (errors.APIError, httpx.HTTPError, RuntimeError, ValueError)

# 인라인 전송 한도(요청 전체 약 20MB)보다 작을 때만 바로 보낸다
INLINE_LIMIT_BYTES = 15 * 1024 * 1024

TRANSCRIBE_PROMPT = (
    "이 녹취 파일을 들리는 그대로 한국어 텍스트로 받아써라. "
    "요약하거나 설명을 덧붙이지 말고 받아쓴 본문만 출력하라. "
    "말소리가 없으면 빈 문자열을 출력하라."
)

SPLIT_PROMPT = """아래 회의 본문을 요약 / 결정사항 / 할 일 세 갈래로 나눠라.

- 요약: 회의 전체를 3~5줄로. 새로운 사실을 지어내지 말 것
- 결정사항: 「하기로 했다 / 확정 / 승인」 처럼 합의가 끝난 것만. 논의만 하고 안 정한 것은 넣지 말 것
- 할 일: 담당자와 기한이 드러난 것만. 담당자가 없으면 미정으로 적을 것
- 셋 중 어디에도 안 들어가는 잡담은 버릴 것

기한(when)은 회의에서 말한 그대로 적고 날짜로 바꾸지 말 것.
해당하는 항목이 없으면 빈 목록으로 둘 것.

[회의 본문]
"""

# Gemini 클라이언트는 모듈에 한 번만 만들어 재사용한다
# (호출마다 만들면 도중에 회수되어 'client has been closed' 오류가 난다)
_client: genai.Client | None = None
_client_lock = threading.Lock()


def get_client() -> genai.Client:
    global _client
    with _client_lock:
        if _client is None:
            _client = genai.Client(api_key=get_gemini_api_key())
        return _client


class TodoOut(BaseModel):
    what: str
    who: str
    when: str


class SplitOut(BaseModel):
    summary: list[str]
    decisions: list[str]
    todos: list[TodoOut]


def transcribe_audio(data: bytes, mime_type: str) -> str:
    client = get_client()
    if len(data) <= INLINE_LIMIT_BYTES:
        audio = types.Part.from_bytes(data=data, mime_type=mime_type)
    else:
        audio = client.files.upload(
            file=io.BytesIO(data), config=types.UploadFileConfig(mime_type=mime_type)
        )
    response = client.models.generate_content(
        model=get_gemini_model(), contents=[TRANSCRIBE_PROMPT, audio]
    )
    return (response.text or "").strip()


def _one_line(text: str) -> str:
    return " ".join(text.split()).strip()


def split_note(body: str) -> dict[str, str]:
    """본문을 세 갈래로 나눠 저장 형식(줄바꿈 구분 문자열)으로 돌려준다."""
    client = get_client()
    response = client.models.generate_content(
        model=get_gemini_model(),
        contents=SPLIT_PROMPT + body,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SplitOut,
        ),
    )
    result = SplitOut.model_validate_json(response.text)
    return {
        "summary": "\n".join(_one_line(s) for s in result.summary if s.strip()),
        "decisions": "\n".join(_one_line(s) for s in result.decisions if s.strip()),
        # '|' 는 todos 의 구분자이므로 내용 안에서는 '/' 로 바꾼다
        "todos": "\n".join(
            " | ".join(_one_line(v).replace("|", "/") for v in (t.what, t.who or "미정", t.when))
            for t in result.todos
            if t.what.strip()
        ),
    }
