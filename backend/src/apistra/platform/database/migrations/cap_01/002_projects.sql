CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id) ON DELETE RESTRICT,
    name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 128),
    project_key TEXT NOT NULL CHECK (project_key ~ '^[A-Z0-9][A-Z0-9-]{1,31}$'),
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'ARCHIVED')),
    version INTEGER NOT NULL CHECK (version >= 1),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT projects_owner_key_unique UNIQUE (owner_administrator_id, project_key),
    CONSTRAINT projects_updated_after_created CHECK (updated_at >= created_at)
);

CREATE INDEX IF NOT EXISTS projects_owner_status_idx
    ON projects (owner_administrator_id, status, project_key);

CREATE TABLE IF NOT EXISTS project_idempotency (
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id) ON DELETE CASCADE,
    idempotency_key TEXT NOT NULL CHECK (char_length(idempotency_key) BETWEEN 1 AND 128),
    request_fingerprint CHAR(64) NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (owner_administrator_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS project_audit_events (
    id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    correlation_id TEXT NOT NULL,
    actor_id UUID NOT NULL,
    actor_username TEXT NOT NULL,
    project_id UUID NOT NULL,
    project_key TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS project_audit_project_created_idx
    ON project_audit_events (project_id, created_at, id);
