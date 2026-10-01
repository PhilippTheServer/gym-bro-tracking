"""Shared fixtures.

Pure-domain tests run anywhere. The API tests need a real Postgres because the models
use Postgres-specific column types; point TEST_DATABASE_URL at a throwaway database
or they are skipped:

    docker compose up -d postgres
    createdb -h localhost -U gymbro gymbro_test
    TEST_DATABASE_URL=postgresql+asyncpg://gymbro:gymbro_secret@localhost:5432/gymbro_test \\
        uv run pytest
"""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import get_current_user
from app.main import app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

requires_db = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not set")

OWNER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_ID = "22222222-2222-2222-2222-222222222222"
TEST_USER_HEADER = "x-test-user"


async def _user_from_header(request: Request) -> dict[str, str]:
    """
    Arg: request - the incoming request.
    Operation: stands in for Keycloak token validation, taking the subject from a header
               so each test client can act as a different user.
    Return: claims dict containing the caller's subject.
    """
    return {"sub": request.headers.get(TEST_USER_HEADER, OWNER_ID)}


@pytest.fixture(scope="session")
def schema() -> None:
    """
    Arg: none.
    Operation: builds the schema once per test run over a synchronous connection. DDL is
               deliberately not async — a session-scoped async fixture would bind itself
               to an event loop the individual tests do not share.
    Return: None.
    """
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set")
    sync_engine = create_engine(TEST_DATABASE_URL.replace("+asyncpg", "+psycopg2"))
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    yield
    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


@pytest_asyncio.fixture
async def session(schema) -> AsyncGenerator[AsyncSession]:
    """
    Arg: schema - ensures the tables exist before the first test.
    Operation: runs each test inside a transaction that is rolled back afterwards, so
               tests never see each other's rows. join_transaction_mode='create_savepoint'
               makes the application's own commit() release a savepoint instead of
               committing the outer transaction, which would defeat the rollback.
    Return: async session scoped to one test.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    connection = await engine.connect()
    transaction = await connection.begin()
    factory = async_sessionmaker(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    async with factory() as db_session:
        yield db_session
    await transaction.rollback()
    await connection.close()
    await engine.dispose()


def _client_for(session: AsyncSession, user_id: str) -> AsyncClient:
    """
    Arg: session - the test database session; user_id - subject to authenticate as.
    Operation: points the app's database dependency at the test session and resolves the
               caller's identity from a request header instead of a Keycloak token. The
               identity has to travel per request: dependency_overrides is global, so
               binding a fixed user here would make the second client's override apply to
               the first client too.
    Return: an httpx client bound to the ASGI app, tagged with the given identity.
    """

    async def _override_db() -> AsyncGenerator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _user_from_header
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={TEST_USER_HEADER: user_id},
    )


@pytest_asyncio.fixture
async def client(session) -> AsyncGenerator[AsyncClient]:
    """
    Arg: session - the test database session.
    Operation: yields an API client authenticated as the owning user.
    Return: httpx AsyncClient.
    """
    async with _client_for(session, OWNER_ID) as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def other_client(session) -> AsyncGenerator[AsyncClient]:
    """
    Arg: session - the test database session.
    Operation: yields an API client authenticated as a different user, for checking that
               ownership is enforced.
    Return: httpx AsyncClient.
    """
    async with _client_for(session, OTHER_ID) as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def exercise(client: AsyncClient) -> dict:
    """
    Arg: client - authenticated API client.
    Operation: creates one exercise to hang templates and sessions off.
    Return: the created exercise as a dict.
    """
    response = await client.post(
        "/api/v1/exercises",
        json={"name": "Barbell Bench Press", "muscle_group": "chest", "equipment": "barbell"},
    )
    assert response.status_code == 201, response.text
    return response.json()
