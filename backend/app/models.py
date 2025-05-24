from sqlmodel import SQLModel, Field
from datetime import datetime
class Device(SQLModel, table=True):
    id: str = Field(primary_key=True)   # SHA-256(pubkey)
    token_hash: str
    exp: datetime


class Revoked(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token_hash: str  # sha256 hex of the JWT
    ts: datetime = Field(default_factory=datetime.utcnow)

