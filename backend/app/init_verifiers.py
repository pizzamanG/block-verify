from .db import DBSession, engine, SQLModel
from .verifier import Verifier
from uuid import uuid4

SQLModel.metadata.create_all(engine)

with DBSession() as s:
    if not s.query(Verifier).first():
        key = uuid4().hex
        verifier = Verifier(name="DefaultDev", api_key=key)
        s.add(verifier)
        s.commit()
        print("API key:", key)
    else:
        print("Verifier already initialized.")