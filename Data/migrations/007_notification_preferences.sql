CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    events_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    chat_mode TEXT NOT NULL DEFAULT 'limited' CHECK (chat_mode IN ('off','all','limited')),
    chat_interval_minutes INTEGER NOT NULL DEFAULT 30 CHECK (chat_interval_minutes IN (15,30,60,120)),
    last_chat_notification_at TIMESTAMPTZ
);
