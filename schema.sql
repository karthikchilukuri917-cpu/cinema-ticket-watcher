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