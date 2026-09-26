WITH filtered_messages AS (
    SELECT
        m.*
    FROM messages m
    WHERE m.message_type = 'outgoing'

    [[ AND m.created_at::date >= CAST({{fecha_inicio}} AS date) ]]
    [[ AND m.created_at::date <= CAST({{fecha_fin}} AS date) ]]

    [[
        AND (
            NULLIF(TRIM(LOWER({{estado}})), '') IS NULL
            OR TRIM(LOWER({{estado}})) IN ('vacio', 'vacío', 'todos', 'all')
            OR LOWER(m.status) = TRIM(LOWER({{estado}}))
        )
    ]]
),

sla_filtered AS (
    SELECT
        s.*
    FROM vw_incoming_sla_detail s
    WHERE 1 = 1

    [[ AND s.incoming_at::date >= CAST({{fecha_inicio}} AS date) ]]
    [[ AND s.incoming_at::date <= CAST({{fecha_fin}} AS date) ]]
),

outgoing_kpis AS (
    SELECT
        COUNT(*) AS outgoing_messages,

        COUNT(*) FILTER (
            WHERE status = 'failed'
        ) AS failed_messages,

        COUNT(*) FILTER (
            WHERE status = 'read'
        ) AS read_messages,

        COUNT(*) FILTER (
            WHERE status = 'delivered'
        ) AS delivered_messages,

        COUNT(*) FILTER (
            WHERE status = 'sent'
        ) AS sent_messages

    FROM filtered_messages
),

sla_kpis AS (
    SELECT
        COUNT(*) AS incoming_messages,

        COUNT(*) FILTER (
            WHERE next_action_at IS NOT NULL
        ) AS answered_messages,

        COUNT(*) FILTER (
            WHERE next_action_at IS NULL
        ) AS unanswered_incoming,

        ROUND(
            AVG(response_minutes)
            FILTER (
                WHERE response_minutes IS NOT NULL
            )::numeric,
            2
        ) AS avg_sla_minutes,

        ROUND(
            PERCENTILE_CONT(0.5)
            WITHIN GROUP (
                ORDER BY response_minutes
            )
            FILTER (
                WHERE response_minutes IS NOT NULL
            )::numeric,
            2
        ) AS median_sla_minutes,

        ROUND(
            PERCENTILE_CONT(0.9)
            WITHIN GROUP (
                ORDER BY response_minutes
            )
            FILTER (
                WHERE response_minutes IS NOT NULL
            )::numeric,
            2
        ) AS p90_sla_minutes

    FROM sla_filtered
)

SELECT
    o.outgoing_messages,

    o.failed_messages,

    ROUND(
        100.0 * o.failed_messages
        / NULLIF(o.outgoing_messages, 0),
        2
    ) AS failed_pct,

    o.read_messages,

    ROUND(
        100.0 * o.read_messages
        / NULLIF(o.outgoing_messages, 0),
        2
    ) AS read_pct,

    o.delivered_messages,

    ROUND(
        100.0 * o.delivered_messages
        / NULLIF(o.outgoing_messages, 0),
        2
    ) AS delivered_pct,

    o.sent_messages,

    ROUND(
        100.0 * o.sent_messages
        / NULLIF(o.outgoing_messages, 0),
        2
    ) AS sent_pct,

    s.incoming_messages,

    s.answered_messages,

    s.unanswered_incoming,

    ROUND(
        100.0 * s.answered_messages
        / NULLIF(s.incoming_messages, 0),
        2
    ) AS sla_coverage_pct,

    s.avg_sla_minutes,

    s.median_sla_minutes,

    s.p90_sla_minutes

FROM outgoing_kpis o
CROSS JOIN sla_kpis s;