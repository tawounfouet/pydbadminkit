"""Secret redaction helpers for external diagnostic text."""

from pydbadminkit.domain.connection import SecretValue


def redact_secret(value: str, secret: SecretValue | None) -> str:
    """Replace the exact resolved secret in diagnostic text."""

    if secret is None:
        return value
    raw = secret.reveal()
    if not raw:
        return value
    return value.replace(raw, "<redacted>")
