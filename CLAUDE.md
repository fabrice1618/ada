# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Plateforme étudiante Ada déployée via Docker Compose. L'architecture est documentée en détail dans `infrastructure.md`.

## Architecture

Un conteneur, tenant du reverse proxy d'argos (TLS, routage, logs) :

- **Ada (Flask + Gunicorn)**, conteneur `ada`, port 8000, réseau `reverse-proxy-net` — connexion, classes, devoirs (dépôt de fichiers), pages de cours sous `/cours/`

Toutes les données sont dans le volume `data` (`/data`), une base SQLite par classe :

```
/data/ada.db                    comptes, classes, inscriptions, sessions
/data/classes/<id>/classe.db    créneaux, devoirs, groupes, rendus, quiz de la classe
/data/classes/<id>/fichiers/    fichiers rendus de la classe
/data/cours/                    pages de cours
/data/sauvegardes/<date>-<motif>/   sauvegardes complètes (bases + fichiers)
/data/exports/                  archives zip des classes
```

Les fichiers rendus et les cours sont servis par Flask après contrôle d'identité, jamais en statique. `/cours/` : personnel toujours, étudiant si un créneau `page` ouvert de l'une de ses classes couvre le chemin (un créneau couvre son `chemin_page` et tout ce qui est dessous) ; non connecté → page de connexion. Le quiz n'existe qu'en tables (pas d'interface).

Les identifiants d'utilisateurs de `ada.db` sont référencés dans les bases de classe sans clé étrangère (deux fichiers SQLite) : `AUTOINCREMENT`, jamais réattribués. Dates en UTC (texte ISO, `ada/temps.py`), saisies et affichées à l'heure de Paris.

**Sessions** : table `sessions` de `ada.db` (sha256 du jeton gardé dans le cookie signé `ada`), révocables : déconnexion, changement de mot de passe (ferme les autres sessions), compte désactivé ou supprimé. CSRF : jeton de session, champ `csrf` de chaque formulaire POST. Les mots de passe Django (`pbkdf2_sha256$`) repris de MySQL sont acceptés puis rehachés à la connexion.

Un devoir a un type de rendu (un fichier, plusieurs fichiers, lien GitHub) et un mode (individuel ou groupe), verrouillés dès le premier rendu. Un rendu (`soumissions`) appartient à un étudiant ou à un groupe ; ses fichiers sont dans `fichiers_rendus`. Les groupes sont propres à un devoir, créés et rejoints par les étudiants (un groupe par étudiant et par devoir, taille maximale fixée par le professeur). Tout se modifie jusqu'à la date limite.

**Schéma et sauvegardes** : scripts `app/ada/schema/<commun|classe>/NNN_*.sql`, numéro dans `PRAGMA user_version`. `flask migrer` (lancé au démarrage du conteneur) fait une sauvegarde complète avant d'appliquer un script en attente, et refuse une base plus récente que le code. Une nouvelle classe est créée directement au dernier schéma.

## Commandes

```bash
# Lancer (argos doit déjà tourner : reverse-proxy-net + logs_rsyslog)
./start.sh

# Premier administrateur (le volume est initialisé au démarrage par flask migrer)
docker compose exec ada flask creer-admin

# Tests (sans Docker, dossier de données temporaire)
cd app && python3 -m unittest discover -s tests -t .

# Pages de cours
docker compose cp content/. ada:/data/cours/

# Sauvegarde complète, liste, restauration (service arrêté)
docker compose exec ada flask sauvegarder --motif avant-rentree
docker compose exec ada flask sauvegardes
docker compose stop ada && docker compose run --rm ada flask restaurer <nom> && docker compose start ada

# Archiver puis supprimer une classe (ada/archivage.py)
docker compose exec -T ada flask archiver-classe 3 --sortie - > ada-classe-3.zip
docker compose exec -T ada flask archiver-classe 3 --supprimer - < ada-classe-3.zip

# Migration depuis la version Django/MySQL (une fois) : migration/1-sauvegarder-mysql.sh puis 2-migrer.sh

# Logs : page Logs du dashboard argos (conteneur ada), ou
docker exec logs_rsyslog python3 -c "import sqlite3; c=sqlite3.connect('file:/logs/logs.db?mode=ro',uri=True); [print(*r) for r in c.execute(\"select received_at, container, msg from system_logs where container like 'ada%' order by id desc limit 50\")]"

# Rebuild après modification
docker compose build ada
docker compose up -d ada
```

## Structure

`app/` est l'image du service `ada`, `app/ada/` le paquet Flask (SQL direct avec `sqlite3`, sans ORM) :

- `__init__.py` — `create_app`, filtres Jinja, CSRF, erreurs ; `config.py` — lecture de `.env`
- `db.py` — arborescence de `/data`, connexions (`commun()`, `classe(id)`, `transaction()`), schéma et `migrer()`
- `modeles.py` — objets lus en base et requêtes partagées ; `comptes.py` — mots de passe, sessions, décorateurs d'accès
- `vues/` — `connexion`, `cours`, `devoirs` (étudiant), `enseignant` (`/admin/devoirs/`), `admin` (classes, import, archivage)
- `fichiers.py` (dépôt), `archivage.py`, `sauvegardes.py`, `import_mysql.py`, `commandes.py` (CLI `flask …`)
- `templates/` — pages ; `schema/` — scripts SQL
- `app/tests/` — unittest

Le dépôt écrit sous `/data/classes/<classe>/fichiers/` avec un nom généré : `{devoir_id}/{etudiant_id}.ext` (groupe : `g{groupe_id}`), et `{devoir_id}/{etudiant_id}/{uuid}.ext` pour un rendu en plusieurs fichiers. Un fichier n'est jamais réécrit sur place (`os.replace`) : les sauvegardes le recopient en lien physique. L'extension vient de la whitelist, la taille de `MAX_UPLOAD_SIZE_MB`, le nombre de fichiers de `MAX_UPLOAD_FILES`. Les URL des devoirs portent la classe : `/devoirs/<classe>/<devoir>/`.

## Conventions

- Langue du code et des modèles : **français**
- Configuration via `.env`
- Logs : `[YYYY-MM-DD HH:MM:SS] LEVEL message` sur stdout uniquement (logger `ada`), envoyé par le driver syslog à argos (tag `ada`). Rien n'est écrit dans `logs/`
- Changement de schéma : nouveau script `NNN_*.sql` dans `schema/commun/` ou `schema/classe/`, jamais modifier un script déjà livré
