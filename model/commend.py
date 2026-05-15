from sqlmodel import Field, SQLModel

class Commendation(SQLModel, table=True):
	id: int = Field(primary_key=True, default=None)
	user_id: int = Field(index=True)
	amount: int = Field(default=0, nullable=False)

