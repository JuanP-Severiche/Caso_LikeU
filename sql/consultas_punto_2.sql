-- ============================================================
-- Caso LikeU - Punto 2
-- Consultas solicitadas en el caso técnico
-- ============================================================

-- 1. Funnel de entrega
-- Porcentaje de mensajes outgoing en read, delivered y failed
-- sobre el total de mensajes salientes.
WITH outgoing AS (
    SELECT status
    FROM messages
    WHERE message_type = 'outgoing'
),
total AS (
    SELECT COUNT(*) AS total_messages
    FROM outgoing
),
by_status AS (
    SELECT
        status,
        COUNT(*) AS messages
    FROM outgoing
    WHERE status IN ('read', 'delivered', 'failed')
    GROUP BY status
)
SELECT
    b.status,
    b.messages,
    ROUND(100.0 * b.messages / NULLIF(t.total_messages, 0), 2) AS percentage
FROM by_status b
CROSS JOIN total t
ORDER BY b.messages DESC, b.status;


-- 2. SLA de respuesta operativa
-- Tiempo desde cada incoming hasta la siguiente acción activity u outgoing
-- dentro de la misma conversation_id.
WITH ordered_events AS (
    SELECT
        id,
        conversation_id,
        message_type,
        created_at,
        MIN(created_at) FILTER (
            WHERE message_type IN ('activity', 'outgoing')
        ) OVER (
            PARTITION BY conversation_id
            ORDER BY created_at, id
            ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING
        ) AS next_action_at
    FROM messages
),
incoming_sla AS (
    SELECT
        id,
        conversation_id,
        created_at AS incoming_at,
        next_action_at,
        EXTRACT(EPOCH FROM (next_action_at - created_at)) / 60.0 AS response_minutes
    FROM ordered_events
    WHERE message_type = 'incoming'
)
SELECT
    COUNT(*) AS incoming_messages,
    COUNT(next_action_at) AS answered_messages,
    COUNT(*) - COUNT(next_action_at) AS unanswered_messages,
    ROUND(100.0 * COUNT(next_action_at) / NULLIF(COUNT(*), 0), 2) AS coverage_pct,
    ROUND(AVG(response_minutes)::numeric, 2) AS avg_response_minutes,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_minutes)::numeric,
        2
    ) AS median_response_minutes,
    ROUND(
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY response_minutes)::numeric,
        2
    ) AS p90_response_minutes
FROM incoming_sla;


-- 3. Curva de calor horaria
-- Volumen de mensajes incoming por hora del día.
WITH hours AS (
    SELECT generate_series(0, 23) AS hour_of_day
),
incoming_by_hour AS (
    SELECT
        EXTRACT(HOUR FROM created_at)::int AS hour_of_day,
        COUNT(*) AS incoming_messages
    FROM messages
    WHERE message_type = 'incoming'
    GROUP BY 1
)
SELECT
    h.hour_of_day,
    COALESCE(i.incoming_messages, 0) AS incoming_messages
FROM hours h
LEFT JOIN incoming_by_hour i USING (hour_of_day)
ORDER BY h.hour_of_day;
