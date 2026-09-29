CREATE TABLE IF NOT EXISTS watches (
    id TEXT PRIMARY KEY,
    movie TEXT NOT NULL,
    movie_event_code TEXT,
    target_date DATE NOT NULL,
    city TEXT NOT NULL,
    cinemas JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watch_state (
    watch_id TEXT PRIMARY KEY,
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_watch_state_watch
        FOREIGN KEY (watch_id)
        REFERENCES watches(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS watch_health (
    watch_id TEXT PRIMARY KEY,
    last_checked TIMESTAMPTZ,
    status TEXT,
    message TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_watch_health_watch
        FOREIGN KEY (watch_id)
        REFERENCES watches(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS watch_history (
    id BIGSERIAL PRIMARY KEY,
    watch_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cinema TEXT,
    show_time TEXT,
    previous TEXT,
    current TEXT,
    previous_tickets INTEGER,
    current_tickets INTEGER,
    show_id TEXT,

    CONSTRAINT fk_watch_history_watch
        FOREIGN KEY (watch_id)
        REFERENCES watches(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_watch_history_watch_id
    ON watch_history(watch_id);

CREATE INDEX IF NOT EXISTS idx_watch_history_timestamp
    ON watch_history(timestamp);
    -- =========================================================
-- BOOKMYSHOW CATALOGUE
-- =========================================================

CREATE TABLE IF NOT EXISTS cinema_catalogue (
    city TEXT NOT NULL,
    city_code TEXT NOT NULL,
    name TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    slug TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (city_code, provider_id)
);

CREATE INDEX IF NOT EXISTS idx_cinema_catalogue_city
    ON cinema_catalogue(city);


CREATE TABLE IF NOT EXISTS movie_catalogue (
    city TEXT NOT NULL,
    event_code TEXT NOT NULL,
    title TEXT NOT NULL,
    event_name TEXT,
    event_url TEXT,
    event_group TEXT,
    language TEXT,
    dimension TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (city, event_code)
);

CREATE INDEX IF NOT EXISTS idx_movie_catalogue_city
    ON movie_catalogue(city);

CREATE INDEX IF NOT EXISTS idx_movie_catalogue_title
    ON movie_catalogue(title); 
CREATE INDEX IF NOT EXISTS idx_watch_history_timestamp
    ON watch_history(timestamp);

-- =========================================================
-- BOOKMYSHOW CATALOGUE
-- =========================================================

CREATE TABLE IF NOT EXISTS cinema_catalogue (
    city TEXT NOT NULL,
    city_code TEXT NOT NULL,
    name TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    slug TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (city_code, provider_id)
);

CREATE INDEX IF NOT EXISTS idx_cinema_catalogue_city
    ON cinema_catalogue(city);

CREATE TABLE IF NOT EXISTS movie_catalogue (
    city TEXT NOT NULL,
    event_code TEXT NOT NULL,
    title TEXT NOT NULL,
    event_name TEXT,
    event_url TEXT,
    event_group TEXT,
    language TEXT,
    dimension TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (city, event_code)
);

CREATE INDEX IF NOT EXISTS idx_movie_catalogue_city
    ON movie_catalogue(city);

CREATE INDEX IF NOT EXISTS idx_movie_catalogue_title
    ON movie_catalogue(title);