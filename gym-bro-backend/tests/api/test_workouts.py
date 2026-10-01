"""API tests for workout sessions and their sets."""

from httpx import AsyncClient

from tests.conftest import requires_db

pytestmark = requires_db


async def _start_session(client: AsyncClient, exercise_id: str) -> dict:
    response = await client.post(
        "/api/v1/workouts",
        json={
            "name": "Push Day",
            "exercises": [
                {
                    "exercise_id": exercise_id,
                    "sets": [
                        {"set_type": "working_set", "weight": 90.0, "reps": 5},
                        {"set_type": "working_set", "weight": 95.0, "reps": 3},
                    ],
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_start_session_persists_exercises_and_sets(
    client: AsyncClient, exercise: dict
) -> None:
    session = await _start_session(client, exercise["id"])
    assert session["completed_at"] is None
    assert len(session["exercises"][0]["sets"]) == 2
    assert [entry["order"] for entry in session["exercises"][0]["sets"]] == [0, 1]


async def test_active_session_is_returned_until_finished(
    client: AsyncClient, exercise: dict
) -> None:
    session = await _start_session(client, exercise["id"])
    active = (await client.get("/api/v1/workouts/active")).json()
    assert active["id"] == session["id"]

    finished = (await client.post(f"/api/v1/workouts/{session['id']}/finish")).json()
    assert finished["completed_at"] is not None
    assert (await client.get("/api/v1/workouts/active")).json() is None


async def test_added_set_appears_in_the_response(client: AsyncClient, exercise: dict) -> None:
    session = await _start_session(client, exercise["id"])
    session_exercise_id = session["exercises"][0]["id"]

    response = await client.post(
        f"/api/v1/workouts/{session['id']}/exercises/{session_exercise_id}/sets",
        json={"set_type": "until_failure", "weight": 80.0, "reps": 9},
    )
    assert response.status_code == 200, response.text
    sets = response.json()["exercises"][0]["sets"]
    # Regression: the reload used to return the pre-write state from the identity map.
    assert len(sets) == 3
    assert sets[-1]["order"] == 2


async def test_set_can_be_completed_then_deleted(client: AsyncClient, exercise: dict) -> None:
    session = await _start_session(client, exercise["id"])
    first_set = session["exercises"][0]["sets"][0]

    updated = (
        await client.patch(
            f"/api/v1/workouts/{session['id']}/sets/{first_set['id']}",
            json={"completed": True},
        )
    ).json()
    assert updated["exercises"][0]["sets"][0]["completed"] is True

    after_delete = (
        await client.delete(f"/api/v1/workouts/{session['id']}/sets/{first_set['id']}")
    ).json()
    assert len(after_delete["exercises"][0]["sets"]) == 1


async def test_exercise_can_be_added_mid_session(client: AsyncClient, exercise: dict) -> None:
    session = await _start_session(client, exercise["id"])
    response = await client.post(
        f"/api/v1/workouts/{session['id']}/exercises",
        json={"exercise_id": exercise["id"], "sets": []},
    )
    assert response.status_code == 200, response.text
    exercises = response.json()["exercises"]
    assert len(exercises) == 2
    assert exercises[1]["order"] == 1


async def test_history_only_lists_finished_sessions(client: AsyncClient, exercise: dict) -> None:
    session = await _start_session(client, exercise["id"])
    assert (await client.get("/api/v1/workouts")).json() == []

    await client.post(f"/api/v1/workouts/{session['id']}/finish")
    history = (await client.get("/api/v1/workouts")).json()
    assert [entry["id"] for entry in history] == [session["id"]]
    # Regression: nested relations must be eager-loaded for the list response.
    assert history[0]["exercises"][0]["exercise"]["id"] == exercise["id"]


async def test_another_user_cannot_touch_the_session(
    client: AsyncClient, other_client: AsyncClient, exercise: dict
) -> None:
    session = await _start_session(client, exercise["id"])
    assert (await other_client.get(f"/api/v1/workouts/{session['id']}")).status_code == 403
    assert (await other_client.delete(f"/api/v1/workouts/{session['id']}")).status_code == 403
    assert (await other_client.get("/api/v1/workouts/active")).json() is None
