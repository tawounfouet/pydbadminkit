# PyDBAdminKit 1.0 — Roles, Memberships and Privileges

## Objective

Administer PostgreSQL roles, role memberships and direct relation privileges through the guarded
PyDBAdminKit 1.0 security mutation surface.

This guide focuses on:

```text
role create
role alter
role drop
role membership-add
role membership-remove
access grant
access revoke
```

and their public Python equivalents.

For the higher-level security model and safety philosophy, see
[Security Administration](11_SECURITY_ADMINISTRATION.md).

## Prerequisites

Before performing any mutation:

1. verify the selected profile;
2. verify the target server/database;
3. inspect the current role/access state;
4. confirm the profile environment classification;
5. use `--dry-run` first.

Recommended preflight:

```bash
pydbadmin -c staging server info
pydbadmin -c staging role list
pydbadmin -c staging role describe app_user
pydbadmin -c staging access list --role app_user
```

## Mutation pipeline

Every security mutation follows the same high-level model:

```text
typed command
    ↓
plan_*
    ↓
OperationPlan
    ↓
policy guard
    ↓
confirmation
    ↓
audit
    ↓
PostgreSQL execution
    ↓
OperationResult
```

The CLI wraps this with:

```text
--dry-run
--yes
--non-interactive
--confirm-target
```

## Safety first

Use:

```bash
pydbadmin -c staging --dry-run ...
```

before execution.

A dry-run returns the planned:

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

and does not mutate PostgreSQL.

# Role creation

## CLI

Basic role:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role create reporting_user
```

Login-enabled role:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role create reporting_user \
  --login
```

Available creation options:

```text
--login
--superuser
--createdb
--createrole
--replication
--inherit / --no-inherit
--bypass-rls
--connection-limit <n>
--confirm-target <target>
```

Defaults:

```text
LOGIN             false
SUPERUSER         false
CREATEDB          false
CREATEROLE        false
REPLICATION       false
INHERIT           true
BYPASSRLS         false
CONNECTION LIMIT  -1
```

## CreateRoleCommand

The public Python model is:

```python
from pydbadminkit.domain.security import CreateRoleCommand

command = CreateRoleCommand(
    name="reporting_user",
    can_login=True,
)
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

Password material is intentionally absent from this command model.

## Validation

The role name must be non-blank.

Connection limit must satisfy:

```text
connection_limit >= -1
```

`-1` means unlimited in PostgreSQL semantics.

## Creation risk

Base risk rules:

```text
ordinary role
    → medium

CREATEDB / CREATEROLE / REPLICATION
    → high

SUPERUSER / BYPASSRLS
    → critical
```

Production then escalates:

```text
medium → high
high   → critical
```

## Privileged-role warning

If elevated attributes are requested, the plan records a warning listing them.

For example:

```text
Elevated role attributes requested: SUPERUSER, CREATEROLE.
```

## Python dry-run

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

outcome = service.create_role(
    command,
    MutationOptions(dry_run=True),
    plan=plan,
)

print(outcome.risk)
print(outcome.confirmation)
print(outcome.target)
```

# Role alteration

## CLI tri-state model

`role alter` does not use simple booleans for most switches.

Instead:

```text
--login enable
--login disable
```

and similarly for:

```text
--superuser
--createdb
--createrole
--replication
--inherit
--bypass-rls
```

If an option is not provided, that attribute remains unchanged.

Example:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role alter reporting_user \
  --login enable \
  --connection-limit 5
```

## AlterRoleCommand

```python
from pydbadminkit.domain.security import AlterRoleCommand

command = AlterRoleCommand(
    name="reporting_user",
    can_login=True,
    connection_limit=5,
)
```

Nullable fields mean:

```text
None        → leave unchanged
True        → enable
False       → disable
integer     → set connection limit
```

## Empty alteration is invalid

This is rejected:

```python
AlterRoleCommand(name="reporting_user")
```

because at least one attribute must change.

## Alteration risk

Base rules:

```text
SUPERUSER=True or BYPASSRLS=True
    → critical

CREATEDB / CREATEROLE / REPLICATION changed
    → high

other role attributes
    → medium
```

Note that changing an elevated attribute in either direction is classified as high because the
authorization shape changes materially.

## Immediate authorization effect

High-risk role alterations include a warning that role attributes can change effective
authorization immediately.

This is important for:

```text
CREATEROLE
CREATEDB
REPLICATION
SUPERUSER
BYPASSRLS
```

# Role deletion

## CLI

Always dry-run first:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role drop reporting_user
```

## Risk

Role drop is:

```text
high      outside production
critical  in production
```

The plan warns that:

```text
Dropping a role is destructive and may fail while dependencies remain.
```

## Protected cases

PyDBAdminKit blocks:

```text
dropping pg_* built-in roles
dropping the current connection role
```

through `PolicyDeniedError`.

## Production confirmation

In production, role drop is critical.

Therefore the exact target must be supplied or typed:

```bash
pydbadmin \
  -c prod \
  role drop reporting_user \
  --confirm-target reporting_user
```

`--yes` does not replace this proof.

# Role memberships

## Membership semantics

PyDBAdminKit models a membership as:

```text
member belongs to role
```

Example:

```text
member = alice
role   = reporting_readers
```

means:

```text
alice → reporting_readers
```

## Add membership

Dry-run:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role membership-add reporting_readers alice
```

Execution after review:

```bash
pydbadmin \
  -c staging \
  role membership-add reporting_readers alice \
  --yes
```

depending on the generated confirmation level.

## Membership target

The generated plan target is:

```text
member->role
```

For the previous example:

```text
alice->reporting_readers
```

This exact string matters when a critical production operation requires typed-target proof.

## MembershipCommand

```python
from pydbadminkit.domain.security import MembershipCommand

command = MembershipCommand(
    role="reporting_readers",
    member="alice",
)
```

Fields:

```text
role
member
admin_option
```

## Self-membership is invalid

This is rejected:

```python
MembershipCommand(
    role="alice",
    member="alice",
)
```

A role cannot be a member of itself.

## WITH ADMIN OPTION

CLI:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role membership-add reporting_readers alice \
  --admin-option
```

This maps to PostgreSQL:

```text
WITH ADMIN OPTION
```

and raises the base risk from:

```text
medium → high
```

because the member receives authority to manage the membership.

## Remove membership

Dry-run:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role membership-remove reporting_readers alice
```

Base risk:

```text
medium
```

Production escalation makes this:

```text
high
```

because removing inherited privileges can impact live applications/users.

## Membership inspection

Before changing membership, use:

```bash
pydbadmin -c staging role describe alice
pydbadmin -c staging role describe reporting_readers
```

The detailed role description exposes both:

```text
member_of
members
```

# Direct relation privileges

## Supported AccessType values

PyDBAdminKit 1.0 supports:

```text
SELECT
INSERT
UPDATE
DELETE
TRUNCATE
REFERENCES
TRIGGER
```

These are represented by:

```text
AccessType
```

## Inspect direct privileges

Before granting or revoking:

```bash
pydbadmin \
  -c staging \
  access list \
  --role reporting_user \
  --schema public
```

## Grant privilege

Dry-run:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  access grant \
  --role reporting_user \
  --object public.orders \
  --access SELECT
```

## RelationAccessCommand

Python:

```python
from pydbadminkit.domain.common import parse_qualified_name
from pydbadminkit.domain.security import AccessType, RelationAccessCommand

command = RelationAccessCommand(
    principal="reporting_user",
    access_type=AccessType.SELECT,
    object=parse_qualified_name("public.orders"),
)
```

Fields:

```text
principal
access_type
object
grant_option
```

## Default schema

If the relation is unqualified:

```text
orders
```

the PostgreSQL adapter executes the grant against:

```text
public.orders
```

Prefer explicit:

```text
public.orders
```

to avoid ambiguity.

## Cross-database mutation is rejected

This is invalid:

```text
analytics.public.orders
```

for a relation privilege mutation.

`RelationAccessCommand` raises a validation error because cross-database relation access mutation
is unsupported.

Connect to the target database instead.

## Grant target format

The generated plan target is:

```text
principal:relation:ACCESS
```

Example:

```text
reporting_user:public.orders:SELECT
```

This is the typed-target proof required if the plan becomes critical.

## Grant risk

Without grant option:

```text
medium
```

With:

```text
--grant-option
```

base risk becomes:

```text
high
```

because privilege delegation is being granted.

In production:

```text
medium → high
high   → critical
```

## WITH GRANT OPTION

CLI:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  access grant \
  --role reporting_user \
  --object public.orders \
  --access SELECT \
  --grant-option
```

The plan warns:

```text
WITH GRANT OPTION delegates privilege management.
```

## Revoke privilege

Dry-run:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  access revoke \
  --role reporting_user \
  --object public.orders \
  --access SELECT
```

Base risk:

```text
high
```

This is intentionally stricter than a normal grant because revocation may immediately break
dependent application behavior.

In production this becomes:

```text
critical
```

and therefore requires exact target confirmation.

## Production revoke example

Plan first:

```bash
pydbadmin \
  -c prod \
  --dry-run \
  access revoke \
  --role reporting_user \
  --object public.orders \
  --access SELECT
```

If the plan target is:

```text
reporting_user:public.orders:SELECT
```

execution requires:

```bash
pydbadmin \
  -c prod \
  access revoke \
  --role reporting_user \
  --object public.orders \
  --access SELECT \
  --confirm-target 'reporting_user:public.orders:SELECT'
```

## Direct access versus effective access

Do not assume that revoking a direct grant removes effective access.

A role may still retain access through:

```text
inherited
public
owner
superuser
```

sources.

Before revocation, inspect:

```bash
pydbadmin \
  -c prod \
  effective-access list \
  --role reporting_user \
  --schema public \
  --object orders
```

Guide 13 covers this in detail.

# Python mutation workflow

## Build the service

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_security_mutation_service

service = build_security_mutation_service(
    "staging",
    Path("config.toml"),
)
```

## Plan a grant

```python
from pydbadminkit.domain.common import parse_qualified_name
from pydbadminkit.domain.security import AccessType, RelationAccessCommand

command = RelationAccessCommand(
    principal="reporting_user",
    access_type=AccessType.SELECT,
    object=parse_qualified_name("public.orders"),
)

plan = service.plan_grant_access(command)

print(plan.target)
print(plan.risk)
print(plan.confirmation)
print(plan.effects)
print(plan.warnings)
```

## Dry-run

```python
from pydbadminkit.domain.safety import MutationOptions

outcome = service.grant_access(
    command,
    MutationOptions(dry_run=True),
    plan=plan,
)
```

The result is the plan itself.

## Approved execution

For a non-typed-target confirmation:

```python
outcome = service.grant_access(
    command,
    MutationOptions(approved=True),
    plan=plan,
)
```

For a critical typed-target operation:

```python
outcome = service.grant_access(
    command,
    MutationOptions(
        confirmed_target=plan.target,
    ),
    plan=plan,
)
```

Do not set both merely out of habit.

Use the confirmation model required by the plan.

# Confirmation matrix

The implemented mapping is:

```text
low       → none
medium    → simple
high      → explicit
critical  → type_target
```

CLI behavior:

```text
none
    → execution proceeds

simple / explicit
    → prompt unless --yes
    → --non-interactive without approval fails

type_target
    → exact target required
    → --yes does not bypass it
```

## Non-interactive use

For automation, dry-run first:

```bash
pydbadmin \
  -c staging \
  --output json \
  --non-interactive \
  --dry-run \
  role create reporting_user \
  --login
```

Then, if the plan is approved by your workflow, execute with the required proof.

For simple/explicit confirmation:

```bash
pydbadmin \
  -c staging \
  --output json \
  --non-interactive \
  --yes \
  role create reporting_user \
  --login
```

For critical confirmation:

```bash
pydbadmin \
  -c prod \
  --output json \
  --non-interactive \
  role drop reporting_user \
  --confirm-target reporting_user
```

# Policy guardrails

Mutation execution is blocked when:

```text
profile.read_only == true
environment == unknown
protected pg_* role policy applies
current connection role is being dropped
```

These are application-layer guards.

Directly calling an internal adapter to evade them is outside the public supported workflow.

# PostgreSQL execution safety

The PostgreSQL adapter uses Psycopg composable SQL for identifiers.

Conceptually:

```text
sql.Identifier(role_name)
sql.Identifier(schema, relation)
sql.Literal(connection_limit)
```

Privilege keywords are selected from the fixed `AccessType` mapping.

This avoids building administrative SQL by concatenating user-provided identifiers into raw strings.

Consumers should still use the public command/service layer rather than the adapter directly.

# Role inspection after mutation

After creating or altering a role:

```bash
pydbadmin -c staging role describe reporting_user
```

After membership mutation:

```bash
pydbadmin -c staging role describe reporting_user
```

and/or describe the role being granted.

After privilege mutation:

```bash
pydbadmin \
  -c staging \
  access list \
  --role reporting_user \
  --schema public \
  --object orders
```

Then inspect effective access if required.

# OperationResult

Successful mutation execution returns:

```text
OperationResult
```

with:

```text
operation
status
changed
message
metadata
```

For security mutations, metadata includes:

```text
target
risk
correlation_id
```

The correlation ID is important for audit traceability.

# Machine output

Use:

```bash
pydbadmin -c staging --output json --dry-run ...
```

to obtain an `OperationPlan` machine payload.

Executed mutations emit an `OperationResult`.

This means automation must distinguish:

```text
dry-run  → OperationPlan
execute  → OperationResult
```

Do not assume identical payload fields.

# Error handling

Important error classes include:

```text
ValidationError / CLI usage error
ResourceNotFoundError
AuthorizationError
PolicyDeniedError
ConfirmationRequiredError
DatabaseOperationError
```

Typical meanings:

```text
ValueError / CLI exit 2
    → invalid command model or syntax

AuthorizationError
    → PostgreSQL authorization denied execution

PolicyDeniedError
    → PyDBAdminKit blocked the mutation

ConfirmationRequiredError
    → required proof/approval was absent

ResourceNotFoundError
    → referenced role/object not found or not visible
```

Detailed exit-code mappings are documented in guide 26.

# Worked workflow: create a reporting role

Inspect current state:

```bash
pydbadmin -c staging role list
```

Plan:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role create reporting_user \
  --login
```

Execute after review:

```bash
pydbadmin \
  -c staging \
  --yes \
  role create reporting_user \
  --login
```

Verify:

```bash
pydbadmin -c staging role describe reporting_user
```

# Worked workflow: grant read access through a role

Create a group-style role:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role create reporting_readers
```

Grant SELECT:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  access grant \
  --role reporting_readers \
  --object public.orders \
  --access SELECT
```

Add user membership:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  role membership-add reporting_readers alice
```

Inspect effective access:

```bash
pydbadmin \
  -c staging \
  effective-access list \
  --role alice \
  --schema public \
  --object orders
```

This pattern makes the difference between direct privileges and inherited privileges explicit.

# Worked Python workflow

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_security_mutation_service
from pydbadminkit.domain.common import parse_qualified_name
from pydbadminkit.domain.safety import MutationOptions
from pydbadminkit.domain.security import (
    AccessType,
    CreateRoleCommand,
    MembershipCommand,
    RelationAccessCommand,
)

service = build_security_mutation_service(
    "staging",
    Path("config.toml"),
)

role_command = CreateRoleCommand(
    name="reporting_readers",
)

role_plan = service.plan_create_role(role_command)

service.create_role(
    role_command,
    MutationOptions(dry_run=True),
    plan=role_plan,
)

grant_command = RelationAccessCommand(
    principal="reporting_readers",
    access_type=AccessType.SELECT,
    object=parse_qualified_name("public.orders"),
)

grant_plan = service.plan_grant_access(grant_command)

service.grant_access(
    grant_command,
    MutationOptions(dry_run=True),
    plan=grant_plan,
)

membership_command = MembershipCommand(
    role="reporting_readers",
    member="alice",
)

membership_plan = service.plan_add_membership(
    membership_command,
)

service.add_membership(
    membership_command,
    MutationOptions(dry_run=True),
    plan=membership_plan,
)
```

This example intentionally stops at dry-run.

Execution requires the caller to supply the approval form required by each resulting plan.

# Troubleshooting

## role alter says at least one attribute must change

Provide at least one alter option:

```bash
--login enable
```

or another supported attribute.

## connection limit rejected

The minimum allowed value is:

```text
-1
```

## membership rejected as self-membership

The same name cannot be both:

```text
role
member
```

## cross-database privilege target rejected

Use:

```text
schema.relation
```

inside the database selected by the active profile.

## --yes does not authorize execution

If the plan is critical, this is expected.

Use exact:

```text
--confirm-target <plan.target>
```

## production grant unexpectedly requires stronger confirmation

Production escalates risk.

For example:

```text
grant without grant option
medium → high
```

## production revoke requires typed target

Expected:

```text
revoke base high
production → critical
critical → type_target
```

## role drop fails because dependencies exist

PyDBAdminKit delegates the actual PostgreSQL role drop.

PostgreSQL may reject it while owned objects or privilege dependencies remain.

Inspect ownership and access before retrying.

Guide 13 is the next step.

# Production considerations

For production role/privilege administration:

1. use a dedicated mutation-capable profile;
2. keep inspection profiles read-only;
3. verify role state before mutation;
4. inspect direct and effective access before revoke;
5. inspect ownership before role drop;
6. dry-run first;
7. archive the operation plan for sensitive changes;
8. preserve exact target proof for critical operations;
9. avoid routine use of SUPERUSER or BYPASSRLS;
10. use group-style roles/memberships where appropriate;
11. treat WITH ADMIN OPTION and WITH GRANT OPTION as delegation changes;
12. verify resulting state after execution;
13. preserve correlation IDs and audit evidence.

# Best practices

Prefer:

```text
least privilege
group-style roles
explicit membership
schema-qualified relation names
dry-run
inspection before revoke/drop
typed commands
exact target confirmation
post-mutation verification
```

Avoid:

```text
direct SQL concatenation
direct adapter calls
SUPERUSER by default
BYPASSRLS by default
blind --yes
cross-database privilege mutation
role drop without ownership analysis
revoke without effective-access analysis
self-membership
```

## Key takeaways

- Role creation, alteration, deletion, membership and relation privileges are guarded mutations.
- `CreateRoleCommand`, `AlterRoleCommand`, `MembershipCommand` and
  `RelationAccessCommand` are the public typed command models.
- `role alter` is tri-state: omitted means unchanged.
- Role creation risk increases for elevated attributes.
- SUPERUSER and BYPASSRLS are critical.
- WITH ADMIN OPTION and WITH GRANT OPTION increase risk.
- Revoke is high-risk by default.
- Production escalates medium to high and high to critical.
- Critical operations require exact target proof.
- Relation privilege mutation is limited to the active database.
- PyDBAdminKit composes PostgreSQL identifiers safely through Psycopg composable SQL.
- Direct privilege state and effective privilege state are not the same.
- Ownership and effective access should be inspected before destructive security changes.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Security Administration](11_SECURITY_ADMINISTRATION.md)
- [Effective Access and Ownership](13_EFFECTIVE_ACCESS_AND_OWNERSHIP.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Audit and Operation Traceability](25_AUDIT_AND_OPERATION_TRACEABILITY.md)
- [Error Handling and Exit Codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Production Usage and Safety](31_PRODUCTION_USAGE_AND_SAFETY.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Effective Access and Ownership](13_EFFECTIVE_ACCESS_AND_OWNERSHIP.md).
