"""Basic package smoke tests."""

import pytest

import pydbadminkit

pytestmark = pytest.mark.unit


def test_package_exposes_version() -> None:
    assert pydbadminkit.__version__ == "0.5.0b1"
