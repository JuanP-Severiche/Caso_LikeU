from dashboard.render import render_dashboard
from dashboard.server import valid_date


def test_valid_date_accepts_iso_date():
    assert valid_date("2023-07-25") is True
    assert valid_date("25/07/2023") is False


def test_dashboard_render_contains_main_metrics():
    html = render_dashboard(
        kpis={
            "outgoing_messages": 2507,
            "failed_messages": 1396,
            "failed_pct": 55.68,
            "read_pct": 28.24,
            "delivered_pct": 3.31,
            "avg_sla_minutes": 127.24,
            "median_sla_minutes": 0.68,
            "p90_sla_minutes": 81.33,
            "coverage_pct": 85.81,
            "unanswered_messages": 61,
        },
        funnel=[{"status": "failed", "messages": 1396, "percentage": 55.68}],
        hourly=[{"hour_of_day": h, "incoming_messages": 0} for h in range(24)],
        errors=[{"label": "params", "total": 1374, "percentage": 98.42}],
        templates=[{"label": "lanzamiento_", "total": 1352, "percentage": 96.85}],
        categories=[{"label": "Otros", "total": 100, "percentage": 23.26}],
        summary={"records": 3687, "conversations": 2153, "min_date": "2023-07-25", "max_date": "2023-08-02"},
        query_support={
            "kpis": {"sql": "SELECT 1;", "params": []},
            "sla": {"sql": "SELECT 2;", "params": []},
            "funnel": {"sql": "SELECT 3;", "params": []},
            "hourly": {"sql": "SELECT 4;", "params": []},
            "errors": {"sql": "SELECT 5;", "params": []},
            "templates": {"sql": "SELECT 6;", "params": []},
            "categories": {"sql": "SELECT 7;", "params": []},
        },
        date_from="2023-07-25",
        date_to="2023-08-02",
        status="",
    )
    assert "LikeU Analytics" in html
    assert "55.68%" in html
    assert "lanzamiento_" in html
    assert "Consulta de apoyo" in html
    assert "SELECT 3;" in html
