# LOT-19 — OpenTelemetry Design Spike

## Status

Design-only foundation for `0.6.x`. LOT-19 adds no OpenTelemetry SDK dependency.

## Boundary

```text
Metric
  ↓
MetricExporterPort
  ↓
future OpenTelemetry adapter
  ↓
OTel Meter / Collector
```

The Core owns metric meaning. The adapter owns OpenTelemetry instruments and transport.

## Metrics

`MetricDescriptor` provides the minimum metadata needed for a future mapping:

```text
name
unit
metric_type
description
label_names
```

`GAUGE` maps naturally to point-in-time observations. `COUNTER` requires explicit
cumulative semantics and reset handling. `STATE` should not be coerced into a numeric
counter without an adapter-level mapping decision.

## Resource attributes

Stable deployment context such as profile/environment may become OpenTelemetry resource
attributes instead of metric labels. That decision belongs to the adapter so the Domain
remains vendor-neutral.

## Tracing

Future internal tracing may follow:

```text
CLI command
→ application service
→ adapter
→ database call
```

Tracing is deliberately outside the LOT-19 implementation. The framework does not create a
global tracer provider or mutate an application's OpenTelemetry configuration.

## Internal self-observability naming

PyDBAdminKit-owned metrics reserve the dotted `pydbadmin.` namespace, for example:

```text
pydbadmin.operation.duration_ms
pydbadmin.adapter.calls
pydbadmin.rows.fetched
pydbadmin.errors
```

Database observations continue to use neutral names such as `connections.total`.

## Follow-up adapter

A post-1.0 OpenTelemetry adapter can implement `MetricExporterPort` and own:

- SDK/API dependency selection;
- MeterProvider integration;
- instrument lifecycle;
- resource attributes;
- metric export transport;
- optional tracing/log integration.
