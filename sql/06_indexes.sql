-- Índices orientados a los filtros y cálculos utilizados por el dashboard.
CREATE INDEX IF NOT EXISTS idx_messages_type_status
    ON messages (message_type, status);

CREATE INDEX IF NOT EXISTS idx_messages_created_at
    ON messages (created_at);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
    ON messages (conversation_id, created_at, id);

CREATE INDEX IF NOT EXISTS idx_messages_failed_template
    ON messages (template_name)
    WHERE message_type = 'outgoing' AND status = 'failed';
