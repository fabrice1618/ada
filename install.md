# Installation

## Prérequis

- Docker Engine >= 24.0
- Docker Compose >= 2.20

```bash
docker --version
docker compose version
```

---

## 1. Configuration

Copier le fichier d'environnement et l'éditer :

```bash
cp .env.example .env
```

Modifier `.env` avec vos valeurs :

```
SECRET_KEY=une_cle_secrete_longue_et_aleatoire
```

Pour générer une clé secrète :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 2. Installation locale (laptop)

Ada est un tenant d'argos. Le TLS et le nom `ada.localhost` viennent du reverse proxy d'argos.

Dans `.env` : `DOMAIN=ada.localhost` et `SESSION_COOKIE_SECURE=1`.

### Lancer la stack

Argos doit déjà tourner (`reverse-proxy-net` et `logs_rsyslog`).

```bash
./start.sh
```

Au premier démarrage, le conteneur crée l'arborescence du volume `data` et la base commune `/data/ada.db` (`flask migrer`, lancé avant gunicorn). Aux démarrages suivants, il applique les changements de schéma en attente, après une sauvegarde complète.

### Créer le compte administrateur

```bash
docker compose exec ada flask creer-admin
```

Renseigner l'email, le nom et le mot de passe lorsque demandé.

### Déposer les pages de cours

```bash
docker compose cp content/. ada:/data/cours/
```

### Accès

Une fois le proxy branché sur `ada:8000` :

| URL | Service |
|---|---|
| https://ada.localhost/auth/login/ | Connexion |
| https://ada.localhost/admin/ | Import des classes |
| https://ada.localhost/admin/devoirs/ | Création d'un devoir et suivi des rendus |
| https://ada.localhost/devoirs/ | Dépôt étudiant |
| https://ada.localhost/cours/math-101/ | Pages de cours (créneau ouvert pour les étudiants) |

### Données de test

1. Importer un classeur `.xlsx` (colonnes `NOM Prénom` et `Email`, une feuille par classe) avec génération des mots de passe.
2. Créer un devoir : classe, titre, date limite.
3. Se connecter avec un compte étudiant de cette classe et déposer un fichier.
4. Revenir sur le suivi du devoir pour télécharger le fichier ou l'archive zip.

### Arrêter la stack

```bash
docker compose down
```

Pour supprimer aussi toutes les données (bases, fichiers, cours, sauvegardes) :

```bash
docker compose down -v
```

---

## 3. VPS de test

Le nom public est `https://ada.mips.science`. Le certificat est déjà celui du reverse proxy. Ce dépôt ne lie pas les ports 80 et 443.

### `.env` sur le VPS

```
DOMAIN=ada.mips.science
DEBUG=0
SESSION_COOKIE_SECURE=1
SECRET_KEY=cle_secrete_production
```

### Lancer

```bash
./start.sh
```

### Jonction proxy

Dans `argos/applications/ada/sites.conf`, `ada.mips.science` et `ada.localhost` pointent vers `ada`, port `8000`, option `body_size=20m`. Plus de fragment `sites-extra/` : `/cours/` est servi par ada, qui contrôle lui-même session et créneau. Puis `socle/reverse_proxy/reverse_proxy apply`.

`ada` doit être démarré avant l'apply.

### Initialiser

```bash
docker compose exec ada flask creer-admin
docker compose cp content/. ada:/data/cours/
```

### Vérifier

```bash
curl -I https://ada.mips.science/auth/login/
```

La réponse doit afficher `HTTP/2 200`. Le certificat est celui déjà émis pour ce nom.

Arrêt : `docker compose down` (le volume `data` est conservé).

### Migrer depuis la version Django/MySQL (une fois)

Pour un serveur où tournent encore `ada-auth`, `ada-cours` et `ada-mysql`. Comptes (mots de passe compris), classes, devoirs, groupes, rendus, fichiers, créneaux et quiz sont repris avec leurs identifiants. Les sessions ne le sont pas : chacun se reconnecte.

Hors des heures de dépôt, ou avec la page de maintenance d'argos :

```bash
git pull                                       # nouvelle version ; l'ancienne pile tourne toujours
migration/1-sauvegarder-mysql.sh               # → migration-mysql/<date>/
```

L'étape 1 écrit, avant de toucher à quoi que ce soit : le dump MySQL (`mysql.sql.gz`), le volume `uploads` (`uploads.tar.gz`), l'export zip de chaque classe par l'ancien `archiver_classe` (`exports/`), et leurs sommes (`SHA256SUMS`). Copier ce dossier hors du serveur.

```bash
migration/2-migrer.sh migration-mysql/<date>
```

L'étape 2 arrête `ada-auth` et `ada-cours` (MySQL reste lancé, en lecture), vérifie les sommes, recopie le dossier dans `/data/sauvegardes/<date>-avant-migration-mysql/`, puis remplit le volume `ada_data`. Elle contrôle le résultat : même nombre de lignes table par table, mêmes fichiers (sha256), et chaque classe identique à son export de l'étape 1. Au moindre écart (par exemple un rendu déposé entre les deux étapes), rien n'est gardé : `docker volume rm ada_data`, puis reprendre à l'étape 1.

Ensuite :

1. `.env` : `SECRET_KEY` (les variables `MYSQL_*` et `DJANGO_SECRET_KEY` ne servent plus) ;
2. `./start.sh` : démarre `ada` et retire les conteneurs `ada-auth`, `ada-cours`, `ada-mysql` ;
3. argos : `sites.conf` vers `ada`, port `8000`, suppression du fragment `sites-extra/`, puis apply ;
4. `docker compose cp content/. ada:/data/cours/` ;
5. vérifier connexion, devoirs, téléchargements. Les anciens volumes `ada_db_data` et `ada_uploads` restent : les supprimer plus tard seulement (`docker volume rm ada_db_data ada_uploads`).

Retour arrière possible tant que ces volumes existent : `git checkout` de l'ancienne version, `./start.sh`, argos rétabli. Ce qui a été déposé dans la nouvelle version entre-temps n'y est pas.

---

## 4. Commandes utiles

### Logs

Tous les logs partent vers le syslog d'argos (tag `ada`) : rien n'est écrit dans `logs/`, et `docker logs` reste vide. Les lire dans la page Logs du dashboard argos, ou :

```bash
docker exec logs_rsyslog python3 -c "import sqlite3; c=sqlite3.connect('file:/logs/logs.db?mode=ro',uri=True); [print(*r) for r in c.execute(\"select received_at, container, msg from system_logs where container like 'ada%' order by id desc limit 50\")]"
```

### Rebuild d'un service après modification

```bash
docker compose build ada
docker compose up -d ada
```

Au démarrage, `flask migrer` sauvegarde tout (`/data/sauvegardes/<date>-avant-migration`) avant d'appliquer un nouveau script de schéma.

### Accès direct aux bases

L'image n'a pas le client `sqlite3` : passer par Python, en lecture seule.

```bash
docker compose exec ada python -c "import sqlite3; c=sqlite3.connect('file:/data/ada.db?mode=ro',uri=True); [print(*r) for r in c.execute('select id, nom, annee from classes')]"
docker compose exec ada python -c "import sqlite3; c=sqlite3.connect('file:/data/classes/3/classe.db?mode=ro',uri=True); [print(*r) for r in c.execute('select id, titre, date_limite from devoirs')]"
```

### Modifier le schéma

Ajouter un script numéroté, sans toucher aux scripts déjà livrés : `app/ada/schema/commun/002_<objet>.sql` (base commune) ou `app/ada/schema/classe/002_<objet>.sql` (chaque base de classe). Rebuild : le démarrage sauvegarde, puis applique le script à toutes les bases concernées ; un échec annule le script sur la base en cause.

### Archiver une classe (fin d'année)

Exporte tout ce qui concerne la classe (étudiants, devoirs, groupes, rendus, fichiers ; aucun mot de passe), puis la supprime de la prod. Les étudiants inscrits dans une autre classe gardent leur compte ; enseignants et admins ne sont jamais supprimés.

Depuis le navigateur : page de la classe (`/admin/classes/<id>/`), « Exporter l'archive », puis « Supprimer la classe ». La suppression retire la ligne de `ada.db` et tout le dossier `/data/classes/<id>/` (base et fichiers).

Sur le serveur (grosse classe, ou sans navigateur) :

```bash
docker compose exec -T ada flask archiver-classe                    # liste les classes et leur id
docker compose exec -T ada flask archiver-classe 3                  # archive dans /data/exports/
docker compose exec -T ada flask archiver-classe 3 --sortie - > ada-classe-3.zip
unzip -l ada-classe-3.zip                                            # ouvrir, contrôler, mettre à l'abri
docker compose exec -T ada flask archiver-classe 3 --supprimer - < ada-classe-3.zip
```

La suppression revérifie l'archive contre les données : elle est refusée si l'archive est abîmée, d'une autre classe, ou si les données ont changé depuis l'export (un rendu déposé entre-temps : réexporter).

### Sauvegarder

Une sauvegarde est complète : `ada.db`, chaque `classe.db` (copie cohérente par l'API de SQLite, service lancé), les fichiers rendus (liens physiques, presque gratuits) et les cours.

```bash
docker compose exec ada flask sauvegarder --motif avant-rentree
docker compose exec ada flask sauvegardes                            # de la plus récente à la plus ancienne
```

Elle reste dans le volume, donc sur le même disque : la copier ailleurs.

```bash
docker compose exec -T ada tar -C /data/sauvegardes -czf - 20261024-131410-avant-rentree > ada-sauvegarde.tar.gz
```

### Restaurer une sauvegarde

Service arrêté : rien ne doit écrire pendant la restauration. L'état remplacé est d'abord sauvegardé (`…-avant-restauration`).

```bash
docker compose stop ada
docker compose run --rm ada flask restaurer 20261024-131410-avant-rentree
docker compose start ada
```

Depuis une copie extérieure : `docker compose cp ada-sauvegarde/. ada:/data/sauvegardes/<nom>/` (ou `tar -x` dans le volume), puis la commande ci-dessus.

---

## 5. Structure des fichiers

```
.
├── docker-compose.yml          ← service ada + volume data
├── start.sh                    ← garde-fou argos, puis compose up
├── .env                        ← variables d'environnement (non versionné)
├── .env.example                ← modèle de .env
├── app/                        ← image ada : Flask (ada/), tests (tests/)
├── content/                    ← exemples de pages de cours, à copier dans /data/cours
├── migration/                  ← reprise de la version Django/MySQL (une fois)
```

Le volume `data` :

```
/data/
├── ada.db                      ← comptes, classes, inscriptions, sessions
├── classes/<id>/classe.db      ← créneaux, devoirs, groupes, rendus, quiz de la classe
├── classes/<id>/fichiers/      ← fichiers rendus de la classe
├── cours/                      ← pages servies sous /cours/
├── sauvegardes/<date>-<motif>/ ← sauvegardes complètes
└── exports/                    ← archives zip des classes
```

---

## 6. Différences entre les deux modes

| | Local | Production |
|---|---|---|
| Commande | `./start.sh` | `./start.sh` |
| TLS | Certificat du reverse proxy | Certificat du reverse proxy |
| `DOMAIN` | `ada.localhost` | `ada.mips.science` |
| `DEBUG` | `0` | `0` |
| `SESSION_COOKIE_SECURE` | `1` | `1` |
