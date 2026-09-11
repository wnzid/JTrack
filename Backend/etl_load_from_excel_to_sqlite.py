"""Load an Excel workbook into an indexed, atomically replaced SQLite database."""

from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from jtrack.data import normalize_identifier
from jtrack.reports import FALLBACK_QUERIES


BASE_DIR = Path(__file__).resolve().parent
INDEX_CANDIDATES = {
    "id",
    "student_id",
    "application_id",
    "offer_id",
    "enrollment_id",
    "visa_id",
    "agent_id",
    "term",
    "intake",
    "status",
    "created_at",
    "updated_at",
    "offer_date",
    "offer_expiry_date",
    "startdate",
}


def unique_columns(columns) -> list[str]:
    """Normalize column names and suffix collisions deterministically."""
    counts: dict[str, int] = {}
    result: list[str] = []
    for column in columns:
        base = normalize_identifier(str(column))
        counts[base] = counts.get(base, 0) + 1
        result.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return result


def read_workbook(path: Path) -> dict[str, pd.DataFrame]:
    if not path.is_file():
        raise FileNotFoundError(f"Excel workbook not found: {path}")
    workbook = pd.ExcelFile(path)
    sheets: dict[str, pd.DataFrame] = {}
    for sheet_name in workbook.sheet_names:
        frame = pd.read_excel(workbook, sheet_name=sheet_name)
        frame.columns = unique_columns(frame.columns)
        for column in frame.select_dtypes(include=["datetime", "datetimetz"]).columns:
            frame[column] = frame[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        sheets[normalize_identifier(sheet_name)] = frame
    return sheets


def write_table(connection: sqlite3.Connection, name: str, frame: pd.DataFrame) -> None:
    frame.to_sql(name, connection, index=False, if_exists="replace", chunksize=1000)
    indexed = 0
    for column in sorted(set(frame.columns) & INDEX_CANDIDATES):
        connection.execute(
            f'CREATE INDEX "idx_{name}_{column}" ON "{name}" ("{column}")'
        )
        indexed += 1
    print(f"[loaded] {name}: {len(frame.index):,} rows, {indexed} indexes")


def create_report_views(connection: sqlite3.Connection) -> int:
    has_report_data = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'reportdata'"
    ).fetchone()
    if not has_report_data:
        print("[note] No 'reportdata' sheet found; report views were not created.")
        return 0
    for view_name, query in FALLBACK_QUERIES.items():
        connection.execute(f'DROP VIEW IF EXISTS "{view_name}"')
        connection.execute(f'CREATE VIEW "{view_name}" AS {query}')
    return len(FALLBACK_QUERIES)


def load(source: Path, destination: Path) -> None:
    sheets = read_workbook(source)
    if not sheets:
        raise ValueError("The workbook contains no sheets.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    try:
        with closing(sqlite3.connect(temporary)) as connection:
            connection.execute("PRAGMA journal_mode = DELETE")
            connection.execute("PRAGMA foreign_keys = ON")
            for name, frame in sheets.items():
                if frame.empty:
                    print(f"[skipped] {name}: empty sheet")
                    continue
                write_table(connection, name, frame)
            views = create_report_views(connection)
            connection.execute("PRAGMA optimize")
            connection.commit()
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    print(f"[ready] {destination} ({views} report views)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=BASE_DIR / "dummy_data.xlsx")
    parser.add_argument("--destination", type=Path, default=BASE_DIR / "dummy_data.db")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    load(arguments.source.resolve(), arguments.destination.resolve())
