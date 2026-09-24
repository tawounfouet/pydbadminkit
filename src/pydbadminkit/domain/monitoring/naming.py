"""Stable metric naming rules."""

import re

_METRIC_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")

INTERNAL_METRIC_PREFIX = "pydbadmin."
PROMETHEUS_METRIC_PREFIX = "pydbadmin_"


def validate_metric_name(name: str) -> None:
    """Validate the engine-neutral dotted metric namespace."""

    if not _METRIC_NAME_PATTERN.fullmatch(name):
        raise ValueError(
            "metric name must use lowercase dotted segments (for example 'connections.total')"
        )


def internal_metric_name(name: str) -> str:
    """Return a reserved name for PyDBAdminKit self-observability."""

    candidate = f"{INTERNAL_METRIC_PREFIX}{name}"
    validate_metric_name(candidate)
    return candidate


def prometheus_metric_name(name: str) -> str:
    """Map an internal dotted metric name to the future Prometheus namespace."""

    validate_metric_name(name)
    return f"{PROMETHEUS_METRIC_PREFIX}{name.replace('.', '_')}"
