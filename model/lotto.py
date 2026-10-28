from typing import List, Optional

from sqlmodel import Field, SQLModel, select

from internal import db


class Lotto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, unique=True)


def list_pool() -> List[int]:
    with db.get_session() as session:
        sql = select(Lotto)
        return [o.user_id for o in session.exec(sql).all()]


def has_user(user_id: int) -> bool:
    with db.get_session() as session:
        sql = select(Lotto).where(Lotto.user_id == user_id)
        return session.exec(sql).first() is not None


def add_user(user_id: int) -> None:
    with db.get_session() as session:
        sql = select(Lotto).where(Lotto.user_id == user_id)
        if session.exec(sql).first() is None:
            session.add(Lotto(user_id=user_id))


def remove_user(user_id: int) -> None:
    with db.get_session() as session:
        sql = select(Lotto).where(Lotto.user_id == user_id)
        objs = session.exec(sql).all()
        for o in objs:
            session.delete(o)
