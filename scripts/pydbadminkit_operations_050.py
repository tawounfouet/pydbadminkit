"""
pydbadminkit_operations_050.py
==============================
Lab exécutable pour PyDBAdminKit 0.5.x (testé avec 0.5.0b1).

Le script explore la ligne Operations :
- capabilities Backup / Restore / Maintenance ;
- backup custom en dry-run, puis création optionnelle ;
- validation d'un artefact de backup ;
- restore en dry-run, puis exécution optionnelle vers une nouvelle base ;
- VACUUM / ANALYZE / REINDEX en dry-run ;
- vues de progression VACUUM / REINDEX ;
- mutations réelles désactivées par défaut.

Aucun secret n'est stocké ou affiché.

Variables utiles :
    PYDBADMIN_PROFILE=local-native
    PYDBADMIN_CONFIG=/chemin/vers/config.toml
    PYDBADMIN_RUN_BACKUP=1
    PYDBADMIN_RUN_MAINTENANCE=1
    PYDBADMIN_RUN_RESTORE=1
    PYDBADMIN_LAB_TABLE=public.ma_table
    PYDBADMIN_LAB_INDEX=public.mon_index
    PYDBADMIN_LAB_BACKUP=/chemin/vers/un_backup.dump
    PYDBADMIN_LAB_RESTORE_DB=pydbadmin_restore_lab

Les opérations réelles sont volontairement limitées aux profils
development/testing avec read_only=false.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from uuid import uuid4

from pydbadminkit import __version__
from pydbadminkit.bootstrap import (
    build_backup_service,
    build_backup_validation_service,
    build_capability_service,
    build_catalog_service,
    build_maintenance_service,
    build_restore_service,
    resolve_connection,
)
from pydbadminkit.domain.common import parse_qualified_name
from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    BackupFormat,
    CreateBackupCommand,
    ReindexCommand,
    ReindexTargetType,
    RestoreBackupCommand,
    VacuumCommand,
)
from pydbadminkit.domain.safety import MutationOptions

SEPARATOR = "-" * 78
CONNECTION_PROFILE = os.getenv("PYDBADMIN_PROFILE", "local-native")
RUN_BACKUP = os.getenv("PYDBADMIN_RUN_BACKUP", "0") == "1"
RUN_MAINTENANCE = os.getenv("PYDBADMIN_RUN_MAINTENANCE", "0") == "1"
RUN_RESTORE = os.getenv("PYDBADMIN_RUN_RESTORE", "0") == "1"
EXPLICIT_TABLE = os.getenv("PYDBADMIN_LAB_TABLE")
EXPLICIT_INDEX = os.getenv("PYDBADMIN_LAB_INDEX")
EXISTING_BACKUP = os.getenv("PYDBADMIN_LAB_BACKUP")
RESTORE_DATABASE = os.getenv(
    "PYDBADMIN_LAB_RESTORE_DB",
    f"pydbadmin_restore_lab_{uuid4().hex[:8]}",
)


def section(title: str) -> None:
    print(f"\n{'=' * 78}\n  {title}\n{'=' * 78}")


def subsection(title: str) -> None:
    print(f"\n{SEPARATOR}\n  >> {title}\n{SEPARATOR}")


def find_config_path() -> Path:
    configured = os.getenv("PYDBADMIN_CONFIG")
    if configured:
        return Path(configured).expanduser().resolve()

    root = Path(__file__).resolve().parent.parent
    candidates = (
        root / "config.toml",
        Path.cwd() / "config.toml",
        Path.cwd().parent / "config.toml",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "config.toml introuvable. Définissez PYDBADMIN_CONFIG si nécessaire."
    )


def mutation_allowed(config: object) -> bool:
    read_only = bool(getattr(config, "read_only", True))
    environment = str(getattr(config, "environment", "unknown"))
    return not read_only and environment in {"development", "testing"}


def print_plan(plan: object) -> None:
    print("  operation    :", getattr(plan, "operation", "-"))
    print("  target       :", getattr(plan, "target", "-"))
    risk = getattr(plan, "risk", None)
    print("  risk         :", getattr(risk, "label", risk))
    confirmation = getattr(plan, "confirmation", None)
    print("  confirmation :", getattr(confirmation, "value", confirmation))
    for effect in getattr(plan, "effects", ()):
        print("  effect       :", effect)
    for warning in getattr(plan, "warnings", ()):
        print("  warning      :", warning)


def main() -> int:
    config_path = find_config_path()
    config = resolve_connection(CONNECTION_PROFILE, config_path)
    can_mutate = mutation_allowed(config)

    section("1. Version et configuration")
    print("  pydbadminkit :", __version__)
    print("  profil       :", CONNECTION_PROFILE)
    print("  config       :", config_path)
    print("  database     :", config.database)
    print("  environment  :", config.environment)
    print("  read_only    :", config.read_only)
    print("  RUN_BACKUP   :", RUN_BACKUP)
    print("  RUN_MAINT.   :", RUN_MAINTENANCE)
    print("  RUN_RESTORE  :", RUN_RESTORE)

    section("2. Capabilities Operations")
    capabilities = build_capability_service().list()
    prefixes = ("backup.", "maintenance.", "postgres.")
    for capability in capabilities:
        if capability.name.startswith(prefixes):
            reason = f" — {capability.reason}" if capability.reason else ""
            print(
                f"  {capability.name:<36} "
                f"{capability.availability.value}{reason}"
            )

    section("3. Cibles de maintenance disponibles")
    catalog = build_catalog_service(CONNECTION_PROFILE, config_path)
    tables = catalog.list_tables(schema="public")
    indexes = catalog.list_indexes(schema="public")

    print(f"  Tables public : {len(tables)}")
    for table in tables[:10]:
        print("   -", table.name)

    print(f"  Index public  : {len(indexes)}")
    for index in indexes[:10]:
        print("   -", index.name, "table=", index.table)

    maintenance = build_maintenance_service(CONNECTION_PROFILE, config_path)

    subsection("Progress VACUUM / REINDEX")
    vacuum_progress = maintenance.list_vacuum_progress()
    reindex_progress = maintenance.list_reindex_progress()
    print(f"  VACUUM en cours : {len(vacuum_progress)}")
    print(f"  REINDEX en cours: {len(reindex_progress)}")

    section("4. Maintenance — dry-run")
    dry_table = (
        parse_qualified_name(EXPLICIT_TABLE)
        if EXPLICIT_TABLE
        else (tables[0].name if tables else None)
    )
    dry_index = (
        parse_qualified_name(EXPLICIT_INDEX)
        if EXPLICIT_INDEX
        else (indexes[0].name if indexes else None)
    )

    if dry_table is None:
        print("  [SKIP] Aucune table public disponible pour le dry-run.")
    else:
        vacuum_command = VacuumCommand(
            table=dry_table,
            analyze=True,
            statement_timeout_seconds=60,
            lock_timeout_seconds=5,
        )
        vacuum_plan = maintenance.plan_vacuum(vacuum_command)
        subsection("VACUUM ANALYZE")
        print_plan(vacuum_plan)
        maintenance.vacuum(
            vacuum_command,
            MutationOptions(dry_run=True),
            plan=vacuum_plan,
        )

        analyze_command = AnalyzeCommand(table=dry_table)
        analyze_plan = maintenance.plan_analyze(analyze_command)
        subsection("ANALYZE")
        print_plan(analyze_plan)
        maintenance.analyze(
            analyze_command,
            MutationOptions(dry_run=True),
            plan=analyze_plan,
        )

    if dry_index is None:
        print("  [SKIP] Aucun index public disponible pour le dry-run REINDEX.")
    else:
        reindex_command = ReindexCommand(
            target_type=ReindexTargetType.INDEX,
            target=dry_index,
            concurrently=True,
            statement_timeout_seconds=120,
            lock_timeout_seconds=5,
        )
        reindex_plan = maintenance.plan_reindex(reindex_command)
        subsection("REINDEX INDEX CONCURRENTLY")
        print_plan(reindex_plan)
        maintenance.reindex(
            reindex_command,
            MutationOptions(dry_run=True),
            plan=reindex_plan,
        )

    section("5. Backup — dry-run")
    lab_dir = Path(tempfile.gettempdir()) / "pydbadminkit-050-lab"
    generated_backup = lab_dir / f"{config.database}_{uuid4().hex[:8]}.dump"
    backup_path = Path(EXISTING_BACKUP).expanduser() if EXISTING_BACKUP else generated_backup

    backup_service = build_backup_service(CONNECTION_PROFILE, config_path)
    backup_command = CreateBackupCommand(
        database=config.database,
        format=BackupFormat.CUSTOM,
        output_path=str(backup_path),
        checksum=True,
        timeout_seconds=300,
    )
    backup_plan = backup_service.plan_create_backup(backup_command)
    print_plan(backup_plan)
    backup_service.create_backup(
        backup_command,
        MutationOptions(dry_run=True),
        plan=backup_plan,
    )

    section("6. Backup réel optionnel + validation")
    backup_available = backup_path.exists()
    if not RUN_BACKUP:
        print("  [SKIP] PYDBADMIN_RUN_BACKUP != 1")
        if EXISTING_BACKUP:
            print("  Artefact fourni :", backup_path)
    elif not can_mutate:
        print("  [SKIP] Profil non development/testing ou read_only=true.")
    else:
        lab_dir.mkdir(parents=True, exist_ok=True)
        outcome = backup_service.create_backup(
            backup_command,
            MutationOptions(approved=True),
            plan=backup_plan,
        )
        backup_available = True
        print("  Backup ID   :", outcome.id)
        print("  Path        :", outcome.path)
        print("  Size        :", outcome.size_bytes)
        print("  SHA-256     :", outcome.checksum)

    if backup_available:
        validation = build_backup_validation_service().validate_backup(
            str(backup_path)
        )
        print("  Validation  :", validation.valid)
        print("  Level       :", validation.level)
        for warning in validation.warnings:
            print("  Warning     :", warning)
        for error in validation.errors:
            print("  Error       :", error)
    else:
        print("  Aucun artefact réel à valider.")

    section("7. Maintenance réelle optionnelle")
    if not RUN_MAINTENANCE:
        print("  [SKIP] PYDBADMIN_RUN_MAINTENANCE != 1")
    elif not can_mutate:
        print("  [SKIP] Profil non development/testing ou read_only=true.")
    elif not EXPLICIT_TABLE:
        print(
            "  [SKIP] Définissez PYDBADMIN_LAB_TABLE pour éviter de choisir "
            "implicitement une table à modifier."
        )
    else:
        table_target = parse_qualified_name(EXPLICIT_TABLE)

        vacuum_command = VacuumCommand(
            table=table_target,
            analyze=True,
            statement_timeout_seconds=60,
            lock_timeout_seconds=5,
        )
        vacuum_plan = maintenance.plan_vacuum(vacuum_command)
        vacuum_result = maintenance.vacuum(
            vacuum_command,
            MutationOptions(approved=True),
            plan=vacuum_plan,
        )
        print("  VACUUM :", vacuum_result.status.value, vacuum_result.message)

        analyze_command = AnalyzeCommand(table=table_target)
        analyze_plan = maintenance.plan_analyze(analyze_command)
        analyze_result = maintenance.analyze(
            analyze_command,
            MutationOptions(approved=True),
            plan=analyze_plan,
        )
        print("  ANALYZE:", analyze_result.status.value, analyze_result.message)

        if EXPLICIT_INDEX:
            index_target = parse_qualified_name(EXPLICIT_INDEX)
            reindex_command = ReindexCommand(
                target_type=ReindexTargetType.INDEX,
                target=index_target,
                concurrently=True,
                statement_timeout_seconds=120,
                lock_timeout_seconds=5,
            )
            reindex_plan = maintenance.plan_reindex(reindex_command)
            reindex_result = maintenance.reindex(
                reindex_command,
                MutationOptions(approved=True),
                plan=reindex_plan,
            )
            print(
                "  REINDEX:",
                reindex_result.status.value,
                reindex_result.message,
            )
        else:
            print("  REINDEX: [SKIP] PYDBADMIN_LAB_INDEX non défini.")

    section("8. Restore optionnel")
    if not backup_available:
        print("  [SKIP] Un artefact backup réel est requis pour planifier le restore.")
    else:
        restore_service = build_restore_service(
            CONNECTION_PROFILE,
            config_path,
        )
        restore_command = RestoreBackupCommand(
            backup_path=str(backup_path),
            target_database=RESTORE_DATABASE,
            create=True,
            timeout_seconds=300,
        )
        restore_plan = restore_service.plan_restore(restore_command)
        print_plan(restore_plan)
        restore_service.restore(
            restore_command,
            MutationOptions(dry_run=True),
            plan=restore_plan,
        )

        if not RUN_RESTORE:
            print("  [SKIP] PYDBADMIN_RUN_RESTORE != 1")
        elif not can_mutate:
            print("  [SKIP] Profil non development/testing ou read_only=true.")
        else:
            restore_result = restore_service.restore(
                restore_command,
                MutationOptions(approved=True),
                plan=restore_plan,
            )
            print("  Target      :", restore_result.target_database)
            print("  Status      :", restore_result.status.value)
            print("  Tool        :", restore_result.tool)
            print("  Verification:", restore_result.verification_passed)
            print(
                "  Note        : la base restaurée est conservée pour inspection ; "
                "supprimez-la explicitement après votre test."
            )

    section("9. Fin")
    print("  [OK] Lab Operations 0.5 terminé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
