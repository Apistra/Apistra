ALTER TABLE identity_administrators
    ADD COLUMN IF NOT EXISTS login_enabled BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE identity_administrators
    DROP CONSTRAINT IF EXISTS identity_administrators_installation_id_key;

CREATE INDEX IF NOT EXISTS identity_administrators_installation_idx
    ON identity_administrators (installation_id, id);

INSERT INTO apistra_schema_migrations (migration_id)
VALUES ('cap_01/003_multiple_principals')
ON CONFLICT (migration_id) DO NOTHING;
