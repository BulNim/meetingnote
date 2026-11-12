"""세 갈래 저장 형식 변환과 구분 흐름 (02-specs 1.2 · 7.1)."""

import logging
from dataclasses import dataclass

from app import gemini
from app.config import MIN_CLASSIFY_LENGTH

logger = logging.getLogger(__name__)

TODO_SEPARATOR = " | "
UNASSIGNED = "미정"


@dataclass(frozen=True)
class ThreeWay:
    summary: str = ""
    decisions: str = ""
    todos: str = ""


def _clean_line(text: str) -> str:
    """한 줄에 한 항목이므로 줄바꿈을 지우고, 할 일 구분자와 겹치는 | 도 바꾼다."""
    return " ".join(text.replace("|", "/").split())


def format_todo(what: str, who: str, when: str) -> str:
    return TODO_SEPARATOR.join([_clean_line(what), _clean_line(who) or UNASSIGNED, _clean_line(when)])


def parse_todo(line: str) -> tuple[str, str, str]:
    """「내용 | 담당자 | 기한」 한 줄을 나눈다. 칸이 모자라면 담당자는 미정, 기한은 빈 값."""
    parts = [part.strip() for part in line.split("|")]
    what = parts[0] if parts else ""
    who = parts[1] if len(parts) > 1 and parts[1] else UNASSIGNED
    when = parts[2] if len(parts) > 2 else ""
    return what, who, when


def split_three_ways(body: str) -> ThreeWay:
    """본문을 세 갈래로 나눈다. 실패하면 빈 값으로 두고 로그만 남긴다."""
    if len(body.strip()) < MIN_CLASSIFY_LENGTH:
        return ThreeWay()
    try:
        result = gemini.classify(body)
    except gemini.GeminiError:
        logger.exception("세 갈래 구분 실패 - 빈 값으로 저장합니다")
        return ThreeWay()
    if not result.is_meeting:
        logger.info("회의 내용이 아닌 본문 - 세 칸을 비웁니다")
        return ThreeWay()
    return ThreeWay(
        summary="\n".join(_clean_line(line) for line in result.summary if line.strip()),
        decisions="\n".join(_clean_line(line) for line in result.decisions if line.strip()),
        todos="\n".join(format_todo(t.what, t.who, t.when) for t in result.todos if t.what.strip()),
    )
