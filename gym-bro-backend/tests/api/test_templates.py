"""API tests for workout templates."""

import pytest
from httpx import AsyncClient

from tests.conftest import requires_db

pytestmark = requires_db


def _template_payload(exercise_id: str, with_order: bool = True) -> dict:
    sets = [
        {"set_type": "warmup", "target_reps": 10, "target_weight": 40.0},
        {"set_type": "working_set", "target_reps": 5, "target_weight": 90.0},
    ]
    if with_order:
        for position, entry in enumerate(sets):
            entry["order"] = position
    exercise: dict = {"exercise_id": exercise_id, "sets": sets}
    if with_order:
        exercise["order"] = 0
    return {"name": "Push Day", "description": "Chest", "exercises": [exercise]}


async def test_create_returns_the_full_graph(client: AsyncClient, exercise: dict) -> None:
    response = await client.post("/api/v1/templates", json=_template_payload(exercise["id"]))
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Push Day"
    assert len(body["exercises"]) == 1
    assert len(body["exercises"][0]["sets"]) == 2
    assert body["exercises"][0]["exercise"]["name"] == "Barbell Bench Press"


async def test_create_without_order_numbers_them_by_position(
    client: AsyncClient, exercise: dict
) -> None:
    response = await client.post(
        "/api/v1/templates", json=_template_payload(exercise["id"], with_order=False)
    )
    assert response.status_code == 201, response.text
    sets = response.json()["exercises"][0]["sets"]
    assert [entry["order"] for entry in sets] == [0, 1]


async def test_list_includes_nested_exercises_and_sets(client: AsyncClient, exercise: dict) -> None:
    await client.post("/api/v1/templates", json=_template_payload(exercise["id"]))
    response = await client.get("/api/v1/templates")
    assert response.status_code == 200, response.text
    templates = response.json()
    assert len(templates) == 1
    # Regression: these used to be lazy-loaded and blew up during serialisation.
    assert templates[0]["exercises"][0]["exercise"]["id"] == exercise["id"]
    assert len(templates[0]["exercises"][0]["sets"]) == 2


async def test_update_replaces_the_exercise_graph(client: AsyncClient, exercise: dict) -> None:
    created = (
        await client.post("/api/v1/templates", json=_template_payload(exercise["id"]))
    ).json()
    response = await client.put(
        f"/api/v1/templates/{created['id']}",
        json={
            "name": "Pull Day",
            "exercises": [
                {
                    "exercise_id": exercise["id"],
                    "sets": [{"set_type": "working_set", "target_reps": 8}],
                }
            ],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "Pull Day"
    assert len(body["exercises"][0]["sets"]) == 1


async def test_delete_removes_the_template(client: AsyncClient, exercise: dict) -> None:
    created = (
        await client.post("/api/v1/templates", json=_template_payload(exercise["id"]))
    ).json()
    assert (await client.delete(f"/api/v1/templates/{created['id']}")).status_code == 204
    assert (await client.get(f"/api/v1/templates/{created['id']}")).status_code == 404


async def test_missing_template_is_a_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/templates/33333333-3333-3333-3333-333333333333")
    assert response.status_code == 404


@pytest.mark.parametrize("method", ["get", "delete"])
async def test_another_user_cannot_reach_the_template(
    client: AsyncClient, other_client: AsyncClient, exercise: dict, method: str
) -> None:
    created = (
        await client.post("/api/v1/templates", json=_template_payload(exercise["id"]))
    ).json()
    response = await getattr(other_client, method)(f"/api/v1/templates/{created['id']}")
    assert response.status_code == 403


async def test_another_user_sees_an_empty_list(
    client: AsyncClient, other_client: AsyncClient, exercise: dict
) -> None:
    await client.post("/api/v1/templates", json=_template_payload(exercise["id"]))
    assert (await other_client.get("/api/v1/templates")).json() == []


async def test_a_template_set_can_carry_a_rep_range(client: AsyncClient, exercise: dict) -> None:
    created = (
        await client.post(
            "/api/v1/templates",
            json={
                "name": "Hypertrophy",
                "exercises": [
                    {
                        "exercise_id": exercise["id"],
                        "sets": [
                            {"set_type": "working_set", "target_reps": 8, "target_reps_max": 12}
                        ],
                    }
                ],
            },
        )
    ).json()

    stored = created["exercises"][0]["sets"][0]
    assert (stored["target_reps"], stored["target_reps_max"]) == (8, 12)


async def test_a_rep_range_that_counts_backwards_is_rejected(
    client: AsyncClient, exercise: dict
) -> None:
    response = await client.post(
        "/api/v1/templates",
        json={
            "name": "Nonsense",
            "exercises": [
                {
                    "exercise_id": exercise["id"],
                    "sets": [{"set_type": "working_set", "target_reps": 12, "target_reps_max": 8}],
                }
            ],
        },
    )
    assert response.status_code == 422


async def test_a_template_exercise_keeps_its_note(client: AsyncClient, exercise: dict) -> None:
    created = (
        await client.post(
            "/api/v1/templates",
            json={
                "name": "Push Day",
                "exercises": [
                    {
                        "exercise_id": exercise["id"],
                        "notes": "Pause a beat on the chest.",
                        "sets": [{"set_type": "working_set", "target_reps": 5}],
                    }
                ],
            },
        )
    ).json()

    assert created["exercises"][0]["notes"] == "Pause a beat on the chest."
