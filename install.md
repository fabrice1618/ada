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
MYSQL_ROOT_PASSWORD=un_vrai_mot_de_passe_root
MYSQL_PASSWORD=un_vrai_mot_de_passe_user
DJANGO_SECRET_KEY=une_cle_secrete_longue_et_aleatoire
```

Pour générer une clé secrète Django :

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

### Initialiser la base de données

```bash
docker compose exec auth python manage.py migrate
```

### Créer le compte administrateur

```bash
docker compose exec auth python manage.py createsuperuser
```

Renseigner l'email et le mot de passe lorsque demandé.

### Collecter les fichiers statiques Django

```bash
docker compose exec auth python manage.py collectstatic --noinput
```

### Accès

Une fois le proxy branché sur `ada-auth:8000` :

| URL | Service |
|---|---|
| https://ada.localhost/auth/login/ | Connexion |
| https://ada.localhost/admin/ | Import des classes |
| https://ada.localhost/admin/devoirs/ | Création d'un devoir et suivi des rendus |
| https://ada.localhost/devoirs/ | Dépôt étudiant |

### Données de test

1. Importer un classeur `.xlsx` (colonnes `NOM Prénom` et `Email`, une feuille par classe) avec génération des mots de passe.
2. Créer un devoir : classe, titre, date limite.
3. Se connecter avec un compte étudiant de cette classe et déposer un fichier.
4. Revenir sur le suivi du devoir pour télécharger le fichier ou l'archive zip.

### Arrêter la stack

```bash
docker compose down
```

Pour supprimer aussi la base MySQL et les fichiers déposés :

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
MYSQL_ROOT_PASSWORD=mot_de_passe_fort
MYSQL_PASSWORD=mot_de_passe_fort
DJANGO_SECRET_KEY=cle_secrete_production
```

### Lancer

```bash
./start.sh
```

### Jonction proxy

Dans `reverse_proxy/sites.conf`, `ada.mips.science` et `ada.localhost` pointent vers `ada-auth`, port `8000`, option `body_size=20m`. Puis `./reverse_proxy apply`. Cette jonction remplace l'upstream `securetest-web` : SecureTest ne répond plus sur ce nom.

`ada-auth` doit être démarré avant l'apply.

### Initialiser la base

```bash
docker compose exec auth python manage.py migrate
docker compose exec auth python manage.py createsuperuser
docker compose exec auth python manage.py collectstatic --noinput
```

### Vérifier

```bash
curl -I https://ada.mips.science/auth/login/
```

La réponse doit afficher `HTTP/2 200`. Le certificat est celui déjà émis pour ce nom.

Arrêt : `docker compose down` (le volume `uploads` et la base MySQL sont conservés).

---

## 4. Commandes utiles

### Logs

```bash
# Fichier applicatif (le driver syslog n'alimente pas `docker logs`)
tail -f logs/auth/app.log
```

Les lignes stdout partent vers le syslog d'argos, tag `ada`.

### Rebuild d'un service après modification

```bash
docker compose build auth
docker compose up -d auth
```

### Accès direct à MySQL

```bash
docker compose exec mysql mysql -u plateforme_user -p plateforme
```

### Migrations après modification des modèles

```bash
docker compose exec auth python manage.py makemigrations
docker compose exec auth python manage.py migrate
```

### Archiver une classe (fin d'année)

Exporte tout ce qui concerne la classe (étudiants, devoirs, groupes, rendus, fichiers ; aucun mot de passe), puis la supprime de la prod. Les étudiants inscrits dans une autre classe gardent leur compte ; enseignants et admins ne sont jamais supprimés.

Depuis le navigateur : page de la classe (`/admin/classes/<id>/`), « Exporter l'archive », puis « Supprimer la classe ».

Sur le serveur (grosse classe, ou sans navigateur) :

```bash
docker compose exec -T auth python manage.py archiver_classe            # liste les classes et leur id
docker compose exec -T auth python manage.py archiver_classe 3 > ada-classe-3.zip
unzip -l ada-classe-3.zip                                                # ouvrir, contrôler, mettre à l'abri
docker compose exec -T auth python manage.py archiver_classe 3 --supprimer - < ada-classe-3.zip
```

La suppression revérifie l'archive contre la base : elle est refusée si l'archive est abîmée, d'une autre classe, ou si les données ont changé depuis l'export (un rendu déposé entre-temps : réexporter).

### Sauvegarder la base de données

```bash
docker compose exec mysql mysqldump -u root -p plateforme > backup.sql
```

### Restaurer une sauvegarde

```bash
docker compose exec -T mysql mysql -u root -p plateforme < backup.sql
```

---

## 5. Structure des fichiers

```
.
├── docker-compose.yml          ← ada-auth + ada-mysql
├── start.sh                    ← garde-fou argos, puis compose up
├── .env                        ← variables d'environnement (non versionné)
├── .env.example                ← modèle de .env
├── auth/                       ← Django : connexion, classes, devoirs
└── logs/                       ← logs applicatifs (non versionné)
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
