"""Canonical report definitions and fallback queries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportSpec:
    slug: str
    title: str
    eyebrow: str
    description: str
    page_path: str
    api_path: str
    role: str
    view_name: str
    dimension: str
    metrics: tuple[str, ...]
    columns: tuple[tuple[str, str], ...]
    chart_type: str = "bar"


REPORTS = {
    "current-vs-enrolled": ReportSpec(
        "current-vs-enrolled",
        "Current vs enrolled",
        "Student pipeline",
        "Compare active students with new enrollments by start year.",
        "/report/current-students",
        "/api/current-vs-enrolled",
        "Manager",
        "v_current_vs_enrolled",
        "term",
        ("current_students", "enrolled"),
        (("term", "Year"), ("current_students", "Current students"), ("enrolled", "Enrolled")),
    ),
    "enrolled-vs-offer": ReportSpec(
        "enrolled-vs-offer",
        "Offers to enrollment",
        "Conversion",
        "See how issued offers convert into enrolled students by start year.",
        "/report/enrolled-offer",
        "/api/enrolled-vs-offer",
        "Manager",
        "v_enrolled_vs_offer",
        "term",
        ("offers", "enrolled"),
        (("term", "Year"), ("offers", "Offers"), ("enrolled", "Enrolled")),
    ),
    "visa-breakdown": ReportSpec(
        "visa-breakdown",
        "Visa status mix",
        "Student profile",
        "Understand the current distribution of visa categories.",
        "/report/visa-status",
        "/api/visa-breakdown",
        "Manager",
        "v_visa_breakdown",
        "visa_type",
        ("total",),
        (("visa_type", "Visa status"), ("total", "Students")),
        "doughnut",
    ),
    "offer-expiry-surge": ReportSpec(
        "offer-expiry-surge",
        "Offer expiry schedule",
        "Workload planning",
        "Spot dates with a high concentration of expiring offers.",
        "/report/offer-expiry",
        "/api/offer-expiry-surge",
        "Manager",
        "v_offer_expiry_surge_daily",
        "expiry_day",
        ("expiring_offers",),
        (("expiry_day", "Expiry date"), ("expiring_offers", "Offers")),
        "line",
    ),
    "application-status": ReportSpec(
        "application-status",
        "Application status",
        "Pipeline health",
        "Review how applications are distributed across workflow states.",
        "/report/application-status",
        "/api/application-status",
        "Leader",
        "v_application_status_totals",
        "status",
        ("total",),
        (("status", "Status"), ("total", "Applications")),
        "doughnut",
    ),
    "deferred-offers": ReportSpec(
        "deferred-offers",
        "Deferred offers",
        "Intake movement",
        "Compare deferrals with total offers across previous intake terms.",
        "/report/deferred-offers",
        "/api/deferred-offers",
        "Leader",
        "v_deferred_offers_overview",
        "term",
        ("deferred_count", "total_offers"),
        (("term", "Intake"), ("deferred_count", "Deferred"), ("total_offers", "Total offers")),
    ),
    "agent-performance": ReportSpec(
        "agent-performance",
        "Agent performance",
        "Team output",
        "Compare applications, offers, and enrollments across agents.",
        "/report/agent-performance",
        "/api/agent-performance",
        "Leader",
        "v_agent_performance",
        "agent",
        ("applications", "offers", "enrolled"),
        (("agent", "Agent"), ("applications", "Applications"), ("offers", "Offers"), ("enrolled", "Enrolled")),
    ),
    "student-classification": ReportSpec(
        "student-classification",
        "Student classification",
        "Course profile",
        "See the student population grouped by course type.",
        "/report/student-classification",
        "/api/student-classification",
        "Leader",
        "v_student_classification",
        "classification",
        ("total",),
        (("classification", "Classification"), ("total", "Students")),
        "doughnut",
    ),
}


FALLBACK_QUERIES = {
    "v_application_status_totals": """
        SELECT COALESCE(status, 'Unknown') AS status, COUNT(*) AS total
        FROM reportdata GROUP BY COALESCE(status, 'Unknown') ORDER BY total DESC
    """,
    "v_deferred_offers_overview": """
        SELECT COALESCE(
                   previous_offer_intake || ' ' || CAST(CAST(previous_offer_year AS INTEGER) AS TEXT),
                   'Unknown'
               ) AS term,
               SUM(CASE
                   WHEN LOWER(COALESCE(is_the_offer_deferred, '')) IN ('1','y','yes','true') THEN 1
                   WHEN status = 'Deferred' THEN 1 ELSE 0 END) AS deferred_count,
               COUNT(*) AS total_offers
        FROM reportdata GROUP BY term ORDER BY term
    """,
    "v_agent_performance": """
        SELECT COALESCE(agentname, 'Unknown') AS agent,
               SUM(CASE WHEN status = 'New Application Request' THEN 1 ELSE 0 END) AS applications,
               SUM(CASE WHEN status = 'Offered' THEN 1 ELSE 0 END) AS offers,
               SUM(CASE WHEN status LIKE 'Enrolled%' THEN 1 ELSE 0 END) AS enrolled
        FROM reportdata GROUP BY agent
        ORDER BY enrolled DESC, offers DESC, applications DESC
    """,
    "v_student_classification": """
        SELECT COALESCE(coursetype, 'Unknown') AS classification, COUNT(*) AS total
        FROM reportdata GROUP BY COALESCE(coursetype, 'Unknown') ORDER BY total DESC
    """,
    "v_current_vs_enrolled": """
        SELECT COALESCE(strftime('%Y', date(substr(startdate,7,4)||'-'||substr(startdate,4,2)||'-'||substr(startdate,1,2))), 'Unknown') AS term,
               SUM(CASE WHEN status = 'Current Student' THEN 1 ELSE 0 END) AS current_students,
               SUM(CASE WHEN status LIKE 'Enrolled%' THEN 1 ELSE 0 END) AS enrolled
        FROM reportdata GROUP BY term ORDER BY term
    """,
    "v_enrolled_vs_offer": """
        SELECT COALESCE(strftime('%Y', date(substr(startdate,7,4)||'-'||substr(startdate,4,2)||'-'||substr(startdate,1,2))), 'Unknown') AS term,
               SUM(CASE WHEN status = 'Offered' THEN 1 ELSE 0 END) AS offers,
               SUM(CASE WHEN status LIKE 'Enrolled%' THEN 1 ELSE 0 END) AS enrolled
        FROM reportdata GROUP BY term ORDER BY term
    """,
    "v_offer_expiry_surge_daily": """
        SELECT date(substr(offer_expiry_date,7,4)||'-'||substr(offer_expiry_date,4,2)||'-'||substr(offer_expiry_date,1,2)) AS expiry_day,
               COUNT(*) AS expiring_offers
        FROM reportdata
        WHERE offer_expiry_date IS NOT NULL AND offer_expiry_date <> ''
        GROUP BY expiry_day ORDER BY expiry_day
    """,
    "v_visa_breakdown": """
        SELECT COALESCE(visa_status, 'Unknown') AS visa_type, COUNT(*) AS total
        FROM reportdata GROUP BY COALESCE(visa_status, 'Unknown') ORDER BY total DESC
    """,
}


def reports_for_role(role: str) -> list[ReportSpec]:
    return [report for report in REPORTS.values() if report.role == role]
