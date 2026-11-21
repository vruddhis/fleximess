"""Test fixtures.

Tests run against the database in backend/.env (Supabase), but every test runs
inside a single outer transaction that is ROLLED BACK afterwards. The app's own
db.commit() calls only release SAVEPOINTs inside that transaction
(join_transaction_mode="create_savepoint"), so nothing is ever committed.

As an extra guard, `_database_unchanged` snapshots every public table's row
count and the full column layout before the test session and fails the run if
anything differs afterwards.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app


def _snapshot():
    with engine.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        tables = c.execute(text(
            "select table_name from information_schema.tables "
            "where table_schema='public' and table_type='BASE TABLE' order by 1")).scalars().all()
        counts = {t: c.execute(text('select count(*) from public."%s"' % t)).scalar() for t in tables}
        columns = c.execute(text(
            "select table_name, column_name, data_type, is_nullable, coalesce(column_default,'') "
            "from information_schema.columns where table_schema='public' order by 1, ordinal_position")).all()
        constraints = c.execute(text(
            "select conrelid::regclass::text, conname, pg_get_constraintdef(oid) from pg_constraint "
            "where connamespace='public'::regnamespace order by 1, 2")).all()
        c.rollback()
    return {"counts": counts, "columns": [tuple(r) for r in columns], "constraints": [tuple(r) for r in constraints]}


@pytest.fixture(scope="session", autouse=True)
def _database_unchanged():
    before = _snapshot()
    yield
    after = _snapshot()
    assert after["columns"] == before["columns"], "Schema columns changed during tests!"
    assert after["constraints"] == before["constraints"], "Constraints changed during tests!"
    assert after["counts"] == before["counts"], f"Row counts changed during tests! before={before['counts']} after={after['counts']}"


@pytest.fixture
def db_session():
    conn = engine.connect()
    outer = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        conn.close()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def new_username():
    return "t_" + uuid.uuid4().hex[:12]


@pytest.fixture
def auth(client):
    """Sign up a throwaway user (rolled back with the test) and return auth headers."""
    username = new_username()
    r = client.post("/api/auth/signup", json={"name": "Test User", "username": username, "password": "password123"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}", "_username": username}


def headers(auth):
    return {"Authorization": auth["Authorization"]}
