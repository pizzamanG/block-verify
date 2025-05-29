from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid

class Device(SQLModel, table=True):
    id: str = Field(primary_key=True)   # SHA-256(pubkey)
    token_hash: str
    exp: datetime


class Revoked(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token_hash: str  # sha256 hex of the JWT
    ts: datetime = Field(default_factory=datetime.utcnow)


class Verifier(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    business_name: str
    contact_email: str = Field(unique=True)
    website_url: str
    use_case_description: str
    api_key: str  # SHA-256 hash of the actual API key
    status: str = Field(default="active")  # active, suspended, revoked
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    request_count: int = Field(default=0)

