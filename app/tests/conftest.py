import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-do-not-use-in-production")

# Patch DB engine to SQLite before importing app
import app.database as _db_module

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_db_module.engine = _test_engine

from app.main import app  # noqa: E402
from app.core.base import Base  # noqa: E402
from app.core.security import get_db  # noqa: E402

Base.metadata.create_all(bind=_test_engine)


def _override_get_db():
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate all tables before each test for isolation."""
    yield
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _register(client, email: str, password: str = "password123"):
    res = client.post("/auth/register", json={"email": email, "password": password})
    assert res.status_code == 201, res.json()
    return {"email": email, "password": password, "id": res.json()["id"]}


def _login(client, email: str, password: str = "password123") -> dict:
    res = client.post("/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200, res.json()
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner(client):
    user = _register(client, "owner@example.com")
    user["headers"] = _login(client, user["email"])
    return user


@pytest.fixture
def admin_user(client):
    user = _register(client, "admin@example.com")
    user["headers"] = _login(client, user["email"])
    return user


@pytest.fixture
def member_user(client):
    user = _register(client, "member@example.com")
    user["headers"] = _login(client, user["email"])
    return user


@pytest.fixture
def outsider(client):
    user = _register(client, "outsider@example.com")
    user["headers"] = _login(client, user["email"])
    return user


# ---------------------------------------------------------------------------
# Resource helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def org(client, owner):
    res = client.post(
        "/orgs/",
        json={"name": "Acme Corp", "slug": "acme"},
        headers=owner["headers"],
    )
    assert res.status_code == 201, res.json()
    return res.json()


@pytest.fixture
def org_with_admin(client, org, owner, admin_user):
    """Org where admin_user has admin role."""
    client.post(
        f"/orgs/{org['id']}/members",
        json={"email": admin_user["email"], "role": "admin"},
        headers=owner["headers"],
    )
    return org


@pytest.fixture
def org_with_member(client, org_with_admin, owner, member_user):
    """Org where member_user has member role."""
    client.post(
        f"/orgs/{org_with_admin['id']}/members",
        json={"email": member_user["email"], "role": "member"},
        headers=owner["headers"],
    )
    return org_with_admin


@pytest.fixture
def project(client, org_with_admin, owner):
    res = client.post(
        f"/orgs/{org_with_admin['id']}/projects/",
        json={"name": "Alpha", "description": "First project"},
        headers=owner["headers"],
    )
    assert res.status_code == 201, res.json()
    return res.json()


@pytest.fixture
def issue(client, project, org_with_admin, owner):
    res = client.post(
        f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/",
        json={"title": "First issue", "description": "Needs work"},
        headers=owner["headers"],
    )
    assert res.status_code == 201, res.json()
    return res.json()
