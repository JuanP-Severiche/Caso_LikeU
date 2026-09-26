from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_FILE = BASE_DIR / "templates" / "dashboard.html"
CSS_FILE = BASE_DIR / "static" / "dashboard.css"


def format_number(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "0"
    if isinstance(value, float):
        return f"{value:,.{decimals}f}"
    return f"{value:,}"


def horizontal_bars(rows: list[dict[str, Any]], label_key: str = "label", value_key: str = "total") -> str:
    if not rows:
        return '<p class="empty">Sin datos disponibles</p>'

    maximum = max(float(row[value_key] or 0) for row in rows) or 1
    html: list[str] = []
    for row in rows:
        label = escape(str(row[label_key]))
        value = float(row[value_key] or 0)
        percentage = float(row.get("percentage") or 0)
        width = value / maximum * 100
        html.append(
            f"""
            <div class="bar-row" title="{label}: {value:g}">
                <div class="bar-label">
                    <span>{label}</span>
                    <strong>{format_number(int(value))} <small>({percentage:.2f}%)</small></strong>
                </div>
                <div class="bar-track"><div class="bar-fill" style="width:{width:.2f}%"></div></div>
            </div>
            """
        )
    return "\n".join(html)


def funnel_bars(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="empty">Sin datos disponibles</p>'
    html: list[str] = []
    for row in rows:
        percentage = float(row["percentage"] or 0)
        html.append(
            f"""
            <div class="funnel-row">
                <div class="funnel-header">
                    <span>{escape(str(row['status']).title())}</span>
                    <strong>{percentage:.2f}%</strong>
                </div>
                <div class="bar-track"><div class="bar-fill" style="width:{percentage:.2f}%"></div></div>
                <small>{format_number(row['messages'], 0)} mensajes</small>
            </div>
            """
        )
    return "\n".join(html)


def hourly_chart(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="empty">Sin datos disponibles</p>'
    maximum = max(float(row["incoming_messages"] or 0) for row in rows) or 1
    bars: list[str] = []
    for row in rows:
        total = int(row["incoming_messages"] or 0)
        height = total / maximum * 100
        hour = int(row["hour_of_day"])
        bars.append(
            f"""
            <div class="hour-item" title="{hour:02d}:00 · {total} mensajes">
                <div class="hour-number">{total if total else ''}</div>
                <div class="hour-value" style="height:{max(height, 1.5):.2f}%"></div>
                <span>{hour:02d}</span>
            </div>
            """
        )
    return "\n".join(bars)


def option_selected(current: str, value: str) -> str:
    return "selected" if current == value else ""


def render_dashboard(
    *,
    kpis: dict[str, Any],
    funnel: list[dict[str, Any]],
    hourly: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    templates: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    summary: dict[str, Any],
    date_from: str,
    date_to: str,
    status: str,
) -> str:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    css = CSS_FILE.read_text(encoding="utf-8")

    top_error = errors[0] if errors else {"percentage": 0}
    top_template = templates[0] if templates else {"label": "Sin datos", "percentage": 0}

    replacements = {
        "{{CSS}}": css,
        "{{DATE_FROM}}": escape(date_from),
        "{{DATE_TO}}": escape(date_to),
        "{{SELECT_FAILED}}": option_selected(status, "failed"),
        "{{SELECT_READ}}": option_selected(status, "read"),
        "{{SELECT_SENT}}": option_selected(status, "sent"),
        "{{SELECT_DELIVERED}}": option_selected(status, "delivered"),
        "{{OUTGOING}}": format_number(kpis.get("outgoing_messages"), 0),
        "{{FAILED_MESSAGES}}": format_number(kpis.get("failed_messages"), 0),
        "{{FAILED_PCT}}": format_number(kpis.get("failed_pct")),
        "{{READ_PCT}}": format_number(kpis.get("read_pct")),
        "{{DELIVERED_PCT}}": format_number(kpis.get("delivered_pct")),
        "{{AVG_SLA}}": format_number(kpis.get("avg_sla_minutes")),
        "{{MEDIAN_SLA}}": format_number(kpis.get("median_sla_minutes")),
        "{{P90_SLA}}": format_number(kpis.get("p90_sla_minutes")),
        "{{COVERAGE}}": format_number(kpis.get("coverage_pct")),
        "{{UNANSWERED}}": format_number(kpis.get("unanswered_messages"), 0),
        "{{FUNNEL}}": funnel_bars(funnel),
        "{{HOURLY}}": hourly_chart(hourly),
        "{{ERRORS}}": horizontal_bars(errors),
        "{{TEMPLATES}}": horizontal_bars(templates),
        "{{CATEGORIES}}": horizontal_bars(categories),
        "{{RECORDS}}": format_number(summary.get("records"), 0),
        "{{CONVERSATIONS}}": format_number(summary.get("conversations"), 0),
        "{{MIN_DATE}}": escape(str(summary.get("min_date") or "-")),
        "{{MAX_DATE}}": escape(str(summary.get("max_date") or "-")),
        "{{TOP_ERROR_PCT}}": format_number(top_error.get("percentage")),
        "{{TOP_TEMPLATE}}": escape(str(top_template.get("label") or "Sin datos")),
        "{{TOP_TEMPLATE_PCT}}": format_number(top_template.get("percentage")),
    }

    for key, value in replacements.items():
        template = template.replace(key, str(value))
    return template
