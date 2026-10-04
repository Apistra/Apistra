"""AES-256-GCM envelope adapter with explicit key identifiers."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from apistra.modules.catalog.domain import EncryptedSecretEnvelope

NONCE_BYTES = 12
MASTER_KEY_BYTES = 32
ENVELOPE_FORMAT_VERSION = 1


class AesGcmSecretCipher:
    def __init__(self, active_key_id: str, keys: dict[str, bytes]) -> None:
        if active_key_id not in keys or any(len(key) != MASTER_KEY_BYTES for key in keys.values()):
            raise ValueError("The active AES-256-GCM key ring is invalid.")
        self._active_key_id = active_key_id
        self._keys = dict(keys)

    @classmethod
    def from_key_ring_file(cls, active_key_id: str, path: str) -> AesGcmSecretCipher:
        try:
            document: Any = json.loads(Path(path).read_text(encoding="utf-8"))
            encoded_keys = document["keys"]
            if not isinstance(encoded_keys, dict) or not encoded_keys:
                raise ValueError
            keys = {
                str(key_id): base64.urlsafe_b64decode(str(encoded))
                for key_id, encoded in encoded_keys.items()
            }
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("The secret key-ring file is invalid.") from error
        return cls(active_key_id, keys)

    def encrypt(self, plaintext: bytes, associated_data: bytes) -> EncryptedSecretEnvelope:
        nonce = os.urandom(NONCE_BYTES)
        ciphertext = AESGCM(self._keys[self._active_key_id]).encrypt(
            nonce, plaintext, associated_data
        )
        return EncryptedSecretEnvelope(
            format_version=ENVELOPE_FORMAT_VERSION,
            key_id=self._active_key_id,
            nonce=nonce,
            ciphertext=ciphertext,
        )

    def decrypt(self, envelope: EncryptedSecretEnvelope, associated_data: bytes) -> bytes:
        key = self._keys.get(envelope.key_id)
        if envelope.format_version != ENVELOPE_FORMAT_VERSION or key is None:
            raise ValueError("Secret reference is unavailable.")
        try:
            return AESGCM(key).decrypt(envelope.nonce, envelope.ciphertext, associated_data)
        except InvalidTag as error:
            raise ValueError("Secret reference is unavailable.") from error
