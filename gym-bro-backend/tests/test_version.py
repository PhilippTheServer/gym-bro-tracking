"""The version the API reports is the one the backend and frontend packages declare."""

import json
import tomllib
from pathlib import Path

from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BACKEND_DIR.parent / "gym-bro-frontend"


def test_api_reports_the_backend_package_version() -> None:
    pyproject = tomllib.loads((BACKEND_DIR / "pyproject.toml").read_text())
    assert app.version == pyproject["project"]["version"]


def test_frontend_package_declares_the_same_version() -> None:
    package = json.loads((FRONTEND_DIR / "package.json").read_text())
    lock = json.loads((FRONTEND_DIR / "package-lock.json").read_text())
    assert package["version"] == app.version
    assert lock["version"] == app.version
    assert lock["packages"][""]["version"] == app.version
