-- Ta datoteka vsebuje vse potrebne create ukaze,
-- s katerimi lahko ustvarimo bazo od začetka.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE roles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE people (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    birth_date DATE,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(40) NOT NULL DEFAULT '',
    voice VARCHAR(20) NOT NULL CHECK (voice IN ('Sopran', 'Alt', 'Tenor', 'Bas')),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    person_id BIGINT NOT NULL UNIQUE REFERENCES people(id) ON DELETE CASCADE,
    username VARCHAR(120) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE person_roles (
    person_id BIGINT NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (person_id, role_id)
);

CREATE TABLE categories (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE songs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    notes_path TEXT,
    audio_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE song_categories (
    song_id BIGINT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (song_id, category_id)
);

CREATE TABLE song_reviews (
    person_id BIGINT NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    song_id BIGINT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (person_id, song_id)
);

CREATE TABLE events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_date TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(40) NOT NULL,
    name VARCHAR(255) NOT NULL,
    place VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE event_program (
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    song_id BIGINT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    performance_rating SMALLINT CHECK (performance_rating BETWEEN 1 AND 5),
    comment TEXT NOT NULL DEFAULT '',
    position SMALLINT NOT NULL DEFAULT 1,
    PRIMARY KEY (event_id, song_id)
);

CREATE TABLE attendance (
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    person_id BIGINT NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL CHECK (status IN ('present', 'late_under', 'late_over', 'excused', 'absent')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    PRIMARY KEY (event_id, person_id)
);

CREATE TABLE transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_date DATE NOT NULL,
    description TEXT NOT NULL,
    person_name VARCHAR(255) NOT NULL,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('Prihodek', 'Odhodek')),
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    settled BOOLEAN NOT NULL DEFAULT FALSE,
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX people_name_idx ON people(last_name, first_name);
CREATE INDEX events_date_idx ON events(event_date);
CREATE INDEX attendance_person_idx ON attendance(person_id);
CREATE INDEX reviews_song_idx ON song_reviews(song_id);
CREATE INDEX transactions_date_idx ON transactions(transaction_date DESC);
