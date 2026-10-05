"""Composition root for the API process."""

import os
from datetime import timedelta

from apistra.modules.agents.adapters.memory import InMemoryAgentStore
from apistra.modules.agents.adapters.postgres import PostgresAgentStore
from apistra.modules.agents.application import AgentService
from apistra.modules.agents.ports import AgentStore
from apistra.modules.catalog.adapters.crypto import AesGcmSecretCipher
from apistra.modules.catalog.adapters.endpoint_memory import InMemoryEndpointStore
from apistra.modules.catalog.adapters.endpoint_postgres import PostgresEndpointStore
from apistra.modules.catalog.adapters.memory import InMemorySecretStore
from apistra.modules.catalog.adapters.postgres import PostgresSecretStore
from apistra.modules.catalog.adapters.probe import (
    DenyByDefaultDestinationPolicy,
    OpenAiCompatibleEndpointProbe,
)
from apistra.modules.catalog.adapters.tool_memory import InMemoryToolStore
from apistra.modules.catalog.adapters.tool_postgres import PostgresToolStore
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.application.endpoints import EndpointService
from apistra.modules.catalog.application.tools import ToolService
from apistra.modules.catalog.ports import SecretStore
from apistra.modules.catalog.ports.endpoints import EndpointStore
from apistra.modules.catalog.ports.tools import ToolStore
from apistra.modules.identity.adapters.memory import InMemoryIdentityStore
from apistra.modules.identity.adapters.postgres import PostgresIdentityStore
from apistra.modules.identity.adapters.security import (
    Argon2PasswordHasher,
    SecureTokenService,
    UtcClock,
)
from apistra.modules.identity.application import IdentityService
from apistra.modules.identity.ports import IdentityStore
from apistra.modules.policies.adapters.memory import InMemoryPolicyStore
from apistra.modules.policies.adapters.postgres import PostgresPolicyStore
from apistra.modules.policies.application import PolicyService
from apistra.modules.policies.ports import PolicyStore
from apistra.modules.projects.adapters.memory import InMemoryProjectStore
from apistra.modules.projects.adapters.postgres import PostgresProjectStore
from apistra.modules.projects.application import ProjectService
from apistra.modules.projects.ports import ProjectStore
from apistra.platform.runtime import RuntimeSettings

EPHEMERAL_SECRET_KEY_BYTES = 32
LOCAL_ENVIRONMENTS = {"local", "test"}
DATABASE_REQUIRED_MESSAGE = "APISTRA_DATABASE_URL is required outside local/test environments"


def build_identity_service(settings: RuntimeSettings) -> IdentityService:
    """Select the durable adapter when configured; memory is local/test only."""

    if settings.database_url:
        store: IdentityStore = PostgresIdentityStore(settings.database_url)
    elif settings.environment in LOCAL_ENVIRONMENTS:
        store = InMemoryIdentityStore()
    else:
        raise RuntimeError(DATABASE_REQUIRED_MESSAGE)
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
        raise RuntimeError(DATABASE_REQUIRED_MESSAGE)
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
        raise RuntimeError(DATABASE_REQUIRED_MESSAGE)
    return EndpointService(
        store,
        secrets,
        DenyByDefaultDestinationPolicy(),
        OpenAiCompatibleEndpointProbe(),
        UtcClock(),
    )


def build_tool_service(settings: RuntimeSettings) -> ToolService:
    """Compose immutable governed-tool persistence."""

    if settings.database_url:
        store: ToolStore = PostgresToolStore(settings.database_url)
    elif settings.environment in LOCAL_ENVIRONMENTS:
        store = InMemoryToolStore()
    else:
        raise RuntimeError(DATABASE_REQUIRED_MESSAGE)
    return ToolService(store, UtcClock())


def build_policy_service(settings: RuntimeSettings) -> PolicyService:
    """Compose deterministic approval-policy persistence."""

    if settings.database_url:
        store: PolicyStore = PostgresPolicyStore(settings.database_url)
    elif settings.environment in LOCAL_ENVIRONMENTS:
        store = InMemoryPolicyStore()
    else:
        raise RuntimeError(DATABASE_REQUIRED_MESSAGE)
    return PolicyService(store, UtcClock())


def build_agent_service(
    settings: RuntimeSettings, endpoints: EndpointService, tools: ToolService
) -> AgentService:
    """Compose immutable agent-version persistence."""

    if settings.database_url:
        store: AgentStore = PostgresAgentStore(settings.database_url)
    elif settings.environment in LOCAL_ENVIRONMENTS:
        store = InMemoryAgentStore()
    else:
        raise RuntimeError(DATABASE_REQUIRED_MESSAGE)
    return AgentService(store, endpoints, tools, UtcClock())
