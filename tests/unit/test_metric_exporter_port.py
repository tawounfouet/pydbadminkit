"""Public protocol tests for metric exporters."""

import pytest

from pydbadminkit.ports import MetricExporterPort

pytestmark = pytest.mark.unit


def test_metric_exporter_port_is_public() -> None:
    assert MetricExporterPort.__name__ == "MetricExporterPort"
