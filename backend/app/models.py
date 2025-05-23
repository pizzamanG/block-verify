from sqlmodel import SQLModel, Field
from datetime import datetime
class Device(SQLModel, table=True):
    id: str = Field(primary_key=True)   # SHA-256(pubkey)
    token_hash: str
    exp: datetime
