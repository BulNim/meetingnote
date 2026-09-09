from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import TodoItem
from ..services.meeting_service import list_meetings
from ..services.todo_parser import parse_todos

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("", response_model=list[TodoItem])
def get_todos(db: Session = Depends(get_db)) -> list[TodoItem]:
    result: list[TodoItem] = []
    for meeting in list_meetings(db):
        for what, who, when in parse_todos(meeting.todos):
            result.append(
                TodoItem(
                    what=what,
                    who=who,
                    when=when,
                    note_id=meeting.id,
                    note_title=meeting.title,
                )
            )
    return result
