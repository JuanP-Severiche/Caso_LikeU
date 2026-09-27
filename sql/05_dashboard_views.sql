-- Vistas reutilizables para evitar repetir la logica analitica en el dashboard.
CREATE OR REPLACE VIEW vw_delivery_funnel AS
WITH outgoing AS (
    SELECT status
    FROM messages
    WHERE message_type = 'outgoing'
),
summary AS (
    SELECT status, COUNT(*) AS messages
    FROM outgoing
    GROUP BY status
)
SELECT
    status,
    messages,
    ROUND(100.0 * messages / SUM(messages) OVER (), 2) AS percentage
FROM summary;

CREATE OR REPLACE VIEW vw_incoming_hourly AS
SELECT
    DATE(created_at) AS event_date,
    EXTRACT(HOUR FROM created_at)::int AS hour_of_day,
    incoming_category,
    COUNT(*) AS incoming_messages
FROM messages
WHERE message_type = 'incoming'
GROUP BY 1, 2, 3;

CREATE OR REPLACE VIEW vw_failed_errors AS
SELECT
    COALESCE(external_error, 'Sin error identificado') AS external_error,
    COALESCE(template_name, 'Sin plantilla identificada') AS template_name,
    COUNT(*) AS failed_messages
FROM messages
WHERE message_type = 'outgoing'
  AND status = 'failed'
GROUP BY 1, 2;

CREATE OR REPLACE VIEW vw_incoming_sla_detail AS
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
)
SELECT
    id AS incoming_message_id,
    conversation_id,
    created_at AS incoming_at,
    next_action_at,
    CASE
        WHEN next_action_at IS NULL THEN NULL
        ELSE EXTRACT(EPOCH FROM (next_action_at - created_at)) / 60.0
    END AS response_minutes
FROM ordered_events
WHERE message_type = 'incoming';

CREATE OR REPLACE VIEW vw_incoming_human_sla_detail AS
WITH ordered_events AS (
    SELECT
        id,
        conversation_id,
        message_type,
        created_at,
        MIN(created_at) FILTER (
            WHERE message_type = 'outgoing'
        ) OVER (
            PARTITION BY conversation_id
            ORDER BY created_at, id
            ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING
        ) AS next_outgoing_at
    FROM messages
)
SELECT
    id AS incoming_message_id,
    conversation_id,
    created_at AS incoming_at,
    next_outgoing_at,
    CASE
        WHEN next_outgoing_at IS NULL THEN NULL
        ELSE EXTRACT(EPOCH FROM (next_outgoing_at - created_at)) / 60.0
    END AS response_minutes
FROM ordered_events
WHERE message_type = 'incoming';
