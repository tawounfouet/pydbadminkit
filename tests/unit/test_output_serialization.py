"""Unit tests for JSON/YAML machine serialization."""

import json

import pytest
import yaml

from pydbadminkit.domain.catalog import (
    ColumnInfo,
    TableDescription,
    TableInfo,
)
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.output.serialization import (
    render_json,
    render_yaml,
    to_machine_value,
)

pytestmark = pytest.mark.unit


def _table_description() -> TableDescription:
    return TableDescription(
        table=TableInfo(
            name=QualifiedName(schema="public", name="customers"),
            owner="postgres",
            estimated_rows=42,
            size_bytes=8192,
        ),
        columns=(
            ColumnInfo(
                name="id",
                position=1,
                data_type="bigint",
                nullable=False,
            ),
        ),
    )


def test_machine_value_preserves_nested_public_structure() -> None:
    value = to_machine_value(_table_description())

    assert isinstance(value, dict)
    assert value["table"]["name"] == {
        "name": "customers",
        "schema": "public",
        "database": None,
    }
    assert value["columns"][0]["data_type"] == "bigint"


def test_json_output_is_parseable_and_stable() -> None:
    parsed = json.loads(render_json(_table_description()))

    assert parsed["table"]["kind"] == "table"
    assert parsed["table"]["estimated_rows"] == 42
    assert parsed["columns"][0]["nullable"] is False


def test_yaml_output_is_safe_and_parseable() -> None:
    parsed = yaml.safe_load(render_yaml(_table_description()))

    assert parsed["table"]["name"]["schema"] == "public"
    assert parsed["columns"][0]["name"] == "id"


def test_tuple_serializes_as_machine_array() -> None:
    parsed = json.loads(
        render_json(
            (
                TableInfo(name=QualifiedName(schema="public", name="a")),
                TableInfo(name=QualifiedName(schema="public", name="b")),
            )
        )
    )

    assert [item["name"]["name"] for item in parsed] == ["a", "b"]


def test_unsupported_machine_type_fails_explicitly() -> None:
    with pytest.raises(TypeError):
        to_machine_value(object())
