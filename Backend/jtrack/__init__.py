"""JTrack application factory."""

from __future__ import annotations

import logging
import secrets
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from . import auth, database, pages
from .api import bp as api_blueprint
from .config import Config
from .security import init_security
from .reports import reports_for_role


def create_app(test_config: dict | None = None) -> Flask:
    base_dir = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        instance_path=str(base_dir / "instance"),
        static_folder=str(base_dir / "static"),
        static_url_path="/static",
        template_folder=str(base_dir / "templates"),
    )
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config.get("SECRET_KEY"):
        if app.config.get("ENVIRONMENT") == "production":
            raise RuntimeError("SECRET_KEY is required when JTRACK_ENV=production")
        app.config["SECRET_KEY"] = secrets.token_urlsafe(48)
        app.logger.warning(
            "SECRET_KEY is not configured; generated an ephemeral development key."
        )

    database.init_app(app)
    init_security(app)
    app.jinja_env.globals["reports_for_role"] = reports_for_role
    app.register_blueprint(auth.bp)
    app.register_blueprint(pages.bp)
    app.register_blueprint(api_blueprint)

    @app.get("/health")
    def health():
        analytics_db = Path(app.config["ANALYTICS_DATABASE"])
        source = (
            "sharepoint"
            if app.config["USE_SHAREPOINT"]
            else "sqlite"
            if analytics_db.exists()
            else "excel"
        )
        return jsonify({"status": "ok", "service": "jtrack", "data_source": source})

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        if request.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "private, no-store")
        return response

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "error": {
                            "code": error.name.lower().replace(" ", "_"),
                            "message": error.description,
                        }
                    }
                ),
                error.code,
            )
        return render_template("error.html", status=error.code, error=error), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled request error", exc_info=error)
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "internal_error",
                            "message": "JTrack could not complete this request.",
                        }
                    }
                ),
                500,
            )
        return render_template("error.html", status=500, error=None), 500

    logging.getLogger("werkzeug").setLevel(
        logging.DEBUG if app.config["DEBUG"] else logging.INFO
    )
    return app
