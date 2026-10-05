CREATE TABLE limit_policy_versions (
    policy_id UUID NOT NULL,
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version INTEGER NOT NULL CHECK (version > 0),
    status VARCHAR(16) NOT NULL CHECK (status IN ('DRAFT', 'PUBLISHED')),
    name VARCHAR(128) NOT NULL,
    maximum_duration_seconds BIGINT NOT NULL CHECK (maximum_duration_seconds BETWEEN 1 AND 9007199254740991),
    maximum_calls BIGINT NOT NULL CHECK (maximum_calls BETWEEN 1 AND 9007199254740991),
    maximum_tokens BIGINT NOT NULL CHECK (maximum_tokens BETWEEN 1 AND 9007199254740991),
    maximum_cost_minor_units BIGINT NOT NULL CHECK (maximum_cost_minor_units BETWEEN 1 AND 9007199254740991),
    currency CHAR(3) NOT NULL,
    maximum_concurrency BIGINT NOT NULL CHECK (maximum_concurrency BETWEEN 1 AND 9007199254740991),
    rate_limit_requests BIGINT NOT NULL CHECK (rate_limit_requests BETWEEN 1 AND 9007199254740991),
    rate_limit_window_seconds BIGINT NOT NULL CHECK (rate_limit_window_seconds BETWEEN 1 AND 9007199254740991),
    warning_threshold_percent SMALLINT CHECK (
        warning_threshold_percent IS NULL
        OR warning_threshold_percent BETWEEN 1 AND 99
    ),
    created_at TIMESTAMPTZ NOT NULL,
    created_by UUID NOT NULL REFERENCES identity_administrators(id),
    PRIMARY KEY (policy_id, version)
);

CREATE INDEX limit_policy_versions_project_latest_idx
    ON limit_policy_versions (owner_administrator_id, project_id, policy_id, version DESC);

CREATE TABLE limit_policy_idempotency (
    owner_administrator_id UUID NOT NULL REFERENCES identity_administrators(id),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    idempotency_key VARCHAR(128) NOT NULL,
    request_fingerprint CHAR(64) NOT NULL,
    policy_id UUID NOT NULL,
    policy_version INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (owner_administrator_id, project_id, idempotency_key),
    FOREIGN KEY (policy_id, policy_version)
        REFERENCES limit_policy_versions(policy_id, version) ON DELETE CASCADE
);

CREATE TABLE limit_policy_audit_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    correlation_id VARCHAR(128) NOT NULL,
    actor_id UUID NOT NULL REFERENCES identity_administrators(id),
    actor_username VARCHAR(128) NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    policy_id UUID NOT NULL,
    policy_version INTEGER NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    FOREIGN KEY (policy_id, policy_version)
        REFERENCES limit_policy_versions(policy_id, version) ON DELETE CASCADE
);
