from datetime import datetime, timezone
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    PlainSerializer,
    StringConstraints,
)


def _to_naive_utc(value: datetime) -> datetime:
    # 시간대가 있으면 UTC 로 바꾸고, 없으면 UTC 로 간주한다
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _to_iso_z(value: datetime) -> str:
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[
    datetime,
    AfterValidator(_to_naive_utc),
    # model_dump() 는 datetime 그대로 두고, JSON 응답에서만 문자열(Z)로 바꾼다
    PlainSerializer(_to_iso_z, return_type=str, when_used="json"),
]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Body = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class NoteCreate(BaseModel):
    # 스펙 외 필드는 조용히 무시하지 않고 422 로 거절한다
    model_config = ConfigDict(extra="forbid")

    title: Title
    met_at: UtcDatetime
    attendees: str | None = None
    body: Body


class NoteUpdate(NoteCreate):
    summary: str | None = None
    decisions: str | None = None
    todos: str | None = None


class NoteListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    met_at: UtcDatetime
    attendees: str | None
    summary: str | None
    decisions: str | None
    todos: str | None


class NoteDetail(NoteListItem):
    body: str


class TodoItem(BaseModel):
    what: str
    who: str
    when: str
    note_id: int
    note_title: str


class UploadResult(BaseModel):
    text: str
