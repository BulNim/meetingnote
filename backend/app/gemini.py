"""Gemini 호출 - 받아쓰기와 3항목 구분 (03-design #5).

05-conventions 금지 항목: 클라이언트를 한 줄로 만들어 바로 호출하지 않는다.
모듈에 한 번 만들어 재사용한다.
"""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
_API_KEY = os.getenv("GEMINI_API_KEY")

# 모듈에 한 번 만들고 재사용한다 (05-conventions 금지 6번)
client = genai.Client(api_key=_API_KEY) if _API_KEY else None

MIME_BY_EXT = {".mp3": "audio/mpeg", ".wav": "audio/wav"}

SPLIT_PROMPT = """아래는 회의 받아쓰기 원문이다. 세 갈래로 구분하라.

요약 - 회의 전체를 3~5줄로. 새로운 사실을 지어내지 말 것
결정사항 - 「하기로 했다 / 확정 / 승인」 처럼 합의가 끝난 것만.
           논의만 하고 안 정한 것은 넣지 말 것
할 일 - 담당자와 기한이 드러난 것만. 담당자가 없으면 미정으로 적을 것
셋 중 어디에도 안 들어가는 잡담은 버릴 것

기한은 회의에서 말한 그대로 둔다. 날짜로 바꾸지 않는다.

출력 형식 (이 머리말을 그대로 쓰고 다른 말은 붙이지 말 것):
[요약]
(한 줄에 하나씩)
[결정사항]
(한 줄에 하나씩)
[할 일]
(한 줄에 하나씩, 내용 | 담당자 | 기한)

원문:
"""


class GeminiError(RuntimeError):
    """외부 호출 실패."""


def transcribe(data: bytes, filename: str) -> str:
    """녹취 파일을 받아쓴다. 실패하면 GeminiError."""
    if client is None:
        raise GeminiError("GEMINI_API_KEY 가 없습니다")
    mime = MIME_BY_EXT.get(Path(filename).suffix.lower())
    if mime is None:
        raise GeminiError(f"지원하지 않는 형식: {filename}")
    try:
        res = client.models.generate_content(
            model=MODEL,
            contents=[
                "이 오디오를 한국어로 그대로 받아써라. 말한 내용만 적고 다른 말은 붙이지 마라.",
                types.Part.from_bytes(data=data, mime_type=mime),
            ],
        )
    except Exception as exc:  # 외부 호출 실패 - 02-specs 상 502
        logger.error("받아쓰기 실패: %s", exc)
        raise GeminiError(str(exc)) from exc
    return (res.text or "").strip()


def split3(body: str) -> tuple[str, str, str]:
    """본문을 요약 / 결정사항 / 할 일로 구분한다.

    실패하면 빈 값 세 개를 돌려준다 (02-specs - 저장은 201 그대로).
    """
    if client is None:
        logger.error("구분 실패: GEMINI_API_KEY 가 없습니다")
        return "", "", ""
    try:
        res = client.models.generate_content(
            model=MODEL,
            contents=SPLIT_PROMPT + body,
        )
        text = res.text or ""
    except Exception as exc:
        logger.error("구분 실패: %s", exc)
        return "", "", ""
    return _parse(text)


def _parse(text: str) -> tuple[str, str, str]:
    buckets = {"요약": [], "결정사항": [], "할 일": []}
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        key = line.strip("[]").strip()
        if key in buckets and line.startswith("["):
            cur = key
            continue
        if cur is None:
            continue
        buckets[cur].append(line.lstrip("-•* ").strip())
    return (
        "\n".join(buckets["요약"]),
        "\n".join(buckets["결정사항"]),
        "\n".join(buckets["할 일"]),
    )
