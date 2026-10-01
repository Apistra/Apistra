"""Security and time adapters used by the identity application service."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type

ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST_KIB = 65_536
ARGON2_PARALLELISM = 4
ARGON2_HASH_LENGTH = 32
ARGON2_SALT_LENGTH = 16
TOKEN_ENTROPY_BYTES = 32


class Argon2PasswordHasher:
    """Pinned Argon2id policy; parameters are explicit and centrally reviewable."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST_KIB,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LENGTH,
            salt_len=ARGON2_SALT_LENGTH,
            type=Type.ID,
        )

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (InvalidHashError, VerificationError):
            return False


class SecureTokenService:
    def issue(self) -> tuple[str, str]:
        raw_token = secrets.token_urlsafe(TOKEN_ENTROPY_BYTES)
        return raw_token, self.digest(raw_token)

    def digest(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class UtcClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
