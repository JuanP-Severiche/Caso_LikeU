-- Soporte visual: KPIs de entrega
-- Parámetros del dashboard: :date_from, :date_to, :status
SELECT
    COUNT(*) AS outgoing_messages,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_messages,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'failed') / NULLIF(COUNT(*), 0), 2) AS failed_pct,
    COUNT(*) FILTER (WHERE status = 'read') AS read_messages,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'read') / NULLIF(COUNT(*), 0), 2) AS read_pct,
    COUNT(*) FILTER (WHERE status = 'delivered') AS delivered_messages,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'delivered') / NULLIF(COUNT(*), 0), 2) AS delivered_pct
FROM messages
WHERE message_type = 'outgoing'
  AND created_at::date BETWEEN :date_from AND :date_to
  AND (:status IS NULL OR status = :status);
