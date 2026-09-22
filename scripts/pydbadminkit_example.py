"""
pydbadminkit_example.py
=======================
Script de démonstration de l'API Python de pydbadminkit.

Montre comment utiliser directement les services et objets du package
sans passer par la CLI, en important et en manipulant les objets du domaine.

Usage :
    Windows PowerShell :
        $env:PYDBADMIN_NATIVE_PASSWORD = "postgres"
        python scripts/pydbadminkit_example.py

    Linux / macOS :
        export PYDBADMIN_NATIVE_PASSWORD="postgres"
        python scripts/pydbadminkit_example.py

Prérequis :
    - pip install -e ".[dev,binary]"
    - PostgreSQL démarré (local ou Docker)
    - Variable d'environnement PYDBADMIN_NATIVE_PASSWORD (ou PYDBADMIN_LOCAL_PASSWORD) définie
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Imports du domaine et des services
# ---------------------------------------------------------------------------
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
from pydbadminkit.domain.connection import (
    ConnectionTestResult,
    ResolvedConnectionConfig,
)
from pydbadminkit.domain.security import (
    AccessSource,
    AccessType,
    CreateRoleCommand,
    DirectAccess,
    EffectiveAccess,
    OwnershipInfo,
    RoleDescription,
    RoleInfo,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Profil de connexion et chemin du config.toml
# Adapter si vous utilisez le profil Docker : CONNECTION_PROFILE = "local"
CONNECTION_PROFILE: str = "local-native"
CONFIG_PATH: Path = Path(__file__).parent.parent / "config.toml"

# Vérification que le mot de passe est défini
_env_var = "PYDBADMIN_NATIVE_PASSWORD" if CONNECTION_PROFILE == "local-native" else "PYDBADMIN_LOCAL_PASSWORD"
if not os.environ.get(_env_var):
    print(f"  [WARN] Variable d'environnement '{_env_var}' non definie.")
    print(f"   Definissez-la avant d'executer ce script :")
    print(f"   Windows : $env:{_env_var} = 'postgres'")
    print(f"   Linux   : export {_env_var}='postgres'")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Utilitaires d'affichage
# ---------------------------------------------------------------------------
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SEPARATOR = "-" * 60

def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def subsection(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  >> {title}")
    print(SEPARATOR)

def print_list(items: list, key: str | None = None) -> None:
    if not items:
        print("  (aucun resultat)")
        return
    for item in items:
        if key:
            print(f"  - {getattr(item, key, item)}")
        else:
            print(f"  - {item}")

def print_json(obj: object) -> None:
    try:
        if hasattr(obj, "__dataclass_fields__"):
            data = asdict(obj)  # type: ignore[arg-type]
        elif isinstance(obj, list) and obj and hasattr(obj[0], "__dataclass_fields__"):
            data = [asdict(i) for i in obj]  # type: ignore[arg-type]
        else:
            data = obj
        print(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    except Exception:
        print(repr(obj))


# ===========================================================================
# PARTIE 1 — VERSION ET CONFIGURATION
# ===========================================================================
section("1. Version et configuration")

print(f"  pydbadminkit version : {__version__}")
print(f"  Profil               : {CONNECTION_PROFILE}")
print(f"  Config               : {CONFIG_PATH.resolve()}")

# Résolution du profil de connexion (objet domaine ResolvedConnectionConfig)
subsection("ResolvedConnectionConfig — objet domaine")
config: ResolvedConnectionConfig = resolve_connection(CONNECTION_PROFILE, CONFIG_PATH)
print(f"  Engine               : {config.engine}")
print(f"  Host                 : {config.host}")
print(f"  Port                 : {config.port}")
print(f"  Database             : {config.database}")
print(f"  Username             : {config.username}")
print(f"  Environment          : {config.environment}")
print(f"  Read-only            : {config.read_only}")
print(f"  SSL mode             : {config.ssl.mode}")


# ===========================================================================
# PARTIE 2 — CONNEXION
# ===========================================================================
section("2. Service de connexion")

connection_svc = build_connection_service(CONFIG_PATH)

subsection("Test de connexion → ConnectionTestResult")
result: ConnectionTestResult = connection_svc.test(CONNECTION_PROFILE)
print(f"  Succès     : {result.success}")
print(f"  Engine     : {result.engine}")
print(f"  Version    : {result.server_version}")
print(f"  Database   : {result.database}")
print(f"  User       : {result.username}")
print(f"  Latency    : {result.latency_ms:.2f} ms")

if not result.success:
    print("\n❌ Connexion échouée. Vérifiez que PostgreSQL est démarré.")
    sys.exit(1)


# ===========================================================================
# PARTIE 3 — CAPABILITIES
# ===========================================================================
section("3. Capabilities de l'adaptateur")

cap_svc = build_capability_service()
capabilities = cap_svc.list_capabilities()

subsection("Liste des capacités disponibles")
for cap in capabilities:
    print(f"  [+] {cap.name}")


# ===========================================================================
# PARTIE 4 — SERVER SERVICE
# ===========================================================================
section("4. Server Service")

server_svc = build_server_service(CONNECTION_PROFILE, CONFIG_PATH)

subsection("Informations serveur")
server_info = server_svc.get_info()
print(f"  Engine   : {server_info.engine}")
print(f"  Version  : {server_info.version}")
print(f"  Database : {server_info.database}")
print(f"  User     : {server_info.username}")


# ===========================================================================
# PARTIE 5 — CATALOG SERVICE (Object Explorer)
# ===========================================================================
section("5. Catalog Service — Object Explorer")

catalog_svc = build_catalog_service(CONNECTION_PROFILE, CONFIG_PATH)

# --- Databases ---
subsection("Bases de données")
databases = catalog_svc.list_databases()
print(f"  {len(databases)} base(s) trouvée(s) :")
for db in databases:
    print(f"  - {db.name}  |  owner: {db.owner}  |  encoding: {db.encoding}")

# --- Schemas ---
subsection("Schémas (public uniquement)")
schemas = catalog_svc.list_schemas(include_system=False)
print(f"  {len(schemas)} schéma(s) trouvé(s) :")
for s in schemas:
    print(f"  - {s.name}  |  owner: {s.owner}")

# --- Tables ---
subsection("Tables dans 'public'")
tables = catalog_svc.list_tables(schema="public")
if tables:
    print(f"  {len(tables)} table(s) :")
    for t in tables:
        print(f"  - {t.schema}.{t.name}  |  owner: {t.owner}")

    # Décrire la première table trouvée
    first_table = tables[0]
    subsection(f"Détail de la table : {first_table.schema}.{first_table.name}")
    description = catalog_svc.describe_table(f"{first_table.schema}.{first_table.name}")
    print(f"  Nom      : {description.name}")
    print(f"  Schéma   : {description.schema}")
    print(f"  Colonnes ({len(description.columns)}) :")
    for col in description.columns:
        nullable = "" if col.nullable else " NOT NULL"
        default = f" DEFAULT {col.default}" if col.default else ""
        print(f"    · {col.name:<20} {col.data_type}{nullable}{default}")
    if description.constraints:
        print(f"  Contraintes ({len(description.constraints)}) :")
        for c in description.constraints:
            print(f"    · {c.constraint_type:<10} {c.name}")
else:
    print("  (aucune table dans public — créez des objets de démonstration d'abord)")

# --- Vues ---
subsection("Vues dans 'public'")
views = catalog_svc.list_views(schema="public")
print(f"  {len(views)} vue(s) :")
for v in views:
    print(f"  - {v.schema}.{v.name}  |  type: {'matérialisée' if getattr(v, 'is_materialized', False) else 'standard'}")

# --- Index ---
subsection("Index dans 'public'")
indexes = catalog_svc.list_indexes(schema="public")
print(f"  {len(indexes)} index :")
for idx in indexes:
    print(f"  - {idx.name:<35} sur {idx.table}  |  {idx.index_type}")


# ===========================================================================
# PARTIE 6 — SECURITY SERVICE (Read-only)
# ===========================================================================
section("6. Security Service — Inspection")

security_svc = build_security_service(CONNECTION_PROFILE, CONFIG_PATH)

# --- Rôles ---
subsection("Rôles PostgreSQL")
roles: list[RoleInfo] = security_svc.list_roles()
print(f"  {len(roles)} rôle(s) :")
for role in roles:
    flags = []
    if role.can_login:   flags.append("LOGIN")
    if role.is_superuser: flags.append("SUPERUSER")
    if role.can_create_db: flags.append("CREATEDB")
    print(f"  - {role.name:<20} {' '.join(flags)}")

# --- Rôles avec LOGIN seulement ---
subsection("Rôles avec LOGIN uniquement")
login_roles = security_svc.list_roles(login_only=True)
print(f"  {len(login_roles)} rôle(s) avec LOGIN :")
print_list(login_roles, key="name")

# --- Décrire le rôle postgres ---
subsection("RoleDescription — rôle 'postgres'")
desc: RoleDescription = security_svc.describe_role("postgres")
print(f"  Nom           : {desc.name}")
print(f"  LOGIN         : {desc.can_login}")
print(f"  SUPERUSER     : {desc.is_superuser}")
print(f"  CREATEDB      : {desc.can_create_db}")
print(f"  CREATEROLE    : {desc.can_create_role}")
print(f"  INHERIT       : {desc.inherit}")
print(f"  BYPASSRLS     : {desc.bypass_rls}")
print(f"  Conn. limit   : {desc.connection_limit}")
print(f"  Membre de     : {[m.role for m in desc.member_of] or '(aucun)'}")
print(f"  Membres       : {[m.member for m in desc.members] or '(aucun)'}")

# --- Accès directs ---
subsection("Accès directs du rôle 'postgres'")
direct_accesses: list[DirectAccess] = security_svc.list_access(role="postgres")
if direct_accesses:
    for da in direct_accesses[:5]:  # Afficher les 5 premiers
        print(f"  - {da.relation:<30} {[a.value for a in da.access_types]}")
    if len(direct_accesses) > 5:
        print(f"  ... et {len(direct_accesses) - 5} autres")
else:
    print("  (aucun accès direct)")

# --- Accès effectifs ---
subsection("Accès effectifs du rôle 'postgres'")
effective_accesses: list[EffectiveAccess] = security_svc.list_effective_access(role="postgres")
sources = {}
for ea in effective_accesses:
    src = ea.source.value
    sources[src] = sources.get(src, 0) + 1
print(f"  {len(effective_accesses)} accès effectif(s) — par source :")
for src, count in sources.items():
    print(f"    · {src:<15} : {count}")

# --- Ownership ---
subsection("Objets possédés par 'postgres' (tables)")
ownerships: list[OwnershipInfo] = security_svc.list_ownership(owner="postgres", object_type="table")
if ownerships:
    for own in ownerships:
        print(f"  - {own.schema}.{own.name}  |  type: {own.object_type}")
else:
    print("  (aucune table possédée)")


# ===========================================================================
# PARTIE 7 — SECURITY MUTATION SERVICE (Mutations gardées)
# ===========================================================================
section("7. Security Mutation Service — Mutations gardées")

mutation_svc = build_security_mutation_service(CONNECTION_PROFILE, CONFIG_PATH)

# --- Dry-run : créer un rôle ---
subsection("Dry-run : planifier role create 'demo_script_user'")
create_cmd = CreateRoleCommand(
    name="demo_script_user",
    can_login=True,
    is_superuser=False,
    can_create_db=False,
    can_create_role=False,
    connection_limit=-1,
)
print(f"  Commande créée : {create_cmd}")
plan = mutation_svc.plan_create_role(create_cmd)
print(f"  Operation      : {plan.operation}")
print(f"  Target         : {plan.target}")
print(f"  Risk           : {plan.risk.value}")
print(f"  Confirmation   : {plan.confirmation.value}")
print(f"  Correlation ID : {plan.correlation_id}")
print("  → Dry-run : aucune mutation PostgreSQL exécutée.")

# --- Exécution réelle ---
subsection("Exécution réelle : role create 'demo_script_user'")
try:
    event = mutation_svc.execute_create_role(create_cmd, confirmed=True)
    print(f"  [OK] Role cree : {event.target}")
    print(f"  Resultat      : {event.outcome}")
    print(f"  Correlation ID: {event.correlation_id}")
except Exception as e:
    print(f"  [INFO] {type(e).__name__}: {e}")

# --- Vérification ---
subsection("Vérification : describe 'demo_script_user'")
try:
    created_role = security_svc.describe_role("demo_script_user")
    print(f"  Nom      : {created_role.name}")
    print(f"  LOGIN    : {created_role.can_login}")
    print(f"  SUPERUSER: {created_role.is_superuser}")
except Exception as e:
    print(f"  [INFO] {type(e).__name__}: {e}")


# ===========================================================================
# PARTIE 8 — NETTOYAGE
# ===========================================================================
section("8. Nettoyage")

subsection("Suppression du rôle 'demo_script_user'")
try:
    from pydbadminkit.domain.security.mutations import DropRoleCommand
    drop_cmd = DropRoleCommand(name="demo_script_user")
    event = mutation_svc.execute_drop_role(drop_cmd, confirmed=True)
    print(f"  [OK] Role supprime : {event.target}")
except Exception as e:
    print(f"  [INFO] {type(e).__name__}: {e}")

# Vérification finale
subsection("État final des rôles avec LOGIN")
final_roles = security_svc.list_roles(login_only=True)
print(f"  {len(final_roles)} rôle(s) avec LOGIN :")
print_list(final_roles, key="name")


# ===========================================================================
# FIN
# ===========================================================================
print(f"\n{'=' * 60}")
print("  [OK] Script termine avec succes.")
print(f"{'=' * 60}\n")
