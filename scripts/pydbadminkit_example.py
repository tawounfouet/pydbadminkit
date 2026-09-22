"""
pydbadminkit_example.py
=======================
Démonstration de l'API Python publique de PyDBAdminKit 0.3.0.

Le script exerce les services applicatifs directement, sans passer par la CLI.
Les mutations sont limitées aux profils development/testing et utilisent un rôle
temporaire unique automatiquement supprimé en fin d'exécution.

Usage :
    Windows PowerShell :
        $env:PYDBADMIN_NATIVE_PASSWORD = "<mot-de-passe>"
        python scripts/pydbadminkit_example.py

    Linux / macOS :
        export PYDBADMIN_NATIVE_PASSWORD="<mot-de-passe>"
        python scripts/pydbadminkit_example.py

Prérequis :
    - pip install -e ".[dev,binary]"
    - PostgreSQL démarré (local ou Docker)
    - variable d'environnement du profil de connexion définie
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from pydbadminkit import __version__
from pydbadminkit.bootstrap import (
    build_capability_service,
    build_catalog_service,
    build_connection_service,
    build_security_mutation_service,
    build_security_service,
    build_server_service,
    resolve_connection,
)
from pydbadminkit.domain.common import DatabaseObjectType
from pydbadminkit.domain.connection import ConnectionTestResult, ResolvedConnectionConfig
from pydbadminkit.domain.safety import MutationOptions
from pydbadminkit.domain.security import CreateRoleCommand

CONNECTION_PROFILE = "local-native"
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"
SEPARATOR = "-" * 72


def section(title: str) -> None:
    print(f"\n{'=' * 72}\n  {title}\n{'=' * 72}")


def subsection(title: str) -> None:
    print(f"\n{SEPARATOR}\n  >> {title}\n{SEPARATOR}")


def _password_env_var(profile: str) -> str:
    return (
        "PYDBADMIN_NATIVE_PASSWORD"
        if profile == "local-native"
        else "PYDBADMIN_LOCAL_PASSWORD"
    )


def _check_environment() -> bool:
    env_var = _password_env_var(CONNECTION_PROFILE)
    if os.environ.get(env_var):
        return True

    print(f"[ERREUR] Variable d'environnement '{env_var}' non définie.")
    print(f"Windows : $env:{env_var} = '<mot-de-passe>'")
    print(f"Linux   : export {env_var}='<mot-de-passe>'")
    return False


def main() -> int:
    if not _check_environment():
        return 2

    section("1. Version et configuration")
    print(f"  pydbadminkit version : {__version__}")
    print(f"  Profil               : {CONNECTION_PROFILE}")
    print(f"  Config               : {CONFIG_PATH}")

    config: ResolvedConnectionConfig = resolve_connection(CONNECTION_PROFILE, CONFIG_PATH)
    print(f"  Engine               : {config.engine}")
    print(f"  Host                 : {config.host}")
    print(f"  Port                 : {config.port}")
    print(f"  Database             : {config.database}")
    print(f"  Username             : {config.username}")
    print(f"  Environment          : {config.environment}")
    print(f"  Read-only            : {config.read_only}")
    print(f"  SSL mode             : {config.ssl.mode}")

    section("2. Service de connexion")
    connection_svc = build_connection_service(CONFIG_PATH)
    result: ConnectionTestResult = connection_svc.test(CONNECTION_PROFILE)
    print(f"  Engine     : {result.engine}")
    print(f"  Version    : {result.version}")
    print(f"  Database   : {result.current_database}")
    print(f"  User       : {result.current_user}")
    print(f"  Latency    : {result.latency_ms:.2f} ms")

    section("3. Capabilities de l'adaptateur")
    capabilities = build_capability_service().list()
    for capability in capabilities:
        reason = f" — {capability.reason}" if capability.reason else ""
        print(f"  - {capability.name:<35} {capability.availability.value}{reason}")

    section("4. Server Service")
    server_info = build_server_service(CONNECTION_PROFILE, CONFIG_PATH).get_info()
    print(f"  Engine   : {server_info.engine}")
    print(f"  Version  : {server_info.version}")
    print(f"  Database : {server_info.current_database}")
    print(f"  User     : {server_info.current_user}")

    section("5. Catalog Service — Object Explorer")
    catalog_svc = build_catalog_service(CONNECTION_PROFILE, CONFIG_PATH)

    subsection("Bases de données")
    databases = catalog_svc.list_databases()
    for database in databases:
        print(
            f"  - {database.name} | owner={database.owner} "
            f"| encoding={database.encoding}"
        )

    subsection("Schémas utilisateur")
    schemas = catalog_svc.list_schemas(include_system=False)
    for schema in schemas:
        print(f"  - {schema.name} | owner={schema.owner}")

    subsection("Tables dans public")
    tables = catalog_svc.list_tables(schema="public")
    if not tables:
        print("  (aucune table dans public)")
    for table in tables:
        print(f"  - {table.name} | owner={table.owner} | kind={table.kind.value}")

    if tables:
        first_table = tables[0]
        subsection(f"Détail de la table {first_table.name}")
        description = catalog_svc.describe_table(first_table.name)
        print(f"  Table    : {description.table.name}")
        print(f"  Owner    : {description.table.owner}")
        print(f"  Colonnes : {len(description.columns)}")
        for column in description.columns:
            nullable = "NULL" if column.nullable else "NOT NULL"
            default = f" DEFAULT {column.default}" if column.default else ""
            print(f"    - {column.name:<24} {column.data_type} {nullable}{default}")
        for constraint in description.constraints:
            print(
                f"    - contrainte {constraint.constraint_type.value}: "
                f"{constraint.name}"
            )

    subsection("Vues dans public")
    views = catalog_svc.list_views(schema="public")
    for view in views:
        print(f"  - {view.name} | owner={view.owner} | kind={view.kind.value}")
    if not views:
        print("  (aucune vue dans public)")

    subsection("Index dans public")
    indexes = catalog_svc.list_indexes(schema="public")
    for index in indexes:
        print(f"  - {index.name} | table={index.table} | method={index.method}")
    if not indexes:
        print("  (aucun index dans public)")

    section("6. Security Service — Inspection")
    security_svc = build_security_service(CONNECTION_PROFILE, CONFIG_PATH)

    subsection("Rôles PostgreSQL")
    roles = security_svc.list_roles()
    for role in roles:
        flags = []
        if role.can_login:
            flags.append("LOGIN")
        if role.is_superuser:
            flags.append("SUPERUSER")
        if role.can_create_db:
            flags.append("CREATEDB")
        print(f"  - {role.name:<24} {' '.join(flags)}")

    subsection("Description du rôle postgres")
    role_description = security_svc.describe_role("postgres")
    role = role_description.role
    print(f"  Nom           : {role.name}")
    print(f"  LOGIN         : {role.can_login}")
    print(f"  SUPERUSER     : {role.is_superuser}")
    print(f"  CREATEDB      : {role.can_create_db}")
    print(f"  CREATEROLE    : {role.can_create_role}")
    print(f"  INHERIT       : {role.inherit}")
    print(f"  BYPASSRLS     : {role.bypass_rls}")
    print(f"  Conn. limit   : {role.connection_limit}")
    print(f"  Membre de     : {[item.role for item in role_description.member_of] or '(aucun)'}")
    print(f"  Membres       : {[item.member for item in role_description.members] or '(aucun)'}")

    subsection("Accès directs du rôle postgres")
    direct_accesses = security_svc.list_direct_access("postgres")
    for access in direct_accesses[:5]:
        print(
            f"  - {access.object.name} | {access.access_type.value} "
            f"| issuer={access.issuer} | delegable={access.delegable}"
        )
    if not direct_accesses:
        print("  (aucun accès direct)")

    subsection("Accès effectifs du rôle postgres")
    effective_accesses = security_svc.list_effective_access("postgres")
    source_counts: dict[str, int] = {}
    for access in effective_accesses:
        for source in access.sources:
            source_counts[source.value] = source_counts.get(source.value, 0) + 1
    print(f"  {len(effective_accesses)} accès effectif(s)")
    for source, count in sorted(source_counts.items()):
        print(f"    - {source:<15}: {count}")

    subsection("Tables possédées par postgres")
    ownerships = security_svc.list_ownership(
        "postgres",
        object_type=DatabaseObjectType.TABLE,
    )
    for ownership in ownerships:
        print(
            f"  - {ownership.object.name} "
            f"| type={ownership.object.object_type.value}"
        )
    if not ownerships:
        print("  (aucune table possédée)")

    section("7. Security Mutation Service — Dry-run et mutation contrôlée")
    mutation_svc = build_security_mutation_service(CONNECTION_PROFILE, CONFIG_PATH)
    role_name = f"demo_script_user_{uuid4().hex[:8]}"
    command = CreateRoleCommand(name=role_name, can_login=True)
    plan = mutation_svc.plan_create_role(command)

    print(f"  Operation      : {plan.operation}")
    print(f"  Target         : {plan.target}")
    print(f"  Risk           : {plan.risk.label}")
    print(f"  Confirmation   : {plan.confirmation.value}")
    print(f"  Correlation ID : {plan.correlation_id}")

    dry_run = mutation_svc.create_role(
        command,
        MutationOptions(dry_run=True),
        plan=plan,
    )
    print(f"  Dry-run type   : {type(dry_run).__name__}")

    environment = str(config.environment)
    can_mutate = not config.read_only and environment in {"development", "testing"}
    if not can_mutate:
        print(
            "  Mutation réelle ignorée : le profil doit être development/testing "
            "et read_only=false."
        )
        return 0

    created = False
    try:
        outcome = mutation_svc.create_role(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )
        created = True
        print(f"  Create status  : {outcome.status.value}")
        print(f"  Changed        : {outcome.changed}")
        print(f"  Message        : {outcome.message}")
        print(f"  Metadata       : {outcome.metadata}")

        created_role = security_svc.describe_role(role_name).role
        print(f"  Vérification   : {created_role.name} LOGIN={created_role.can_login}")
    finally:
        if created:
            drop_plan = mutation_svc.plan_drop_role(role_name)
            drop_outcome = mutation_svc.drop_role(
                role_name,
                MutationOptions(approved=True),
                plan=drop_plan,
            )
            print(f"  Cleanup status : {drop_outcome.status.value}")

    section("8. Fin")
    print("  [OK] Démonstration terminée avec succès.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
