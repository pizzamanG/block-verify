from sqlmodel import SQLModel, create_engine, Session
from .settings import settings

engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)

class DBSession:
    def __enter__(self): self.session = Session(engine); return self.session
    def __exit__(self, *_): self.session.close()

def get_session():
    """Dependency for FastAPI to inject database sessions"""
    with Session(engine) as session:
        yield session
