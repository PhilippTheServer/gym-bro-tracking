"""API tests for the progress aggregates."""

from httpx import AsyncClient

from tests.conftest import requires_db

pytestmark = requires_db


async def _completed_session(client: AsyncClient, exercise_id: str) -> dict:
    session = (
        await client.post(
            "/api/v1/workouts",
            json={
                "name": "Push Day",
                "exercises": [
                    {
                        "exercise_id": exercise_id,
                        "sets": [
                            {"set_type": "working_set", "weight": 100.0, "reps": 5},
                            {"set_type": "working_set", "weight": 80.0, "reps": 10},
                        ],
                    }
                ],
            },
        )
    ).json()
    for entry in session["exercises"][0]["sets"]:
        await client.patch(
            f"/api/v1/workouts/{session['id']}/sets/{entry['id']}", json={"completed": True}
        )
    return (await client.post(f"/api/v1/workouts/{session['id']}/finish")).json()


async def test_empty_account_reports_zeroes(client: AsyncClient) -> None:
    overview = (await client.get("/api/v1/progress/overview")).json()
    assert overview["total_workouts"] == 0
    assert overview["total_volume"] == 0
    assert overview["personal_records"] == []


async def test_overview_counts_volume_and_personal_records(
    client: AsyncClient, exercise: dict
) -> None:
    await _completed_session(client, exercise["id"])
    overview = (await client.get("/api/v1/progress/overview")).json()

    assert overview["total_workouts"] == 1
    assert overview["total_sets"] == 2
    assert overview["total_volume"] == 100.0 * 5 + 80.0 * 10
    assert overview["current_streak"] == 1

    record = overview["personal_records"][0]
    assert record["exercise_name"] == "Barbell Bench Press"
    # Epley rates 100kg x 5 (116.7) above 80kg x 10 (106.7), so that is the PR.
    assert record["weight"] == 100.0
    assert record["reps"] == 5
    assert record["estimated_1rm"] == 116.7


async def test_unfinished_sessions_do_not_count(client: AsyncClient, exercise: dict) -> None:
    await client.post(
        "/api/v1/workouts",
        json={
            "name": "In progress",
            "exercises": [
                {
                    "exercise_id": exercise["id"],
                    "sets": [{"set_type": "working_set", "weight": 100.0, "reps": 5}],
                }
            ],
        },
    )
    overview = (await client.get("/api/v1/progress/overview")).json()
    assert overview["total_workouts"] == 0
    assert overview["total_sets"] == 0


async def test_two_sessions_on_one_day_both_count(client: AsyncClient, exercise: dict) -> None:
    await _completed_session(client, exercise["id"])
    await _completed_session(client, exercise["id"])
    overview = (await client.get("/api/v1/progress/overview")).json()
    # Regression: this used to de-duplicate by date and report 1.
    assert overview["total_workouts"] == 2


async def test_exercise_progress_has_a_point_per_session(
    client: AsyncClient, exercise: dict
) -> None:
    await _completed_session(client, exercise["id"])
    detail = (await client.get(f"/api/v1/progress/exercises/{exercise['id']}")).json()

    assert detail["exercise_name"] == "Barbell Bench Press"
    assert len(detail["points"]) == 1
    assert detail["points"][0]["max_weight"] == 100.0
    assert detail["points"][0]["total_volume"] == 100.0 * 5 + 80.0 * 10


async def test_progress_is_per_user(
    client: AsyncClient, other_client: AsyncClient, exercise: dict
) -> None:
    await _completed_session(client, exercise["id"])
    overview = (await other_client.get("/api/v1/progress/overview")).json()
    assert overview["total_workouts"] == 0
