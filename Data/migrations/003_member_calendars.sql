-- Each member authorizes their own primary Google Calendar. Old shared
-- event links remain historical, but its OAuth tokens are discarded.
UPDATE google_calendar_connection
SET active=FALSE, access_token_encrypted=NULL, refresh_token_encrypted=NULL,
    token_expires_at=NULL, updated_at=NOW();
ALTER TABLE event_google_calendar_links
    DROP CONSTRAINT IF EXISTS event_google_calendar_links_event_id_fkey;
ALTER TABLE event_google_calendar_links
    ADD CONSTRAINT event_google_calendar_links_event_id_fkey
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE;
CREATE TABLE IF NOT EXISTS user_google_calendar_connections (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    google_subject VARCHAR(255) NOT NULL UNIQUE,
    google_email VARCHAR(255) NOT NULL,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    scopes TEXT NOT NULL DEFAULT '',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_event_google_calendar_links (
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    google_event_id VARCHAR(255) NOT NULL,
    last_synced_at TIMESTAMPTZ,
    last_error TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, event_id),
    UNIQUE (user_id, google_event_id)
);

CREATE TABLE IF NOT EXISTS user_google_calendar_pending_deletions (
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    google_event_id VARCHAR(255) NOT NULL,
    last_error TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, google_event_id)
);
