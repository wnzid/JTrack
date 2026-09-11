"""User database lifecycle and administration commands."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Leader', 'Manager')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db() -> sqlite3.Connection:
    if "users_db" not in g:
        path = Path(current_app.config["USERS_DATABASE"])
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        g.users_db = connection
    return g.users_db


def close_db(_error=None) -> None:
    connection = g.pop("users_db", None)
    if connection is not None:
        connection.close()


def initialize() -> None:
    get_db().executescript(SCHEMA)
    get_db().commit()


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    initialize()
    click.echo("Initialized the JTrack user database.")


@click.command("create-user")
@click.option("--email", prompt=True)
@click.option(
    "--role", type=click.Choice(["Leader", "Manager"], case_sensitive=False), prompt=True
)
@click.password_option(confirmation_prompt=True)
@with_appcontext
def create_user_command(email: str, role: str, password: str) -> None:
    normalized_email = email.strip().lower()
    normalized_role = role.title()
    if len(password) < 12:
        raise click.ClickException("Password must contain at least 12 characters.")
    try:
        get_db().execute(
            "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
            (normalized_email, generate_password_hash(password), normalized_role),
        )
        get_db().commit()
    except sqlite3.IntegrityError as exc:
        raise click.ClickException("That email is already registered.") from exc
    click.echo(f"Created {normalized_role} account for {normalized_email}.")


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_user_command)
    with app.app_context():
        initialize()
