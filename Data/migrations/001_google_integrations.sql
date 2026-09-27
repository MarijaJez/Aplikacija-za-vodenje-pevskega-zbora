BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM people
        GROUP BY lower(trim(email))
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Migracija ni mogoča: več članov uporablja isti e-poštni naslov (ne glede na velike/male črke).';
    END IF;
END $$;

UPDATE people SET email = lower(trim(email));
CREATE UNIQUE INDEX IF NOT EXISTS people_email_lower_uidx ON people (lower(email));

CREATE TABLE IF NOT EXISTS user_google_identities (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    issuer VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    UNIQUE (issuer, subject)
);

CREATE TABLE IF NOT EXISTS google_calendar_connection (
    singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    google_email VARCHAR(255) NOT NULL,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    scopes TEXT NOT NULL DEFAULT '',
    calendar_id VARCHAR(1024),
    calendar_name VARCHAR(255),
    connected_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS event_google_calendar_links (
    event_id BIGINT PRIMARY KEY REFERENCES events(id) ON DELETE RESTRICT,
    calendar_id VARCHAR(1024) NOT NULL,
    google_event_id VARCHAR(255) NOT NULL,
    last_synced_at TIMESTAMPTZ,
    last_error TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (calendar_id, google_event_id)
);

COMMIT;
