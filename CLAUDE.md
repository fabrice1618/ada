# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Plateforme étudiante multi-services déployée via Docker Compose. L'architecture est documentée en détail dans `infrastructure.md`.

## Architecture

Deux conteneurs, tenant du reverse proxy d'argos (TLS, routage, logs) :

- **Auth (Django + Gunicorn)**, conteneur `ada-auth`, port 8000 — connexion, classes, devoirs (dépôt de fichier), endpoint `/auth/verify/`
- **MySQL 8.0**, conteneur `ada-mysql` — réseau `backend` uniquement

`ada-auth` rejoint `reverse-proxy-net`. Les fichiers déposés sont dans le volume `uploads` (`/uploads`), servis par Django après contrôle d'identité, jamais en statique. Quiz et pages de cours ne sont pas dans ce compose.

**Sessions** : Django, table `django_session` dans MySQL. Un devoir a un type de rendu (un fichier, plusieurs fichiers, lien GitHub) et un mode (individuel ou groupe), verrouillés dès le premier rendu. Un rendu (`Soumission`) appartient à un étudiant ou à un groupe ; ses fichiers sont des `FichierRendu`. Les groupes sont propres à un devoir, créés et rejoints par les étudiants (un groupe par étudiant et par devoir, taille maximale fixée par le professeur). Tout se modifie jusqu'à la date limite.

## Commandes

```bash
# Lancer (argos doit déjà tourner : reverse-proxy-net + logs_rsyslog)
./start.sh

# Initialiser la base
docker compose exec auth python manage.py migrate
docker compose exec auth python manage.py createsuperuser

# Tests du dépôt de fichiers (SQLite, sans Docker)
cd auth && python manage.py test core --settings=config.settings_test

# Archiver puis supprimer une classe (core/archivage.py)
docker compose exec -T auth python manage.py archiver_classe 3 > ada-classe-3.zip
docker compose exec -T auth python manage.py archiver_classe 3 --supprimer - < ada-classe-3.zip

# Logs applicatifs (stdout : syslog d'argos, tag ada)
tail -f logs/auth/app.log

# Rebuild d'un service après modification
docker compose build <service>
docker compose up -d <service>
```

## Structure

`auth/` est le projet Django :

- `config/` — settings, urls, wsgi
- `core/` — modèles, connexion, import de classes, dépôt de fichiers (`fichiers.py`, `views_devoirs.py`)
- `templates/` — pages

Le dépôt écrit sous `UPLOAD_ROOT` avec un nom généré : `{devoir_id}/{etudiant_id}.ext` (groupe : `g{groupe_id}`), et `{devoir_id}/{etudiant_id}/{uuid}.ext` pour un rendu en plusieurs fichiers. L'extension vient de la whitelist, la taille de `MAX_UPLOAD_SIZE_MB`, le nombre de fichiers de `MAX_UPLOAD_FILES`.

## Conventions

- Langue du code et des modèles : **français**
- Configuration via `.env`
- Logs : `[YYYY-MM-DD HH:MM:SS] LEVEL message` sur stdout (syslog, tag `ada`) et `logs/auth/app.log`
