-- Soporte visual: Funnel de entrega
WITH grouped AS (
    SELECT status, COUNT(*) AS messages
    FROM messages
    WHERE message_type = 'outgoing'
      AND created_at::date BETWEEN :date_from AND :date_to
      AND (:status IS NULL OR status = :status)
    GROUP BY status
)
SELECT
    status,
    messages,
    ROUND(100.0 * messages / NULLIF(SUM(messages) OVER (), 0), 2) AS percentage
FROM grouped
ORDER BY messages DESC;
