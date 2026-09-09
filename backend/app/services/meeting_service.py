from datetime import date, datetime, time, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..errors import NotFoundError
from ..models import Meeting
from ..schemas import NoteInput
from .gemini_service import GeminiService


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def from_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc)


def analyze_or_empty(body: str, gemini: GeminiService):
    try:
        return gemini.analyze_text(body)
    except RuntimeError:
        return type("Analysis", (), {"summary": "", "decisions": "", "todos": ""})()


def create_meeting(db: Session, payload: NoteInput, gemini: GeminiService) -> Meeting:
    analysis = analyze_or_empty(payload.body, gemini)
    meeting = Meeting(
        title=payload.title,
        met_at=to_utc(payload.met_at),
        attendees=payload.attendees,
        body=payload.body,
        summary=analysis.summary,
        decisions=analysis.decisions,
        todos=analysis.todos,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def get_meeting(db: Session, note_id: int) -> Meeting:
    meeting = db.get(Meeting, note_id)
    if meeting is None:
        raise NotFoundError()
    return meeting


def list_meetings(
    db: Session,
    q: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[Meeting]:
    statement = select(Meeting)
    if q:
        pattern = f"%{q}%"
        statement = statement.where(
            or_(Meeting.title.ilike(pattern), Meeting.attendees.ilike(pattern))
        )
    if from_date:
        statement = statement.where(
            Meeting.met_at >= datetime.combine(from_date, time.min)
        )
    if to_date:
        next_day = datetime.combine(to_date, time.min).replace(tzinfo=None)
        statement = statement.where(Meeting.met_at < next_day)
    return list(db.scalars(statement.order_by(Meeting.met_at.desc())))


def update_meeting(
    db: Session, note_id: int, payload: NoteInput, gemini: GeminiService
) -> Meeting:
    meeting = get_meeting(db, note_id)
    body_changed = meeting.body != payload.body
    meeting.title = payload.title
    meeting.met_at = to_utc(payload.met_at)
    meeting.attendees = payload.attendees
    meeting.body = payload.body
    if body_changed:
        analysis = analyze_or_empty(payload.body, gemini)
        meeting.summary = analysis.summary
        meeting.decisions = analysis.decisions
        meeting.todos = analysis.todos
    db.commit()
    db.refresh(meeting)
    return meeting


def delete_meeting(db: Session, note_id: int) -> None:
    meeting = get_meeting(db, note_id)
    db.delete(meeting)
    db.commit()
