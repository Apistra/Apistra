CREATE TABLE agent_versions (
    agent_id UUID NOT NULL,
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version INTEGER NOT NULL CHECK (version > 0),
    status VARCHAR(16) NOT NULL CHECK (status IN ('DRAFT', 'PUBLISHED')),
    name VARCHAR(128) NOT NULL,
    instructions TEXT NOT NULL,
    primary_endpoint_id UUID NOT NULL,
    primary_endpoint_version INTEGER NOT NULL CHECK (primary_endpoint_version > 0),
    fallback_endpoint_id UUID,
    fallback_endpoint_version INTEGER,
    tool_versions JSONB NOT NULL DEFAULT '[]'::JSONB,
    limits_policy_id UUID,
    limits_policy_version INTEGER,
    created_at TIMESTAMPTZ NOT NULL,
    created_by UUID NOT NULL REFERENCES identity_administrators(id),
    PRIMARY KEY (agent_id, version),
    CHECK ((fallback_endpoint_id IS NULL) = (fallback_endpoint_version IS NULL)),
    CHECK ((limits_policy_id IS NULL) = (limits_policy_version IS NULL)),
    CHECK (fallback_endpoint_id IS NULL OR fallback_endpoint_id <> primary_endpoint_id)
);

CREATE INDEX agent_versions_project_latest_idx
    ON agent_versions (owner_administrator_id, project_id, agent_id, version DESC);

CREATE TABLE agent_idempotency (
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    idempotency_key VARCHAR(128) NOT NULL,
    request_fingerprint CHAR(64) NOT NULL,
    agent_id UUID NOT NULL,
    agent_version INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (owner_administrator_id, project_id, idempotency_key),
    FOREIGN KEY (agent_id, agent_version) REFERENCES agent_versions(agent_id, version) ON DELETE CASCADE
);

CREATE TABLE agent_audit_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    correlation_id VARCHAR(128) NOT NULL,
    actor_id UUID NOT NULL REFERENCES identity_administrators(id),
    actor_username VARCHAR(128) NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL,
    agent_version INTEGER NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    FOREIGN KEY (agent_id, agent_version) REFERENCES agent_versions(agent_id, version) ON DELETE CASCADE
);
