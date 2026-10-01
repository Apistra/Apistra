"""Composition root for the isolated CAP-01 fixture process."""

from apistra.modules.identity.adapters.security import Argon2PasswordHasher
from apistra.modules.identity.ports import PasswordHasher


def build_fixture_password_hasher() -> PasswordHasher:
    """Reuse the product password policy without exposing its adapter to the entrypoint."""

    return Argon2PasswordHasher()
