from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from jtrack import create_app  # noqa: E402


def create_analytics_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE reportdata (
                status TEXT,
                previous_offer_intake TEXT,
                previous_offer_year TEXT,
                is_the_offer_deferred TEXT,
                agentname TEXT,
                coursetype TEXT,
                startdate TEXT,
                offer_expiry_date TEXT,
                visa_status TEXT
            )
            """
        )
        connection.executemany(
            "INSERT INTO reportdata VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("Offered", "T1", "2026", "no", "A. Khan", "Higher Ed", "15/02/2026", "20/10/2026", "Student"),
                ("Enrolled - Active", "T1", "2026", "no", "A. Khan", "Higher Ed", "15/02/2026", "20/10/2026", "Student"),
                ("Deferred", "T2", "2026", "yes", "M. Chen", "VET", "01/07/2026", "02/11/2026", "Bridging"),
                ("Current Student", "T2", "2026", "no", "M. Chen", "VET", "01/07/2026", "02/11/2026", "Student"),
            ],
        )


@pytest.fixture()
def app(tmp_path):
    analytics_path = tmp_path / "analytics.db"
    create_analytics_database(analytics_path)
    return create_app(
        {
            "TESTING": True,
            "DEBUG": False,
            "SECRET_KEY": "test-secret-key",
            "USERS_DATABASE": str(tmp_path / "users.db"),
            "ANALYTICS_DATABASE": str(analytics_path),
            "EXCEL_DATA_PATH": str(tmp_path / "missing.xlsx"),
            "ALLOW_REGISTRATION": True,
            "ALLOW_ROLE_SELECTION": True,
        }
    )


@pytest.fixture()
def client(app):
    return app.test_client()


def login_as(client, role: str, email: str = "person@example.com") -> None:
    with client.session_transaction() as session:
        session["email"] = email
        session["role"] = role
        session["csrf_token"] = "test-csrf"
