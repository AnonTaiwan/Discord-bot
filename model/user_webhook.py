from sqlmodel import SQLModel, Field, select

from internal import db

class UserWebhookData(SQLModel, table=True):
    __tablename__ = "user_webhooks"

    user_id: int = Field(primary_key=True)
    channel_id: int = Field(primary_key=True)
    webhook_id: int = Field(nullable=False)
    webhook_token: str = Field(nullable=False)

def get_webhook_data(user_id: int, channel_id: int) -> UserWebhookData | None:
    with db.get_session() as session:
        return session.exec(select(UserWebhookData).where(UserWebhookData.user_id == user_id, UserWebhookData.channel_id == channel_id)).first()

async def update_user_webhook(user_id: int, channel_id: int, webhook_id: int, webhook_token: str):
    with db.get_session() as session:
        user_webhook_data = get_webhook_data(user_id, channel_id)
        if user_webhook_data:
            user_webhook_data.webhook_id = webhook_id
            user_webhook_data.webhook_token = webhook_token
        else:
            user_webhook_data = UserWebhookData(user_id=user_id, channel_id=channel_id, webhook_id=webhook_id, webhook_token=webhook_token)
            session.add(user_webhook_data)