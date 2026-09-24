# LOT-21 / T21-006 — Machine Interface Qualification

## Decision

```text
Ticket: T21-006
Result: PASS
Formats: JSON and YAML
Primary frozen contract: JSON
```

## Machine-output architecture

PyDBAdminKit serializes public immutable domain/application models through one machine
serialization boundary.

The stable conversion rules are:

```text
None                 → null
bool/int/float/str   → same primitive
datetime/date        → ISO-8601 string
StrEnum              → enum value
RiskLevel            → lowercase label
SecretValue          → "<redacted>"
dataclass            → object in declaration order
tuple/list           → array
Mapping[str, ...]    → object
```

Unsupported values and mappings with non-string keys fail instead of being silently
stringified.

## Frozen JSON behavior

The qualification freezes:

- UTF-8 / unescaped Unicode;
- two-space indentation;
- deterministic declaration order;
- explicit `null` rather than omission for nullable dataclass fields;
- list commands as arrays;
- empty lists as `[]`;
- stable enum wire values;
- lowercase risk labels;
- explicit secret redaction.

Representative DTO shapes are guarded by
`tests/unit/test_json_contract_inventory.py`.

The health-report machine shape is independently frozen by the monitoring release-contract
tests.

## CLI machine purity

CLI regression tests verify that JSON/YAML modes emit machine payloads without the
human-readable labels used by table/text renderers.

Live PostgreSQL integration tests additionally parse JSON from catalog, security, runtime,
health and other implemented CLI surfaces. A human-output prefix or malformed payload would
therefore fail those tests.

## Error and exit semantics

Machine consumers also depend on stable process semantics. LOT-20 separately froze:

```text
error codes
exit codes
CLI command/options
operation names
capability names
```

T21-006 treats those contracts together with JSON serialization as the machine interface
boundary for 1.0.

## Compatibility rule

For the 1.0 line, the following require compatibility review:

- field removal or rename;
- field type change;
- enum wire-value change;
- `null` ↔ omission changes;
- list ↔ object shape changes;
- date/time encoding changes;
- error/exit semantic changes;
- adding credential material;
- even additive fields where strict downstream consumers may reject unknown keys.

## Documentation correction

The original T20-003 inventory predated T20-012 and stated that serializer-level redaction
was absent. T21-006 synchronizes that inventory with the implemented `SecretValue →
<redacted>` behavior.

## Release gate

The 1.0 conditions:

```text
JSON contracts frozen
error codes frozen
exit codes frozen
CLI frozen
```

are satisfied by the current contract inventories and executable drift guards.

## Next ticket

```text
T21-007 — installation smoke tests
```
