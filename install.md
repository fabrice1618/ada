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

Le mode local utilise un certificat auto-signé généré automatiquement par Traefik. Pas de nom de domaine ni de configuration DNS nécessaire.

### Lancer la stack

```bash
docker compose up -d --build
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

| URL | Service |
|---|---|
| https://localhost/auth/login/ | Page de connexion |
| https://localhost/admin/ | Interface d'administration Django |
| https://localhost/cours/math-101/ | Pages de cours (Forward Auth) |

Le navigateur affichera un avertissement de certificat. C'est normal : accepter l'exception pour continuer.

- **Firefox** : cliquer "Avancé" → "Accepter le risque et poursuivre"
- **Chrome** : cliquer "Avancé" → "Continuer vers localhost (non sécurisé)", ou taper `thisisunsafe` au clavier

### Données de test

Via l'admin Django (https://localhost/admin/) :

1. **Créer une classe** : ex. `Math-101`, année `2026`
2. **Créer un utilisateur étudiant** : renseigner email, nom, rôle `Étudiant`, lui affecter la classe
3. **Créer un créneau** : classe `Math-101`, type `page`, chemin `/cours/math-101/`, ouverture et fermeture englobant la date courante

Tester ensuite l'accès aux pages de cours avec le compte étudiant.

### Arrêter la stack

```bash
docker compose down
```

Pour supprimer aussi les données MySQL :

```bash
docker compose down -v
```

---

## 3. Mise en production (VPS)

### Prérequis serveur

- Un nom de domaine pointant vers l'IP du VPS (enregistrement DNS de type A)
- Ports 80 et 443 ouverts dans le pare-feu

### Configurer le `.env` de production

```
DOMAIN=votre-domaine.fr
ACME_EMAIL=votre-email@example.com
DEBUG=0
MYSQL_ROOT_PASSWORD=mot_de_passe_fort
MYSQL_PASSWORD=mot_de_passe_fort
DJANGO_SECRET_KEY=cle_secrete_production
```

### Lancer avec le profil production

Le fichier `docker-compose.prod.yml` active Let's Encrypt à la place du certificat auto-signé :

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Initialiser la base

```bash
docker compose exec auth python manage.py migrate
docker compose exec auth python manage.py createsuperuser
docker compose exec auth python manage.py collectstatic --noinput
```

### Vérifier le certificat

Let's Encrypt met quelques secondes à émettre le certificat au premier démarrage. Vérifier :

```bash
curl -I https://votre-domaine.fr/auth/login/
```

La réponse doit afficher `HTTP/2 200` sans erreur de certificat.

### Alias recommandé

Pour éviter de retaper les deux fichiers à chaque commande, ajouter dans `~/.bashrc` :

```bash
alias dcp='docker compose -f docker-compose.yml -f docker-compose.prod.yml'
```

Utilisation :

```bash
dcp up -d --build
dcp logs -f auth
dcp exec auth python manage.py migrate
dcp down
```

---

## 4. Commandes utiles

### Logs

```bash
# Logs d'un service en temps réel
docker compose logs -f auth

# Logs applicatifs sur le système de fichiers
tail -f logs/auth/app.log
tail -f logs/traefik/access.log

# Chercher les erreurs 403
grep "403" logs/*/app.log
```

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
├── docker-compose.yml          ← stack de base (dev local, cert auto-signé)
├── docker-compose.prod.yml     ← overlay production (Let's Encrypt)
├── .env                        ← variables d'environnement (non versionné)
├── .env.example                ← modèle de .env
├── traefik/
│   ├── traefik.yml             ← config Traefik locale
│   └── traefik.prod.yml        ← config Traefik production (ACME)
├── auth/                       ← service Django (authentification)
├── nginx/                      ← service Nginx (pages statiques)
├── shared/                     ← utilitaires partagés (Flask)
├── content/                    ← pages de cours HTML
└── logs/                       ← fichiers de logs (non versionné)
```

---

## 6. Différences entre les deux modes

| | Local | Production |
|---|---|---|
| Commande | `docker compose up -d` | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` |
| TLS | Certificat auto-signé (Traefik) | Let's Encrypt |
| Domaine | `localhost` | Nom de domaine réel |
| `DOMAIN` | `localhost` | `votre-domaine.fr` |
| `DEBUG` | `1` (optionnel) | `0` |
| `ACME_EMAIL` | Non utilisé | Requis |
