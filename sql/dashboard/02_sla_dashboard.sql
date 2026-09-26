-- Soporte visual: SLA operativo
-- La vista vw_incoming_sla_detail se construye con Window Functions.
SELECT
    COUNT(*) AS incoming_messages,
    COUNT(*) FILTER (WHERE next_action_at IS NOT NULL) AS answered_messages,
    COUNT(*) FILTER (WHERE next_action_at IS NULL) AS unanswered_messages,
    ROUND(100.0 * COUNT(*) FILTER (WHERE next_action_at IS NOT NULL) / NULLIF(COUNT(*), 0), 2) AS coverage_pct,
    ROUND(AVG(response_minutes) FILTER (WHERE response_minutes IS NOT NULL)::numeric, 2) AS avg_sla_minutes,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_minutes)
          FILTER (WHERE response_minutes IS NOT NULL)::numeric, 2) AS median_sla_minutes,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY response_minutes)
          FILTER (WHERE response_minutes IS NOT NULL)::numeric, 2) AS p90_sla_minutes
FROM vw_incoming_sla_detail
WHERE incoming_at::date BETWEEN :date_from AND :date_to;
