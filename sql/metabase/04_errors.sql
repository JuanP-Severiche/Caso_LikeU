SELECT
    COALESCE(external_error, 'Sin identificar') AS error,
    COUNT(*) AS failed_messages,
    ROUND(
        100.0 * COUNT(*) / NULLIF(
            SUM(COUNT(*)) OVER (),
            0
        ),
        2
    ) AS percentage
FROM messages
WHERE message_type = 'outgoing'
  AND status = 'failed'

[[ AND created_at::date >= CAST({{fecha_inicio}} AS date) ]]
[[ AND created_at::date <= CAST({{fecha_fin}} AS date) ]]

GROUP BY COALESCE(external_error, 'Sin identificar')
ORDER BY failed_messages DESC;