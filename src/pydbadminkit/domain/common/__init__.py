"""Shared domain primitives."""

from pydbadminkit.domain.common.capabilities import CapabilityAvailability, CapabilityStatus
from pydbadminkit.domain.common.database_version import DatabaseVersion
from pydbadminkit.domain.common.engine import DatabaseEngine
from pydbadminkit.domain.common.environment import EnvironmentName
from pydbadminkit.domain.common.names import QualifiedName, parse_qualified_name
from pydbadminkit.domain.common.objects import DatabaseObjectRef, DatabaseObjectType
from pydbadminkit.domain.common.operations import OperationResult, OperationStatus, RiskLevel

__all__ = [
    "CapabilityAvailability",
    "CapabilityStatus",
    "DatabaseEngine",
    "DatabaseObjectRef",
    "DatabaseObjectType",
    "DatabaseVersion",
    "EnvironmentName",
    "OperationResult",
    "OperationStatus",
    "QualifiedName",
    "RiskLevel",
    "parse_qualified_name",
]
