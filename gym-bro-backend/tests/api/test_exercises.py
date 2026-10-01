"""API tests for the exercise library."""

from httpx import AsyncClient

from tests.conftest import requires_db

pytestmark = requires_db


async def test_create_and_fetch_a_custom_exercise(client: AsyncClient) -> None:
    created = (
        await client.post(
            "/api/v1/exercises",
            json={"name": "Zercher Squat", "muscle_group": "legs", "equipment": "barbell"},
        )
    ).json()
    assert created["is_custom"] is True

    fetched = (await client.get(f"/api/v1/exercises/{created['id']}")).json()
    assert fetched["name"] == "Zercher Squat"


async def test_search_filters_by_name(client: AsyncClient, exercise: dict) -> None:
    await client.post(
        "/api/v1/exercises",
        json={"name": "Front Squat", "muscle_group": "legs", "equipment": "barbell"},
    )
    results = (await client.get("/api/v1/exercises", params={"search": "squat"})).json()
    assert [entry["name"] for entry in results] == ["Front Squat"]


async def test_update_patches_only_supplied_fields(client: AsyncClient, exercise: dict) -> None:
    updated = (
        await client.patch(
            f"/api/v1/exercises/{exercise['id']}", json={"instructions": "Brace hard."}
        )
    ).json()
    assert updated["instructions"] == "Brace hard."
    assert updated["name"] == "Barbell Bench Press"


async def test_delete_removes_the_exercise(client: AsyncClient, exercise: dict) -> None:
    assert (await client.delete(f"/api/v1/exercises/{exercise['id']}")).status_code == 204
    assert (await client.get(f"/api/v1/exercises/{exercise['id']}")).status_code == 404


async def test_missing_exercise_is_a_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/exercises/44444444-4444-4444-4444-444444444444")
    assert response.status_code == 404


async def test_another_user_cannot_delete_a_custom_exercise(
    client: AsyncClient, other_client: AsyncClient, exercise: dict
) -> None:
    assert (await other_client.delete(f"/api/v1/exercises/{exercise['id']}")).status_code == 403
