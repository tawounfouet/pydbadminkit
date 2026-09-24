# LOT-20 / T20-006 — Configuration Contract Freeze

## Status

```text
Ticket: T20-006
Lot: LOT-20 — Hardening
Baseline: 0.6.0
Contract: frozen for the route to 1.0
```

This contract freezes the **implemented 0.6 configuration surface**. Earlier architecture
documents describe a broader target model (application defaults, environment overrides,
guardrails, health settings and nested SSL/timeouts). Those remain design direction unless
implemented explicitly; T20-006 does not pretend that planned configuration already exists.

## Configuration source

The implemented persistent format is TOML.

An explicit CLI path is supplied through:

```text
--config /path/to/config.toml
```

When no explicit path is supplied, PyDBAdminKit uses the platform-specific user config
directory returned by `platformdirs.user_config_path("pydbadminkit")`, followed by:

```text
config.toml
```

The architecture document mentions `PYDBADMIN_CONFIG`, but the 0.6 runtime does not
currently resolve that variable. It is therefore **not** part of the frozen 0.6 contract.

## Top-level structure

The implemented loader consumes connection profiles below:

```toml
[connections.<profile-name>]
```

Multiple profiles are supported and `list_connection_profiles()` returns them in
deterministic profile-name order.

## Connection profile fields

| Field | Type | Required | Default |
| --- | --- | --- | --- |
| `engine` | string | no | `postgresql` |
| `host` | string | yes | — |
| `port` | integer | no | `5432` |
| `database` | string | yes | — |
| `username` | string | yes | — |
| `environment` | string enum | no | `unknown` |
| `read_only` | boolean | no | `false` |
| `ssl_mode` | string enum | no | `prefer` |
| `ssl_root_cert` | string | no | `null` |
| `ssl_cert` | string | no | `null` |
| `ssl_key` | string | no | `null` |
| `connect_timeout_seconds` | integer | no | `10` |
| `statement_timeout_ms` | integer | no | `null` |
| `lock_timeout_ms` | integer | no | `null` |

The implemented 0.6 syntax keeps SSL and timeout fields on the profile table. The nested
`[connections.<name>.ssl]` and `[connections.<name>.timeouts]` forms shown in earlier
design examples are not the current loader contract.

## Secret reference

A profile may contain:

```toml
[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
```

Both `provider` and `reference` are required non-blank strings when the secret table is
present.

A persisted `ConnectionProfile` stores the reference, never the resolved raw secret.
The current bootstrap registers the environment secret provider.

## Enumerated values

### engine

The current implementation accepts the values supported by `DatabaseEngine`; the 0.6
PostgreSQL line uses:

```text
postgresql
```

### environment

```text
development
testing
staging
production
unknown
```

### ssl_mode

```text
disable
allow
prefer
require
verify-ca
verify-full
```

## Validation contract

The loader rejects, through `ConfigurationError`, malformed TOML and invalid profile
values including:

- non-table `connections` or profile values;
- missing/blank `host`, `database` or `username`;
- invalid engine, environment or SSL mode;
- non-integer `port` or timeout fields;
- non-boolean `read_only`;
- invalid domain values such as an out-of-range port or non-positive timeout;
- malformed secret references.

A missing requested profile raises `ProfileNotFoundError`.

## Resolution boundary

The implemented resolution path is:

```text
TOML profile
    ↓
ConnectionProfile
    ↓
SecretProviderPort
    ↓
ResolvedConnectionConfig
```

The persisted profile contains no raw password. The resolved runtime object may contain a
`SecretValue`, whose string and repr forms remain redacted.

The broader precedence model documented in the architecture
(explicit CLI/Python > PYDBADMIN_* > profile > defaults) is not yet implemented as a
general override engine and is therefore not frozen here.

## Compatibility rules

Before a future major-version compatibility break:

- existing profile field names must not be removed or silently repurposed;
- existing enum wire values must remain stable;
- existing defaults must not change silently;
- secret material must not be added to persisted profiles;
- required fields must not become optional through implicit driver magic;
- new fields may be added only with deterministic defaults and validation;
- a future nested configuration syntax must be introduced deliberately, not by changing
  the meaning of the current flat fields.

## Automated drift guard

`tests/unit/test_config_contract.py` freezes:

- the default profile values;
- the complete implemented profile field mapping;
- secret-reference shape;
- environment and SSL wire values;
- deterministic profile ordering;
- the default config filename/location convention.

## Next ticket

```text
T20-007 — capability-name freeze
```
