"""Server-rendered product pages."""

from __future__ import annotations

from flask import Blueprint, abort, render_template, session, url_for

from .reports import REPORTS, reports_for_role
from .security import login_required, roles_required


bp = Blueprint("pages", __name__)


@bp.get("/")
def landing():
    return render_template("landing.html")


@bp.get("/about")
def about():
    return render_template("about.html")


@bp.get("/welcome")
@login_required
def welcome():
    role = session["role"]
    return render_template(
        "welcome.html",
        role=role,
        reports=reports_for_role(role),
        dashboard_url=url_for("pages.leader_dashboard" if role == "Leader" else "pages.dashboard"),
    )


def _dashboard(role: str):
    return render_template(
        "dashboard.html", role=role, reports=reports_for_role(role)
    )


@bp.get("/managerial")
@roles_required("Manager")
def dashboard():
    return _dashboard("Manager")


@bp.get("/managerial-dashboard")
@roles_required("Manager")
def managerial_dashboard():
    return _dashboard("Manager")


@bp.get("/leader-dashboard")
@roles_required("Leader")
def leader_dashboard():
    return _dashboard("Leader")


@bp.get("/custom-dashboard")
@login_required
def custom_dashboard():
    return render_template("builder.html")


def _report_page(slug: str):
    spec = REPORTS[slug]
    if session.get("role") != spec.role:
        abort(403)
    return render_template("report.html", report=spec)


@bp.get("/report/current-students")
@roles_required("Manager")
def current_students_report():
    return _report_page("current-vs-enrolled")


@bp.get("/report/enrolled-offer")
@roles_required("Manager")
def enrolled_offer_report():
    return _report_page("enrolled-vs-offer")


@bp.get("/report/visa-status")
@roles_required("Manager")
def visa_status_breakdown():
    return _report_page("visa-breakdown")


@bp.get("/report/offer-expiry")
@roles_required("Manager")
def offer_expiry_report():
    return _report_page("offer-expiry-surge")


@bp.get("/report/application-status")
@roles_required("Leader")
def application_status_report():
    return _report_page("application-status")


@bp.get("/report/deferred-offers")
@roles_required("Leader")
def deferred_offers_report():
    return _report_page("deferred-offers")


@bp.get("/report/agent-performance")
@roles_required("Leader")
def agent_performance_report():
    return _report_page("agent-performance")


@bp.get("/report/student-classification")
@roles_required("Leader")
def student_classification_report():
    return _report_page("student-classification")
