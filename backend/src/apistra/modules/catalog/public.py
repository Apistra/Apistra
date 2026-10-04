"""Stable public boundary of the configuration catalogue."""

from apistra.modules.catalog.application import SecretResult, SecretService
from apistra.modules.catalog.application.endpoints import EndpointResult, EndpointService
from apistra.modules.catalog.domain import SecretErrorCode, SecretReference, SecretStatus
from apistra.modules.catalog.domain.endpoints import (
    EndpointErrorCode,
    EndpointPurpose,
    EndpointStatus,
    ModelEndpoint,
    NetworkProfile,
    ProbeOutcome,
    ProviderProtocol,
)

__all__ = [
    "EndpointErrorCode",
    "EndpointPurpose",
    "EndpointResult",
    "EndpointService",
    "EndpointStatus",
    "ModelEndpoint",
    "NetworkProfile",
    "ProbeOutcome",
    "ProviderProtocol",
    "SecretErrorCode",
    "SecretReference",
    "SecretResult",
    "SecretService",
    "SecretStatus",
]
