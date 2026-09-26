# PyDBAdminKit 1.0 — Security Administration

## Objective

Understand PyDBAdminKit's security-administration model before performing role, membership and
privilege changes.

This guide introduces the complete security surface and the safety model around it.

Detailed workflows are split across:

- [Roles, Memberships and Privileges](12_ROLES_MEMBERSHIPS_AND_PRIVILEGES.md)
- [Effective Access and Ownership](13_EFFECTIVE_ACCESS_AND_OWNERSHIP.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)

## Prerequisites

Before performing security administration, understand:

- connection profiles;
- environment classification;
- credentials;
- CLI root options;
- Python API fundamentals;
- dry-run versus execution.

Always verify the target first:

```bash
pydbadmin -c prod server info
pydbadmin -c prod role list
```

## Security architecture

PyDBAdminKit deliberately separates security inspection from mutation.

```text
SecurityService
    → read-only inspection

SecurityMutationService
    → plan
    → guard
    → confirm
    → audit
    → execute
```

This separation is a core safety boundary.

## Security CLI groups

PyDBAdminKit 1.0 exposes four security-oriented groups:

```text
role
access
effective-access
ownership
```

Their responsibilities are:

| Group | Purpose |
| --- | --- |
| `role` | inspect and administer roles and memberships |
| `access` | inspect and administer explicit relation privileges |
| `effective-access` | inspect effective privileges and their sources |
| `ownership` | inspect database objects owned by a role |

## Inspection commands

The read-only security commands are:

```text
role list
role describe <name>

access list --role <role>

effective-access list --role <role>

ownership list --owner <role>
```

These commands do not enter the mutation planning/confirmation pipeline.

## Mutation commands

The guarded mutation surface is:

```text
role create
role alter
role drop
role membership-add
role membership-remove

access grant
access revoke
```

Every one of these commands is executed through `SecurityMutationService`.

## SecurityService

The public read-only service is built with:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_security_service

security = build_security_service(
    "prod",
    Path("config.toml"),
)
```

It exposes:

```text
list_roles
describe_role
list_role_memberships
list_direct_access
list_effective_access
list_ownership
```

## SecurityMutationService

Build guarded mutation orchestration with:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_security_mutation_service

security_mutation = build_security_mutation_service(
    "staging",
    Path("config.toml"),
)
```

The service exposes plan and execution methods for role, membership and relation-access changes.

## Plan before execution

The mutation model is:

```text
typed command
    ↓
plan_*()
    ↓
OperationPlan
    ↓
policy + approval
    ↓
execute
    ↓
OperationResult
```

For example:

```text
CreateRoleCommand
    ↓
plan_create_role(...)
    ↓
OperationPlan
    ↓
create_role(...)
```

CLI `--dry-run` exposes the plan instead of applying the mutation.

## OperationPlan

Every planned security mutation includes:

```text
operation
target
environment
risk
confirmation
effects
warnings
correlation_id
```

Example conceptual plan:

```text
Operation: security.role.create
Target: reporting_user
Environment: staging
Risk: medium
Confirmation: simple
Effects:
- Create role 'reporting_user'.
```

The exact risk and confirmation level depend on the requested change and environment.

## Risk levels

PyDBAdminKit uses:

```text
low
medium
high
critical
```

Security mutations are not all treated equally.

Examples from the implemented 1.0 rules:

```text
normal role create
    → medium

role create with CREATEDB / CREATEROLE / REPLICATION
    → high

role create with SUPERUSER or BYPASSRLS
    → critical
```

Role alteration follows similar privilege-sensitive escalation.

## Production risk escalation

When the selected profile is classified as:

```text
production
```

the security mutation service escalates risk:

```text
medium   → high
high     → critical
critical → critical
```

Low-risk behavior remains low where applicable.

This means the same logical operation may require stronger confirmation in production.

## Confirmation levels

Risk maps to confirmation as follows:

| Risk | Confirmation |
| --- | --- |
| low | none |
| medium | simple |
| high | explicit |
| critical | exact target typing |

The domain values are:

```text
none
simple
explicit
type_target
```

## Typed-target confirmation

Critical operations require exact target proof.

For example, the plan may require:

```text
reporting_user
```

or a composite target such as:

```text
member->role
```

or:

```text
principal:schema.object:SELECT
```

The supplied `--confirm-target` value must match the generated plan target exactly.

## --yes is not universal

```text
--yes
```

can approve simple/explicit confirmations where allowed.

It does not bypass:

```text
type_target
```

confirmation.

Critical operations still require exact target proof.

## Dry-run

Always prefer a dry-run before an unfamiliar mutation:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role create reporting_user \
  --login
```

The result is an `OperationPlan`.

No security mutation is executed.

## Read-only profile guardrail

If the selected profile has:

```toml
read_only = true
```

security mutation execution is blocked.

The service raises:

```text
PolicyDeniedError
```

with semantics:

```text
Mutation blocked by read-only connection profile.
```

This guardrail applies at the application service layer, not only in the CLI.

## Unknown environment guardrail

A mutation is also blocked when the resolved connection environment is:

```text
unknown
```

The service requires an explicit environment classification before mutation execution.

This prevents potentially destructive administration against an unclassified target.

## Protected PostgreSQL role namespace

Security mutations protect PostgreSQL built-in role names beginning with:

```text
pg_
```

Examples include built-in administrative roles provided by PostgreSQL.

Dropping or mutating protected built-in role targets can be denied by policy.

Do not treat `pg_*` roles as ordinary application roles.

## Current connection role protection

Dropping the current connection role is blocked.

This prevents a destructive operation against the principal currently being used to administer the database.

## Audit lifecycle

Executed security mutations are audited.

Lifecycle events include:

```text
BLOCKED
STARTED
FAILED
SUCCEEDED
```

Audit entries include operational context such as:

```text
actor
profile
environment
database
operation
target
risk
status
correlation_id
message
```

Audit details are covered in guide 25.

## Role inspection

List roles:

```bash
pydbadmin -c prod role list
```

Show login-capable roles only:

```bash
pydbadmin -c prod role list --login-only
```

Include PostgreSQL built-in roles:

```bash
pydbadmin -c prod role list --include-system
```

Describe one role:

```bash
pydbadmin -c prod role describe app_user
```

## RoleInfo

Role summaries expose:

```text
name
can_login
is_superuser
can_create_db
can_create_role
can_replicate
inherit
connection_limit
valid_until
bypass_rls
is_system
```

These values represent PostgreSQL role attributes through a stable cross-engine model.

## RoleDescription

A detailed role description contains:

```text
role
member_of
members
```

This gives both directions of membership:

```text
member_of
    → roles inherited by this role

members
    → principals belonging to this role
```

## Membership model

A role membership is represented by:

```text
RoleMembership
```

with:

```text
role
member
grantor
admin_option
```

The edge semantics are:

```text
member belongs to role
```

## Direct access inspection

Inspect explicit relation privileges:

```bash
pydbadmin -c prod access list --role app_user
```

Filter:

```bash
pydbadmin \
  -c prod \
  access list \
  --role app_user \
  --schema public \
  --object orders
```

## DirectAccess

An explicit access entry contains:

```text
principal
access_type
object
issuer
delegable
```

The supported relation access vocabulary is:

```text
SELECT
INSERT
UPDATE
DELETE
TRUNCATE
REFERENCES
TRIGGER
```

## AccessType

The public enum is:

```text
AccessType
```

Its wire values remain uppercase PostgreSQL-style privilege names.

Example Python:

```python
from pydbadminkit.domain.security import AccessType

print(AccessType.SELECT.value)
```

Output:

```text
SELECT
```

## Effective access

Direct privileges are not the same as effective privileges.

Use:

```bash
pydbadmin -c prod effective-access list --role app_user
```

The effective-access model attributes each resulting privilege to one or more sources.

## AccessSource

Implemented sources are:

```text
direct
inherited
public
owner
superuser
```

This lets the operator distinguish:

```text
"the role has SELECT"
```

from:

```text
"why the role has SELECT"
```

That distinction is central to PostgreSQL authorization analysis.

## EffectiveAccess

An effective access entry contains:

```text
principal
access_type
object
sources
```

and requires at least one source.

Detailed interpretation is covered in guide 13.

## Ownership inspection

Use:

```bash
pydbadmin -c prod ownership list --owner app_owner
```

Filter by schema:

```bash
pydbadmin \
  -c prod \
  ownership list \
  --owner app_owner \
  --schema public
```

Filter by object type:

```bash
pydbadmin \
  -c prod \
  ownership list \
  --owner app_owner \
  --type table
```

## OwnershipInfo

Ownership is represented by:

```text
owner
object
```

where `object` is a typed `DatabaseObjectRef`.

Ownership matters because owners can receive effective access independently of explicit grants.

## DatabaseObjectType

The cross-engine object-type vocabulary currently includes:

```text
server
database
schema
table
view
index
```

The ownership command can filter by one of these types where supported by the implementation.

## Security mutation commands

The role mutation surface is:

```text
role create
role alter
role drop
role membership-add
role membership-remove
```

The direct-access mutation surface is:

```text
access grant
access revoke
```

These commands are covered in depth in guide 12.

## Create-role command model

Python security mutation uses:

```text
CreateRoleCommand
```

Fields:

```text
name
can_login
is_superuser
can_create_db
can_create_role
can_replicate
inherit
bypass_rls
connection_limit
```

Passwords are intentionally absent.

PyDBAdminKit does not put password material in this role-creation command model.

## Alter-role command model

`AlterRoleCommand` uses nullable attributes.

```text
None
    → leave unchanged

True / False
    → explicitly enable/disable
```

At least one role attribute must be changed.

An all-`None` alter command is rejected.

## MembershipCommand

A membership mutation uses:

```text
role
member
admin_option
```

Self-membership is rejected:

```text
role == member
```

is invalid.

## RelationAccessCommand

Relation privilege mutation uses:

```text
principal
access_type
object
grant_option
```

Cross-database relation mutation is rejected.

The target relation must belong to the database selected by the active profile.

## Grant option

A relation grant can include:

```text
WITH GRANT OPTION
```

through:

```text
--grant-option
```

This increases the planned risk because it delegates privilege-management capability.

## Admin option

A membership can include:

```text
WITH ADMIN OPTION
```

through:

```text
--admin-option
```

This also raises the mutation risk because the member gains the ability to manage that membership.

## Revoke risk

Privilege revocation is treated as a high-risk base operation.

That is deliberate because removing access can immediately disrupt applications or users.

In production, high risk escalates to:

```text
critical
```

which requires exact target confirmation.

## Drop-role risk

Role drop is:

```text
high
```

outside production and:

```text
critical
```

in production.

The plan explicitly warns that role drop is destructive and may fail while dependencies remain.

## Production warning

Every security mutation planned against a production-classified profile receives a warning equivalent to:

```text
Target connection is classified as production.
```

This warning becomes part of the operation plan.

## Python dry-run example

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_security_mutation_service
from pydbadminkit.domain.safety import MutationOptions
from pydbadminkit.domain.security import CreateRoleCommand

service = build_security_mutation_service(
    "staging",
    Path("config.toml"),
)

command = CreateRoleCommand(
    name="reporting_user",
    can_login=True,
)

plan = service.plan_create_role(command)

result = service.create_role(
    command,
    MutationOptions(dry_run=True),
    plan=plan,
)

print(result.operation)
print(result.target)
print(result.risk)
print(result.confirmation)
```

The returned value is the `OperationPlan`.

## Python execution model

Execution requires explicit mutation options.

Conceptually:

```python
MutationOptions(
    approved=True,
)
```

or for a typed-target operation:

```python
MutationOptions(
    confirmed_target=plan.target,
)
```

Application services never prompt by themselves.

Prompt handling belongs to the CLI layer.

## Why Python services do not prompt

The public domain contract says:

```text
MutationOptions
    → caller-supplied execution approval
    → never prompts by itself
```

This design keeps:

- notebooks;
- services;
- web applications;
- tests;
- CI pipelines

in control of their own interaction model.

## Mutation result

Successful execution returns an `OperationResult` with:

```text
operation
status
changed
message
metadata
```

Security mutation metadata includes:

```text
target
risk
correlation_id
```

The correlation ID links planning, execution and audit evidence.

## Machine output

Security inspection works with all standard output modes.

Examples:

```bash
pydbadmin -c prod --output json role list

pydbadmin \
  -c prod \
  --output json \
  effective-access list \
  --role app_user
```

List commands produce arrays.

Describe commands produce objects.

Dry-run mutation commands produce operation-plan objects.

## Security errors

Important public errors include:

```text
AuthorizationError
ResourceNotFoundError
PolicyDeniedError
ConfirmationRequiredError
SafetyPolicyError
AuditUnavailableError
```

Different failure classes map to stable CLI exit categories.

Detailed mappings are covered in guide 26.

## Authorization versus policy denial

These are distinct concepts.

```text
AuthorizationError
    → database authorization rejected the requested behavior

PolicyDeniedError
    → PyDBAdminKit safety policy blocked the operation
```

For example:

```text
read_only = true
```

causing mutation rejection is a framework policy denial.

## Common security workflow

A safe operational sequence is:

```text
1. verify server/profile
2. inspect role
3. inspect direct access
4. inspect effective access
5. inspect ownership
6. plan mutation with dry-run
7. review risk / warnings / target
8. execute with required confirmation
9. verify resulting state
10. preserve audit evidence
```

## Worked CLI workflow

Inspect the role:

```bash
pydbadmin -c staging role describe reporting_user
```

Inspect direct access:

```bash
pydbadmin \
  -c staging \
  access list \
  --role reporting_user
```

Inspect effective access:

```bash
pydbadmin \
  -c staging \
  effective-access list \
  --role reporting_user
```

Inspect ownership:

```bash
pydbadmin \
  -c staging \
  ownership list \
  --owner reporting_user
```

Plan a new grant:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  access grant \
  --role reporting_user \
  --object public.orders \
  --access SELECT
```

Only after reviewing the plan should execution be considered.

## Security inspection before mutation

Do not mutate from assumptions.

Before a role change:

```text
role describe
```

Before access change:

```text
access list
effective-access list
ownership list
```

This helps distinguish direct privilege changes from inherited/owner/public/superuser behavior.

## Troubleshooting

### Mutation blocked by read-only profile

Check:

```toml
read_only = true
```

Use a correctly authorized mutation profile only when mutation is intended.

Do not disable read-only protection merely to make a command pass without reviewing the operational need.

### Mutation blocked because environment is unknown

Classify the profile environment explicitly.

Supported environment values are documented in guide 04.

### --yes still asks for a target

Expected for critical operations.

Provide the exact required:

```text
--confirm-target
```

value.

### Role mutation targets pg_* role

Built-in PostgreSQL role namespaces are protected by policy.

Use inspection unless there is a supported and intentional workflow outside this mutation surface.

### Effective privilege exists without direct grant

Inspect:

```text
effective-access
```

and review its sources:

```text
inherited
public
owner
superuser
```

### Revoke seems more risky than expected

Revocation is intentionally high-risk because it may immediately remove required application access.

Production escalation can make it critical.

## Production considerations

For production security administration:

1. use separate read-only and mutation-capable profiles;
2. classify the environment as `production`;
3. inspect current state first;
4. dry-run every meaningful mutation;
5. review the generated target exactly;
6. do not use `--yes` as a critical-operation bypass;
7. preserve typed-target confirmation;
8. review inherited and ownership-derived access before revoking direct grants;
9. preserve audit output;
10. avoid manipulating built-in PostgreSQL roles through application-role workflows;
11. verify post-mutation state;
12. use least privilege for the administrative connection.

## Best practices

Prefer:

```text
inspect → plan → review → execute → verify
read-only inspection profiles
explicit production classification
dry-run
effective-access analysis
ownership analysis
typed public command models
audit correlation IDs
```

Avoid:

```text
direct adapter mutation
unknown environment classification
using --yes as a universal bypass
granting SUPERUSER casually
granting BYPASSRLS casually
WITH GRANT OPTION without review
WITH ADMIN OPTION without review
revoking access without checking effective sources
dropping roles without dependency analysis
```

## Key takeaways

- Security inspection and mutation are separate application services.
- `role`, `access`, `effective-access` and `ownership` are the security CLI groups.
- Role and direct-access mutations are guarded, planned and audited.
- Mutation risk depends on the requested privilege change.
- Production raises medium risk to high and high risk to critical.
- Critical operations require exact target typing.
- `--yes` does not bypass typed-target confirmation.
- Read-only profiles block security mutations.
- Unknown environments block security mutations.
- PostgreSQL `pg_*` built-in role names receive protection.
- Effective access explains whether privileges come from direct, inherited, public, owner or superuser sources.
- Ownership is part of authorization analysis and should be inspected before privilege changes.
- Guide 12 covers roles, memberships and privileges in depth.
- Guide 13 covers effective access and ownership in depth.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Python API Fundamentals](08_PYTHON_API_FUNDAMENTALS.md)
- [Schemas, Tables, Views and Indexes](10_SCHEMA_TABLE_VIEW_AND_INDEX_EXPLORATION.md)
- [Roles, Memberships and Privileges](12_ROLES_MEMBERSHIPS_AND_PRIVILEGES.md)
- [Effective Access and Ownership](13_EFFECTIVE_ACCESS_AND_OWNERSHIP.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Audit and Operation Traceability](25_AUDIT_AND_OPERATION_TRACEABILITY.md)
- [Error Handling and Exit Codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Production Usage and Safety](31_PRODUCTION_USAGE_AND_SAFETY.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Roles, Memberships and Privileges](12_ROLES_MEMBERSHIPS_AND_PRIVILEGES.md).
