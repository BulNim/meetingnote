import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

import gemini_service
from config import MAX_UPLOAD_BYTES
from database import Base, engine, get_db
from models import Meeting
from schemas import (
    NoteCreate,
    NoteDetail,
    NoteListItem,
    NoteUpdate,
    TodoItem,
    UploadResult,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AUDIO_MIME_TYPES = {".mp3": "audio/mpeg", ".wav": "audio/wav"}
UNDECIDED_WHO = "미정"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="MeetingNote", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # 검증 실패는 400 으로 바꾸고, 스펙 외 필드 오류만 422 로 남긴다
    errors = exc.errors()
    only_extra = bool(errors) and all(e["type"] == "extra_forbidden" for e in errors)
    detail = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in errors]
    return JSONResponse(status_code=422 if only_extra else 400, content={"detail": detail})


def get_meeting_or_404(db: Session, note_id: int) -> Meeting:
    meeting = db.get(Meeting, note_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="회의록을 찾을 수 없습니다.")
    return meeting


@app.post("/api/notes", status_code=201, response_model=NoteDetail)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    meeting = Meeting(**payload.model_dump())
    try:
        parts = gemini_service.split_note(payload.body)
    except gemini_service.GEMINI_ERRORS:
        # 구분에 실패해도 저장은 그대로 하고, 세 갈래는 빈 값으로 둔다
        logger.exception("세 갈래 구분 실패")
        parts = {"summary": "", "decisions": "", "todos": ""}
    meeting.summary = parts["summary"]
    meeting.decisions = parts["decisions"]
    meeting.todos = parts["todos"]
    db.add(meeting)
    db.commit()
    return meeting


@app.get("/api/notes", response_model=list[NoteListItem])
def list_notes(
    q: str | None = None,
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    stmt = select(Meeting)
    keyword = (q or "").strip()
    if keyword:
        stmt = stmt.where(
            or_(
                Meeting.title.icontains(keyword, autoescape=True),
                Meeting.attendees.icontains(keyword, autoescape=True),
            )
        )
    if date_from:
        stmt = stmt.where(Meeting.met_at >= datetime.combine(date_from, time.min))
    if date_to:
        # to 는 그날 23:59:59 까지 포함하므로 다음 날 0시 미만으로 거른다
        stmt = stmt.where(Meeting.met_at < datetime.combine(date_to + timedelta(days=1), time.min))
    stmt = stmt.order_by(Meeting.met_at.desc(), Meeting.id.desc())
    return db.scalars(stmt).all()


@app.get("/api/notes/{note_id}", response_model=NoteDetail)
def get_note(note_id: int, db: Session = Depends(get_db)):
    return get_meeting_or_404(db, note_id)


@app.put("/api/notes/{note_id}", response_model=NoteDetail)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)):
    meeting = get_meeting_or_404(db, note_id)
    for field, value in payload.model_dump().items():
        setattr(meeting, field, value)
    db.commit()
    return meeting


@app.delete("/api/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    meeting = get_meeting_or_404(db, note_id)
    db.delete(meeting)
    db.commit()
    return Response(status_code=204)


def parse_todo_line(line: str) -> tuple[str, str, str]:
    """`내용 | 담당자 | 기한` 한 줄을 (what, who, when) 으로 나눈다."""
    parts = [p.strip() for p in line.split("|")]
    what = parts[0]
    who = parts[1] if len(parts) > 1 and parts[1] else UNDECIDED_WHO
    when = parts[2] if len(parts) > 2 else ""
    return what, who, when


@app.get("/api/todos", response_model=list[TodoItem])
def list_todos(db: Session = Depends(get_db)):
    stmt = select(Meeting).where(Meeting.todos.is_not(None)).order_by(Meeting.met_at.asc(), Meeting.id.asc())
    items: list[TodoItem] = []
    for meeting in db.scalars(stmt):
        for line in (meeting.todos or "").splitlines():
            if not line.strip():
                continue
            what, who, when = parse_todo_line(line)
            items.append(
                TodoItem(what=what, who=who, when=when, note_id=meeting.id, note_title=meeting.title)
            )
    return items


@app.post("/api/upload", response_model=UploadResult)
def upload_audio(file: UploadFile):
    ext = Path((file.filename or "").lower()).suffix
    if ext not in AUDIO_MIME_TYPES:
        raise HTTPException(status_code=415, detail="mp3, wav 파일만 올릴 수 있습니다.")
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="25MB 이하 파일만 올릴 수 있습니다.")
    try:
        text = gemini_service.transcribe_audio(data, AUDIO_MIME_TYPES[ext])
    except gemini_service.GEMINI_ERRORS:
        logger.exception("받아쓰기 실패")
        raise HTTPException(status_code=502, detail="받아쓰기에 실패했습니다.")
    return UploadResult(text=text)
