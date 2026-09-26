-- SLA solicitado por el caso técnico:
-- desde cada incoming hasta la siguiente acción activity u outgoing
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
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_minutes)::numeric, 2)
        AS median_response_minutes,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY response_minutes)::numeric, 2)
        AS p90_response_minutes
FROM incoming_sla;
