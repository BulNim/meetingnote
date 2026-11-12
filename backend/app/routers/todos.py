"""할 일만 모아 보기 (02-specs 3.1)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Meeting
from app.schemas import TodoOut
from app.services import parse_todo

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("", response_model=list[TodoOut])
def list_todos(db: Session = Depends(get_db)) -> list[TodoOut]:
    # 회의 날짜 오래된 순. 기한으로는 정렬 · 거르기를 하지 않는다 (02-specs 2.1)
    meetings = db.scalars(select(Meeting).where(Meeting.todos != "").order_by(Meeting.met_at.asc(), Meeting.id.asc()))
    result: list[TodoOut] = []
    for meeting in meetings:
        for line in meeting.todos.splitlines():
            if not line.strip():
                continue
            what, who, when = parse_todo(line)
            result.append(TodoOut(what=what, who=who, when=when, note_id=meeting.id, note_title=meeting.title))
    return result
