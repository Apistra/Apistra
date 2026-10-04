CREATE TABLE model_endpoints (
    id UUID PRIMARY KEY,
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(64) NOT NULL,
    purpose VARCHAR(32) NOT NULL CHECK (purpose IN ('GENERATIVE', 'EMBEDDING')),
    provider_protocol VARCHAR(64) NOT NULL CHECK (provider_protocol IN ('OPENAI_COMPATIBLE')),
    base_url TEXT NOT NULL,
    model_identifier VARCHAR(256) NOT NULL,
    secret_reference_id UUID NOT NULL REFERENCES secret_references(id),
    network_profile VARCHAR(32) NOT NULL CHECK (network_profile IN ('CLOUD', 'ON_PREMISE', 'LOCAL')),
    status VARCHAR(32) NOT NULL CHECK (status IN ('UNVERIFIED', 'VERIFIED')),
    version INTEGER NOT NULL CHECK (version > 0),
    last_probe_outcome VARCHAR(64) CHECK (
        last_probe_outcome IS NULL OR last_probe_outcome IN (
            'CONNECTION_VERIFIED', 'CONNECTION_FAILED', 'DESTINATION_BLOCKED',
            'AUTHENTICATION_FAILED', 'TIMED_OUT', 'PROBE_NOT_SUPPORTED'
        )
    ),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT model_endpoints_owner_project_name_unique
        UNIQUE (owner_administrator_id, project_id, name)
);

CREATE TABLE endpoint_idempotency (
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    idempotency_key VARCHAR(128) NOT NULL,
    request_fingerprint CHAR(64) NOT NULL,
    endpoint_id UUID NOT NULL REFERENCES model_endpoints(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (owner_administrator_id, project_id, idempotency_key)
);

CREATE TABLE endpoint_audit_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    correlation_id VARCHAR(128) NOT NULL,
    actor_id UUID NOT NULL REFERENCES identity_administrators(id),
    actor_username VARCHAR(128) NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    endpoint_id UUID NOT NULL REFERENCES model_endpoints(id) ON DELETE CASCADE,
    details JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE INDEX endpoint_audit_events_project_created_idx
    ON endpoint_audit_events (project_id, created_at DESC);
