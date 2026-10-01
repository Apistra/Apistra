"""Composition root for the API process."""

from datetime import timedelta

from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.adapters.postgres import PostgresIdentityStore
from apistra.modules.identity.adapters.security import (
    Argon2PasswordHasher,
    SecureTokenService,
    UtcClock,
)
from apistra.modules.identity.application import IdentityService
from apistra.platform.runtime import RuntimeSettings


def build_identity_service(settings: RuntimeSettings) -> IdentityService:
    """Select the durable adapter when configured; memory is local/test only."""

    if settings.database_url:
        store = PostgresIdentityStore(settings.database_url)
    elif settings.environment in {"local", "test"}:
        store = InMemoryIdentityStore()
    else:
        raise RuntimeError("APISTRA_DATABASE_URL is required outside local/test environments")
    return IdentityService(
        store=store,
        password_hasher=Argon2PasswordHasher(),
        tokens=SecureTokenService(),
        clock=UtcClock(),
        session_ttl=timedelta(seconds=settings.session_ttl_seconds),
    )
