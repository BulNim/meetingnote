"""Pydantic 스키마 - 02-specs 검증 규칙.

스펙 외 필드를 막으려고 extra="forbid" 를 준다.
기본값으로 두면 모르는 필드가 조용히 무시되어 201 이 나온다.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MeetingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    met_at: datetime
    attendees: str | None = None
    body: str = Field(min_length=1)


class MeetingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    met_at: datetime
    attendees: str | None = None
    body: str = Field(min_length=1)


class MeetingListItem(BaseModel):
    """목록 응답 - body 를 뺀다 (02-specs)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    met_at: datetime
    attendees: str | None = None
    summary: str | None = None
    decisions: str | None = None
    todos: str | None = None


class MeetingDetail(MeetingListItem):
    """단건 응답 - body 를 포함한다 (02-specs)."""

    body: str


class TodoOut(BaseModel):
    what: str
    who: str
    when: str
    note_id: int
    note_title: str


class UploadOut(BaseModel):
    body: str
