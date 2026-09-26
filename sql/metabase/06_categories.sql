SELECT
    COALESCE(incoming_category, 'Otros') AS category,
    COUNT(*) AS incoming_messages,
    ROUND(
        100.0 * COUNT(*) / NULLIF(
            SUM(COUNT(*)) OVER (),
            0
        ),
        2
    ) AS percentage
FROM messages
WHERE message_type = 'incoming'

[[ AND created_at::date >= CAST({{fecha_inicio}} AS date) ]]
[[ AND created_at::date <= CAST({{fecha_fin}} AS date) ]]

GROUP BY COALESCE(incoming_category, 'Otros')
ORDER BY incoming_messages DESC;