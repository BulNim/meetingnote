"""MeetingNote API - 02-specs REST 7개. 모든 경로에 /api/ 접두사."""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import gemini
from app.db import get_db, init_db
from app.models import Meeting
from app.schemas import (
    MeetingDetail,
    MeetingIn,
    MeetingListItem,
    MeetingUpdate,
    TodoOut,
    UploadOut,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_SUFFIXES = {".mp3", ".wav"}




@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="MeetingNote API", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    """02-specs - 검증 실패는 400. 스펙 외 필드만 422 로 남긴다."""
    errors = exc.errors()
    if any(e.get("type") == "extra_forbidden" for e in errors):
        return JSONResponse(status_code=422, content={"detail": errors})
    return JSONResponse(status_code=400, content={"detail": errors})


def _to_utc(dt: datetime) -> datetime:
    """met_at 은 UTC 로 저장한다 (02-specs)."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _get_or_404(db: Session, note_id: int) -> Meeting:
    note = db.get(Meeting, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="없는 id 입니다")
    return note


# --- 1. 저장 (세 갈래 구분까지) ------------------------------------------
@app.post("/api/notes", response_model=MeetingDetail, status_code=201)
def create_note(payload: MeetingIn, db: Session = Depends(get_db)):
    summary, decisions, todos = gemini.split3(payload.body)
    note = Meeting(
        title=payload.title,
        met_at=_to_utc(payload.met_at),
        attendees=payload.attendees,
        body=payload.body,
        summary=summary,
        decisions=decisions,
        todos=todos,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# --- 2. 목록 (body 제외) -------------------------------------------------
@app.get("/api/notes", response_model=list[MeetingListItem])
def list_notes(
    q: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Meeting)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Meeting.title.like(like), Meeting.attendees.like(like)))
    if from_:
        try:
            start = datetime.strptime(from_, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="from 은 YYYY-MM-DD")
        stmt = stmt.where(Meeting.met_at >= start)
    if to:
        try:
            end = datetime.strptime(to, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            raise HTTPException(status_code=400, detail="to 는 YYYY-MM-DD")
        stmt = stmt.where(Meeting.met_at <= end)
    stmt = stmt.order_by(Meeting.met_at.desc())
    return db.scalars(stmt).all()


# --- 3. 단건 (body 포함) -------------------------------------------------
@app.get("/api/notes/{note_id}", response_model=MeetingDetail)
def read_note(note_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, note_id)


# --- 4. 수정 -------------------------------------------------------------
@app.put("/api/notes/{note_id}", response_model=MeetingDetail)
def update_note(note_id: int, payload: MeetingUpdate, db: Session = Depends(get_db)):
    note = _get_or_404(db, note_id)
    note.title = payload.title
    note.met_at = _to_utc(payload.met_at)
    note.attendees = payload.attendees
    if payload.body != note.body:
        note.body = payload.body
        note.summary, note.decisions, note.todos = gemini.split3(payload.body)
    db.commit()
    db.refresh(note)
    return note


# --- 5. 삭제 -------------------------------------------------------------
@app.delete("/api/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = _get_or_404(db, note_id)
    db.delete(note)
    db.commit()
    return None


# --- 6. 할 일 모아 보기 --------------------------------------------------
@app.get("/api/todos", response_model=list[TodoOut])
def list_todos(db: Session = Depends(get_db)):
    """회의 날짜 최신순. 기한은 회의에서 말한 그대로 둔다 (02-specs)."""
    out: list[TodoOut] = []
    stmt = select(Meeting).order_by(Meeting.met_at.desc())
    for note in db.scalars(stmt).all():
        for line in (note.todos or "").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            what = parts[0] if parts else line
            who = parts[1] if len(parts) > 1 and parts[1] else "미정"
            when = parts[2] if len(parts) > 2 and parts[2] else "미정"
            out.append(
                TodoOut(
                    what=what,
                    who=who,
                    when=when,
                    note_id=note.id,
                    note_title=note.title,
                )
            )
    return out


# --- 7. 받아쓰기 ---------------------------------------------------------
@app.post("/api/upload", response_model=UploadOut)
async def upload(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="mp3, wav 만 받습니다")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="25MB 를 넘습니다")
    try:
        text = gemini.transcribe(data, file.filename or "")
    except gemini.GeminiError as exc:
        logger.error("업로드 받아쓰기 실패: %s", exc)
        raise HTTPException(status_code=502, detail="받아쓰기에 실패했습니다") from exc
    return UploadOut(body=text)
