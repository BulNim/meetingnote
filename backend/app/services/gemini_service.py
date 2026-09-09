import json
import os
from dataclasses import dataclass
from typing import Any

from ..config import GEMINI_API_KEY, GEMINI_MODEL


class GeminiServiceError(RuntimeError):
    """Gemini API 호출 또는 응답 처리 실패를 나타낸다."""


PROMPT = """다음 회의 본문을 아래 기준으로 세 갈래로 분류하라.
요약- 회의 전체를 3~5줄로. 새로운 사실을 지어내지 말것
결정사항- 「하기로 했다/ 확정/ 승인」처럼 합의가 끝난 것만
논의만 하고 안 정한 것은 넣지 말것
할일- 담당자와 기한이 드러난 것만. 담당자가 없으면 미정으로 적을 것

반드시 JSON 객체로만 응답하라.
summary는 줄바꿈으로 구분된 문자열, decisions도 줄바꿈으로 구분된 문자열,
todos는 한 줄에 하나씩 '내용| 담당자| 기한' 형식의 문자열로 작성하라.

회의 본문:
"""


@dataclass
class AnalysisResult:
    summary: str
    decisions: str
    todos: str


class GeminiService:
    def __init__(self, client: Any | None = None) -> None:
        self.client = client

    def _client(self) -> Any:
        if self.client is not None:
            return self.client
        if not GEMINI_API_KEY:
            raise GeminiServiceError("GEMINI_API_KEY가 설정되지 않았습니다.")
        try:
            from google import genai

            self.client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as exc:
            raise GeminiServiceError("Gemini 클라이언트를 초기화할 수 없습니다.") from exc
        return self.client

    def _generate_content(self, *, contents: Any, config: Any) -> Any:
        try:
            return self._client().models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=config,
            )
        except GeminiServiceError:
            raise
        except Exception as exc:
            raise GeminiServiceError("Gemini API 호출에 실패했습니다.") from exc

    def analyze_text(self, body: str) -> AnalysisResult:
        response = self._generate_content(
            contents=PROMPT + body,
            config={"response_mime_type": "application/json"},
        )
        raw_text = getattr(response, "text", "") or "{}"
        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise GeminiServiceError("Gemini 응답 형식이 올바르지 않습니다.") from exc
        return AnalysisResult(
            summary=str(result.get("summary", "")),
            decisions=str(result.get("decisions", "")),
            todos=str(result.get("todos", "")),
        )

    def transcribe(self, data: bytes, filename: str) -> str:
        try:
            from google.genai import types

            audio_part = types.Part.from_bytes(
                data=data,
                mime_type=_mime_type(filename),
            )
        except Exception as exc:
            raise GeminiServiceError("오디오 데이터를 처리할 수 없습니다.") from exc

        response = self._generate_content(
            contents=[audio_part],
            config=types.GenerateContentConfig(responseMimeType="text/plain"),
        )
        return (getattr(response, "text", "") or "").strip()


def _mime_type(filename: str) -> str:
    return "audio/mpeg" if filename.lower().endswith(".mp3") else "audio/wav"
