CREATE TABLE secret_references (
    id UUID PRIMARY KEY,
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id) ON DELETE RESTRICT,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    purpose TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'REVOKED')),
    version INTEGER NOT NULL CHECK (version >= 1),
    envelope_format_version INTEGER NOT NULL,
    key_id TEXT NOT NULL,
    nonce BYTEA NOT NULL,
    ciphertext BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT secret_references_owner_project_name_unique
        UNIQUE (owner_administrator_id, project_id, name)
);

CREATE INDEX secret_references_owner_project_idx
    ON secret_references (owner_administrator_id, project_id);

CREATE TABLE secret_idempotency (
    owner_administrator_id UUID NOT NULL,
    project_id UUID NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    secret_reference_id UUID NOT NULL REFERENCES secret_references(id),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (owner_administrator_id, project_id, idempotency_key)
);

CREATE TABLE secret_audit_events (
    id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    correlation_id TEXT NOT NULL,
    actor_id UUID NOT NULL REFERENCES identity_administrators(id),
    actor_username TEXT NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id),
    secret_reference_id UUID NOT NULL REFERENCES secret_references(id),
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX secret_audit_events_project_created_idx
    ON secret_audit_events (project_id, created_at DESC);
