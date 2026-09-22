# PyDBAdminKit 0.3.0 — Guide d'exploitation locale

> Guide pratique pour installer, exécuter et tester localement l'état actuel de PyDBAdminKit.
> **Ce guide couvre Windows PowerShell et Linux/macOS**, ainsi que les deux modes de démarrage PostgreSQL (Docker et installation locale).

PyDBAdminKit `0.3.0` est exécutable localement et permet de tester un workflow PostgreSQL réel de bout en bout.

À ce stade, trois grandes briques sont disponibles :

- **Foundation** : connexion, configuration, CLI, erreurs, capabilities, sorties machine.
- **Object Explorer** : server, databases, schemas, tables, colonnes, contraintes, vues, materialized views et index.
- **Security Administration** : rôles, memberships, accès directs/effectifs, ownership et mutations protégées.

La ligne `0.4.x` ajoutera ensuite Runtime Administration : sessions, requêtes, transactions, locks, blocking chains, cancel/terminate.

---

> **Convention de lecture**
> Chaque section de commande est présentée en deux blocs :
> - ` ```bash ` → Linux / macOS
> - ` ```powershell ` → Windows PowerShell
>
> Les commandes sont identiques dans les grandes lignes ; seuls la syntaxe de continuation de ligne et les appels de programme diffèrent.

---

## 1. Récupérer `main` et installer le projet

### Cloner le dépôt

```bash
# Linux / macOS & Windows (même commande dans Git Bash ou PowerShell)
git clone https://github.com/tawounfouet/pydbadminkit.git
cd pydbadminkit
git checkout main
git pull origin main
```

### Créer l'environnement virtuel et installer

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev,binary]"
```

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev,binary]"
```

### Vérifier la version

```bash
# Linux / macOS
pydbadmin --version
```

```powershell
# Windows PowerShell
python -m pydbadminkit --version
```

Résultat attendu :

```text
pydbadminkit 0.3.0
```

> **Windows — commande `pydbadmin` :** pip génère un `pydbadmin.exe` qui peut être bloqué
> par certains environnements. Si vous obtenez "Accès refusé", ajoutez ceci à votre `$PROFILE` :
> ```powershell
> function pydbadmin { python -m pydbadminkit @args }
> ```
> Rechargez avec `. $PROFILE`. Après cela, `pydbadmin` fonctionnera comme sur Linux.
> Dans ce guide, les exemples Windows utilisent systématiquement `python -m pydbadminkit`.

---

## 2. Démarrer PostgreSQL localement

Deux options sont disponibles : **Docker** (recommandé, version figée) ou **PostgreSQL installé localement**.

---

### Option A — Docker (PostgreSQL 18)

#### Linux / macOS et Windows (même commande)

```bash
docker compose up -d postgres
docker compose ps
```

Configuration Docker :

| Paramètre | Valeur |
|---|---|
| Image | `postgres:18` |
| Host | `localhost` |
| Port | `5432` |
| User | `postgres` |
| Password | `postgres` |
| Database | `pydbadmin_dev` |

Afficher les logs :

```bash
docker compose logs postgres --tail 20
```

> **Note Windows — postgres:18 :** À partir de la version 18, PostgreSQL stocke ses données
> dans un sous-dossier de `/var/lib/postgresql` (et non plus directement dans `/var/lib/postgresql/data`).
> Le fichier `docker-compose.yml` fourni est déjà corrigé en conséquence.
>
> Si le conteneur plante au démarrage (`Exited (1)`), réinitialisez le volume :
> ```bash
> docker compose down -v
> docker compose up -d postgres
> ```

#### Se connecter au conteneur pour exécuter du SQL

```bash
# Linux / macOS & Windows
docker compose exec postgres psql -U postgres -d pydbadmin_dev
```

---

### Option B — PostgreSQL installé localement

#### Windows — Vérifier le service PostgreSQL

```powershell
Get-Service -Name "*postgres*"
# Exemple : postgresql-x64-17  Running  Automatic
```

```powershell
# Démarrer le service si arrêté
Start-Service postgresql-x64-17
```

#### Linux / macOS — Vérifier le service

```bash
pg_isready
# ou
sudo systemctl status postgresql
```

#### Créer la base de données de développement (première fois)

```powershell
# Windows PowerShell
$env:PGPASSWORD = "votre_mot_de_passe"
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE pydbadmin_dev;"
```

```bash
# Linux / macOS
PGPASSWORD="votre_mot_de_passe" psql -U postgres -c "CREATE DATABASE pydbadmin_dev;"
# ou si peer auth est configuré :
sudo -u postgres psql -c "CREATE DATABASE pydbadmin_dev;"
```

#### Se connecter directement avec psql

```powershell
# Windows PowerShell
$env:PGPASSWORD = "votre_mot_de_passe"
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d pydbadmin_dev
```

```bash
# Linux / macOS
psql -U postgres -d pydbadmin_dev
```

---

### Tableau récapitulatif des options

| Option | Avantage | Prérequis |
|--------|----------|-----------|
| Docker postgres:18 | Version figée, reproductible, isolée | Docker Desktop installé |
| PostgreSQL local | Pas besoin de Docker, démarrage automatique | PostgreSQL installé sur la machine |

---

## 3. Créer un profil PyDBAdminKit

Créer ou mettre à jour `./config.toml` dans le répertoire du projet.

### Profil Docker (`local`)

```toml
[connections.local]
engine = "postgresql"
host = "localhost"
port = 5432
database = "pydbadmin_dev"
username = "postgres"
environment = "development"
read_only = false
ssl_mode = "disable"
connect_timeout_seconds = 10

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_LOCAL_PASSWORD"
```

Exporter le mot de passe :

```bash
# Linux / macOS
export PYDBADMIN_LOCAL_PASSWORD="postgres"
```

```powershell
# Windows PowerShell
$env:PYDBADMIN_LOCAL_PASSWORD = "postgres"
```

### Profil PostgreSQL local (`local-native`)

```toml
[connections.local-native]
engine = "postgresql"
host = "localhost"
port = 5432
database = "pydbadmin_dev"
username = "postgres"
environment = "development"
read_only = false
ssl_mode = "disable"
connect_timeout_seconds = 10

[connections.local-native.secret]
provider = "env"
reference = "PYDBADMIN_NATIVE_PASSWORD"
```

Exporter le mot de passe :

```bash
# Linux / macOS
export PYDBADMIN_NATIVE_PASSWORD="votre_mot_de_passe"
```

```powershell
# Windows PowerShell
$env:PYDBADMIN_NATIVE_PASSWORD = "votre_mot_de_passe"
```

> Dans la suite du guide, les exemples utilisent `--connection local` (Docker).
> Remplacez par `--connection local-native` si vous utilisez le PostgreSQL local.

---

# 4. Tester la Foundation

## 4.1 Connection test

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  connection test
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  connection test
```

Résultat attendu :

```text
Connection OK
Engine:   postgresql
Version:  18.x  (ou 17.x selon votre installation)
Database: pydbadmin_dev
User:     postgres
Latency:  xx ms
```

## 4.2 Server info

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  server info
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  server info
```

## 4.3 Sortie JSON

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  --output json \
  server info
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --output json `
  server info
```

## 4.4 Sortie YAML

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  --output yaml \
  server info
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --output yaml `
  server info
```

Les formats machine sont conçus pour être exploitables par des scripts, CI/CD, `jq`, `yq` ou de futurs agents.

---

# 5. Tester l'Object Explorer — 0.2.x

## 5.1 Bases de données

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  database list
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  database list
```

Décrire une base :

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  database describe pydbadmin_dev
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  database describe pydbadmin_dev
```

## 5.2 Schemas

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  schema list

# Inclure les schemas système
pydbadmin \
  --connection local \
  --config ./config.toml \
  schema list \
  --include-system
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  schema list

# Inclure les schemas système
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  schema list `
  --include-system
```

## 5.3 Créer quelques objets PostgreSQL de démonstration

Avec `psql` (SQL identique sur toutes les plateformes) :

```sql
CREATE TABLE public.customers (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX customers_name_idx
ON public.customers(name);

CREATE VIEW public.active_customers AS
SELECT id, email, name
FROM public.customers;
```

Via le conteneur Docker :

```bash
# Linux / macOS & Windows
docker compose exec postgres psql -U postgres -d pydbadmin_dev
```

Via PostgreSQL local (Windows) :

```powershell
# Windows PowerShell
$env:PGPASSWORD = "votre_mot_de_passe"
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d pydbadmin_dev
```

Via PostgreSQL local (Linux / macOS) :

```bash
psql -U postgres -d pydbadmin_dev
```

## 5.4 Tables

Lister les tables :

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  table list \
  --schema public
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  table list `
  --schema public
```

Décrire une table :

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  table describe public.customers
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  table describe public.customers
```

Le `describe` expose : colonnes, types, nullabilité, valeurs par défaut, identity/generated, contraintes (PK, UNIQUE, FK, CHECK).

## 5.5 Vues

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  view list \
  --schema public

pydbadmin \
  --connection local \
  --config ./config.toml \
  view describe public.active_customers
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  view list `
  --schema public

python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  view describe public.active_customers
```

Les vues matérialisées sont distinguées des vues classiques.

## 5.6 Index

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  index list \
  --schema public \
  --table customers

pydbadmin \
  --connection local \
  --config ./config.toml \
  index describe public.customers_name_idx
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  index list `
  --schema public `
  --table customers

python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  index describe public.customers_name_idx
```

PyDBAdminKit peut déjà être utilisé comme un **Object Explorer PostgreSQL CLI**, sans GUI.

---

# 6. Tester Security Administration — 0.3.0

## 6.1 Inspection des rôles

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  role list

# Login-only
pydbadmin \
  --connection local \
  --config ./config.toml \
  role list \
  --login-only

# Inclure les rôles système
pydbadmin \
  --connection local \
  --config ./config.toml \
  role list \
  --include-system

# Décrire un rôle
pydbadmin \
  --connection local \
  --config ./config.toml \
  role describe postgres
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  role list

# Login-only
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  role list `
  --login-only

# Inclure les rôles système
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  role list `
  --include-system

# Décrire un rôle
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  role describe postgres
```

La description d'un rôle expose : LOGIN, SUPERUSER, CREATEDB, CREATEROLE, REPLICATION, INHERIT, BYPASSRLS, connection limit, VALID UNTIL, memberships entrants/sortants.

---

# 7. Tester les accès directs

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  access list \
  --role app

# Filtrer sur un objet
pydbadmin \
  --connection local \
  --config ./config.toml \
  access list \
  --role app \
  --schema public \
  --object customers
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  access list `
  --role app

# Filtrer sur un objet
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  access list `
  --role app `
  --schema public `
  --object customers
```

Cette commande expose les ACL **explicitement attribuées** au rôle (ne mélange pas héritage, PUBLIC, ownership, superuser).

---

# 8. Tester les accès effectifs

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  effective-access list \
  --role app
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  effective-access list `
  --role app
```

Sources possibles : `direct`, `inherited`, `public`, `owner`, `superuser`.

---

# 9. Tester l'ownership

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  ownership list \
  --owner postgres

# Tables du schema public seulement
pydbadmin \
  --connection local \
  --config ./config.toml \
  ownership list \
  --owner postgres \
  --type table \
  --schema public
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  ownership list `
  --owner postgres

# Tables du schema public seulement
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  ownership list `
  --owner postgres `
  --type table `
  --schema public
```

---

# 10. Tester les mutations — toujours commencer par `--dry-run`

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  --dry-run \
  role create test_user \
  --login

# En JSON
pydbadmin \
  --connection local \
  --config ./config.toml \
  --dry-run \
  --output json \
  role create test_user \
  --login
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --dry-run `
  role create test_user `
  --login

# En JSON
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --dry-run `
  --output json `
  role create test_user `
  --login
```

Résultat attendu (`OperationPlan`) :

```text
Operation:      security.role.create
Target:         test_user
Environment:    development
Risk:           medium
Confirmation:   simple
Correlation ID: ...
```

Aucune mutation PostgreSQL n'est exécutée en dry-run.

---

# 11. Exécuter réellement une création de rôle

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role create test_user \
  --login

pydbadmin \
  --connection local \
  --config ./config.toml \
  role describe test_user

# Modifier le rôle
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role alter test_user \
  --createdb enable
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  role create test_user `
  --login

python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  role describe test_user

# Modifier le rôle
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  role alter test_user `
  --createdb enable
```

---

# 12. Tester les memberships

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role create reader

pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role membership-add reader test_user

pydbadmin \
  --connection local \
  --config ./config.toml \
  role describe test_user

# Retirer le membership
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role membership-remove reader test_user
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  role create reader

python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  role membership-add reader test_user

python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  role describe test_user

# Retirer le membership
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  role membership-remove reader test_user
```

---

# 13. Tester GRANT / REVOKE

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  access grant \
  --role test_user \
  --object public.customers \
  --access SELECT

pydbadmin \
  --connection local \
  --config ./config.toml \
  access list \
  --role test_user

pydbadmin \
  --connection local \
  --config ./config.toml \
  effective-access list \
  --role test_user

pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  access revoke \
  --role test_user \
  --object public.customers \
  --access SELECT
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  access grant `
  --role test_user `
  --object public.customers `
  --access SELECT

python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  access list `
  --role test_user

python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  effective-access list `
  --role test_user

python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  access revoke `
  --role test_user `
  --object public.customers `
  --access SELECT
```

---

# 14. Tester les guardrails

## 14.1 Profil read-only

Modifier temporairement `config.toml` :

```toml
read_only = true
```

Puis tenter une mutation :

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role create should_fail
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  role create should_fail
```

L'opération doit être bloquée. Code de sortie attendu : `7`

Remettre ensuite `read_only = false`.

## 14.2 Environnement UNKNOWN

Les mutations fonctionnent en **fail-closed** si l'environnement n'est pas connu :

```text
UNKNOWN → PolicyDenied → aucune mutation
```

---

# 15. Tester une opération critique

```bash
# Linux / macOS — doit être REFUSÉ
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  --non-interactive \
  role create local_super \
  --superuser

# Version correcte avec confirmation explicite
pydbadmin \
  --connection local \
  --config ./config.toml \
  --non-interactive \
  role create local_super \
  --superuser \
  --confirm-target local_super
```

```powershell
# Windows PowerShell — doit être REFUSÉ
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  --non-interactive `
  role create local_super `
  --superuser

# Version correcte avec confirmation explicite
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --non-interactive `
  role create local_super `
  --superuser `
  --confirm-target local_super
```

Niveaux de confirmation :

```text
LOW      → aucune confirmation
MEDIUM   → confirmation simple (--yes suffit)
HIGH     → confirmation explicite
CRITICAL → confirmation TYPE_TARGET (--confirm-target <nom>)
```

---

# 16. Audit des mutations

Pipeline de toute mutation Security :

```text
Command → OperationPlan → Risk classification → Policy → Confirmation → Execution → Audit
```

Les événements d'audit incluent : opération, target, environnement, niveau de risque, résultat, correlation ID, timestamp. Les secrets et mots de passe ne sont jamais écrits dans le journal.

---

# 17. Supprimer les objets de démonstration

```bash
# Linux / macOS
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role drop test_user

pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role drop reader
```

```powershell
# Windows PowerShell
python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  role drop test_user

python -m pydbadminkit `
  --connection local `
  --config ./config.toml `
  --yes `
  role drop reader
```

Nettoyer les objets SQL :

```sql
-- Identique sur toutes les plateformes
DROP VIEW IF EXISTS public.active_customers;
DROP TABLE IF EXISTS public.customers;
```

---

# 18. Lancer la qualification locale complète

## Ruff Format

```bash
ruff format --check .
```

## Ruff Lint

```bash
ruff check .
```

## Mypy strict

```bash
mypy src/pydbadminkit
```

## Unit Tests + couverture

```bash
# Linux / macOS & Windows
pytest -m unit \
  --cov=pydbadminkit \
  --cov-report=term-missing
```

```powershell
# Windows PowerShell (une ligne)
pytest -m unit --cov=pydbadminkit --cov-report=term-missing
```

Seuil projet : `coverage >= 85 %`

## Intégration PostgreSQL

Avec le conteneur Docker ou le PostgreSQL local démarré :

```bash
# Linux / macOS & Windows
pytest -m "integration and postgresql"
```

---

# 19. Parcours de smoke-test recommandé

```text
01. pydbadmin --version
        ↓
02. connection test
        ↓
03. server info
        ↓
04. database list
        ↓
05. schema list
        ↓
06. table list / describe
        ↓
07. view list / describe
        ↓
08. index list / describe
        ↓
09. role list / describe
        ↓
10. role create --dry-run
        ↓
11. role create --yes
        ↓
12. membership-add
        ↓
13. access grant
        ↓
14. access list
        ↓
15. effective-access list
        ↓
16. ownership list
        ↓
17. access revoke
        ↓
18. membership-remove
        ↓
19. role drop
```

---

# 20. État fonctionnel actuel

```text
PostgreSQL
│
├── Connection / Server
│
├── Database Explorer
│   ├── Databases
│   ├── Schemas
│   ├── Tables
│   │   ├── Columns
│   │   └── Constraints
│   ├── Views
│   ├── Materialized Views
│   └── Indexes
│
└── Security Administration
    ├── Roles
    ├── Memberships
    ├── Direct Access
    ├── Effective Access
    ├── Ownership
    ├── Role mutations
    ├── Membership mutations
    ├── GRANT / REVOKE
    ├── Dry-run
    ├── Risk classification
    ├── Guardrails
    └── Audit
```

---

# 21. Suite de la roadmap

```text
0.4.x — Runtime Administration
```

avec notamment : `pg_stat_activity`, sessions, requêtes actives, transactions, waits, locks, blocking relations, blocking chains, cancel query, terminate session, protections contre self-termination et backends protégés, dry-run et guardrails réutilisant le moteur Safety de `0.3.0`.

---

## Recommandation

Pour les premiers essais, utiliser uniquement :

- PostgreSQL Docker local **ou** PostgreSQL installé localement ;
- une base disposable (`pydbadmin_dev`) ;
- `environment = "development"` ou `"testing"` ;
- `--dry-run` avant les mutations ;
- `--yes` uniquement après validation du plan ;
- `--confirm-target` pour les opérations critiques.

Ne pas commencer les essais de mutations Security sur une base PostgreSQL de production.
