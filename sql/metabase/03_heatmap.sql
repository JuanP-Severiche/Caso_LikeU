SELECT
    EXTRACT(HOUR FROM created_at)::int AS hour_of_day,
    COUNT(*) AS incoming_messages
FROM messages
WHERE message_type = 'incoming'
  AND created_at::date BETWEEN {{fecha_inicio}} AND {{fecha_fin}}
GROUP BY 1
ORDER BY 1;
