from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, select
from internal import db


class FacebookPostedId(SQLModel, table=True):
    """Stores Facebook post IDs that have been posted to Discord."""

    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.now)


class FacebookCommentCheckQueue(SQLModel, table=True):
    """Queue of Facebook posts waiting for comment source verification."""

    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: str = Field(unique=True)
    post_data: str  # JSON-serialized post data
    created_time: datetime = Field(index=True)


def check_posted_id_exists(post_id: str) -> bool:
    """Check if a post ID has been posted."""
    with db.get_session() as session:
        sql = select(FacebookPostedId).where(FacebookPostedId.post_id == post_id)
        return session.exec(sql).first() is not None


def add_posted_id(post_id: str) -> FacebookPostedId | None:
    """Add a post ID to the posted list."""
    with db.get_session() as session:
        sql = select(FacebookPostedId).where(FacebookPostedId.post_id == post_id)
        if session.exec(sql).first():
            return None

        obj = FacebookPostedId(post_id=post_id)
        session.add(obj)
        return obj


def list_all_posted_ids() -> List[str]:
    """Get all posted post IDs."""
    with db.get_session() as session:
        sql = select(FacebookPostedId).order_by(FacebookPostedId.created_at)
        return [obj.post_id for obj in session.exec(sql).all()]


def add_comment_check_queue(post_id: str, post_data: str, created_time: datetime) -> FacebookCommentCheckQueue:
    """Add a post to the comment check queue."""
    with db.get_session() as session:
        obj = FacebookCommentCheckQueue(post_id=post_id, post_data=post_data, created_time=created_time)
        session.add(obj)
        return obj


def get_due_comment_checks(before_or_equal: datetime) -> List[FacebookCommentCheckQueue]:
    """Get posts that are ready for comment check (created <= before_or_equal time)."""
    with db.get_session() as session:
        sql = select(FacebookCommentCheckQueue).where(FacebookCommentCheckQueue.created_time <= before_or_equal)
        return list(session.exec(sql).all())


def remove_comment_check_by_id(_id: int) -> None:
    """Remove a post from comment check queue by ID."""
    with db.get_session() as session:
        obj = session.get(FacebookCommentCheckQueue, _id)
        if obj:
            session.delete(obj)


def list_all_comment_checks() -> List[FacebookCommentCheckQueue]:
    """Get all posts in comment check queue."""
    with db.get_session() as session:
        sql = select(FacebookCommentCheckQueue).order_by(FacebookCommentCheckQueue.created_time)
        return list(session.exec(sql).all())
