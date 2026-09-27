-- Punto 2. Funnel de entrega.
-- Porcentaje de mensajes outgoing en read, delivered y failed
-- sobre el total de mensajes salientes.
WITH outgoing AS (
    SELECT status
    FROM messages
    WHERE message_type = 'outgoing'
),
total AS (
    SELECT COUNT(*) AS total_messages
    FROM outgoing
),
by_status AS (
    SELECT
        status,
        COUNT(*) AS messages
    FROM outgoing
    WHERE status IN ('read', 'delivered', 'failed')
    GROUP BY status
)
SELECT
    b.status,
    b.messages,
    ROUND(100.0 * b.messages / NULLIF(t.total_messages, 0), 2) AS percentage
FROM by_status b
CROSS JOIN total t
ORDER BY b.messages DESC, b.status;
