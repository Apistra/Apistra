"""Runtime configuration for Apistra services."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    service: str
    version: str
    commit: str
    environment: str
    force_not_ready: bool = False
    heartbeat_path: str = "/tmp/apistra-worker-heartbeat"  # noqa: S108 - container tmpfs
    database_url: str | None = None
    session_ttl_seconds: int = 43_200
    secure_cookies: bool = True
    installation_id: str = "local"
    secret_key_ring_file: str | None = None
    secret_active_key_id: str = "local-v1"  # noqa: S105 - identifier, not a credential

    @classmethod
    def from_environment(cls, service: str) -> RuntimeSettings:
        return cls(
            service=service,
            version=os.getenv("APISTRA_VERSION", "0.0.0-dev"),
            commit=os.getenv("APISTRA_COMMIT", "unknown"),
            environment=os.getenv("APISTRA_ENVIRONMENT", "local"),
            force_not_ready=os.getenv("APISTRA_FORCE_NOT_READY", "false").lower()
            in {"1", "true", "yes"},
            heartbeat_path=os.getenv(
                "APISTRA_HEARTBEAT_PATH",
                "/tmp/apistra-worker-heartbeat",  # noqa: S108
            ),
            database_url=os.getenv("APISTRA_DATABASE_URL"),
            session_ttl_seconds=int(os.getenv("APISTRA_SESSION_TTL_SECONDS", "43200")),
            secure_cookies=os.getenv("APISTRA_SECURE_COOKIES", "true").lower()
            in {"1", "true", "yes"},
            installation_id=os.getenv("APISTRA_INSTALLATION_ID", "local"),
            secret_key_ring_file=os.getenv("APISTRA_SECRET_KEY_RING_FILE"),
            secret_active_key_id=os.getenv("APISTRA_SECRET_ACTIVE_KEY_ID", "local-v1"),
        )

    def marker(self) -> dict[str, str]:
        return {
            "service": self.service,
            "version": self.version,
            "commit": self.commit,
            "environment": self.environment,
        }
