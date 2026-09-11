"""Small security helpers shared by the web blueprints."""

from __future__ import annotations

import hmac
import secrets
from functools import wraps

from flask import abort, redirect, request, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("email"):
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)

    return wrapped


def roles_required(*roles: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("email"):
                if request.path.startswith("/api/"):
                    abort(401, description="Sign in to access JTrack data.")
                return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
            if session.get("role") not in roles:
                abort(403, description="Your account cannot access this resource.")
            return view(*args, **kwargs)

        return wrapped

    return decorator


def csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def init_security(app) -> None:
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def protect_forms():
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None
        supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token")
        if not expected or not supplied or not hmac.compare_digest(expected, supplied):
            abort(400, description="The form expired. Refresh the page and try again.")
        return None
