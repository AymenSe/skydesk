CREATE TABLE policies (
    intent TEXT PRIMARY KEY,
    title  TEXT NOT NULL,
    body   TEXT NOT NULL
);

CREATE TABLE tickets (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_email TEXT NOT NULL,
    message        TEXT NOT NULL,
    intent         TEXT NOT NULL,
    confidence     REAL NOT NULL,
    status         TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'drafted', 'escalated', 'failed')),
    draft_reply    TEXT,
    model          TEXT,
    latency_ms     INTEGER,
    attempts       INTEGER NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tickets_status ON tickets (status);
CREATE INDEX idx_tickets_intent ON tickets (intent);