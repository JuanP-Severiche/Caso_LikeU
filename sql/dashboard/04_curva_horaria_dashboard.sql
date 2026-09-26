-- Soporte visual: Curva horaria
WITH hourly AS (
    SELECT EXTRACT(HOUR FROM created_at)::integer AS hour_of_day,
           COUNT(*) AS incoming_messages
    FROM messages
    WHERE message_type = 'incoming'
      AND created_at::date BETWEEN :date_from AND :date_to
    GROUP BY 1
),
hours AS (
    SELECT generate_series(0, 23) AS hour_of_day
)
SELECT h.hour_of_day,
       COALESCE(hr.incoming_messages, 0) AS incoming_messages
FROM hours h
LEFT JOIN hourly hr ON hr.hour_of_day = h.hour_of_day
ORDER BY h.hour_of_day;
