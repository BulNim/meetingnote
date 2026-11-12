"""회의록 CRUD + 검색 (02-specs 3 · 6절)."""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Meeting
from app.schemas import NoteIn, NoteListItem, NoteOut, NoteUpdate
from app.services import split_three_ways

router = APIRouter(prefix="/api/notes", tags=["notes"])


def _get_or_404(db: Session, note_id: int) -> Meeting:
    meeting = db.get(Meeting, note_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="회의록이 없습니다")
    return meeting


def _local_day_start_utc(day: date, tz_offset: int) -> datetime:
    """화면의 로컬 날짜 0시를 UTC 로 바꾼다. tz_offset 은 JS getTimezoneOffset() 값(분)."""
    return datetime(day.year, day.month, day.day) + timedelta(minutes=tz_offset)


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteIn, db: Session = Depends(get_db)) -> Meeting:
    three_way = split_three_ways(payload.body)
    meeting = Meeting(
        **payload.model_dump(),
        summary=three_way.summary,
        decisions=three_way.decisions,
        todos=three_way.todos,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("", response_model=list[NoteListItem])
def list_notes(
    q: str | None = None,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    tz_offset: int = 0,
    db: Session = Depends(get_db),
) -> list[Meeting]:
    stmt = select(Meeting)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        # 제목과 참석자만 본다. 본문은 검색하지 않는다
        stmt = stmt.where(or_(Meeting.title.like(pattern), Meeting.attendees.like(pattern)))
    if from_date:
        stmt = stmt.where(Meeting.met_at >= _local_day_start_utc(from_date, tz_offset))
    if to_date:
        # 양끝 포함 - to 는 그날 23:59:59 까지 (다음 날 0시 미만)
        stmt = stmt.where(Meeting.met_at < _local_day_start_utc(to_date + timedelta(days=1), tz_offset))
    stmt = stmt.order_by(Meeting.met_at.desc(), Meeting.id.desc())
    return list(db.scalars(stmt))


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)) -> Meeting:
    return _get_or_404(db, note_id)


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)) -> Meeting:
    meeting = _get_or_404(db, note_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(meeting, field, value)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> Response:
    meeting = _get_or_404(db, note_id)
    db.delete(meeting)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
