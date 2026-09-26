-- Soporte visual: Fallos por plantilla
WITH grouped AS (
    SELECT COALESCE(NULLIF(template_name, ''), 'Sin identificar') AS template_name,
           COUNT(*) AS total
    FROM messages
    WHERE message_type = 'outgoing'
      AND status = 'failed'
      AND created_at::date BETWEEN :date_from AND :date_to
    GROUP BY 1
)
SELECT template_name, total,
       ROUND(100.0 * total / NULLIF(SUM(total) OVER (), 0), 2) AS percentage
FROM grouped
ORDER BY total DESC
LIMIT 5;
