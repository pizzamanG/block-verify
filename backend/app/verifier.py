from sqlmodel import SQLModel, Field
from datetime import datetime

class Verifier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    api_key: str  # securely generated in production
    created: datetime = Field(default_factory=datetime.utcnow)