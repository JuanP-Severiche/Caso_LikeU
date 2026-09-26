WITH filtered_messages AS (
    SELECT
        m.status,
        COUNT(*) AS messages
    FROM messages m
    WHERE m.message_type = 'outgoing'

    [[ AND m.created_at::date >= CAST({{fecha_inicio}} AS date) ]]
    [[ AND m.created_at::date <= CAST({{fecha_fin}} AS date) ]]

    [[
        AND (
            NULLIF(TRIM(LOWER({{estado}})), '') IS NULL
            OR TRIM(LOWER({{estado}})) IN ('vacio', 'vacío', 'todos', 'all')
            OR LOWER(m.status) = TRIM(LOWER({{estado}}))
        )
    ]]

    GROUP BY m.status
),

totals AS (
    SELECT
        SUM(messages) AS total_messages
    FROM filtered_messages
)

SELECT
    f.status,
    f.messages,
    ROUND(
        100.0 * f.messages / NULLIF(t.total_messages, 0),
        2
    ) AS percentage
FROM filtered_messages f
CROSS JOIN totals t
ORDER BY f.messages DESC;