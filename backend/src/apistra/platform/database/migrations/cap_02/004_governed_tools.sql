CREATE TABLE tool_versions (
    tool_id UUID NOT NULL,
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version INTEGER NOT NULL CHECK (version > 0),
    status VARCHAR(16) NOT NULL CHECK (status IN ('DRAFT', 'PUBLISHED')),
    name VARCHAR(128) NOT NULL,
    description VARCHAR(4096) NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    effect_class VARCHAR(20) NOT NULL CHECK (effect_class IN ('READ', 'WRITE', 'ADMINISTRATIVE')),
    actions TEXT[] NOT NULL CHECK (cardinality(actions) BETWEEN 1 AND 128),
    created_at TIMESTAMPTZ NOT NULL,
    created_by UUID NOT NULL REFERENCES identity_administrators(id),
    PRIMARY KEY (tool_id, version)
);

CREATE INDEX tool_versions_project_latest_idx
    ON tool_versions (owner_administrator_id, project_id, tool_id, version DESC);

CREATE TABLE tool_idempotency (
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    idempotency_key VARCHAR(128) NOT NULL,
    request_fingerprint CHAR(64) NOT NULL,
    tool_id UUID NOT NULL,
    tool_version INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (owner_administrator_id, project_id, idempotency_key),
    FOREIGN KEY (tool_id, tool_version) REFERENCES tool_versions(tool_id, version) ON DELETE CASCADE
);

CREATE TABLE tool_audit_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    correlation_id VARCHAR(128) NOT NULL,
    actor_id UUID NOT NULL REFERENCES identity_administrators(id),
    actor_username VARCHAR(128) NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL,
    tool_version INTEGER NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    FOREIGN KEY (tool_id, tool_version) REFERENCES tool_versions(tool_id, version) ON DELETE CASCADE
);

CREATE TABLE policy_approval_exceptions (
    id UUID PRIMARY KEY,
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL,
    tool_version INTEGER NOT NULL,
    action VARCHAR(128) NOT NULL,
    scope VARCHAR(512) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    active BOOLEAN NOT NULL,
    FOREIGN KEY (tool_id, tool_version) REFERENCES tool_versions(tool_id, version) ON DELETE CASCADE
);

CREATE INDEX policy_approval_exception_exact_idx ON policy_approval_exceptions
    (owner_administrator_id, project_id, tool_id, tool_version, action, scope, expires_at DESC)
    WHERE active=TRUE;

CREATE TABLE policy_audit_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    correlation_id VARCHAR(128) NOT NULL,
    actor_id UUID NOT NULL REFERENCES identity_administrators(id),
    actor_username VARCHAR(128) NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL,
    tool_version INTEGER NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    FOREIGN KEY (tool_id, tool_version) REFERENCES tool_versions(tool_id, version) ON DELETE CASCADE
);
