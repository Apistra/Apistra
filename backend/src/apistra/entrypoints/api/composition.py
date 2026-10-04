"""Composition root for the API process."""

import os
from datetime import timedelta

from apistra.modules.catalog.adapters.crypto import AesGcmSecretCipher
from apistra.modules.catalog.adapters.endpoint_memory import InMemoryEndpointStore
from apistra.modules.catalog.adapters.endpoint_postgres import PostgresEndpointStore
from apistra.modules.catalog.adapters.memory import InMemorySecretStore
from apistra.modules.catalog.adapters.postgres import PostgresSecretStore
from apistra.modules.catalog.adapters.probe import (
    DenyByDefaultDestinationPolicy,
    OpenAiCompatibleEndpointProbe,
)
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.catalog.ports import SecretStore
from apistra.modules.catalog.ports.endpoints import EndpointStore
from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.adapters.postgres import PostgresIdentityStore
from apistra.modules.identity.adapters.security import (
    Argon2PasswordHasher,
    SecureTokenService,
    UtcClock,
)
from apistra.modules.identity.application import IdentityService
from apistra.modules.identity.ports import IdentityStore
from apistra.modules.projects.adapters.memory import InMemoryProjectStore
from apistra.modules.projects.adapters.postgres import PostgresProjectStore
from apistra.modules.projects.application import ProjectService
from apistra.modules.projects.ports import ProjectStore
from apistra.platform.runtime import RuntimeSettings

EPHEMERAL_SECRET_KEY_BYTES = 32
LOCAL_ENVIRONMENTS = {"local", "test"}


def build_identity_service(settings: RuntimeSettings) -> IdentityService:
    """Select the durable adapter when configured; memory is local/test only."""

    if settings.database_url:
        store: IdentityStore = PostgresIdentityStore(settings.database_url)
    elif settings.environment in LOCAL_ENVIRONMENTS:
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


def build_project_service(settings: RuntimeSettings) -> ProjectService:
    """Select a project adapter without leaking persistence into the use case."""

    if settings.database_url:
        store: ProjectStore = PostgresProjectStore(settings.database_url)
    elif settings.environment in LOCAL_ENVIRONMENTS:
        store = InMemoryProjectStore()
    else:
        raise RuntimeError("APISTRA_DATABASE_URL is required outside local/test environments")
    return ProjectService(store=store, clock=UtcClock())


def build_secret_service(settings: RuntimeSettings) -> SecretService:
    """Compose encrypted storage; persistent data always requires an operator key file."""

    if settings.database_url:
        if not settings.secret_key_ring_file:
            raise RuntimeError(
                "APISTRA_SECRET_KEY_RING_FILE is required with persistent secret storage"
            )
        store: SecretStore = PostgresSecretStore(settings.database_url)
        cipher = AesGcmSecretCipher.from_key_ring_file(
            settings.secret_active_key_id,
            settings.secret_key_ring_file,
        )
    elif settings.environment in LOCAL_ENVIRONMENTS:
        store = InMemorySecretStore()
        cipher = AesGcmSecretCipher(
            settings.secret_active_key_id,
            {settings.secret_active_key_id: os.urandom(EPHEMERAL_SECRET_KEY_BYTES)},
        )
    else:
        raise RuntimeError("Persistent database and secret master-key file are required")
    return SecretService(store, cipher, UtcClock(), settings.installation_id)


def build_endpoint_service(settings: RuntimeSettings, secrets: SecretService) -> EndpointService:
    """Compose endpoint persistence and the deny-by-default probe boundary."""

    if settings.database_url:
        store: EndpointStore = PostgresEndpointStore(settings.database_url)
    elif settings.environment in LOCAL_ENVIRONMENTS:
        store = InMemoryEndpointStore()
    else:
        raise RuntimeError("APISTRA_DATABASE_URL is required outside local/test environments")
    return EndpointService(
        store,
        secrets,
        DenyByDefaultDestinationPolicy(),
        OpenAiCompatibleEndpointProbe(),
        UtcClock(),
    )
