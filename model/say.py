from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, select
from internal import db


class ScheduledMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message: str
    channel_id: int = Field(index=True)
    scheduled_at: datetime = Field(index=True)


def add_schedule(message: str, channel_id: int, scheduled_at: datetime) -> ScheduledMessage:
    with db.get_session() as session:
        obj = ScheduledMessage(message=message, channel_id=channel_id, scheduled_at=scheduled_at)
        session.add(obj)
        return obj


def get_due_scheduled(before: datetime) -> List[ScheduledMessage]:
    with db.get_session() as session:
        sql = select(ScheduledMessage).where(ScheduledMessage.scheduled_at <= before)
        return list(session.exec(sql).all())


def remove_schedule_by_ids(ids: List[int]) -> None:
    if not ids:
        return
    with db.get_session() as session:
        for _id in ids:
            obj = session.get(ScheduledMessage, _id)
            if obj:
                session.delete(obj)


def list_all_scheduled() -> List[ScheduledMessage]:
    with db.get_session() as session:
        sql = select(ScheduledMessage)
        return list(session.exec(sql).all())
