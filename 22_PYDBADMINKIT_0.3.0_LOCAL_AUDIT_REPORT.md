# 22 — PyDBAdminKit 0.3.0 — Rapport d'audit des expérimentations locales

**Projet :** PyDBAdminKit  
**Version auditée :** `0.3.0`  
**Date de l'audit :** 22 septembre 2026  
**Dépôt :** `tawounfouet/pydbadminkit`  
**Commit local initial audité :** `b0bf8d1a07af78313d8f1bff0021c94b9bb38b40`  
**Commit correctif de qualification :** `a19ebfcceb523325b1bd12969fe82ee2dfc6fdb3`  
**Statut :** **QUALIFIÉ AVEC CORRECTIONS**

---

## 1. Objet du rapport

Ce document formalise l'audit du premier lot d'expérimentations locales réalisé sur PyDBAdminKit `0.3.0`.

Le lot initial avait pour objectif de vérifier que le framework pouvait être utilisé concrètement en local depuis :

- un script Python ;
- un notebook Jupyter orienté API Python ;
- un notebook Jupyter orienté CLI ;
- une instance PostgreSQL locale ;
- une instance PostgreSQL lancée via Docker ;
- les profils de connexion `local` et `local-native`.

L'audit a porté non seulement sur les deux fichiers utilisés pour les premiers tests, mais sur **l'ensemble du commit local** ayant introduit ces expérimentations.

L'objectif de la qualification était de déterminer :

1. si les exemples utilisent réellement les contrats publics de PyDBAdminKit 0.3.0 ;
2. si les notebooks sont reproductibles ;
3. si les exemples sont sûrs vis-à-vis des secrets et des mutations PostgreSQL ;
4. si les fichiers ajoutés ont leur place dans le dépôt ;
5. si les expérimentations permettent de servir de base fiable à la suite de la roadmap.

---

# 2. Périmètre audité

Le commit initial :

`b0bf8d1a07af78313d8f1bff0021c94b9bb38b40`

avait introduit ou modifié les fichiers suivants :

| Fichier | Type | État initial |
|---|---|---|
| `PYDBADMINKIT_0.3.0_LOCAL_USAGE_GUIDE.md` | Documentation | Modifié |
| `README.md` | Documentation | Modifié |
| `config.toml` | Configuration locale | Ajouté |
| `docker-compose.yml` | Infrastructure locale | Modifié |
| `examples/config copy.toml` | Configuration exemple | Ajouté |
| `notebooks/00 - Setup.ipynb` | Notebook Python API | Ajouté |
| `notebooks/00 - Setup - Copie.ipynb` | Copie notebook | Ajouté |
| `notebooks/00 - Setup - Copie (2).ipynb` | Copie notebook | Ajouté |
| `notebooks/pydbadminkit_demo.ipynb` | Notebook CLI | Ajouté |
| `scripts/pydbadminkit_example.py` | Exemple Python | Ajouté |

L'audit a également comparé ces fichiers aux contrats réellement exposés dans :

- `src/pydbadminkit/application/` ;
- `src/pydbadminkit/domain/` ;
- `src/pydbadminkit/ports/` ;
- `src/pydbadminkit/adapters/postgresql/` ;
- `src/pydbadminkit/cli/` ;
- les tests unitaires et d'intégration existants.

---

# 3. Résumé exécutif

Les expérimentations locales ont confirmé un point important :

> **PyDBAdminKit 0.3.0 est suffisamment structuré pour être expérimenté localement depuis Python, Jupyter et la CLI.**

Cependant, le premier lot contenait plusieurs écarts entre les exemples générés et les contrats réels du framework.

Ces écarts n'étaient pas tous immédiatement visibles, notamment lorsque :

- le schéma `public` était vide ;
- aucune ACL directe n'était présente ;
- aucune ownership de table n'était retournée ;
- certaines cellules n'avaient pas encore été exécutées ;
- certaines méthodes erronées ne se trouvaient que dans des chemins de code optionnels.

L'audit a donc mis en évidence deux catégories de problèmes :

1. **erreurs fonctionnelles latentes**, dues à des attributs ou méthodes qui n'existent pas dans la version 0.3.0 ;
2. **problèmes de reproductibilité et de sécurité**, principalement dans les notebooks.

Le commit correctif :

`a19ebfcceb523325b1bd12969fe82ee2dfc6fdb3`

a corrigé ces écarts et transformé les expérimentations locales en exemples cohérents avec la version actuelle du framework.

---

# 4. Méthode d'audit

L'audit a été réalisé selon cinq axes.

## 4.1 Vérification des contrats Python

Chaque appel présent dans les exemples a été confronté aux signatures réelles des services et modèles.

Exemples :

- `ConnectionService`
- `CapabilityService`
- `ServerService`
- `CatalogService`
- `SecurityService`
- `SecurityMutationService`

Les dataclasses utilisées ont également été vérifiées :

- `ConnectionTestResult`
- `ServerInfo`
- `DatabaseInfo`
- `SchemaInfo`
- `TableInfo`
- `TableDescription`
- `ViewInfo`
- `IndexInfo`
- `RoleInfo`
- `RoleDescription`
- `DirectAccess`
- `EffectiveAccess`
- `OwnershipInfo`
- `OperationResult`.

---

## 4.2 Vérification CLI

Les commandes utilisées dans le notebook CLI ont été comparées aux commandes Typer réellement enregistrées dans PyDBAdminKit.

Les sous-commandes principales vérifiées sont :

```text
connection test

capability list
capability get

server info

database list
database describe

schema list

table list
table describe

view list
view describe

index list
index describe

role list
role describe
role create
role alter
role drop
role membership-add
role membership-remove

access list
access grant
access revoke

effective-access list

ownership list
```

---

## 4.3 Vérification sécurité

L'audit a recherché :

- mots de passe stockés directement dans les notebooks ;
- valeurs par défaut implicites pour les secrets ;
- outputs contenant potentiellement des données locales ;
- mutations réellement exécutées sans opt-in ;
- création de rôles privilégiés ;
- possibilité de lancer une mutation sur un environnement non approprié.

---

## 4.4 Vérification de reproductibilité

Les notebooks ont été évalués sur :

- la résolution de `config.toml` ;
- leur dépendance au répertoire courant ;
- leur dépendance à l'état précédent du kernel ;
- les outputs persistés ;
- la capacité à être relancés depuis un clone propre.

---

## 4.5 Vérification du dépôt

Le commit a également été inspecté pour identifier :

- fichiers dupliqués ;
- fichiers temporaires ;
- copies accidentelles ;
- configuration d'exemple incohérente ;
- artefacts Jupyter non ignorés.

---

# 5. Constats détaillés

## 5.1 CapabilityService — méthode inexistante

### Constat

Les premiers exemples utilisaient :

```python
cap_svc.list_capabilities()
```

Or le service public expose :

```python
cap_svc.list()
```

### Impact

**Criticité : moyenne**

L'erreur provoquait directement :

```text
AttributeError:
'CapabilityService' object has no attribute 'list_capabilities'
```

### Correction

Tous les exemples utilisent désormais :

```python
capabilities = build_capability_service().list()
```

---

# 5.2 ConnectionTestResult — attributs incorrects

### Constat

Le script initial utilisait notamment :

```python
result.success
result.server_version
result.database
result.username
```

Le modèle réel est :

```python
ConnectionTestResult(
    engine,
    version,
    current_database,
    current_user,
    latency_ms,
)
```

### Impact

**Criticité : élevée**

Le scénario de connexion Python ne respectait pas le contrat public 0.3.0.

### Correction

Les exemples utilisent désormais :

```python
result.engine
result.version
result.current_database
result.current_user
result.latency_ms
```

---

# 5.3 ServerInfo — attributs incorrects

### Constat

Le script utilisait :

```python
server_info.database
server_info.username
```

Le modèle réel expose :

```python
server_info.current_database
server_info.current_user
```

### Impact

**Criticité : moyenne**

### Correction

Alignement complet sur `ServerInfo`.

---

# 5.4 TableInfo et QualifiedName

### Constat

Le script supposait que `TableInfo` exposait directement :

```python
table.schema
table.name
```

Or :

```python
TableInfo.name
```

est un objet :

```python
QualifiedName
```

contenant notamment :

```text
database
schema
name
```

### Impact

**Criticité : élevée**

Ce bug était latent tant que le schéma `public` ne retournait aucune table.

### Correction

Les exemples manipulent désormais :

```python
table.name
```

comme un `QualifiedName`, notamment lors de :

```python
catalog_svc.describe_table(table.name)
```

---

# 5.5 TableDescription — mauvaise structure supposée

### Constat

Le code initial attendait directement :

```python
description.name
description.schema
```

Le modèle réel contient :

```python
description.table
description.columns
description.constraints
```

### Correction

Le script exploite désormais :

```python
description.table.name
description.table.owner
description.columns
description.constraints
```

---

# 5.6 ViewInfo et IndexInfo

### Constat

Les vues et index étaient traités comme si leurs noms et propriétés étaient de simples chaînes.

En réalité :

- `ViewInfo.name` est un `QualifiedName` ;
- `IndexInfo.name` est un `QualifiedName` ;
- `IndexInfo.table` est également un `QualifiedName` ;
- l'algorithme d'index est exposé via `method`.

### Correction

Les exemples affichent désormais les objets réels sans reconstruire artificiellement leurs identifiants.

---

# 5.7 RoleDescription — structure incorrectement interprétée

### Constat

Le premier script accédait directement à :

```python
desc.name
desc.can_login
desc.is_superuser
desc.can_create_db
```

Le modèle réel est :

```python
RoleDescription(
    role=RoleInfo(...),
    member_of=(...),
    members=(...),
)
```

### Impact

**Criticité : élevée**

### Correction

Le parcours correct est désormais :

```python
description = security_svc.describe_role("postgres")
role = description.role

role.name
role.can_login
role.is_superuser
```

---

# 5.8 Accès directs — méthode et modèle incorrects

### Constat

Le script initial utilisait :

```python
security_svc.list_access(role="postgres")
```

Cette méthode n'existe pas.

La méthode publique est :

```python
security_svc.list_direct_access("postgres")
```

Le code supposait également des propriétés telles que :

```text
relation
access_types
```

alors que `DirectAccess` expose :

```text
principal
access_type
object
issuer
delegable
```

### Correction

Exemple corrigé :

```python
for access in security_svc.list_direct_access("postgres"):
    print(
        access.object.name,
        access.access_type.value,
        access.issuer,
        access.delegable,
    )
```

---

# 5.9 EffectiveAccess — source vs sources

### Constat

Le premier code supposait :

```python
access.source
```

Le modèle expose :

```python
access.sources
```

sous forme de tuple.

Un accès peut donc avoir plusieurs sources explicatives.

### Correction

Le traitement utilise maintenant :

```python
for source in access.sources:
    ...
```

Cette correction est importante car elle respecte la sémantique du modèle d'accès effectif.

---

# 5.10 OwnershipInfo

### Constat

L'exemple initial supposait des champs directs :

```text
schema
name
object_type
```

Le modèle réel est :

```python
OwnershipInfo(
    owner,
    object=DatabaseObjectRef(...),
)
```

### Correction

La lecture correcte utilise :

```python
ownership.object.name
ownership.object.object_type
```

Le filtre utilise maintenant :

```python
DatabaseObjectType.TABLE
```

et non la chaîne brute `"table"`.

---

# 5.11 SecurityMutationService — anciennes méthodes inexistantes

### Constat

Le script initial faisait référence à :

```python
execute_create_role(...)
execute_drop_role(...)
```

Ces méthodes ne font pas partie du service 0.3.0.

Il faisait également référence à :

```python
DropRoleCommand
```

qui n'existe pas dans le modèle actuel.

### Impact

**Criticité : élevée**

Le scénario de mutation Python ne pouvait pas fonctionner correctement.

### Correction

Le pipeline public réel est désormais utilisé :

```python
plan = mutation_svc.plan_create_role(command)

result = mutation_svc.create_role(
    command,
    MutationOptions(...),
    plan=plan,
)
```

Pour la suppression :

```python
drop_plan = mutation_svc.plan_drop_role(role_name)

result = mutation_svc.drop_role(
    role_name,
    MutationOptions(...),
    plan=drop_plan,
)
```

---

# 5.12 Commande CLI `connection list` inexistante

### Constat

Le notebook CLI utilisait :

```text
connection list
```

La version 0.3.0 expose seulement :

```text
connection test
```

### Correction

La commande a été supprimée du notebook et du récapitulatif des commandes.

---

# 5.13 Commande `capability` sans sous-commande

### Constat

Le notebook appelait :

```text
capability
```

Le groupe CLI est configuré avec :

```python
no_args_is_help = True
```

La commande d'inspection attendue est :

```text
capability list
```

### Correction

Tous les exemples utilisent désormais :

```text
capability list
```

---

# 6. Audit sécurité

## 6.1 Secret enregistré dans le notebook

### Constat

Le notebook CLI initial contenait une affectation directe du type :

```python
os.environ["PYDBADMIN_NATIVE_PASSWORD"] = "..."
```

### Risque

**Criticité : élevée**

Même lorsqu'il s'agit d'un mot de passe local de démonstration, un notebook versionné ne doit pas devenir un support de stockage de secrets.

Un notebook peut également conserver des valeurs dans ses outputs ou son historique d'exécution.

### Correction

Aucun mot de passe n'est désormais stocké dans les notebooks.

Les notebooks exigent une variable d'environnement préexistante :

```text
PYDBADMIN_NATIVE_PASSWORD
```

ou :

```text
PYDBADMIN_LOCAL_PASSWORD
```

---

# 6.2 Fallback implicite vers `postgres`

### Constat

Certaines cellules utilisaient un fallback du type :

```python
os.environ.get("...", "postgres")
```

### Risque

Le code pouvait fonctionner avec un credential implicite non visible dans le scénario.

### Correction

Le fallback a été supprimé.

L'absence de variable d'environnement provoque désormais une erreur explicite.

---

# 6.3 Création réelle d'un rôle SUPERUSER

### Constat

Le notebook CLI contenait un scénario créant réellement :

```text
demo_super
```

avec :

```text
--superuser
```

et `--confirm-target`.

### Risque

**Criticité : critique**

Même dans un environnement local, créer un rôle SUPERUSER uniquement pour illustrer un mécanisme de sécurité est inutilement risqué.

### Correction

Le scénario est maintenant limité à :

```text
--dry-run role create demo_super --superuser
```

Il permet de vérifier :

- le plan ;
- le niveau de risque ;
- le mécanisme de confirmation ;

sans créer réellement le rôle privilégié.

---

# 6.4 Mutations réelles des notebooks

### Correction structurelle

Les notebooks utilisent maintenant :

```python
RUN_MUTATIONS = False
```

par défaut.

Une mutation réelle nécessite donc une action explicite de l'utilisateur.

Avant toute mutation, les notebooks vérifient également :

```text
environment ∈ {development, testing}
read_only = false
```

Les environnements non compatibles sont refusés par le scénario d'expérimentation.

---

# 7. Audit des notebooks

## 7.1 Outputs persistés

### Constat initial

Les notebooks contenaient des outputs d'exécution et certaines erreurs précédentes.

Cela rendait les fichiers :

- plus lourds ;
- plus bruyants dans Git ;
- moins reproductibles ;
- susceptibles de contenir des informations locales.

### Correction

Les notebooks sont désormais versionnés avec :

```json
"execution_count": null,
"outputs": []
```

---

# 7.2 Dépendance au répertoire courant

### Constat

Le premier notebook utilisait :

```python
CONFIG_PATH = "../config.toml"
```

Ce chemin dépend du dossier à partir duquel Jupyter est lancé.

### Correction

Le notebook recherche maintenant `config.toml` dans :

1. le répertoire courant ;
2. son parent immédiat.

Cela permet de lancer Jupyter depuis :

```text
pydbadminkit/
```

ou :

```text
pydbadminkit/notebooks/
```

---

# 7.3 Dépendance à l'état du kernel

### Constat

Certaines cellules dépendaient indirectement de variables importées ou calculées précédemment.

### Correction

Le notebook a été restructuré pour rendre les dépendances plus explicites et réduire les effets d'état caché.

---

# 8. Nettoyage du dépôt

## 8.1 Notebooks dupliqués

Trois fichiers identiques avaient été ajoutés :

```text
notebooks/00 - Setup.ipynb
notebooks/00 - Setup - Copie.ipynb
notebooks/00 - Setup - Copie (2).ipynb
```

### Correction

Les deux copies ont été supprimées.

Le fichier canonique est :

```text
notebooks/00 - Setup.ipynb
```

---

# 8.2 Fichier de configuration dupliqué

Le fichier :

```text
examples/config copy.toml
```

était une copie accidentelle.

### Correction

Il a été supprimé.

Le fichier canonique est :

```text
examples/config.toml
```

---

# 8.3 Configuration d'exemple

`examples/config.toml` contient désormais les deux profils :

```text
local
local-native
```

Les secrets sont uniquement référencés via :

```text
PYDBADMIN_LOCAL_PASSWORD
PYDBADMIN_NATIVE_PASSWORD
```

---

# 8.4 Jupyter checkpoints

Ajout dans `.gitignore` :

```text
.ipynb_checkpoints/
```

afin d'éviter le versionnement automatique des artefacts Jupyter.

---

# 9. Évaluation de la modification Docker PostgreSQL 18

Le commit local avait modifié le montage du volume :

ancien :

```yaml
postgres_data:/var/lib/postgresql/data
```

nouveau :

```yaml
postgres_data:/var/lib/postgresql
```

Cette modification a été **conservée** dans le correctif.

Elle fait partie de l'adaptation locale réalisée pour l'image :

```text
postgres:18
```

et n'a pas été considérée comme un artefact accidentel du lot.

---

# 10. Artefacts d'expérimentation retenus

Après qualification, trois artefacts complémentaires sont conservés.

## 10.1 Script Python

```text
scripts/pydbadminkit_example.py
```

Objectif :

> montrer l'utilisation de PyDBAdminKit directement depuis l'API Python dans un scénario séquentiel complet.

Il couvre :

```text
Version
  ↓
Connection
  ↓
Capabilities
  ↓
Server
  ↓
Catalog
  ↓
Security
  ↓
Mutation dry-run
  ↓
Mutation contrôlée
  ↓
Cleanup
```

---

## 10.2 Notebook Python API

```text
notebooks/00 - Setup.ipynb
```

Objectif :

> servir de laboratoire interactif pour explorer progressivement les objets du domaine et les services applicatifs.

Il est particulièrement adapté au développement et à l'apprentissage du framework.

---

## 10.3 Notebook CLI

```text
notebooks/pydbadminkit_demo.ipynb
```

Objectif :

> tester la CLI depuis Jupyter et observer simultanément les sorties humaines et machine.

Il couvre notamment :

```text
table
json
yaml
```

ainsi que les workflows :

```text
Foundation
Object Explorer
Security
Dry-run
Mutations opt-in
```

---

# 11. Validation après correction

Le correctif a fait l'objet des validations suivantes.

## 11.1 Compilation statique

Le script Python a été vérifié syntaxiquement.

Les cellules Python des deux notebooks ont également été compilées individuellement afin de détecter les erreurs syntaxiques indépendamment de l'état du kernel.

---

## 11.2 Vérification des contrats obsolètes

Les fichiers corrigés ont été relus depuis le commit final afin de vérifier l'absence des anciens patterns problématiques.

Résultat :

```text
execute_create_role        absent
DropRoleCommand            absent
list_access(role=...)      absent
connection list            absent
mot de passe écrit         absent
```

---

## 11.3 Nettoyage notebook

Les notebooks finaux sont enregistrés sans outputs ni compteurs d'exécution.

---

## 11.4 État Git

Le correctif est contenu dans :

```text
a19ebfcceb523325b1bd12969fe82ee2dfc6fdb3
```

message :

```text
fix: qualify local 0.3.0 examples and notebooks
```

Ce commit est directement descendant du commit local initial :

```text
b0bf8d1
    ↓
a19ebfc
```

---

# 12. Limites de la validation

L'audit a validé :

- les contrats Python ;
- les structures du domaine ;
- les commandes CLI ;
- les chemins de code visibles ;
- la sécurité des exemples ;
- la structure des notebooks ;
- la cohérence du dépôt ;
- la syntaxe Python.

En revanche, le correctif n'a pas été exécuté depuis cet audit directement contre la base PostgreSQL locale ayant servi aux premiers tests.

La validation finale reste donc à compléter par une exécution réelle depuis le poste de développement.

Les tests recommandés sont :

```powershell
python scripts/pydbadminkit_example.py
```

puis l'exécution progressive :

```text
notebooks/00 - Setup.ipynb
```

et :

```text
notebooks/pydbadminkit_demo.ipynb
```

avec :

```python
RUN_MUTATIONS = False
```

dans un premier temps.

---

# 13. Risque résiduel concernant l'historique Git

Le correctif supprime les secrets et outputs du **HEAD actuel**, mais le commit :

```text
b0bf8d1
```

reste présent dans l'historique Git.

Il contient donc toujours l'ancien contenu des notebooks.

Si les valeurs utilisées dans ce commit correspondent uniquement à des credentials locaux jetables, le risque reste limité.

Si un secret réel ou réutilisé a été exposé, la mesure correcte est :

1. rotation du secret ;
2. puis, uniquement si nécessaire, réécriture de l'historique Git.

La rotation du secret reste prioritaire sur la réécriture d'historique.

---

# 14. Matrice de synthèse

| Axe | Avant audit | Après correction |
|---|---|---|
| Contrats Python | Plusieurs incompatibilités | Alignés 0.3.0 |
| CLI | Commandes invalides présentes | Alignée avec Typer |
| Connection | Modèle mal interprété | Conforme |
| Catalog | Bugs latents sur objets réels | Conforme |
| Security read-only | Méthodes/champs incorrects | Conforme |
| Security mutations | Ancienne API | Pipeline actuel |
| Secrets notebooks | Valeurs enregistrées | Variables d'environnement |
| SUPERUSER demo | Création réelle possible | Dry-run uniquement |
| Mutations notebook | Actives dans le scénario | Opt-in |
| Outputs notebook | Persistés | Nettoyés |
| Config path | Fragile | Résolution robuste |
| Doublons notebooks | 3 copies | 1 fichier canonique |
| Config exemple | Copie accidentelle | Canonique |
| Jupyter checkpoints | Non ignorés | Ignorés |
| Documentation | Étendue | Conservée et référencée |
| Docker PostgreSQL 18 | Adaptation locale | Conservée |

---

# 15. Décision de qualification

## Statut

> **QUALIFIÉ AVEC CORRECTIONS**

Les expérimentations locales de PyDBAdminKit 0.3.0 peuvent désormais être conservées dans le dépôt comme exemples de référence pour la version actuelle.

Le lot fournit trois niveaux complémentaires d'utilisation :

```text
CLI
 │
 ├── notebook CLI
 │
Python API
 │
 ├── notebook interactif
 │
 └── script end-to-end
```

Cette organisation est cohérente avec le positionnement du framework :

> **CLI-first, Python-first database administration framework.**

---

# 16. Recommandations pour la suite

Pour la prochaine ligne de développement, il est recommandé de conserver ces artefacts comme **tests exploratoires manuels** en parallèle des tests automatisés.

Lors de l'arrivée de `0.4.x — Runtime Administration`, les notebooks pourront être étendus avec :

```text
sessions
queries
transactions
locks
blocking chains
cancel
terminate
```

La même discipline devra être conservée :

1. vérifier le contrat public réel avant d'écrire les exemples ;
2. commencer par les opérations read-only ;
3. privilégier le dry-run pour toute mutation ;
4. rendre les mutations réelles explicitement opt-in ;
5. ne jamais stocker de secret dans un notebook ;
6. versionner les notebooks sans outputs ;
7. supprimer les copies temporaires avant commit ;
8. utiliser les notebooks comme validation exploratoire, sans remplacer les tests unitaires et d'intégration.

---

# 17. Conclusion

Le premier test local de PyDBAdminKit 0.3.0 a rempli son rôle : il a permis de confronter l'architecture théorique du framework à une utilisation réelle.

L'audit a révélé plusieurs écarts entre le code d'exemple et les contrats effectifs, en particulier autour des objets du domaine et du service de sécurité.

Ces écarts ont été corrigés avant de poursuivre la roadmap.

Le principal résultat de cette phase n'est donc pas uniquement que :

> **« le framework démarre en local »**

mais plutôt que :

> **« la surface publique de PyDBAdminKit 0.3.0 peut maintenant être explorée localement à partir d'exemples qui respectent réellement ses contrats, ses modèles et ses mécanismes de sécurité. »**

Cette qualification constitue une base saine avant l'ouverture de la ligne :

```text
0.4.x — Runtime Administration
```
