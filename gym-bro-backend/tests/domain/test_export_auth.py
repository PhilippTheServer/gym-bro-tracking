"""Unit tests for the export-caller authorisation rule (no DB required)."""

import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.security import (
    _assert_export_client,
    _assert_intended_for_this_client,
)


def test_assert_export_client_passes_for_the_configured_client_id(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "export_client_id", "daily-gymbro-sync")
    _assert_export_client({"azp": "daily-gymbro-sync"})


def test_assert_export_client_rejects_another_azp(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "export_client_id", "daily-gymbro-sync")
    with pytest.raises(HTTPException) as exc_info:
        _assert_export_client({"azp": "some-other-client"})
    assert exc_info.value.status_code == 403


def test_assert_export_client_rejects_when_setting_is_empty(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "export_client_id", "")
    with pytest.raises(HTTPException) as exc_info:
        _assert_export_client({"azp": "daily-gymbro-sync"})
    assert exc_info.value.status_code == 403


def test_regular_user_routes_reject_a_token_issued_for_the_export_client(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "keycloak_client_id", "gym-bro-app")
    with pytest.raises(HTTPException) as exc_info:
        _assert_intended_for_this_client({"azp": "daily-gymbro-sync"})
    assert exc_info.value.status_code == 401
