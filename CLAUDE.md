# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Plateforme étudiante multi-services déployée via Docker Compose. L'architecture est documentée en détail dans `infrastructure.md`.

## Architecture

6 containers Docker orchestrés par Docker Compose :

- **Traefik** — reverse proxy, HTTPS (Let's Encrypt), routage, Forward Auth
- **Auth (Django + Gunicorn)** — authentification, gestion utilisateurs/classes/créneaux, interface admin, endpoint `/auth/verify/`
- **Devoirs (Flask + Gunicorn)** — dépôt de fichiers et liens GitHub par les étudiants
- **Quiz (Flask + Gunicorn)** — passation de quiz avec timer serveur et anti-triche
- **Nginx** — pages statiques des cours, protégées par Forward Auth via Auth
- **MySQL 8.0** — base unique partagée par tous les services Python

**Réseaux Docker** : `frontend` (Traefik ↔ services web) et `backend` (MySQL ↔ services Python). MySQL n'est pas exposé sur le frontend, Traefik n'est pas sur le backend.

**Sessions** : gérées par Django, stockées dans MySQL (`django_session`). Les services Flask lisent directement cette table pour vérifier l'identité des utilisateurs.

## Commandes

```bash
# Lancer la stack
docker compose up -d

# Initialiser la base
docker compose exec auth python manage.py migrate
docker compose exec auth python manage.py createsuperuser

# Logs
tail -f logs/traefik/access.log
tail -f logs/auth/app.log
grep "403" logs/*/app.log

# Rebuild d'un service après modification
docker compose build <service>
docker compose up -d <service>
```

## Structure des services

Chaque service Flask (`devoirs/`, `quiz/`) suit la même structure :
- `app.py` — point d'entrée Flask
- `models.py` — modèles de données
- `auth_check.py` — lecture de la session Django dans MySQL
- `slot_check.py` — vérification des créneaux horaires
- `templates/` — templates Jinja2

Le service Auth (`auth/`) est un projet Django classique :
- `config/` — settings, urls, wsgi
- `core/` — models (User, Classe, Créneau), views (login, logout, verify), admin
- `templates/` — login, forbidden

## Conventions

- Langue du code et des modèles : **français** (noms de tables, champs, variables)
- Configuration via variables d'environnement (fichier `.env`)
- Logs au format : `[YYYY-MM-DD HH:MM:SS] LEVEL user=ID class=CLASSE ip=IP METHOD /path STATUS [message]`
- Protection des uploads : whitelist d'extensions + taille maximale
- Toute ressource (quiz, devoir, page) est soumise à une vérification de créneau horaire en BDD
