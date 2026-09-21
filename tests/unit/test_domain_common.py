"""Unit tests for initial shared domain primitives."""

import pytest

from pydbadminkit.domain.common import (
    CapabilityAvailability,
    CapabilityStatus,
    DatabaseEngine,
    DatabaseObjectRef,
    DatabaseObjectType,
    DatabaseVersion,
    EnvironmentName,
    OperationResult,
    OperationStatus,
    QualifiedName,
    RiskLevel,
    parse_qualified_name,
)

pytestmark = pytest.mark.unit


def test_database_engine_postgresql_value() -> None:
    assert DatabaseEngine.POSTGRESQL.value == "postgresql"


def test_database_version_is_orderable_and_formats_compactly() -> None:
    assert DatabaseVersion(18) > DatabaseVersion(17, 9)
    assert str(DatabaseVersion(18)) == "18"
    assert str(DatabaseVersion(17, 4)) == "17.4"
    assert str(DatabaseVersion(16, 3, 2)) == "16.3.2"


def test_database_version_rejects_negative_component() -> None:
    with pytest.raises(ValueError):
        DatabaseVersion(18, -1)


def test_unknown_environment_is_not_development() -> None:
    assert EnvironmentName.UNKNOWN != EnvironmentName.DEVELOPMENT


def test_qualified_name_formats_supported_shapes() -> None:
    assert str(QualifiedName(name="customers")) == "customers"
    assert str(QualifiedName(schema="public", name="customers")) == "public.customers"
    assert (
        str(QualifiedName(database="analytics", schema="public", name="customers"))
        == "analytics.public.customers"
    )


def test_qualified_name_rejects_blank_components() -> None:
    with pytest.raises(ValueError):
        QualifiedName(name=" ")

    with pytest.raises(ValueError):
        QualifiedName(name="customers", schema=" ")


def test_parse_qualified_name() -> None:
    assert parse_qualified_name("customers") == QualifiedName(name="customers")
    assert parse_qualified_name("public.customers") == QualifiedName(
        schema="public",
        name="customers",
    )
    assert parse_qualified_name("analytics.public.customers") == QualifiedName(
        database="analytics",
        schema="public",
        name="customers",
    )

    with pytest.raises(ValueError):
        parse_qualified_name("a.b.c.d")


def test_database_object_ref_is_typed() -> None:
    ref = DatabaseObjectRef(
        object_type=DatabaseObjectType.TABLE,
        name=QualifiedName(schema="public", name="customers"),
    )
    assert ref.object_type is DatabaseObjectType.TABLE


def test_risk_levels_are_ordered() -> None:
    assert RiskLevel.CRITICAL > RiskLevel.HIGH > RiskLevel.MEDIUM > RiskLevel.LOW
    assert RiskLevel.CRITICAL.label == "critical"


def test_operation_result_rejects_blank_operation() -> None:
    with pytest.raises(ValueError):
        OperationResult(operation=" ", status=OperationStatus.SUCCEEDED)


def test_capability_available_property() -> None:
    status = CapabilityStatus(
        name="catalog.database.list",
        availability=CapabilityAvailability.AVAILABLE,
    )
    assert status.available is True
