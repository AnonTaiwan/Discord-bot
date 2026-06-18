from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, select
from internal import db, utils


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    channel_id: int = Field(index=True)
    role: str  # 'user' or 'assistant'
    content: str
    user_id: Optional[int] = Field(default=None, index=True)
    user_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utils.TIME_ZONE),
        index=True
    )


class ChatState(SQLModel, table=True):
    channel_id: int = Field(primary_key=True)
    summary: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(utils.TIME_ZONE))


def add_message(channel_id: int, role: str, content: str, user_id: Optional[int] = None, user_name: Optional[str] = None) -> ChatMessage:
    with db.get_session() as session:
        msg = ChatMessage(channel_id=channel_id, role=role, content=content, user_id=user_id, user_name=user_name)
        session.add(msg)
        return msg


def get_messages(channel_id: int) -> List[ChatMessage]:
    with db.get_session() as session:
        sql = select(ChatMessage).where(ChatMessage.channel_id == channel_id).order_by(ChatMessage.created_at.asc())
        return list(session.exec(sql).all())


def delete_messages(message_ids: List[int]) -> None:
    if not message_ids:
        return
    with db.get_session() as session:
        for mid in message_ids:
            msg = session.get(ChatMessage, mid)
            if msg:
                session.delete(msg)


def get_state(channel_id: int) -> ChatState:
    with db.get_session() as session:
        state = session.get(ChatState, channel_id)
        if not state:
            state = ChatState(channel_id=channel_id, summary=None)
            session.add(state)
            session.commit()
            # Refresh by retrieving it again
            state = session.get(ChatState, channel_id)
        return state


def update_summary(channel_id: int, summary: str) -> None:
    with db.get_session() as session:
        state = session.get(ChatState, channel_id)
        if not state:
            state = ChatState(channel_id=channel_id, summary=summary)
            session.add(state)
        else:
            state.summary = summary
            state.updated_at = datetime.now(utils.TIME_ZONE)
            session.add(state)


def clear_chat_history(channel_id: int) -> None:
    with db.get_session() as session:
        sql = select(ChatMessage).where(ChatMessage.channel_id == channel_id)
        messages = session.exec(sql).all()
        for msg in messages:
            session.delete(msg)
        state = session.get(ChatState, channel_id)
        if state:
            state.summary = None
            state.updated_at = datetime.now(utils.TIME_ZONE)
            session.add(state)
