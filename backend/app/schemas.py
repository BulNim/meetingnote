"""요청 · 응답 스키마 (02-specs 3 · 4절)."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


def to_naive_utc(value: datetime) -> datetime:
    """시간대가 없으면 UTC 로 보고, 있으면 UTC 로 바꾼 뒤 시간대를 떼어 저장용으로 만든다."""
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


class NoteIn(BaseModel):
    """회의록 생성 요청. 스펙 외 필드는 422 로 막는다 (extra=forbid)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    met_at: datetime
    attendees: str = ""
    body: str = Field(min_length=1)

    @field_validator("met_at")
    @classmethod
    def normalize_met_at(cls, value: datetime) -> datetime:
        return to_naive_utc(value)


class NoteUpdate(NoteIn):
    """회의록 수정 요청. 세 갈래는 보내면 바꾸고, 빠지면 그대로 둔다."""

    summary: str | None = None
    decisions: str | None = None
    todos: str | None = None


class NoteListItem(BaseModel):
    """목록 응답 - body 제외."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    met_at: datetime
    attendees: str
    summary: str
    decisions: str
    todos: str

    @field_serializer("met_at")
    def serialize_met_at(self, value: datetime) -> str:
        # DB 의 시간대 없는 값은 UTC 다. 화면이 로컬로 바꿀 수 있게 Z 를 붙여 낸다
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class NoteOut(NoteListItem):
    """단건 응답 - body 포함."""

    body: str


class TodoOut(BaseModel):
    what: str
    who: str
    when: str
    note_id: int
    note_title: str


class UploadOut(BaseModel):
    body: str
