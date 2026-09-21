"""Unit tests for PostgreSQL version parsing."""

import pytest

from pydbadminkit.adapters.postgresql.version import parse_server_version_num
from pydbadminkit.domain.common import DatabaseVersion

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw_num", "expected"),
    [
        (180001, DatabaseVersion(18, 1)),
        (170004, DatabaseVersion(17, 4)),
        (140012, DatabaseVersion(14, 12)),
    ],
)
def test_parse_server_version_num(raw_num: int, expected: DatabaseVersion) -> None:
    result = parse_server_version_num(raw_num)
    assert result.raw_num == raw_num
    assert result.version == expected


def test_parse_server_version_rejects_pre_10_encoding() -> None:
    with pytest.raises(ValueError):
        parse_server_version_num(90624)
