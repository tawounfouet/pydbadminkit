"""PostgreSQL version parsing."""

from dataclasses import dataclass

from pydbadminkit.domain.common.database_version import DatabaseVersion


@dataclass(frozen=True, slots=True)
class PostgreSQLVersionInfo:
    """PostgreSQL raw and public version representation."""

    raw_num: int
    version: DatabaseVersion


def parse_server_version_num(raw_num: int) -> PostgreSQLVersionInfo:
    """Parse PostgreSQL 10+ server_version_num encoding."""

    if raw_num < 100000:
        raise ValueError("PostgreSQL versions older than 10 are not supported")

    major = raw_num // 10000
    minor = raw_num % 10000
    return PostgreSQLVersionInfo(
        raw_num=raw_num,
        version=DatabaseVersion(major=major, minor=minor),
    )
