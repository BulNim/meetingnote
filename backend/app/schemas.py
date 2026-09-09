from datetime import datetime

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
        return value.replace(tzinfo=None).isoformat() + "Z"


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
