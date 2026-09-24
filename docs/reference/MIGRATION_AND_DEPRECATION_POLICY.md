# PyDBAdminKit Migration and Deprecation Policy

## Scope

This policy applies to stable public contracts starting with the 1.0 line.

Stable contracts include:

```text
public Python exports and signatures
bootstrap convenience API
public ports
CLI command tree and root options
JSON machine shapes
error codes
exit codes
configuration keys/semantics
capability names
operation/audit names
documented support matrix
```

Implementation-only adapters/infrastructure are not covered unless separately documented as
public.

## Versioning model

PyDBAdminKit follows SemVer concepts with PEP 440 prerelease syntax.

```text
patch   bug/security/compatibility correction
minor   backward-compatible capability
major   breaking public contract
```

Examples of prereleases:

```text
1.0.0rc1
1.0.0rc2
```

## Stable deprecation lifecycle

The normal lifecycle is:

```text
stable
  ↓
deprecated
  ↓ at least one minor release
removed in an appropriate breaking release
```

The minimum post-1.0 deprecation window is **at least one minor release** before removal,
except for an urgent security/safety issue.

A typical longer sequence is:

```text
1.2  deprecation introduced
1.3  warning remains
2.0  removal
```

## Python API deprecation

A deprecated Python symbol should:

1. remain importable during the deprecation window where safely possible;
2. emit an appropriate deprecation warning;
3. document its replacement;
4. include before/after migration examples when non-trivial;
5. be removed only according to the versioning policy.

A port signature or bootstrap-builder change is treated as public API change.

## CLI deprecation

A deprecated command/option remains functional during the deprecation window where safely
possible and writes its warning to stderr.

Example:

```text
Warning: 'query running' is deprecated.
Use 'query list' instead.
```

Machine stdout must not be polluted by deprecation text.

## Machine-interface deprecation

JSON stdout remains parseable and contract-clean.

Warnings belong on stderr unless a future structured metadata contract explicitly defines
another channel.

Removing/renaming fields, changing types/wire enum values, changing nullability semantics,
changing list/object shape, error-code semantics or exit behavior is a compatibility event.

## Capability and operation names

Documented capability names are stable contracts after 1.0.

Operation names used by audit processors/SIEM integrations are also stable. Renaming one
can break downstream automation even when the underlying database action is unchanged.

Such renames therefore require the same migration discipline as other public machine
contracts.

## Configuration migration

A configuration key removal/rename or semantic change must document:

```text
old key/value
new key/value
behavior difference
release introduced
release removed
```

Silent reinterpretation of an existing configuration key is not an acceptable migration.

## Support deprecation

Dropping a Python or PostgreSQL version requires:

```text
documentation
changelog / release-note announcement
explicit CI matrix removal
support-matrix update
```

PostgreSQL Transitional status is the mechanism for a temporary support window with a
reduced future guarantee.

## Security and safety exception

A dangerous API or behavior may be disabled or removed faster than the normal deprecation
window when continuing it would create a serious security or data-safety risk.

The release notes must explain:

```text
the risk
the urgent change
the affected versions/contracts
the replacement or mitigation
```

Safety takes precedence over preserving a dangerous behavior.

## Breaking-release migration guide

A breaking major release must provide a migration guide such as:

```text
MIGRATION_2.md
```

or an equivalent dedicated documentation section.

The guide must cover, where relevant:

```text
removed API
replacement API
before example
after example
configuration changes
CLI changes
machine-schema changes
support-matrix changes
```

## Experimental features

Features explicitly marked `experimental` do not carry the full stable-contract guarantee
and may evolve without a major release.

Experimental status must be visible in the namespace, capability metadata or documentation;
it cannot be inferred only from implementation maturity.

## Release candidates

Before `1.0.0rc1` the public Python surface, CLI tree, error codes and core JSON contracts
are frozen except for release blockers.

During RC:

```text
bug fixes only
documentation
qualification
```

A code correction after RC1 qualification produces RC2 rather than silently mutating the
qualified RC artifact.

Stable promotion contains no new functionality relative to the final qualified RC.

## Immutable releases and rollback

Published package versions and Git tags are immutable.

A defective stable release is corrected by a new version, for example:

```text
1.2.0 → 1.2.1
```

A severely broken/security-sensitive package may be yanked where supported, but release
history remains documented and tags are not moved.

## Contract review checklist

Every stable release reviews:

```text
public API
CLI
JSON/machine contracts
error codes
exit codes
configuration
capability names
operation names
support matrix
```
