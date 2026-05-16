from typing import Optional, List
from sqlmodel import Field, SQLModel, select
from internal import db


class Commendation(SQLModel, table=True):
    id: int = Field(primary_key=True, default=None)
    user_id: int = Field(index=True)
    amount: int = Field(default=0, nullable=False)


def get(user_id: int) -> Optional["Commendation"]:
    """Return the Commendation for `user_id`, or None."""
    with db.get_session() as session:
        sql = select(Commendation).where(Commendation.user_id == user_id)
        return session.exec(sql).first()


def create_or_update(user_id: int, *, set_amount: Optional[int] = None, increment: int = 0) -> "Commendation":
    """Create a Commendation if missing, or update it.

    - If `set_amount` is provided it sets the absolute value.
    - Otherwise `increment` (can be negative) is added to the current amount.
    """
    with db.get_session() as session:
        sql = select(Commendation).where(Commendation.user_id == user_id)
        obj = session.exec(sql).first()
        if obj is None:
            initial = set_amount if set_amount is not None else max(0, increment)
            obj = Commendation(user_id=user_id, amount=initial)
            session.add(obj)
            return obj

        if set_amount is not None:
            obj.amount = set_amount
        else:
            obj.amount += increment
        return obj


def list_all() -> List["Commendation"]:
    """Return all Commendation rows."""
    with db.get_session() as session:
        sql = select(Commendation)
        return list(session.exec(sql).all())
