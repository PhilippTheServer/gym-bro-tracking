"""API tests for restructuring a session while it is running, and for last-performance."""

from httpx import AsyncClient

from tests.conftest import requires_db

pytestmark = requires_db


async def _exercise(client: AsyncClient, name: str, muscle_group: str = "chest") -> dict:
    response = await client.post(
        "/api/v1/exercises",
        json={"name": name, "muscle_group": muscle_group, "equipment": "barbell"},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _session_of(client: AsyncClient, *exercise_ids: str) -> dict:
    response = await client.post(
        "/api/v1/workouts",
        json={
            "name": "Push Day",
            "exercises": [
                {
                    "exercise_id": exercise_id,
                    "sets": [{"set_type": "working_set", "weight": 80.0, "reps": 8}],
                }
                for exercise_id in exercise_ids
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_removing_an_exercise_closes_the_gap_in_the_ordering(
    client: AsyncClient, exercise: dict
) -> None:
    """A hole in the ordering would leave the remaining exercises sorted by chance."""
    bench = exercise
    row = await _exercise(client, "Barbell Row", "back")
    curl = await _exercise(client, "Barbell Curl", "biceps")
    session = await _session_of(client, bench["id"], row["id"], curl["id"])

    response = await client.delete(
        f"/api/v1/workouts/{session['id']}/exercises/{session['exercises'][1]['id']}"
    )

    assert response.status_code == 200, response.text
    remaining = response.json()["exercises"]
    assert [entry["exercise"]["name"] for entry in remaining] == [
        "Barbell Bench Press",
        "Barbell Curl",
    ]
    assert [entry["order"] for entry in remaining] == [0, 1]


async def test_removing_an_exercise_takes_its_sets_with_it(
    client: AsyncClient, exercise: dict
) -> None:
    session = await _session_of(client, exercise["id"])
    response = await client.delete(
        f"/api/v1/workouts/{session['id']}/exercises/{session['exercises'][0]['id']}"
    )
    assert response.json()["exercises"] == []


async def test_exercises_can_be_reordered(client: AsyncClient, exercise: dict) -> None:
    row = await _exercise(client, "Barbell Row", "back")
    session = await _session_of(client, exercise["id"], row["id"])
    first, second = (entry["id"] for entry in session["exercises"])

    response = await client.patch(
        f"/api/v1/workouts/{session['id']}/exercises/reorder",
        json={"exercise_ids": [second, first]},
    )

    assert response.status_code == 200, response.text
    reordered = response.json()["exercises"]
    assert [entry["id"] for entry in reordered] == [second, first]
    assert [entry["order"] for entry in reordered] == [0, 1]


async def test_a_reorder_that_omits_an_exercise_is_rejected(
    client: AsyncClient, exercise: dict
) -> None:
    """Accepting a partial list would leave two exercises sharing an order value."""
    row = await _exercise(client, "Barbell Row", "back")
    session = await _session_of(client, exercise["id"], row["id"])

    response = await client.patch(
        f"/api/v1/workouts/{session['id']}/exercises/reorder",
        json={"exercise_ids": [session["exercises"][0]["id"]]},
    )

    assert response.status_code == 422


async def test_swapping_the_exercise_keeps_the_sets_already_logged(
    client: AsyncClient, exercise: dict
) -> None:
    """The rack is taken, you move to dumbbells — the sets you already did still count."""
    dumbbells = await _exercise(client, "Dumbbell Bench Press")
    session = await _session_of(client, exercise["id"])
    entry_id = session["exercises"][0]["id"]

    response = await client.patch(
        f"/api/v1/workouts/{session['id']}/exercises/{entry_id}",
        json={"exercise_id": dumbbells["id"]},
    )

    assert response.status_code == 200, response.text
    entry = response.json()["exercises"][0]
    assert entry["exercise"]["name"] == "Dumbbell Bench Press"
    assert [(s["weight"], s["reps"]) for s in entry["sets"]] == [(80.0, 8)]


async def test_another_user_cannot_restructure_the_session(
    client: AsyncClient, other_client: AsyncClient, exercise: dict
) -> None:
    session = await _session_of(client, exercise["id"])
    entry_id = session["exercises"][0]["id"]

    assert (
        await other_client.delete(f"/api/v1/workouts/{session['id']}/exercises/{entry_id}")
    ).status_code == 403
    assert (
        await other_client.patch(
            f"/api/v1/workouts/{session['id']}/exercises/reorder",
            json={"exercise_ids": [entry_id]},
        )
    ).status_code == 403
    assert (
        await other_client.patch(
            f"/api/v1/workouts/{session['id']}/exercises/{entry_id}", json={"notes": "mine now"}
        )
    ).status_code == 403


async def test_last_performance_returns_the_completed_sets_of_the_last_session(
    client: AsyncClient, exercise: dict
) -> None:
    session = await _session_of(client, exercise["id"])
    session_set = session["exercises"][0]["sets"][0]
    await client.patch(
        f"/api/v1/workouts/{session['id']}/sets/{session_set['id']}",
        json={"completed": True, "weight": 82.5, "reps": 7},
    )
    await client.post(f"/api/v1/workouts/{session['id']}/finish")

    performance = (await client.get(f"/api/v1/exercises/{exercise['id']}/last-performance")).json()

    assert performance["exercise_id"] == exercise["id"]
    assert [(s["weight"], s["reps"]) for s in performance["sets"]] == [(82.5, 7)]


async def test_last_performance_ignores_sets_that_were_never_ticked_off(
    client: AsyncClient, exercise: dict
) -> None:
    """A set left unticked records an intention, not a lift."""
    session = await _session_of(client, exercise["id"])
    await client.post(f"/api/v1/workouts/{session['id']}/finish")

    performance = (await client.get(f"/api/v1/exercises/{exercise['id']}/last-performance")).json()

    assert performance is None


async def test_last_performance_is_null_for_an_exercise_never_trained(
    client: AsyncClient, exercise: dict
) -> None:
    response = await client.get(f"/api/v1/exercises/{exercise['id']}/last-performance")
    assert response.status_code == 200
    assert response.json() is None


async def test_last_performance_does_not_leak_between_users(
    client: AsyncClient, other_client: AsyncClient, exercise: dict
) -> None:
    session = await _session_of(client, exercise["id"])
    session_set = session["exercises"][0]["sets"][0]
    await client.patch(
        f"/api/v1/workouts/{session['id']}/sets/{session_set['id']}", json={"completed": True}
    )
    await client.post(f"/api/v1/workouts/{session['id']}/finish")

    assert (
        await other_client.get(f"/api/v1/exercises/{exercise['id']}/last-performance")
    ).json() is None
