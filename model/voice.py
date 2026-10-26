from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, SQLModel, select

from internal import db


class KickReservation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    reservation_time: datetime = Field(index=True)


def list_all_kick_reservations() -> List[KickReservation]:
    with db.get_session() as session:
        sql = select(KickReservation)
        return list(session.exec(sql).all())


def list_kick_reservations_by_user(user_id: int) -> List[KickReservation]:
    with db.get_session() as session:
        sql = select(KickReservation).where(KickReservation.user_id == user_id)
        return list(session.exec(sql).all())


def add_kick_reservation(user_id: int, reservation_time: datetime) -> KickReservation:
    with db.get_session() as session:
        obj = KickReservation(user_id=user_id, reservation_time=reservation_time)
        session.add(obj)
        return obj


def get_due_kick_reservations(before: datetime) -> List[KickReservation]:
    with db.get_session() as session:
        sql = select(KickReservation).where(KickReservation.reservation_time <= before)
        return list(session.exec(sql).all())


def remove_kick_reservation_by_id(_id: int) -> None:
    with db.get_session() as session:
        obj = session.get(KickReservation, _id)
        if obj:
            session.delete(obj)


def remove_kick_reservation_by_user(user_id: int) -> int:
    with db.get_session() as session:
        sql = select(KickReservation).where(KickReservation.user_id == user_id)
        objs = list(session.exec(sql).all())
        for o in objs:
            session.delete(o)
        return len(objs)
