-- Funnel de entrega de mensajes salientes.
-- La columna "sent" se conserva porque existe en la fuente, aunque el caso técnico
-- solicita especialmente read, delivered y failed.
WITH outgoing AS (
    SELECT status
    FROM messages
    WHERE message_type = 'outgoing'
),
summary AS (
    SELECT
        status,
        COUNT(*) AS messages
    FROM outgoing
    GROUP BY status
)
SELECT
    status,
    messages,
    ROUND(100.0 * messages / SUM(messages) OVER (), 2) AS percentage
FROM summary
ORDER BY messages DESC, status;
