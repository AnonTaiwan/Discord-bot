from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from internal import db, utils
from functools import wraps


class CommandLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    time: datetime = Field(
        default_factory=lambda: datetime.now(utils.TIME_ZONE),
        nullable=False,
    )
    user_name: str = Field(nullable=False)
    command_content: str = Field(nullable=False)
    user_id: Optional[int] = Field(default=None, index=True)


def record_log(user_name: str, command_content: str, user_id: Optional[int] = None) -> None:
    try:
        with db.get_session() as session:
            log_entry = CommandLog(
                user_name=user_name,
                command_content=command_content,
                user_id=user_id,
            )
            session.add(log_entry)
    except Exception as e:
        utils.get_logger("model.log").error(f"Failed to record command log to database: {e}")


def log_task(task_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            record_log(
                user_name="System",
                command_content=f"Task: {task_name}",
                user_id=None,
            )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
