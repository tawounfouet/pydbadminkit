"""Unit tests for connection value objects."""

import pytest

from pydbadminkit.domain.connection import ConnectionProfileName, SecretReference

pytestmark = pytest.mark.unit


def test_connection_profile_name() -> None:
    assert str(ConnectionProfileName("local")) == "local"

    with pytest.raises(ValueError):
        ConnectionProfileName(" ")


def test_secret_reference_contains_reference_not_secret_value() -> None:
    reference = SecretReference(
        provider="env",
        reference="PYDBADMIN_LOCAL_PASSWORD",
    )
    assert reference.provider == "env"
    assert reference.reference == "PYDBADMIN_LOCAL_PASSWORD"

    with pytest.raises(ValueError):
        SecretReference(provider="", reference="PASSWORD")
