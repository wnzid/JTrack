"""Authenticated JSON API."""

from __future__ import annotations

from datetime import UTC, datetime
from math import ceil

from flask import Blueprint, current_app, jsonify, request

from .data import read_dataset, read_report, records
from .reports import REPORTS
from .security import roles_required


bp = Blueprint("api", __name__, url_prefix="/api")


def _response(data: list[dict], **metadata):
    payload = {
        "data": data,
        "meta": {
            "count": len(data),
            "generated_at": datetime.now(UTC).isoformat(),
            **metadata,
        },
    }
    if request.args.get("legacy") == "1":
        return jsonify(data)
    return jsonify(payload)


@bp.get("/data")
@roles_required("Leader", "Manager")
def data():
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    requested_size = request.args.get("per_page", 100, type=int) or 100
    page_size = min(max(requested_size, 1), current_app.config["API_MAX_PAGE_SIZE"])
    frame, source = read_dataset(request.args.get("table"))
    total = len(frame.index)
    start = (page - 1) * page_size
    subset = frame.iloc[start : start + page_size]
    return _response(
        records(subset),
        source=source,
        page=page,
        per_page=page_size,
        total=total,
        pages=ceil(total / page_size) if total else 0,
        columns=[str(column) for column in frame.columns],
    )


def report_response(slug: str):
    spec = REPORTS[slug]
    frame, source = read_report(spec)
    return _response(records(frame), report=slug, source=source)


def _protected_report(slug: str):
    spec = REPORTS[slug]

    @roles_required(spec.role)
    def view():
        return report_response(slug)

    view.__name__ = f"report_{slug.replace('-', '_')}"
    return view


for _slug, _spec in REPORTS.items():
    bp.add_url_rule(_spec.api_path.removeprefix("/api"), view_func=_protected_report(_slug))
