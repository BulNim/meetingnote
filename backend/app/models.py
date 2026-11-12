"""Meeting 모델 - 02-specs 1절의 8필드, 순서 · 타입 그대로."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Meeting(Base):
    __tablename__ = "meetings"
    # 지운 id 를 다시 쓰지 않도록 테이블에 AUTOINCREMENT 를 넣는다 (02-specs 1.1)
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # UTC 로 저장한다. SQLite 에는 시간대 없이 들어가므로 읽을 때 UTC 로 붙인다
    met_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attendees: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    decisions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    todos: Mapped[str] = mapped_column(Text, nullable=False, default="")
