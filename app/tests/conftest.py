import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.pool import StaticPool

from main import app
from core.database import get_session
from core.limiter import limiter
from api.routes_v1 import get_current_user
from models.models import User, Role
from services.auth_service import encode_permissions, ALL_PERMISSIONS


def _make_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _bootstrap_admin_role(engine) -> int:
    """Insert a hidden test-only admin role; return its id.
    Uses a reserved name so it never collides with roles created inside tests."""
    with Session(engine) as session:
        role = Role(name="__test_admin__", permissions=encode_permissions(list(ALL_PERMISSIONS)))
        session.add(role)
        session.commit()
        session.refresh(role)
        return role.id


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset slowapi in-memory storage before every test to prevent bleed-over."""
    limiter._storage.reset()
    yield


@pytest.fixture(scope="function")
def client():
    """Test client with auth bypassed — current user is an admin with all permissions."""
    engine = _make_engine()
    role_id = _bootstrap_admin_role(engine)
    # id=9999 avoids collision with auto-assigned ids of users created inside tests
    test_user = User(id=9999, name="Test Admin", username="admin", password_hash="x", role_id=role_id)

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def barman_client():
    """Test client where the current user is a barman with only 'tables' permission."""
    engine = _make_engine()
    with Session(engine) as session:
        role = Role(name="barman", permissions=encode_permissions(["tables"]))
        session.add(role)
        session.commit()
        session.refresh(role)
        barman = User(id=2, name="Barman", username="barman", password_hash="x", role_id=role.id)

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user] = lambda: barman
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def raw_client():
    """Test client with real JWT auth enforcement (no get_current_user override)."""
    engine = _make_engine()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)
