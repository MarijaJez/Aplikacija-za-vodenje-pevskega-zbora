CREATE TABLE IF NOT EXISTS event_photos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    file_name VARCHAR(80) NOT NULL UNIQUE,
    caption VARCHAR(300) NOT NULL DEFAULT '',
    alt_text VARCHAR(160) NOT NULL,
    uploaded_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS event_photos_event_idx ON event_photos(event_id, uploaded_at DESC, id DESC);
