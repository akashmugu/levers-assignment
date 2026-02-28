from sqlmodel import Session, create_engine

from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False, pool_size=40, max_overflow=0)


def get_session():
    with Session(engine) as session:
        yield session
