from __future__ import annotations

import base64
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from apistra.modules.catalog.adapters.crypto import AesGcmSecretCipher
from apistra.modules.catalog.adapters.memory import InMemorySecretStore
from apistra.modules.catalog.application import SecretService
from apistra.modules.catalog.domain import SecretErrorCode, SecretMaterial, SecretStatus

CANARY = "CAP02-CANARY-never-visible"


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 4, 12, tzinfo=UTC)


def service() -> tuple[SecretService, InMemorySecretStore]:
    store = InMemorySecretStore()
    cipher = AesGcmSecretCipher("test-v1", {"test-v1": bytes(range(32))})
    return SecretService(store, cipher, Clock(), "installation-test"), store


def test_create_replay_replace_resolve_and_revoke_are_versioned() -> None:
    secrets, store = service()
    owner_id, project_id = uuid4(), uuid4()
    created = secrets.create(
        owner_id,
        "admin.alpha",
        project_id,
        "provider-primary",
        "Primary endpoint credential",
        CANARY,
        "create-primary",
        "corr-create",
    )
    replay = secrets.create(
        owner_id,
        "admin.alpha",
        project_id,
        "provider-primary",
        "Primary endpoint credential",
        CANARY,
        "create-primary",
        "corr-replay",
    )
    assert replay.value == created.value
    assert created.value is not None
    assert CANARY.encode() not in created.value.envelope.ciphertext
    resolved = secrets.resolve(owner_id, project_id, created.value.id)
    assert resolved.value == SecretMaterial(CANARY.encode())
    assert repr(resolved.value) == "SecretMaterial(<redacted>)"

    replaced = secrets.replace(
        owner_id,
        "admin.alpha",
        project_id,
        created.value.id,
        1,
        "rotated-value",
        "corr-replace",
    )
    assert replaced.value is not None and replaced.value.version == 2
    assert secrets.resolve(owner_id, project_id, created.value.id).value == SecretMaterial(
        b"rotated-value"
    )
    revoked = secrets.revoke(
        owner_id,
        "admin.alpha",
        project_id,
        created.value.id,
        2,
        "corr-revoke",
    )
    assert revoked.value is not None and revoked.value.status is SecretStatus.REVOKED
    assert secrets.resolve(owner_id, project_id, created.value.id).error.code is (
        SecretErrorCode.UNAVAILABLE
    )
    assert [event.event_type for event in store.audit_events] == [
        "secret.created",
        "secret.replaced",
        "secret.revoked",
    ]


def test_foreign_revoked_unresolved_and_tampered_are_indistinguishable() -> None:
    secrets, store = service()
    owner_id, project_id = uuid4(), uuid4()
    reference = secrets.create(
        owner_id,
        "admin.alpha",
        project_id,
        "provider-primary",
        "Primary endpoint credential",
        CANARY,
        "create-primary",
        "corr",
    ).value
    assert reference is not None
    unavailable = [
        secrets.resolve(uuid4(), project_id, reference.id),
        secrets.resolve(owner_id, uuid4(), reference.id),
        secrets.resolve(owner_id, project_id, uuid4()),
    ]
    store._references[reference.id] = replace(
        reference,
        envelope=replace(reference.envelope, ciphertext=b"tampered"),
    )
    unavailable.append(secrets.resolve(owner_id, project_id, reference.id))
    assert {item.error.code for item in unavailable if item.error} == {SecretErrorCode.UNAVAILABLE}
    assert {item.error.message for item in unavailable if item.error} == {
        "Secret reference is unavailable."
    }


def test_validation_and_conflicts_never_echo_secret_values() -> None:
    secrets, _store = service()
    owner_id, project_id = uuid4(), uuid4()
    invalid = secrets.create(
        owner_id, "admin.alpha", project_id, "BAD NAME", "purpose", CANARY, "key", "corr"
    )
    assert invalid.error is not None and CANARY not in invalid.error.message
    created = secrets.create(
        owner_id, "admin.alpha", project_id, "valid-name", "purpose", CANARY, "key", "corr"
    )
    assert created.value is not None
    conflict = secrets.create(
        owner_id,
        "admin.alpha",
        project_id,
        "valid-name",
        "purpose",
        "different-secret",
        "key",
        "corr",
    )
    assert conflict.error.code is SecretErrorCode.IDEMPOTENCY_CONFLICT
    assert CANARY not in repr(created.value)


def test_cipher_loads_operator_key_file_and_rejects_unknown_key(tmp_path: Path) -> None:
    key_file = tmp_path / "key-ring.json"
    key_file.write_text(
        json.dumps(
            {
                "keys": {
                    "operator-v1": base64.urlsafe_b64encode(bytes(range(32))).decode(),
                    "operator-v2": base64.urlsafe_b64encode(bytes(reversed(range(32)))).decode(),
                }
            }
        ),
        encoding="utf-8",
    )
    previous = AesGcmSecretCipher.from_key_ring_file("operator-v1", str(key_file))
    previous_envelope = previous.encrypt(b"protected", b"scope")
    rotated = AesGcmSecretCipher.from_key_ring_file("operator-v2", str(key_file))
    assert rotated.decrypt(previous_envelope, b"scope") == b"protected"
    assert rotated.encrypt(b"new", b"scope").key_id == "operator-v2"
    unavailable = replace(previous_envelope, key_id="retired-key")
    try:
        rotated.decrypt(unavailable, b"scope")
    except ValueError as error:
        assert str(error) == "Secret reference is unavailable."
    else:
        raise AssertionError("Unknown key identifiers must fail closed.")
