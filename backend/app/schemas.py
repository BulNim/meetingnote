from datetime import datetime, timezone


def format_utc_datetime(value: datetime) -> str:
    """UTC 시각을 API 응답용 ISO 8601 문자열로 변환한다."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class NoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    met_at: datetime
    attendees: str = ""
    body: str = Field(min_length=1)

    @field_validator("met_at")
    @classmethod
    def validate_met_at(cls, value: datetime) -> datetime:
        return value


class NoteListItem(BaseModel):
    id: int
    title: str
    met_at: datetime
    attendees: str
    summary: str | None
    decisions: str | None
    todos: str | None

    @field_serializer("met_at")
    def serialize_met_at(self, value: datetime) -> str:
        return format_utc_datetime(value)


class NoteDetail(NoteListItem):
    body: str


class TodoItem(BaseModel):
    what: str
    who: str
    when: str
    note_id: int
    note_title: str


class UploadResponse(BaseModel):
    text: str
