"""Analytics data access with SQLite, Excel, and SharePoint adapters."""

from __future__ import annotations

import re
import sqlite3
from io import BytesIO
from pathlib import Path

import pandas as pd
from flask import current_app

from .reports import FALLBACK_QUERIES, ReportSpec


IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9_]+$")


def normalize_identifier(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return f"t_{normalized}" if normalized[:1].isdigit() else normalized or "unnamed"


def _validated_identifier(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if not IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError("Invalid table name.")
    return normalized


def _first_table(connection: sqlite3.Connection) -> str:
    row = connection.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name LIMIT 1"
    ).fetchone()
    if not row:
        raise RuntimeError("The analytics database contains no data tables.")
    return row[0]


def read_sqlite(name: str | None = None) -> pd.DataFrame:
    path = Path(current_app.config["ANALYTICS_DATABASE"])
    if not path.exists():
        raise FileNotFoundError("The analytics database has not been generated.")
    with sqlite3.connect(path) as connection:
        identifier = _validated_identifier(
            name or current_app.config.get("DEFAULT_SQLITE_TABLE")
        ) or _first_table(connection)
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name = ? AND type IN ('table', 'view')",
            (identifier,),
        ).fetchone()
        if not exists:
            raise LookupError(f"Unknown analytics table or view: {identifier}")
        return pd.read_sql_query(f'SELECT * FROM "{identifier}"', connection)


def read_excel() -> pd.DataFrame:
    path = Path(current_app.config["EXCEL_DATA_PATH"])
    if not path.exists():
        raise FileNotFoundError("The configured Excel data file does not exist.")
    return pd.read_excel(path, sheet_name=0)


def read_sharepoint() -> pd.DataFrame:
    required = ("SP_CLIENT_ID", "SP_CLIENT_SECRET", "SP_SITE_URL", "SP_FILE_PATH")
    if any(not current_app.config.get(name) for name in required):
        raise RuntimeError("SharePoint is enabled but its connection is incomplete.")
    try:
        from office365.runtime.auth.client_credential import ClientCredential
        from office365.sharepoint.client_context import ClientContext
    except ImportError as exc:
        raise RuntimeError("Install the SharePoint optional dependency to use this source.") from exc

    credentials = ClientCredential(
        current_app.config["SP_CLIENT_ID"], current_app.config["SP_CLIENT_SECRET"]
    )
    context = ClientContext(current_app.config["SP_SITE_URL"]).with_credentials(credentials)
    response = (
        context.web.get_file_by_server_relative_url(current_app.config["SP_FILE_PATH"])
        .download()
        .execute_query()
    )
    return pd.read_excel(BytesIO(response.content), sheet_name=0)


def read_dataset(table: str | None = None) -> tuple[pd.DataFrame, str]:
    if current_app.config["USE_SHAREPOINT"]:
        return read_sharepoint(), "sharepoint"
    if Path(current_app.config["ANALYTICS_DATABASE"]).exists():
        return read_sqlite(table), "sqlite"
    return read_excel(), "excel"


def _query_excel_fallback(query: str) -> pd.DataFrame:
    frame = read_excel().copy()
    frame.columns = [normalize_identifier(str(column)) for column in frame.columns]
    with sqlite3.connect(":memory:") as connection:
        frame.to_sql("reportdata", connection, index=False, if_exists="replace")
        return pd.read_sql_query(query, connection)


def read_report(spec: ReportSpec) -> tuple[pd.DataFrame, str]:
    query = FALLBACK_QUERIES[spec.view_name]
    database_path = Path(current_app.config["ANALYTICS_DATABASE"])
    if database_path.exists():
        with sqlite3.connect(database_path) as connection:
            view = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name = ? AND type IN ('table', 'view')",
                (spec.view_name,),
            ).fetchone()
            frame = pd.read_sql_query(
                f'SELECT * FROM "{spec.view_name}"' if view else query, connection
            )
        return frame, "sqlite"
    return _query_excel_fallback(query), "excel"


def records(frame: pd.DataFrame) -> list[dict]:
    cleaned = frame.astype(object).where(pd.notna(frame), None)
    return cleaned.to_dict(orient="records")
