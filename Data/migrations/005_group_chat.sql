CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    body VARCHAR(2000) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edited_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    deleted_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    CHECK (length(btrim(body)) > 0)
);

CREATE INDEX IF NOT EXISTS chat_messages_recent_idx ON chat_messages(id DESC);
