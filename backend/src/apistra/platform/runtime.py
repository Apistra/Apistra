"""Runtime configuration for the CAP-00 health-only services."""

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
        )

    def marker(self) -> dict[str, str]:
        return {
            "service": self.service,
            "version": self.version,
            "commit": self.commit,
            "environment": self.environment,
        }
