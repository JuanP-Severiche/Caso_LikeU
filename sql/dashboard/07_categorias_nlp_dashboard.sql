-- Soporte visual: Categorías NLP
WITH grouped AS (
    SELECT COALESCE(NULLIF(incoming_category, ''), 'Otros') AS category,
           COUNT(*) AS total
    FROM messages
    WHERE message_type = 'incoming'
      AND created_at::date BETWEEN :date_from AND :date_to
    GROUP BY 1
)
SELECT category, total,
       ROUND(100.0 * total / NULLIF(SUM(total) OVER (), 0), 2) AS percentage
FROM grouped
ORDER BY total DESC;
