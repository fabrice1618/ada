

# Architecture Plateforme Étudiante

Le compose actuel : `ada-auth` + `ada-cours` (nginx, pages de cours) + `ada-mysql`.
TLS, nom de domaine et syslog viennent d'argos. Les services Flask
(Devoirs, Quiz) décrits plus bas ne sont pas déployés : les devoirs sont dans Django.

## Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────┐
│                        INTERNET                               │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS (443)
                            ▼
                   ┌─────────────────┐
                   │      ARGOS      │
                   │  Reverse Proxy  │
                   │       TLS       │
                   │  Access logs    │
                   └───┬───┬───┬─────┘
                       │   │   │
            ┌──────────┘   │   └──────────┐
            ▼              ▼              ▼
   ┌──────────────┐ ┌───────────┐ ┌──────────────┐
   │     AUTH     │ │  DEVOIRS  │ │     QUIZ     │
   │    Django    │ │   Flask   │ │    Flask     │
   └──────┬───────┘ └─────┬─────┘ └──────┬───────┘
          │               │              │
          │    ┌──────────┐│              │
          │    │  NGINX   ││              │
          │    │  Pages   ││              │
          │    │ statiques││              │
          │    └────┬─────┘│              │
          │         │      │              │
          ▼         ▼      ▼              ▼
   ┌──────────────────────────────────────────┐
   │                MySQL 8.0                  │
   └──────────────────────────────────────────┘
```

---

## Containers

### Reverse proxy — argos (hors de ce dépôt)

| Élément         | Détail                                              |
|-----------------|-----------------------------------------------------|
| Fourni par      | argos (réseau `reverse-proxy-net`)                  |
| Rôle            | Reverse proxy, terminaison HTTPS, routage, logs     |
| Logs            | Syslog d'argos                                      |
| Forward Auth    | Délègue la vérification au service Auth pour Nginx  |

**Routage :**

| Chemin URL       | Container cible |
|------------------|-----------------|
| `/auth/*`        | Auth (Django)   |
| `/devoirs/*`     | Devoirs (Flask) |
| `/quiz/*`        | Quiz (Flask)    |
| `/cours/*`       | Nginx           |
| `/admin/*`       | Auth (Django)   |

---

### Container 1 — Auth (Django)

| Élément         | Détail                                              |
|-----------------|-----------------------------------------------------|
| Framework       | Django + Gunicorn                                   |
| Base de données | MySQL (sessions stockées en BDD)                    |
| Rôle            | Authentification, gestion des utilisateurs          |
|                 | Vérification des permissions et créneaux            |
|                 | Endpoint `/auth/verify/` pour le Forward Auth Nginx |
|                 | Interface admin Django                              |
| Logs            | stdout -> syslog d'argos (tag `ada`)                |

**Responsabilités :**

- Login / Logout
- Gestion des utilisateurs, classes, rôles
- Gestion des créneaux horaires par ressource et par classe
- Sessions Django classiques stockées dans MySQL
- Endpoint `/auth/verify/` appelé par le reverse proxy pour protéger Nginx
- Interface `/admin/` pour gérer utilisateurs, classes, créneaux

---

### Container 2 — Devoirs (Flask)

| Élément         | Détail                                              |
|-----------------|-----------------------------------------------------|
| Framework       | Flask + Gunicorn                                    |
| Base de données | MySQL                                               |
| Rôle            | Dépôt de fichiers et de liens GitHub                |
| Stockage        | Volume Docker `uploads/`                            |
| Logs            | stdout -> syslog d'argos                            |

**Responsabilités :**

- Lister les devoirs assignés à la classe de l'étudiant
- Formulaire de dépôt (fichier uploadé ou lien GitHub)
- Vérification de la date limite
- Whitelist des extensions autorisées, taille maximale
- Historique des soumissions par étudiant

**Vérification de l'identité :**

- Le service Auth transmet via headers HTTP (injectés par le reverse proxy ou par cookie de session partagé) l'identité de l'utilisateur
- Le service Devoirs interroge MySQL pour vérifier la session

---

### Container 3 — Quiz (Flask)

| Élément         | Détail                                              |
|-----------------|-----------------------------------------------------|
| Framework       | Flask + Gunicorn                                    |
| Base de données | MySQL                                               |
| Rôle            | Passation de quiz et tests                          |
| Logs            | stdout -> syslog d'argos                            |

**Responsabilités :**

- Afficher les quiz disponibles pour la classe de l'étudiant
- Gérer le timer côté serveur (anti-triche)
- Enregistrer les réponses et calculer le score
- Limiter à une seule tentative si configuré ainsi
- Afficher les résultats selon la configuration de l'enseignant

---

### Container 4 — Nginx (Pages statiques)

| Élément         | Détail                                              |
|-----------------|-----------------------------------------------------|
| Image           | `nginx:alpine`                                      |
| Rôle            | Servir les supports de cours, PDF, pages HTML       |
| Contenu         | Volume monté depuis `content/`                      |
| Protection      | Forward Auth via argos → appel à `/auth/verify/`    |
| Logs            | Access log du reverse proxy d'argos                 |

**Fonctionnement de la protection :**

```
Étudiant → /cours/math-101/chapitre1.html
    │
    ▼
Argos (auth_request) → Django /auth/verify/
    │   X-Original-URI: /cours/math-101/chapitre1.html
    │                         │
    │                         ├── Session valide ?
    │                         ├── Classe autorisée pour math-101 ?
    │                         ├── Créneau horaire valide ?
    │                         │
    │                         └── Réponse 200, 401 ou 403
    │
    ├── 200 → Argos transmet à Nginx → page servie
    ├── 401 → Argos redirige vers /auth/login/?next=…
    └── 403 → Argos renvoie l'erreur au client
```

---

### Container 5 — MySQL

| Élément         | Détail                                              |
|-----------------|-----------------------------------------------------|
| Image           | `mysql:8.0`                                         |
| Rôle            | Base de données unique partagée                     |
| Persistance     | Volume Docker `db_data`                             |
| Réseau          | Backend uniquement (non exposé)                     |

---

## Modèle de données (MySQL)

```
┌────────────────┐     ┌────────────────┐
│     users      │     │    classes     │
├────────────────┤     ├────────────────┤
│ id             │     │ id             │
│ email          │ N:M │ nom            │
│ password_hash  │◄───►│ année          │
│ nom_complet    │     └───────┬────────┘
│ role           │             │
│ (étudiant,     │             │ 1:N
│  enseignant,   │             ▼
│  admin)        │     ┌────────────────┐
└───────┬────────┘     │   créneaux     │
        │              ├────────────────┤
        │              │ id             │
        │              │ classe_id      │
        │              │ type_ressource │
        │              │  (quiz/devoir/ │
        │              │   page)        │
        │              │ ressource_id   │
        │              │ chemin_page    │
        │              │ ouverture      │
        │              │ fermeture      │
        │              └────────────────┘
        │
        │ 1:N
        ├────►  django_session    (table native Django)
        │
        ├────►  devoirs
        │       ├── id
        │       ├── classe_id
        │       ├── titre
        │       ├── description
        │       ├── date_limite
        │       └── créé_par (user_id)
        │
        ├────►  soumissions
        │       ├── id
        │       ├── devoir_id
        │       ├── étudiant_id
        │       ├── type (fichier / github)
        │       ├── chemin_fichier
        │       ├── lien_github
        │       └── date_soumission
        │
        ├────►  quiz
        │       ├── id
        │       ├── classe_id
        │       ├── titre
        │       ├── durée_max_minutes
        │       ├── tentative_unique (bool)
        │       └── créé_par (user_id)
        │
        ├────►  questions
        │       ├── id
        │       ├── quiz_id
        │       ├── énoncé
        │       ├── choix (JSON)
        │       ├── réponse_correcte
        │       └── points
        │
        └────►  tentatives
                ├── id
                ├── quiz_id
                ├── étudiant_id
                ├── réponses (JSON)
                ├── score
                ├── début
                └── fin
```

---

## Partage des sessions entre containers

Les services Flask (Devoirs, Quiz) doivent vérifier que l'utilisateur est connecté alors que la session est gérée par Django.

**Méthode retenue : lecture directe de la table `django_session` dans MySQL.**

```
Requête vers /devoirs/
    │
    ▼
Flask lit le cookie "sessionid"
    │
    ▼
Flask interroge MySQL : SELECT * FROM django_session WHERE session_key = ?
    │
    ├── Session trouvée et non expirée
    │     → Décoder session_data (format Django documenté)
    │     → Extraire user_id, classe, rôle
    │     → Vérifier le créneau horaire en BDD
    │     → Autoriser ou refuser
    │
    └── Session absente ou expirée
          → Rediriger vers /auth/login/
```

**Alternative possible :** chaque requête vers Flask passe d'abord par un appel interne HTTP à Django `/auth/verify/` (même principe que le Forward Auth Nginx). Plus propre mais ajoute une requête réseau interne.

---

## Gestion des logs

Aucun fichier de log dans ce dépôt : chaque conteneur écrit sur stdout, et le driver
Docker `syslog` envoie ces lignes au rsyslog d'argos (`udp://127.0.0.1:514`), qui les range
dans `logs.db`. Un tag par conteneur : `ada` (auth), `ada-cours`, `ada-mysql`. Les requêtes
HTTP sont journalisées par le reverse proxy d'argos (`nginx-proxy`).

**Format recommandé (commun à tous les services) :**

```
[2025-01-15 14:32:01] INFO user=234 class=INFO-201 ip=192.168.1.42 GET /quiz/7 200
[2025-01-15 14:32:05] WARN user=234 class=INFO-201 ip=192.168.1.42 GET /quiz/8 403 créneau fermé
[2025-01-15 14:33:12] INFO user=234 class=INFO-201 ip=192.168.1.42 POST /devoirs/3/soumettre 201
```

**Consultation :**

- Page Logs du dashboard argos (filtre par conteneur)
- Requête en lecture seule sur `logs.db` dans `logs_rsyslog`

---

## Réseaux Docker

```
┌─────────────────────────────────────────────┐
│  Réseau "frontend"                          │
│                                             │
│  Argos   ◄──► Django (Auth)                 │
│          ◄──► Flask  (Devoirs)              │
│          ◄──► Flask  (Quiz)                 │
│          ◄──► Nginx  (Pages)                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Réseau "backend"                           │
│                                             │
│  MySQL ◄──► Django (Auth)                   │
│        ◄──► Flask  (Devoirs)                │
│        ◄──► Flask  (Quiz)                   │
└─────────────────────────────────────────────┘

MySQL n'est PAS sur le réseau frontend.
Argos n'est PAS sur le réseau backend.
```

---

## Volumes Docker

| Volume          | Utilisé par          | Contenu                          |
|-----------------|----------------------|----------------------------------|
| `db_data`       | MySQL                | Données persistantes             |
| `uploads`       | Devoirs (Flask)      | Fichiers déposés par étudiants   |
| `content`       | Nginx                | Pages statiques des cours        |

---

## Arborescence du projet

```
plateforme/
│
├── docker-compose.yml
├── .env
│
├── auth/
│   ├── Dockerfile
│   ├── requirements.txt       (django, mysqlclient, gunicorn)
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── core/
│   │   ├── models.py          (User, Classe, Créneau)
│   │   ├── views.py           (login, logout, verify)
│   │   ├── urls.py
│   │   └── admin.py
│   └── templates/
│       ├── login.html
│       └── forbidden.html
│
├── devoirs/
│   ├── Dockerfile
│   ├── requirements.txt       (flask, mysqlclient, gunicorn)
│   ├── app.py
│   ├── models.py              (Devoir, Soumission)
│   ├── auth_check.py          (lecture session Django en BDD)
│   ├── slot_check.py          (vérification créneau)
│   └── templates/
│       ├── liste_devoirs.html
│       └── soumettre.html
│
├── quiz/
│   ├── Dockerfile
│   ├── requirements.txt       (flask, mysqlclient, gunicorn)
│   ├── app.py
│   ├── models.py              (Quiz, Question, Tentative)
│   ├── auth_check.py          (lecture session Django en BDD)
│   ├── slot_check.py          (vérification créneau)
│   └── templates/
│       ├── liste_quiz.html
│       ├── passer_quiz.html
│       └── resultats.html
│
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
│
├── content/                   (pages statiques cours)
│   ├── math-101/
│   │   ├── index.html
│   │   └── chapitre1.html
│   └── info-201/
│       └── index.html
│
└── uploads/                   (fichiers déposés)
```

---

## Sécurité

| Risque                 | Protection                                    |
|------------------------|-----------------------------------------------|
| Interception réseau    | HTTPS obligatoire via le reverse proxy argos  |
| Mots de passe          | Hashés par Django (PBKDF2 par défaut)         |
| Injection SQL          | ORM Django + paramétrage MySQL côté Flask     |
| Upload malveillant     | Whitelist extensions + taille maximale         |
| Accès BDD depuis web   | MySQL sur réseau backend uniquement           |
| Secrets dans le code   | Variables d'environnement via `.env`          |
| Accès hors créneau     | Vérification en BDD à chaque requête          |
| Triche quiz            | Timer serveur + tentative unique              |

---

## Déploiement

```bash
# 1. Configurer l'environnement
cp .env.example .env
# Éditer .env : MYSQL_ROOT_PASSWORD, DJANGO_SECRET_KEY, DOMAIN

# 2. Lancer la stack
docker compose up -d

# 3. Initialiser la base
docker compose exec auth python manage.py migrate
docker compose exec auth python manage.py createsuperuser

# 4. Configurer via l'admin Django
# https://domaine.fr/admin/
# → Créer les classes
# → Créer les utilisateurs étudiants
# → Définir les créneaux horaires

# 5. Déposer les pages statiques
# Copier les fichiers HTML/PDF dans content/

# 6. Consulter les logs : page Logs du dashboard argos
```

---

## Résumé

| Élément              | Choix retenu                    |
|----------------------|---------------------------------|
| Containers           | 5 (Auth, Devoirs, Quiz, Nginx, MySQL) |
| Frameworks Python    | Django (auth) + Flask (devoirs, quiz) |
| Base de données      | MySQL 8.0 unique partagée       |
| Sessions             | Django sessions en MySQL        |
| Cache                | Aucun (pas de Redis)            |
| Logs                 | stdout -> syslog d'argos        |
| HTTPS                | Reverse proxy d'argos           |
| Pages statiques      | Nginx protégé par Forward Auth  |
| Permissions          | Vérification en BDD (classe + créneau) |