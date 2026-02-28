import pytest
from alembic import command as alembic_command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from app.config import settings
from app.database import get_session
from app.main import app
import app.models  # noqa: F401 — registers table metadata with SQLModel

test_engine = create_engine(settings.DATABASE_URL, echo=False)

alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


@pytest.fixture(autouse=True)
def setup_db():
    """Run migrations before each test, roll back to base after."""
    alembic_command.upgrade(alembic_cfg, "head")
    yield
    alembic_command.downgrade(alembic_cfg, "base")


@pytest.fixture
def session():
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def client(session):
    """TestClient wired to the test database session."""

    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
