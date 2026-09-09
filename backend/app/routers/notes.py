from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_gemini_service
from ..schemas import NoteDetail, NoteInput, NoteListItem
from ..services.gemini_service import GeminiService
from ..services.meeting_service import (
    create_meeting,
    delete_meeting,
    get_meeting,
    list_meetings,
    update_meeting,
)

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.post("", response_model=NoteDetail, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteInput,
    db: Session = Depends(get_db),
    gemini: GeminiService = Depends(get_gemini_service),
) -> NoteDetail:
    return create_meeting(db, payload, gemini)


@router.get("", response_model=list[NoteListItem])
def get_notes(
    q: str | None = None,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
) -> list[NoteListItem]:
    return list_meetings(db, q, from_date, to_date)


@router.get("/{id}", response_model=NoteDetail)
def get_note(id: int, db: Session = Depends(get_db)) -> NoteDetail:
    return get_meeting(db, id)


@router.put("/{id}", response_model=NoteDetail)
def update_note(
    id: int,
    payload: NoteInput,
    db: Session = Depends(get_db),
    gemini: GeminiService = Depends(get_gemini_service),
) -> NoteDetail:
    return update_meeting(db, id, payload, gemini)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(id: int, db: Session = Depends(get_db)) -> None:
    delete_meeting(db, id)
