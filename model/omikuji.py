from typing import List, Optional
from datetime import date, datetime
from sqlmodel import Field, SQLModel, select
from internal import db, utils

class OmikujiDraw(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    draw_date: date = Field(index=True)

def _today() -> date:
    return datetime.now(utils.TIME_ZONE).date()

def has_drawn(user_id: int, draw_date: Optional[date] = None) -> bool:
    if draw_date is None:
        draw_date = _today()
    with db.get_session() as session:
        sql = select(OmikujiDraw).where(OmikujiDraw.user_id == user_id, OmikujiDraw.draw_date == draw_date)
        return session.exec(sql).first() is not None

def record_draw(user_id: int, draw_date: Optional[date] = None) -> OmikujiDraw:
    if draw_date is None:
        draw_date = _today()
    with db.get_session() as session:
        sql = select(OmikujiDraw).where(OmikujiDraw.user_id == user_id, OmikujiDraw.draw_date == draw_date)
        obj = session.exec(sql).first()
        if obj is None:
            obj = OmikujiDraw(user_id=user_id, draw_date=draw_date)
            session.add(obj)
        return obj

def reset_user(user_id: int, draw_date: Optional[date] = None) -> None:
    if draw_date is None:
        draw_date = _today()
    with db.get_session() as session:
        sql = select(OmikujiDraw).where(OmikujiDraw.user_id == user_id, OmikujiDraw.draw_date == draw_date)
        objs = session.exec(sql).all()
        for o in objs:
            session.delete(o)

def reset_all(draw_date: Optional[date] = None) -> None:
    if draw_date is None:
        draw_date = _today()
    with db.get_session() as session:
        sql = select(OmikujiDraw).where(OmikujiDraw.draw_date == draw_date)
        objs = session.exec(sql).all()
        for o in objs:
            session.delete(o)

def list_all(draw_date: Optional[date] = None) -> List[int]:
    if draw_date is None:
        draw_date = _today()
    with db.get_session() as session:
        sql = select(OmikujiDraw).where(OmikujiDraw.draw_date == draw_date)
        return [o.user_id for o in session.exec(sql).all()]
