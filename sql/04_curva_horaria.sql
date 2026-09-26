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
