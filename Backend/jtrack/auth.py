"""Authentication and account enrollment routes."""

from __future__ import annotations

import re
import sqlite3
from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .database import get_db


bp = Blueprint("auth", __name__)
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")


def _safe_next_url(candidate: str | None) -> str | None:
    if not candidate:
        return None
    target = urlsplit(candidate)
    if target.scheme or target.netloc or not candidate.startswith("/"):
        return None
    return candidate


@bp.route("/register", methods=["GET", "POST"])
def register():
    if not current_app.config["ALLOW_REGISTRATION"]:
        return render_template("registration_closed.html"), 403

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        requested_role = (request.form.get("role") or "").title()
        role = (
            requested_role
            if current_app.config["ALLOW_ROLE_SELECTION"]
            else current_app.config["DEFAULT_REGISTRATION_ROLE"]
        )

        if not EMAIL_PATTERN.fullmatch(email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 12:
            flash("Use at least 12 characters for your password.", "error")
        elif role not in {"Leader", "Manager"}:
            flash("Select a valid account role.", "error")
        else:
            try:
                get_db().execute(
                    "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
                    (email, generate_password_hash(password), role),
                )
                get_db().commit()
            except sqlite3.IntegrityError:
                flash("An account already exists for that email.", "error")
            else:
                session.clear()
                session["email"] = email
                session["role"] = role
                flash("Your workspace is ready.", "success")
                return redirect(url_for("pages.welcome"))

    return render_template(
        "register.html",
        allow_role_selection=current_app.config["ALLOW_ROLE_SELECTION"],
        default_role=current_app.config["DEFAULT_REGISTRATION_ROLE"],
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = get_db().execute(
            "SELECT email, password, role FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["email"] = user["email"]
            session["role"] = user["role"]
            return redirect(
                _safe_next_url(request.form.get("next")) or url_for("pages.welcome")
            )
        flash("Email or password is incorrect.", "error")

    return render_template("login.html", next_url=_safe_next_url(request.args.get("next")))


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("pages.landing"))
