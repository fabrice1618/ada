# Architecture Ada

Un conteneur `ada` (Flask + Gunicorn) et un volume `data`. TLS, nom de domaine et syslog
viennent d'argos. Ada réunit la connexion, les classes, les devoirs et les pages de cours ;
les fonctions à venir (quiz…) s'y ajoutent comme de nouvelles vues et de nouvelles tables.

## Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS (443)
                            ▼
                   ┌─────────────────┐
                   │      ARGOS      │
                   │  Reverse Proxy  │
                   │       TLS       │
                   │  Access logs    │
                   └────────┬────────┘
                            │ HTTP, tout le domaine
                            ▼
                   ┌─────────────────┐
                   │       ADA       │
                   │ Flask, gunicorn │
                   │ /auth/ /admin/  │
                   │ /devoirs/       │
                   │ /cours/         │
                   └────────┬────────┘
                            │
                            ▼
   ┌──────────────────────────────────────────────────┐
   │ volume data (/data)                              │
   │   ada.db                 base commune (SQLite)   │
   │   classes/<id>/classe.db une base par classe     │
   │   classes/<id>/fichiers/ rendus de la classe     │
   │   cours/                 pages de cours          │
   │   sauvegardes/  exports/                         │
   └──────────────────────────────────────────────────┘
```

---

## Reverse proxy — argos (hors de ce dépôt)

| Élément         | Détail                                              |
|-----------------|-----------------------------------------------------|
| Fourni par      | argos (réseau `reverse-proxy-net`)                  |
| Rôle            | Reverse proxy, terminaison HTTPS, logs d'accès      |
| Logs            | Syslog d'argos                                      |
| Routage         | `ada.mips.science`, `ada.localhost` → `ada:8000`, `body_size=20m` |

Plus d'`auth_request` ni de fragment `sites-extra/` : ada contrôle lui-même l'accès à `/cours/`.
Ada lit le schéma, l'hôte et l'IP du client dans les en-têtes `X-Forwarded-*` (ProxyFix).

---

## Conteneur ada

| Élément         | Détail                                              |
|-----------------|-----------------------------------------------------|
| Framework       | Flask + Gunicorn (3 workers), SQL direct (`sqlite3`) |
| Données         | Volume `data` monté sur `/data`                      |
| Démarrage       | `flask migrer` (création ou mise à jour du schéma, sauvegarde avant), puis gunicorn |
| Utilisateur     | `ada` (uid 1000), pas root                           |
| Logs            | stdout → syslog d'argos (tag `ada`)                  |

**Routes :**

| Chemin                    | Rôle                                              |
|---------------------------|---------------------------------------------------|
| `/auth/login/`, `/auth/logout/`, `/auth/profil/` | Connexion, déconnexion, mot de passe |
| `/admin/`                 | Import des classes (xlsx), page d'une classe, archivage et suppression (admin) |
| `/admin/devoirs/`         | Création des devoirs, suivi des rendus, téléchargements (enseignant, admin) |
| `/devoirs/`               | Devoirs de l'étudiant, rendu, groupes : `/devoirs/<classe>/<devoir>/` |
| `/cours/`                 | Pages de `/data/cours/`, après contrôle           |

**Accès aux pages de cours :**

```
Étudiant → /cours/math-101/chapitre1.html
    │
    ▼
ada : session valide ?
    ├── non → 302 /auth/login/?next=/cours/math-101/chapitre1.html
    │
    ├── enseignant ou admin → page servie
    │
    └── étudiant : chemin normalisé (sans .., sans //), puis pour chacune de ses classes,
        créneau « page » ouvert dont chemin_page couvre le chemin ?
            ├── oui → page servie (index.html pour un dossier)
            └── non → 403
```

Un créneau sur `/cours/math-101/` (ou `/cours/math-101`) couvre tout le dossier, pas
`/cours/math-1010/`.

---

## Données

### Volume `data`

```
/data/
├── ada.db                      base commune
├── classes/
│   └── <id>/
│       ├── classe.db           base de la classe
│       └── fichiers/
│           └── <devoir>/<étudiant>.ext, g<groupe>.ext, <étudiant>/<uuid>.ext
├── cours/                      pages servies sous /cours/
├── sauvegardes/
│   └── <AAAAMMJJ-HHMMSS>-<motif>/
│       ├── MANIFESTE.json
│       ├── ada.db
│       ├── classes/<id>/classe.db
│       ├── classes/<id>/fichiers/   (liens physiques)
│       └── cours/
└── exports/                    archives zip des classes (flask archiver-classe)
```

Une classe = un dossier : l'archiver, la sauvegarder ou la supprimer ne touche pas aux autres.

### Base commune `ada.db`

```
┌──────────────────────┐        ┌──────────────────────┐
│ utilisateurs         │        │ classes              │
├──────────────────────┤        ├──────────────────────┤
│ id (AUTOINCREMENT)   │  N:M   │ id (AUTOINCREMENT)   │
│ email (unique, casse │◄──────►│ nom                  │
│   ignorée)           │        │ annee                │
│ nom_complet          │        │ debut_autorisation   │
│ role : etudiant,     │        │ fin_autorisation     │
│   enseignant, admin  │        └──────────────────────┘
│ mot_de_passe         │          via inscriptions
│ actif                │          (utilisateur_id, classe_id)
│ inscrit_le           │
│ derniere_connexion   │
└──────────┬───────────┘
           │ 1:N
           ▼
   sessions (cle = sha256 du jeton, utilisateur_id, cree_le, expire_le)
```

### Base d'une classe `classes/<id>/classe.db`

```
creneaux        id, type_ressource (quiz/devoir/page), ressource_id, chemin_page,
                ouverture, fermeture
devoirs         id, titre, description, date_limite, cree_par,
                type_rendu (fichier/fichiers/github), mode (individuel/groupe),
                taille_groupe_max
groupes         id, devoir_id, nom (unique par devoir), cree_par, date_creation
membres_groupe  id, groupe_id, devoir_id, etudiant_id, date_adhesion
                (unique : devoir_id, etudiant_id → un groupe par étudiant et par devoir)
soumissions     id, devoir_id, etudiant_id ou groupe_id (l'un des deux), deposee_par,
                type, lien_github, date_soumission
fichiers_rendus id, soumission_id, chemin (relatif à fichiers/), nom_original, taille,
                date_depot
quiz            id, titre, duree_max_minutes, tentative_unique, cree_par
questions       id, quiz_id, enonce, choix (JSON), reponse_correcte, points
tentatives      id, quiz_id, etudiant_id, reponses (JSON), score, debut, fin
```

`cree_par`, `etudiant_id`, `deposee_par` désignent des utilisateurs de `ada.db`. Pas de clé
étrangère entre deux fichiers SQLite : c'est pourquoi un identifiant d'utilisateur n'est jamais
réattribué (`AUTOINCREMENT`).

Dates : texte ISO 8601 en UTC, microsecondes fixes (l'ordre du texte est celui du temps),
saisies et affichées à l'heure de Paris.

### Schéma et migrations

- Scripts numérotés `app/ada/schema/commun/NNN_*.sql` et `app/ada/schema/classe/NNN_*.sql` ;
  le dernier numéro appliqué est dans `PRAGMA user_version` de chaque base.
- `flask migrer`, au démarrage du conteneur : crée `/data` au premier lancement ; sinon, si
  une base est en retard, fait une **sauvegarde complète** (`…-avant-migration`), puis
  applique les scripts manquants, chacun dans une transaction.
- Une base plus récente que le code (retour à une ancienne image) bloque le démarrage.
- Une base ouverte à une autre version que celle du code est refusée.
- Une nouvelle classe est créée au dernier schéma.

### Sauvegardes et restauration

- `flask sauvegarder [--motif …]` : copie cohérente de chaque base par l'API de sauvegarde
  de SQLite (service lancé), fichiers rendus en liens physiques (un rendu n'est jamais
  réécrit sur place : un nouveau dépôt crée un nouveau fichier par `os.replace`), cours en
  copie réelle.
- `flask restaurer <nom>`, service arrêté : sauvegarde l'état courant (`…-avant-restauration`),
  puis remplace bases, fichiers et cours.
- Les sauvegardes sont sur le même disque que les données : les copier ailleurs (`tar`).
- Archive d'une classe (fin d'année) : zip vérifié (données en JSON et CSV, fichiers sous leur
  nom d'origine, empreinte sha256), puis suppression de la classe contre cette archive.

### Reprise de la version Django/MySQL

Une fois, par `migration/1-sauvegarder-mysql.sh` (dump MySQL, archive du volume `uploads`,
export zip de chaque classe par l'ancienne application, sommes sha256) puis
`migration/2-migrer.sh` (`flask importer-mysql`). Identifiants et mots de passe Django
conservés (rehachés à la première connexion). Contrôles : effectifs par table, sha256 des
fichiers, et chaque classe migrée identique à son export. Au moindre écart, rien n'est gardé.

---

## Sessions et sécurité des requêtes

```
Connexion réussie
    │
    ├── jeton aléatoire → cookie signé « ada » (HttpOnly, Secure, SameSite=Lax, 2 semaines)
    └── sha256(jeton) → table sessions de ada.db

Requête suivante
    │
    ▼
cookie → sha256 → sessions (non expirée) JOIN utilisateurs (actif)
    ├── trouvée → utilisateur courant
    └── absente → anonyme (redirection vers /auth/login/?next=…)
```

- Déconnexion : la ligne est supprimée. Changement de mot de passe : les autres sessions
  de l'utilisateur sont supprimées. Compte désactivé ou supprimé : sessions sans effet.
- CSRF : jeton aléatoire dans la session, champ `csrf` exigé sur chaque POST (400 sinon).
- Redirection après connexion : chemin local seulement (`/…`, ni `//hôte` ni URL absolue).
- Hôtes acceptés : `DOMAIN`, `localhost`, `127.0.0.1`, `ada`.

---

## Gestion des logs

Aucun fichier de log dans ce dépôt : le conteneur écrit sur stdout, et le driver Docker
`syslog` envoie ces lignes au rsyslog d'argos (`udp://127.0.0.1:514`), qui les range dans
`logs.db`. Tag `ada`. Les requêtes HTTP sont journalisées par le reverse proxy d'argos
(`nginx-proxy`) et par gunicorn (`--access-logfile -`).

**Format (logger `ada`) :**

```
[2026-10-24 14:32:01] INFO Connexion réussie utilisateur=234 ip=192.168.1.42
[2026-10-24 14:32:05] WARNING Cours refusé utilisateur=234 chemin=/cours/info-201/ ip=192.168.1.42
[2026-10-24 14:33:12] INFO Dépôt classe=3 devoir=12 etudiant=234 fichier=rapport.pdf
```

**Consultation :**

- Page Logs du dashboard argos (filtre par conteneur)
- Requête en lecture seule sur `logs.db` dans `logs_rsyslog`

---

## Réseau

`ada` est seul sur `reverse-proxy-net`, le réseau d'argos ; aucun port publié sur l'hôte.
Plus de réseau `backend` : les bases sont des fichiers du volume, sans service réseau.

---

## Arborescence du projet

```
ada/
├── docker-compose.yml         service ada, volume data
├── start.sh                   garde-fou argos, puis compose up
├── .env                       (non versionné) — modèle : .env.example
├── app/                       image du service ada
│   ├── Dockerfile
│   ├── requirements.txt       flask, gunicorn, openpyxl, tzdata, PyMySQL (reprise)
│   ├── wsgi.py
│   ├── ada/
│   │   ├── __init__.py        create_app, CSRF, filtres, erreurs
│   │   ├── config.py          lecture de l'environnement
│   │   ├── db.py              arborescence /data, connexions, schéma, migrer()
│   │   ├── modeles.py         objets lus en base, requêtes partagées
│   │   ├── comptes.py         mots de passe, sessions, accès
│   │   ├── formulaires.py     validation (devoir, lien GitHub, groupe)
│   │   ├── fichiers.py        dépôt et lecture des fichiers rendus
│   │   ├── archivage.py       archive d'une classe, vérification, suppression
│   │   ├── sauvegardes.py     sauvegarde, liste, restauration
│   │   ├── import_mysql.py    reprise de la version Django
│   │   ├── commandes.py       flask migrer, creer-admin, archiver-classe, sauvegarder,
│   │   │                      sauvegardes, restaurer, importer-mysql
│   │   ├── vues/              connexion, cours, devoirs, enseignant, admin
│   │   ├── schema/            commun/NNN_*.sql, classe/NNN_*.sql
│   │   └── templates/
│   └── tests/                 unittest, dossier de données temporaire
├── content/                   exemples de pages de cours
└── migration/                 1-sauvegarder-mysql.sh, 2-migrer.sh
```

---

## Sécurité

| Risque                 | Protection                                    |
|------------------------|-----------------------------------------------|
| Interception réseau    | HTTPS obligatoire via le reverse proxy argos  |
| Mots de passe          | Hachés par werkzeug (scrypt) ; anciens hachés Django vérifiés puis remplacés |
| Vol de session         | Cookie signé HttpOnly/Secure, jeton haché en base, révocable |
| CSRF                   | Jeton de session sur chaque POST, cookie SameSite=Lax |
| Injection SQL          | Requêtes paramétrées partout                  |
| Upload malveillant     | Whitelist d'extensions, taille maximale, nom généré, jamais servi en statique |
| Parcours de chemin     | Fichiers rendus et cours confinés à leur dossier (liens symboliques compris) |
| Accès hors créneau     | Vérification à chaque requête sur `/cours/`   |
| Perte de données       | Sauvegarde avant chaque migration de schéma, sauvegardes à la demande, archive vérifiée avant suppression d'une classe |
| Secrets dans le code   | Variables d'environnement via `.env`          |

---

## Fonctions à venir : quiz

Les tables `quiz`, `questions`, `tentatives` existent dans chaque base de classe (reprises de
la version Django), sans interface. À faire dans ada : quiz disponibles pour la classe
(créneau `quiz`), timer côté serveur, une seule tentative si configuré, score, affichage des
résultats selon l'enseignant.

---

## Déploiement

```bash
# 1. Configurer l'environnement
cp .env.example .env
# Éditer .env : SECRET_KEY, DOMAIN

# 2. Lancer (argos doit tourner)
./start.sh

# 3. Premier administrateur, pages de cours
docker compose exec ada flask creer-admin
docker compose cp content/. ada:/data/cours/

# 4. https://domaine/admin/ : importer les classes (xlsx), créer les devoirs

# 5. Logs : page Logs du dashboard argos
```

---

## Résumé

| Élément              | Choix retenu                    |
|----------------------|---------------------------------|
| Conteneurs           | 1 (`ada`)                       |
| Framework            | Flask + Gunicorn                |
| Base de données      | SQLite : `ada.db` commune + une `classe.db` par classe |
| Données              | Un volume `data`, arborescence par classe |
| Sessions             | Table `sessions` de `ada.db`    |
| Schéma               | Scripts SQL numérotés, `PRAGMA user_version`, sauvegarde avant migration |
| Sauvegardes          | `flask sauvegarder` / `restaurer` |
| Logs                 | stdout → syslog d'argos         |
| HTTPS                | Reverse proxy d'argos           |
| Pages de cours       | Servies par ada après contrôle de session et de créneau |
