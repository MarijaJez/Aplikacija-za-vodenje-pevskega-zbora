CREATE TABLE IF NOT EXISTS gallery_albums (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(160) NOT NULL CHECK (length(trim(name)) > 0),
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE event_photos ALTER COLUMN event_id DROP NOT NULL;
ALTER TABLE event_photos ADD COLUMN IF NOT EXISTS album_id BIGINT REFERENCES gallery_albums(id) ON DELETE CASCADE;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'event_photos_one_album') THEN
        ALTER TABLE event_photos ADD CONSTRAINT event_photos_one_album
            CHECK ((event_id IS NOT NULL)::int + (album_id IS NOT NULL)::int = 1);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS event_photos_album_idx ON event_photos(album_id, uploaded_at DESC, id DESC);
