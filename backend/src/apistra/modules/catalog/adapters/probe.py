"""Deny-by-default network policy and bounded OpenAI-compatible probe."""

from __future__ import annotations

import http.client
import ipaddress
import json
import socket
import ssl
from urllib.parse import urlsplit

from apistra.modules.catalog.domain import SecretMaterial
from apistra.modules.catalog.domain.endpoints import (
    ApprovedDestination,
    NetworkProfile,
    ProbeOutcome,
    ProviderProtocol,
)

DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443
MAXIMUM_PROBE_RESPONSE_BYTES = 65_536
DEFAULT_PROBE_TIMEOUT_SECONDS = 3.0
HTTP_OK = 200
HTTP_REDIRECT_START = 300
HTTP_REDIRECT_END = 400


class DenyByDefaultDestinationPolicy:
    """Resolve once and approve every returned address for the selected profile."""

    def approve(self, base_url: str, profile: NetworkProfile) -> ApprovedDestination | None:
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None
        port = parsed.port or (
            DEFAULT_HTTPS_PORT if parsed.scheme == "https" else DEFAULT_HTTP_PORT
        )
        try:
            resolved = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
        except (OSError, UnicodeError):
            return None
        addresses = tuple(sorted({str(item[4][0]) for item in resolved}))
        if not addresses or any(not self._allowed(address, profile) for address in addresses):
            return None
        return ApprovedDestination(
            scheme=parsed.scheme,
            host=parsed.hostname,
            port=port,
            base_path=parsed.path.rstrip("/"),
            addresses=addresses,
        )

    @staticmethod
    def _allowed(address: str, profile: NetworkProfile) -> bool:
        ip = ipaddress.ip_address(address)
        if ip.is_unspecified or ip.is_multicast or ip.is_link_local or ip.is_reserved:
            return False
        if profile is NetworkProfile.LOCAL:
            return ip.is_loopback
        if profile is NetworkProfile.ON_PREMISE:
            return ip.is_private and not ip.is_loopback
        return ip.is_global


class _PinnedHttpsConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, address: str, timeout: float) -> None:
        self._ssl_context = ssl.create_default_context()
        super().__init__(host, port, timeout=timeout, context=self._ssl_context)
        self._address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection((self._address, self.port), self.timeout)
        self.sock = self._ssl_context.wrap_socket(raw_socket, server_hostname=self.host)


class OpenAiCompatibleEndpointProbe:
    def __init__(self, timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS) -> None:
        self._timeout_seconds = timeout_seconds

    def probe(
        self,
        protocol: ProviderProtocol | str,
        destination: ApprovedDestination,
        model_identifier: str,
        credential: SecretMaterial,
    ) -> ProbeOutcome:
        if protocol is not ProviderProtocol.OPENAI_COMPATIBLE:
            return ProbeOutcome.PROBE_NOT_SUPPORTED
        address = destination.addresses[0]
        connection: http.client.HTTPConnection
        if destination.scheme == "https":
            connection = _PinnedHttpsConnection(
                destination.host,
                destination.port,
                address,
                self._timeout_seconds,
            )
        else:
            connection = http.client.HTTPConnection(
                address,
                destination.port,
                timeout=self._timeout_seconds,
            )
        path = f"{destination.base_path}/models"
        try:
            connection.request(
                "GET",
                path,
                headers={
                    "Authorization": f"Bearer {credential.value.decode()}",
                    "Host": destination.host,
                    "Accept": "application/json",
                },
            )
            response = connection.getresponse()
            response_body = response.read(MAXIMUM_PROBE_RESPONSE_BYTES + 1)
            if response.status == HTTP_OK:
                return (
                    ProbeOutcome.CONNECTION_VERIFIED
                    if self._contains_model(response_body, model_identifier)
                    else ProbeOutcome.CONNECTION_FAILED
                )
            if response.status in {401, 403}:
                return ProbeOutcome.AUTHENTICATION_FAILED
            if HTTP_REDIRECT_START <= response.status < HTTP_REDIRECT_END:
                return ProbeOutcome.DESTINATION_BLOCKED
            return ProbeOutcome.CONNECTION_FAILED
        except TimeoutError:
            return ProbeOutcome.TIMED_OUT
        except (OSError, http.client.HTTPException, UnicodeError):
            return ProbeOutcome.CONNECTION_FAILED
        finally:
            connection.close()

    @staticmethod
    def _contains_model(response_body: bytes, model_identifier: str) -> bool:
        if len(response_body) > MAXIMUM_PROBE_RESPONSE_BYTES:
            return False
        try:
            payload = json.loads(response_body)
            items = payload.get("data", [])
            return isinstance(items, list) and any(
                isinstance(item, dict) and item.get("id") == model_identifier for item in items
            )
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            return False
