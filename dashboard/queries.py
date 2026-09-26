from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row


VALID_STATUSES = {"failed", "read", "sent", "delivered"}


def get_connection():
    """Abre una conexión corta a PostgreSQL usando variables de entorno."""
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "likeu_analytics"),
        user=os.getenv("POSTGRES_USER", "likeu_user"),
        password=os.getenv("POSTGRES_PASSWORD", "likeu_local_password"),
        row_factory=dict_row,
        connect_timeout=5,
    )


def _normalize_number(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _normalize_number(value) for key, value in row.items()}


def _fetch_one(query: str, params: list[Any] | None = None) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or [])
            row = cursor.fetchone()
    return _clean_row(row) if row else {}


def _fetch_all(query: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or [])
            rows = cursor.fetchall()
    return [_clean_row(row) for row in rows]


def build_message_filters(
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    alias: str = "m",
) -> tuple[str, list[Any]]:
    """Construye fragmentos SQL permitidos y mantiene los valores parametrizados."""
    clauses: list[str] = []
    params: list[Any] = []

    if date_from:
        clauses.append(f"{alias}.created_at::date >= %s")
        params.append(date_from)

    if date_to:
        clauses.append(f"{alias}.created_at::date <= %s")
        params.append(date_to)

    if status in VALID_STATUSES:
        clauses.append(f"{alias}.status = %s")
        params.append(status)

    if not clauses:
        return "", []

    return " AND " + " AND ".join(clauses), params


def _dataset_summary_query() -> tuple[str, list[Any]]:
    query = """
        SELECT
            COUNT(*) AS records,
            COUNT(DISTINCT conversation_id) AS conversations,
            MIN(created_at)::date AS min_date,
            MAX(created_at)::date AS max_date
        FROM messages;
    """
    return query, []


def _outgoing_kpis_query(
    date_from: str | None,
    date_to: str | None,
    status: str | None,
) -> tuple[str, list[Any]]:
    filters, params = build_message_filters(date_from, date_to, status)
    query = f"""
        SELECT
            COUNT(*) AS outgoing_messages,
            COUNT(*) FILTER (WHERE m.status = 'failed') AS failed_messages,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE m.status = 'failed')
                / NULLIF(COUNT(*), 0), 2
            ) AS failed_pct,
            COUNT(*) FILTER (WHERE m.status = 'read') AS read_messages,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE m.status = 'read')
                / NULLIF(COUNT(*), 0), 2
            ) AS read_pct,
            COUNT(*) FILTER (WHERE m.status = 'delivered') AS delivered_messages,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE m.status = 'delivered')
                / NULLIF(COUNT(*), 0), 2
            ) AS delivered_pct,
            COUNT(*) FILTER (WHERE m.status = 'sent') AS sent_messages,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE m.status = 'sent')
                / NULLIF(COUNT(*), 0), 2
            ) AS sent_pct
        FROM messages m
        WHERE m.message_type = 'outgoing'
        {filters};
    """
    return query, params


def _sla_query(date_from: str | None, date_to: str | None) -> tuple[str, list[Any]]:
    sla_clauses: list[str] = []
    params: list[Any] = []

    if date_from:
        sla_clauses.append("incoming_at::date >= %s")
        params.append(date_from)
    if date_to:
        sla_clauses.append("incoming_at::date <= %s")
        params.append(date_to)

    where = "WHERE " + " AND ".join(sla_clauses) if sla_clauses else ""
    query = f"""
        SELECT
            COUNT(*) AS incoming_messages,
            COUNT(*) FILTER (WHERE next_action_at IS NOT NULL) AS answered_messages,
            COUNT(*) FILTER (WHERE next_action_at IS NULL) AS unanswered_messages,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE next_action_at IS NOT NULL)
                / NULLIF(COUNT(*), 0), 2
            ) AS coverage_pct,
            ROUND(
                AVG(response_minutes)
                FILTER (WHERE response_minutes IS NOT NULL)::numeric, 2
            ) AS avg_sla_minutes,
            ROUND(
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_minutes)
                FILTER (WHERE response_minutes IS NOT NULL)::numeric, 2
            ) AS median_sla_minutes,
            ROUND(
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY response_minutes)
                FILTER (WHERE response_minutes IS NOT NULL)::numeric, 2
            ) AS p90_sla_minutes
        FROM vw_incoming_sla_detail
        {where};
    """
    return query, params


def _funnel_query(
    date_from: str | None,
    date_to: str | None,
    status: str | None,
) -> tuple[str, list[Any]]:
    filters, params = build_message_filters(date_from, date_to, status)
    query = f"""
        WITH grouped AS (
            SELECT
                m.status,
                COUNT(*) AS messages
            FROM messages m
            WHERE m.message_type = 'outgoing'
            {filters}
            GROUP BY m.status
        )
        SELECT
            status,
            messages,
            ROUND(
                100.0 * messages / NULLIF(SUM(messages) OVER (), 0), 2
            ) AS percentage
        FROM grouped
        ORDER BY messages DESC;
    """
    return query, params


def _hourly_query(date_from: str | None, date_to: str | None) -> tuple[str, list[Any]]:
    clauses = ["message_type = 'incoming'"]
    params: list[Any] = []

    if date_from:
        clauses.append("created_at::date >= %s")
        params.append(date_from)
    if date_to:
        clauses.append("created_at::date <= %s")
        params.append(date_to)

    query = f"""
        WITH hourly AS (
            SELECT
                EXTRACT(HOUR FROM created_at)::integer AS hour_of_day,
                COUNT(*) AS incoming_messages
            FROM messages
            WHERE {" AND ".join(clauses)}
            GROUP BY 1
        ),
        hours AS (
            SELECT generate_series(0, 23) AS hour_of_day
        )
        SELECT
            h.hour_of_day,
            COALESCE(hr.incoming_messages, 0) AS incoming_messages
        FROM hours h
        LEFT JOIN hourly hr
            ON hr.hour_of_day = h.hour_of_day
        ORDER BY h.hour_of_day;
    """
    return query, params


def _errors_query(date_from: str | None, date_to: str | None) -> tuple[str, list[Any]]:
    filters, params = build_message_filters(date_from, date_to, None)
    query = f"""
        WITH grouped AS (
            SELECT
                COALESCE(NULLIF(external_error, ''), 'Sin identificar') AS label,
                COUNT(*) AS total
            FROM messages m
            WHERE m.message_type = 'outgoing'
              AND m.status = 'failed'
              {filters}
            GROUP BY 1
        )
        SELECT
            label,
            total,
            ROUND(
                100.0 * total / NULLIF(SUM(total) OVER (), 0), 2
            ) AS percentage
        FROM grouped
        ORDER BY total DESC
        LIMIT 5;
    """
    return query, params


def _templates_query(date_from: str | None, date_to: str | None) -> tuple[str, list[Any]]:
    filters, params = build_message_filters(date_from, date_to, None)
    query = f"""
        WITH grouped AS (
            SELECT
                COALESCE(NULLIF(template_name, ''), 'Sin identificar') AS label,
                COUNT(*) AS total
            FROM messages m
            WHERE m.message_type = 'outgoing'
              AND m.status = 'failed'
              {filters}
            GROUP BY 1
        )
        SELECT
            label,
            total,
            ROUND(
                100.0 * total / NULLIF(SUM(total) OVER (), 0), 2
            ) AS percentage
        FROM grouped
        ORDER BY total DESC
        LIMIT 5;
    """
    return query, params


def _categories_query(date_from: str | None, date_to: str | None) -> tuple[str, list[Any]]:
    filters, params = build_message_filters(date_from, date_to, None)
    query = f"""
        WITH grouped AS (
            SELECT
                COALESCE(NULLIF(incoming_category, ''), 'Otros') AS label,
                COUNT(*) AS total
            FROM messages m
            WHERE m.message_type = 'incoming'
              {filters}
            GROUP BY 1
        )
        SELECT
            label,
            total,
            ROUND(
                100.0 * total / NULLIF(SUM(total) OVER (), 0), 2
            ) AS percentage
        FROM grouped
        ORDER BY total DESC;
    """
    return query, params


def get_dataset_summary() -> dict[str, Any]:
    query, params = _dataset_summary_query()
    return _fetch_one(query, params)


def get_kpis(
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    outgoing_query, outgoing_params = _outgoing_kpis_query(date_from, date_to, status)
    sla_query, sla_params = _sla_query(date_from, date_to)
    return {
        **_fetch_one(outgoing_query, outgoing_params),
        **_fetch_one(sla_query, sla_params),
    }


def get_delivery_funnel(
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    query, params = _funnel_query(date_from, date_to, status)
    return _fetch_all(query, params)


def get_hourly(
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    query, params = _hourly_query(date_from, date_to)
    return _fetch_all(query, params)


def get_errors(
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    query, params = _errors_query(date_from, date_to)
    return _fetch_all(query, params)


def get_templates(
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    query, params = _templates_query(date_from, date_to)
    return _fetch_all(query, params)


def get_categories(
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    query, params = _categories_query(date_from, date_to)
    return _fetch_all(query, params)


def get_query_support(
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Retorna exactamente las consultas que alimentan cada visualización."""
    queries = {
        "kpis": _outgoing_kpis_query(date_from, date_to, status),
        "sla": _sla_query(date_from, date_to),
        "funnel": _funnel_query(date_from, date_to, status),
        "hourly": _hourly_query(date_from, date_to),
        "errors": _errors_query(date_from, date_to),
        "templates": _templates_query(date_from, date_to),
        "categories": _categories_query(date_from, date_to),
    }
    return {
        key: {
            "sql": query.strip(),
            "params": list(params),
        }
        for key, (query, params) in queries.items()
    }
