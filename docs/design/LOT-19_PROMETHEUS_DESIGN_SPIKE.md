# LOT-19 — Prometheus Design Spike

## Status

Design-only foundation for `0.6.x`. No permanent HTTP daemon and no Prometheus runtime
dependency are introduced in LOT-19.

## Boundary

The Core exposes:

```text
MonitoringService
      ↓
tuple[Metric, ...]
      ↓
MetricCardinalityPolicy
      ↓
MetricExporterPort
      ↓
future Prometheus adapter
```

The exporter remains an adapter. The Domain does not import Prometheus libraries.

## Naming

Engine-neutral names remain dotted:

```text
connections.total
connections.active
connections.utilization_ratio
database.size_bytes
```

A future Prometheus adapter maps them deterministically:

```text
pydbadmin_connections_total
pydbadmin_connections_active
pydbadmin_connections_utilization_ratio
pydbadmin_database_size_bytes
```

The `pydbadmin_` prefix belongs to the Prometheus mapping, not to database metric names.

## Metric types

`MetricDescriptor.metric_type` distinguishes:

```text
GAUGE
COUNTER
STATE
```

Current LOT-17 metrics are gauges. Future cumulative PostgreSQL counters must be explicitly
described as counters and exporters must tolerate PostgreSQL statistics resets.

## Cardinality

The default exporter policy allows only:

```text
profile
environment
database
status
```

It rejects high-cardinality or sensitive labels such as:

```text
pid
query
query_text
client_address
client_ip
```

Table/index labels may be supported by an explicitly relaxed exporter policy later; they are
not silently enabled in the default external surface.

## Delivery options considered

```text
text exposition
HTTP endpoint
Pushgateway integration
```

LOT-19 chooses none of them. A CLI process must not become a permanent metrics server merely
to satisfy observability integration.

## Follow-up adapter

A post-1.0 Prometheus adapter can implement `MetricExporterPort` and own:

- Prometheus client dependency;
- descriptor-to-collector mapping;
- text exposition or transport;
- counter reset semantics;
- adapter-specific integration tests.
