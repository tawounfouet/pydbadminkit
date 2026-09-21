# PyDBAdminKit 0.3.0 — Guide d’exploitation locale

> Guide pratique pour installer, exécuter et tester localement l’état actuel de PyDBAdminKit.

PyDBAdminKit `0.3.0` est déjà exécutable localement et permet de tester un workflow PostgreSQL réel de bout en bout.

À ce stade, trois grandes briques sont disponibles :

- **Foundation** : connexion, configuration, CLI, erreurs, capabilities, sorties machine.
- **Object Explorer** : server, databases, schemas, tables, colonnes, contraintes, vues, materialized views et index.
- **Security Administration** : rôles, memberships, accès directs/effectifs, ownership et mutations protégées.

La ligne `0.4.x` ajoutera ensuite Runtime Administration : sessions, requêtes, transactions, locks, blocking chains, cancel/terminate.

---

## 1. Récupérer `main` et installer le projet

Depuis le repo local :

```bash
git checkout main
git pull origin main

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev,binary]"
```

Sous Windows PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev,binary]"
```

Vérifier la version :

```bash
pydbadmin --version
```

Résultat attendu :

```text
pydbadminkit 0.3.0
```

Puis :

```bash
pydbadmin --help
```

---

## 2. Démarrer PostgreSQL localement

Le repo fournit déjà un `docker-compose.yml` avec PostgreSQL 18.

```bash
docker compose up -d postgres
```

Vérifier l’état :

```bash
docker compose ps
```

Configuration Docker actuelle :

| Paramètre | Valeur |
|---|---|
| Image | `postgres:18` |
| Host | `127.0.0.1` |
| Port | `5432` |
| User | `postgres` |
| Password | `postgres` |
| Database | `pydbadmin_dev` |

Afficher les logs si nécessaire :

```bash
docker compose logs postgres
```

Si `psql` est installé localement :

```bash
psql --version
```

---

## 3. Créer un profil PyDBAdminKit

Créer par exemple un fichier local :

```text
./config.toml
```

avec :

```toml
[connections.local]
engine = "postgresql"
host = "127.0.0.1"
port = 5432
database = "pydbadmin_dev"
username = "postgres"
environment = "testing"
read_only = false
ssl_mode = "disable"
connect_timeout_seconds = 5

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_POSTGRES_PASSWORD"
```

Exporter le mot de passe utilisé par Docker :

```bash
export PYDBADMIN_POSTGRES_PASSWORD="postgres"
```

Sous PowerShell :

```powershell
$env:PYDBADMIN_POSTGRES_PASSWORD = "postgres"
```

Tester la connexion :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  connection test
```

---

# 4. Tester la Foundation

## 4.1 Connection test

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  connection test
```

## 4.2 Server info

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  server info
```

## 4.3 Sortie JSON

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --output json \
  server info
```

## 4.4 Sortie YAML

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --output yaml \
  server info
```

Les formats machine sont conçus pour être exploitables par des scripts, CI/CD, `jq`, `yq` ou de futurs agents.

---

# 5. Tester l’Object Explorer — 0.2.x

## 5.1 Bases de données

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  database list
```

Décrire une base :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  database describe pydbadmin_dev
```

## 5.2 Schemas

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  schema list
```

Inclure les schemas système :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  schema list \
  --include-system
```

## 5.3 Créer quelques objets PostgreSQL de démonstration

Avec `psql` :

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

Ou directement via le conteneur :

```bash
docker compose exec postgres psql -U postgres -d pydbadmin_dev
```

puis exécuter le SQL précédent.

## 5.4 Tables

Lister les tables :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  table list \
  --schema public
```

Décrire une table :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  table describe public.customers
```

Le `describe` expose notamment :

- colonnes ;
- types PostgreSQL ;
- nullabilité ;
- valeurs par défaut ;
- identity/generated ;
- contraintes ;
- PK ;
- UNIQUE ;
- FK ;
- CHECK lorsque présent.

## 5.5 Vues

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  view list \
  --schema public
```

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  view describe public.active_customers
```

Les vues matérialisées sont également distinguées des vues classiques.

## 5.6 Index

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  index list \
  --schema public \
  --table customers
```

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  index describe public.customers_name_idx
```

PyDBAdminKit peut déjà être utilisé comme un **Object Explorer PostgreSQL CLI**, sans GUI.

---

# 6. Tester Security Administration — 0.3.0

## 6.1 Inspection des rôles

Lister les rôles :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  role list
```

Seulement les rôles capables de se connecter :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  role list \
  --login-only
```

Inclure les rôles système PostgreSQL :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  role list \
  --include-system
```

Décrire un rôle :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  role describe postgres
```

Le modèle PostgreSQL retenu est explicite :

```text
User PostgreSQL
    =
Role
    +
LOGIN
```

La description d’un rôle expose notamment :

- LOGIN ;
- SUPERUSER ;
- CREATEDB ;
- CREATEROLE ;
- REPLICATION ;
- INHERIT ;
- BYPASSRLS ;
- connection limit ;
- VALID UNTIL ;
- memberships entrants/sortants.

---

# 7. Tester les accès directs

Une fois un rôle créé et quelques ACL attribuées :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  access list \
  --role app
```

Filtrer sur un objet :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  access list \
  --role app \
  --schema public \
  --object customers
```

Cette commande expose les ACL **explicitement attribuées** au rôle.

Elle ne confond pas les accès directs avec :

- héritage de rôle ;
- `PUBLIC` ;
- ownership ;
- superuser.

---

# 8. Tester les accès effectifs

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  effective-access list \
  --role app
```

Les sources possibles sont :

```text
direct
inherited
public
owner
superuser
```

Cela permet de distinguer :

```text
ACL attribuée directement
        ≠
accès réellement disponible pour le rôle
```

---

# 9. Tester l’ownership

Lister les objets possédés par `postgres` :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  ownership list \
  --owner postgres
```

Uniquement les tables du schema `public` :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  ownership list \
  --owner postgres \
  --type table \
  --schema public
```

L’ownership reste volontairement distinct des ACL.

---

# 10. Tester les mutations — toujours commencer par `--dry-run`

Exemple :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --dry-run \
  role create test_user \
  --login
```

Le résultat doit être un `OperationPlan`, par exemple conceptuellement :

```text
Operation: security.role.create
Target: test_user
Environment: testing
Risk: medium
Confirmation: simple
Correlation ID: ...
```

Aucune mutation PostgreSQL n’est exécutée.

En JSON :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --dry-run \
  --output json \
  role create test_user \
  --login
```

Le dry-run est le parcours recommandé avant toute mutation.

---

# 11. Exécuter réellement une création de rôle

Dans un PostgreSQL local/disposable :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role create test_user \
  --login
```

Puis :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  role describe test_user
```

Modifier le rôle :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role alter test_user \
  --createdb enable
```

---

# 12. Tester les memberships

Créer un rôle de lecture :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role create reader
```

Ajouter `test_user` au rôle `reader` :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role membership-add reader test_user
```

Puis :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  role describe test_user
```

Le rôle doit apparaître dans la section :

```text
MEMBER OF
```

Et :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  role describe reader
```

doit exposer `test_user` parmi ses membres.

Retirer le membership :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role membership-remove reader test_user
```

---

# 13. Tester GRANT / REVOKE

Attribuer `SELECT` :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  access grant \
  --role test_user \
  --object public.customers \
  --access SELECT
```

Vérifier l’ACL directe :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  access list \
  --role test_user
```

Vérifier l’accès effectif :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  effective-access list \
  --role test_user
```

Révoquer ensuite l’accès :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  access revoke \
  --role test_user \
  --object public.customers \
  --access SELECT
```

---

# 14. Tester les guardrails

## 14.1 Profil read-only

Modifier temporairement :

```toml
read_only = true
```

Puis :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role create should_fail
```

L’opération doit être bloquée.

Code de sortie attendu pour un blocage de policy :

```text
7
```

Remettre ensuite :

```toml
read_only = false
```

## 14.2 Environnement UNKNOWN

Les mutations sont conçues pour fonctionner en **fail-closed** si l’environnement n’est pas connu.

```text
UNKNOWN
    ↓
PolicyDenied
    ↓
aucune mutation
```

---

# 15. Tester une opération critique

Exemple volontairement local :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  --non-interactive \
  role create local_super \
  --superuser
```

Cette commande doit être refusée.

Pourquoi ?

```text
--yes
   ≠
autorisation universelle
```

Une opération critique nécessite une preuve explicite de target :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --non-interactive \
  role create local_super \
  --superuser \
  --confirm-target local_super
```

Le principe est :

```text
LOW        → aucune confirmation
MEDIUM     → confirmation simple
HIGH       → confirmation explicite
CRITICAL   → confirmation TYPE_TARGET
```

---

# 16. Audit des mutations

Les mutations Security passent par le pipeline :

```text
Command
  ↓
OperationPlan
  ↓
Risk classification
  ↓
Policy
  ↓
Confirmation
  ↓
Execution
  ↓
Audit
```

Les événements d’audit incluent notamment :

- opération ;
- target ;
- environnement ;
- niveau de risque ;
- résultat ;
- correlation ID ;
- timestamp.

Les secrets et mots de passe ne doivent jamais être écrits dans le journal.

---

# 17. Supprimer les objets de démonstration

Retirer les rôles :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role drop test_user
```

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --yes \
  role drop reader
```

Pour une opération de suppression classifiée critique, utiliser si nécessaire la preuve exacte :

```bash
pydbadmin \
  --connection local \
  --config ./config.toml \
  --non-interactive \
  role drop some_role \
  --confirm-target some_role
```

Puis nettoyer les objets SQL de démonstration :

```sql
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
pytest -m unit \
  --cov=pydbadminkit \
  --cov-report=term-missing
```

Le seuil projet est :

```text
coverage >= 85 %
```

## Intégration PostgreSQL

Avec le conteneur PostgreSQL lancé :

```bash
pytest -m "integration and postgresql"
```

---

# 19. Parcours de smoke-test recommandé

Le parcours manuel recommandé pour tester `0.3.0` est :

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

À `0.3.0`, PyDBAdminKit n’est plus seulement un squelette architectural.

Il sait déjà :

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

On peut donc déjà le considérer comme un **outil CLI d’administration PostgreSQL utilisable localement**, avec une architecture Python réutilisable et des sorties machine adaptées à l’automatisation.

---

# 21. Suite de la roadmap

La prochaine ligne est :

```text
0.4.x — Runtime Administration
```

avec notamment :

- `pg_stat_activity` ;
- sessions ;
- requêtes actives ;
- transactions ;
- waits ;
- locks ;
- blocking relations ;
- blocking chains ;
- cancel query ;
- terminate session ;
- protections contre self-termination et backends protégés ;
- dry-run et guardrails réutilisant le moteur Safety de `0.3.0`.

---

## Recommandation

Pour les premiers essais, utiliser uniquement :

- PostgreSQL Docker local ;
- une base disposable ;
- `environment = "testing"` ;
- `--dry-run` avant les mutations ;
- `--yes` uniquement après validation du plan ;
- `--confirm-target` pour les opérations critiques.

Ne pas commencer les essais de mutations Security sur une base PostgreSQL de production.
