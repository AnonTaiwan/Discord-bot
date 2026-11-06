from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint, select

from internal import db


class UserWebhookData(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "channel_id", name="uq_user_channel"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(nullable=False)
    channel_id: int = Field(nullable=False)
    webhook_id: int = Field(nullable=False)
    webhook_token: str = Field(nullable=False)
    name: str = Field(nullable=False)
    icon: bytes = Field(nullable=False)


def get_webhook_data(user_id: int, channel_id: int) -> UserWebhookData | None:
    with db.get_session() as session:
        return session.exec(
            select(UserWebhookData).where(UserWebhookData.user_id == user_id, UserWebhookData.channel_id == channel_id)
        ).first()


async def update_user_webhook(user_id: int, channel_id: int, webhook_id: int, webhook_token: str, name: str, icon: bytes):
    with db.get_session() as session:
        user_webhook_data = session.exec(
            select(UserWebhookData).where(UserWebhookData.user_id == user_id, UserWebhookData.channel_id == channel_id)
        ).first()
        if user_webhook_data:
            user_webhook_data.webhook_id = webhook_id
            user_webhook_data.webhook_token = webhook_token
            user_webhook_data.name = name
            user_webhook_data.icon = icon
        else:
            user_webhook_data = UserWebhookData(
                user_id=user_id, channel_id=channel_id, webhook_id=webhook_id, webhook_token=webhook_token, name=name, icon=icon
            )
            session.add(user_webhook_data)
