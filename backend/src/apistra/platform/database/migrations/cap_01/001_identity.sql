CREATE TABLE IF NOT EXISTS apistra_schema_migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identity_administrators (
    id UUID PRIMARY KEY,
    installation_id TEXT NOT NULL UNIQUE CHECK (installation_id = 'local'),
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS identity_sessions (
    id UUID PRIMARY KEY,
    administrator_id UUID NOT NULL REFERENCES identity_administrators(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE,
    csrf_hash CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    CONSTRAINT identity_session_expiry_after_creation CHECK (expires_at > created_at),
    CONSTRAINT identity_session_revocation_after_creation
        CHECK (revoked_at IS NULL OR revoked_at >= created_at)
);

CREATE INDEX IF NOT EXISTS identity_sessions_administrator_idx
    ON identity_sessions (administrator_id);
CREATE INDEX IF NOT EXISTS identity_sessions_expiry_idx
    ON identity_sessions (expires_at) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS identity_audit_events (
    id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    correlation_id TEXT NOT NULL,
    actor_id UUID,
    actor_username TEXT,
    subject_id UUID,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

INSERT INTO apistra_schema_migrations (migration_id)
VALUES ('cap_01/001_identity')
ON CONFLICT (migration_id) DO NOTHING;
