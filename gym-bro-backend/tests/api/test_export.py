"""API tests for the export endpoint daily uses to pull completed workouts."""

from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_export_caller
from app.domain.models.workout import WorkoutSession
from app.main import app
from tests.conftest import OWNER_ID, requires_db

pytestmark = requires_db

EXPORT_CLIENT_ID = "daily-gymbro-sync"


async def _export_client(session: AsyncSession) -> AsyncClient:
    """
    Arg: session - the test database session to bind the app to.
    Operation: builds a client with get_db and get_export_caller overridden, standing in
               for a request bearing a valid export-client token.
    Return: an httpx client bound to the ASGI app.
    """

    async def _override_db():
        yield session

    async def _override_export_caller() -> dict[str, str]:
        return {"azp": EXPORT_CLIENT_ID}

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_export_caller] = _override_export_caller
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _set_completed_at(session: AsyncSession, session_id: str, completed_at: datetime) -> None:
    """
    Arg: session - the test database session; session_id - session to update;
         completed_at - the timestamp to force onto the row.
    Operation: writes completed_at directly, bypassing the finish-session use case, so
               tests can control ordering without waiting on real time.
    Return: None.
    """
    await session.execute(
        update(WorkoutSession)
        .where(WorkoutSession.id == session_id)
        .values(completed_at=completed_at)
    )
    await session.commit()


async def _start_and_finish(client: AsyncClient, exercise_id: str) -> dict:
    """
    Arg: client - authenticated API client; exercise_id - exercise to log a set against.
    Operation: starts a session with one exercise and one set, then finishes it.
    Return: the finished session as a dict.
    """
    response = await client.post(
        "/api/v1/workouts",
        json={
            "name": "Push Day",
            "exercises": [
                {
                    "exercise_id": exercise_id,
                    "sets": [{"set_type": "working_set", "weight": 90.0, "reps": 5}],
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    started = response.json()
    finished = await client.post(f"/api/v1/workouts/{started['id']}/finish")
    assert finished.status_code == 200, finished.text
    return finished.json()


async def test_export_returns_only_the_session_completed_after_the_cutoff(
    client: AsyncClient, other_client: AsyncClient, session: AsyncSession, exercise: dict
) -> None:
    older = await _start_and_finish(client, exercise["id"])
    newer = await _start_and_finish(client, exercise["id"])
    await client.post("/api/v1/workouts", json={"name": "Active", "exercises": []})
    await _start_and_finish(other_client, exercise["id"])

    await _set_completed_at(session, older["id"], datetime(2026, 9, 1, tzinfo=UTC))
    await _set_completed_at(session, newer["id"], datetime(2026, 9, 10, tzinfo=UTC))

    async with await _export_client(session) as export_client:
        response = await export_client.get(
            "/api/v1/export/workouts",
            params={"user_id": OWNER_ID, "completed_after": "2026-09-05T00:00:00Z"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert [entry["id"] for entry in body] == [newer["id"]]
    assert body[0]["exercises"][0]["exercise"]["id"] == exercise["id"]
    assert len(body[0]["exercises"][0]["sets"]) == 1


async def test_export_returns_both_sessions_in_ascending_order(
    client: AsyncClient, other_client: AsyncClient, session: AsyncSession, exercise: dict
) -> None:
    older = await _start_and_finish(client, exercise["id"])
    newer = await _start_and_finish(client, exercise["id"])
    await client.post("/api/v1/workouts", json={"name": "Active", "exercises": []})
    await _start_and_finish(other_client, exercise["id"])

    await _set_completed_at(session, older["id"], datetime(2026, 9, 1, tzinfo=UTC))
    await _set_completed_at(session, newer["id"], datetime(2026, 9, 10, tzinfo=UTC))

    async with await _export_client(session) as export_client:
        response = await export_client.get(
            "/api/v1/export/workouts",
            params={"user_id": OWNER_ID, "completed_after": "2026-01-01T00:00:00Z"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert [entry["id"] for entry in body] == [older["id"], newer["id"]]


async def test_export_rejects_a_naive_completed_after(
    client: AsyncClient, session: AsyncSession, exercise: dict
) -> None:
    await _start_and_finish(client, exercise["id"])

    async with await _export_client(session) as export_client:
        response = await export_client.get(
            "/api/v1/export/workouts",
            params={"user_id": OWNER_ID, "completed_after": "2026-09-05T00:00:00"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 422, response.text
