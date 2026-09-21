"""Machine-readable serialization outside the domain layer."""

import json
from dataclasses import fields, is_dataclass
from enum import Enum

import yaml


MachineValue = None | bool | int | float | str | list["MachineValue"] | dict[str, "MachineValue"]


def to_machine_value(value: object) -> MachineValue:
    """Convert supported public models to JSON/YAML-safe primitives."""

    if isinstance(value, Enum):
        enum_value = value.value
        if isinstance(enum_value, (bool, int, float, str)):
            return enum_value
        raise TypeError(f"Unsupported enum value type: {type(enum_value).__name__}")

    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_machine_value(getattr(value, field.name)) for field in fields(value)}

    if isinstance(value, (tuple, list)):
        return [to_machine_value(item) for item in value]

    if isinstance(value, dict):
        result: dict[str, MachineValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Machine-output mappings require string keys")
            result[key] = to_machine_value(item)
        return result

    raise TypeError(f"Unsupported machine-output type: {type(value).__name__}")


def render_json(value: object) -> str:
    """Render deterministic pretty JSON."""

    return json.dumps(
        to_machine_value(value),
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    )


def render_yaml(value: object) -> str:
    """Render safe deterministic YAML."""

    return yaml.safe_dump(
        to_machine_value(value),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).rstrip()
