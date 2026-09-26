-- Soporte visual: Principales errores
WITH grouped AS (
    SELECT COALESCE(NULLIF(external_error, ''), 'Sin identificar') AS error,
           COUNT(*) AS total
    FROM messages
    WHERE message_type = 'outgoing'
      AND status = 'failed'
      AND created_at::date BETWEEN :date_from AND :date_to
    GROUP BY 1
)
SELECT error, total,
       ROUND(100.0 * total / NULLIF(SUM(total) OVER (), 0), 2) AS percentage
FROM grouped
ORDER BY total DESC
LIMIT 5;
