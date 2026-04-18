import sys
import os

# Allow bare module imports (models, core, etc.) as in production code
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.pool import StaticPool

from main import app
from core.database import get_session
from api.routes_v1 import get_current_user
from models.models import User

# Stub admin user returned by all protected routes in tests
_TEST_USER = User(id=1, name="Test Admin", username="admin", password_hash="x", role_id=None)


def _make_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def client():
    """Test client with auth bypassed via get_current_user override."""
    engine = _make_engine()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user] = lambda: _TEST_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def raw_client():
    """Test client with real auth enforcement (no get_current_user override)."""
    engine = _make_engine()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)
