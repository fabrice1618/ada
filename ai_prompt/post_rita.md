# Spécification Technique : Intégration de post.php dans le Framework ADA

**Document Version**: 1.0
**Date**: 2025-11-05
**Auteur**: Claude Code
**Statut**: Spécification Technique Complète

---

## Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Analyse de l'Existant : post.php](#2-analyse-de-lexistant--postphp)
3. [État Actuel du Framework ADA](#3-état-actuel-du-framework-ada)
4. [Architecture Cible](#4-architecture-cible)
5. [Migration de la Base de Données](#5-migration-de-la-base-de-données)
6. [Implémentation Complète](#6-implémentation-complète)
7. [Spécifications de Sécurité](#7-spécifications-de-sécurité)
8. [Plan de Migration (Checklist)](#8-plan-de-migration-checklist)
9. [Tests et Validation](#9-tests-et-validation)
10. [Références](#10-références)

---

## 1. Vue d'Ensemble

### 1.1 Contexte

Le fichier `src/post.php` est un script PHP standalone développé pour gérer la soumission de devoirs étudiants. Il permet aux étudiants de soumettre des travaux via :
- Un formulaire avec informations personnelles (nom, prénom, email)
- Une URL optionnelle pointant vers leur travail
- Un fichier uploadé (optionnel)

Ce script fonctionne indépendamment du framework ADA MVC qui a été développé en parallèle. L'objectif de cette spécification est d'intégrer cette fonctionnalité dans l'architecture MVC en utilisant les composants du framework.

### 1.2 Objectifs de l'Intégration

1. **Conformité MVC** : Migrer la logique de `post.php` vers le pattern MVC (Controller → Model → View)
2. **Sécurité** : Intégrer la protection CSRF, validation robuste, et gestion sécurisée des fichiers
3. **Réutilisation** : Utiliser les composants existants du framework (Router, Request, Validator, Models)
4. **Maintenabilité** : Code structuré, testable, et conforme aux conventions du framework
5. **Performance** : Optimiser le stockage des fichiers et les requêtes base de données

### 1.3 Portée

**Dans la portée :**
- Création du `DeposeController`
- Création des vues de soumission
- Mise à jour du schéma de base de données
- Configuration des routes
- Intégration de la validation et de la sécurité
- Tests fonctionnels

**Hors de portée :**
- Interface d'administration pour consulter les soumissions
- Notifications par email
- API REST pour les soumissions
- Gestion des quotas et limitations par utilisateur

### 1.4 Prérequis Techniques

- Framework ADA MVC Phases 1-6 complètes
- Base de données MySQL configurée
- PHP 8.2+
- Apache avec mod_rewrite
- Extension PHP : PDO, mysqli, fileinfo

---

## 2. Analyse de l'Existant : post.php

### 2.1 Structure du Fichier

**Emplacement** : `/home/fab/code/ada/src/post.php`
**Taille** : 191 lignes
**Dépendances** : Aucune (PHP pur)

### 2.2 Fonctionnalités Implémentées

#### 2.2.1 Connexion à la Base de Données

```php
// Lignes 8-17
function connectToDatabase() {
    $pdo = new PDO('mysql:host=localhost;dbname=ADA;charset=utf8', 'ada', 'ada', [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    ]);
    return $pdo;
}
```

**Analyse** :
- ✅ Utilise PDO avec prepared statements
- ❌ Credentials hardcodés (non configurable)
- ❌ Pas de singleton pattern
- ❌ Pas de gestion de pool de connexions

#### 2.2.2 Validation des Données Personnelles

```php
// Lignes 22-49
function validatePersonalData() {
    $prenom = trim($_POST['prenom'] ?? '');
    $nom = trim($_POST['nom'] ?? '');
    $email = trim($_POST['email'] ?? '');

    // Validations : required + format email
    if (empty($prenom)) throw new Exception("Le prénom est obligatoire.");
    if (empty($nom)) throw new Exception("Le nom est obligatoire.");
    if (empty($email)) throw new Exception("L'email est obligatoire.");
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        throw new Exception("L'email n'est pas valide.");
    }

    return ['prenom' => $prenom, 'nom' => $nom, 'email' => $email, ...];
}
```

**Analyse** :
- ✅ Validation de base fonctionnelle
- ✅ Utilise `filter_var()` pour email
- ❌ Accès direct aux superglobals (`$_POST`)
- ❌ Pas de protection XSS
- ❌ Messages d'erreur non personnalisables
- ❌ Pas de validation de longueur ou de caractères

#### 2.2.3 Traitement des URLs

```php
// Lignes 54-64
function processUrl() {
    if (!empty($_POST['url'])) {
        $url_valide = filter_var($_POST['url'], FILTER_VALIDATE_URL);
        if ($url_valide) return $url_valide;
        throw new Exception("URL non valide.");
    }
    return null;
}
```

**Analyse** :
- ✅ Validation avec `filter_var()`
- ❌ Pas de vérification de protocole (http/https)
- ❌ Pas de protection contre SSRF

#### 2.2.4 Upload de Fichiers

```php
// Lignes 69-118
function processUploadedFile() {
    if (!empty($_FILES['fichier']) && $_FILES['fichier']['error'] === UPLOAD_ERR_OK) {
        $nomfichier_original = $_FILES['fichier']['name'];
        $taille_fichier = $_FILES['fichier']['size'];
        $type_fichier = $_FILES['fichier']['type'];

        // Validation taille (10MB max)
        $taille_max = 10 * 1024 * 1024;
        if ($taille_fichier > $taille_max) {
            throw new Exception("Le fichier est trop volumineux. Taille maximum: 10MB.");
        }

        // Validation type MIME
        $types_autorises = ['image/jpeg', 'image/png', 'application/pdf', 'text/plain'];
        if (!in_array($type_fichier, $types_autorises)) {
            throw new Exception("Type de fichier non autorisé.");
        }

        // Génération nom unique
        $extension = pathinfo($nomfichier_original, PATHINFO_EXTENSION);
        $nomfichier_stockage = uniqid('file_') . '.' . $extension;

        // Stockage dans /src/uploads/
        $dossier_uploads = __DIR__ . '/uploads/';
        if (!is_dir($dossier_uploads)) {
            mkdir($dossier_uploads, 0755, true);
        }

        if (move_uploaded_file($_FILES['fichier']['tmp_name'],
                                $dossier_uploads . $nomfichier_stockage)) {
            return [
                'nomfichier_original' => $nomfichier_original,
                'nomfichier_stockage' => $nomfichier_stockage,
                'taille_fichier' => $taille_fichier,
                'type_fichier' => $type_fichier
            ];
        }
    }
    return ['nomfichier_original' => null, ...];
}
```

**Analyse** :
- ✅ Validation de taille (10MB)
- ✅ Validation de type MIME
- ✅ Génération de nom unique avec `uniqid()`
- ✅ Vérification de `UPLOAD_ERR_OK`
- ❌ Stockage dans `/src/uploads/` au lieu de `/filestore/`
- ❌ Pas de validation d'extension réelle (spoofing MIME possible)
- ❌ `uniqid()` n'est pas cryptographiquement sûr
- ❌ Pas de vérification de contenu malveillant

#### 2.2.5 Sauvegarde en Base de Données

```php
// Lignes 123-142
function saveToDatabase($pdo, $data) {
    $stmt = $pdo->prepare("INSERT INTO deposes
                          (prenom, nom, email, date_depot, url,
                           nomfichier_original, nomfichier_stockage,
                           taille_fichier, type_fichier)
                          VALUES
                          (:prenom, :nom, :email, :date_depot, :url,
                           :nomfichier_original, :nomfichier_stockage,
                           :taille_fichier, :type_fichier)");

    $stmt->execute([...]);
    return $pdo->lastInsertId();
}
```

**Analyse** :
- ✅ Utilise prepared statements (protection SQL injection)
- ✅ Retourne l'ID du nouvel enregistrement
- ❌ Colonnes `email`, `taille_fichier`, `type_fichier` n'existent pas dans le schéma actuel
- ❌ Pas de transaction
- ❌ Pas de gestion de la colonne `iddevoirs` (clé étrangère)

### 2.3 Flux de Traitement

```
POST Request
    ↓
1. Validation données personnelles (prenom, nom, email)
    ↓
2. Traitement URL (optionnel)
    ↓
3. Traitement fichier (optionnel)
    ↓
4. Vérification : URL OU Fichier requis
    ↓
5. Connexion DB + Insertion
    ↓
6. Affichage résultat (succès ou erreur)
```

### 2.4 Problèmes Identifiés

#### Sécurité
1. ❌ **Pas de protection CSRF** - Vulnérable aux attaques cross-site
2. ❌ **Credentials hardcodés** - Pas de configuration externe
3. ❌ **Pas de sanitization XSS** - Echo direct des données utilisateur
4. ❌ **Upload non sécurisé** - Validation MIME insuffisante
5. ❌ **Pas de rate limiting** - Vulnérable au spam

#### Architecture
1. ❌ **Code procédural** - Pas de pattern MVC
2. ❌ **Pas de séparation des préoccupations** - Validation + business logic + DB dans un fichier
3. ❌ **Pas de réutilisabilité** - Fonctions couplées au contexte
4. ❌ **Pas de testabilité** - Dépendances directes aux superglobals

#### Maintenabilité
1. ❌ **Messages en français hardcodés** - Pas d'i18n
2. ❌ **Pas de logging** - Impossible de tracer les erreurs
3. ❌ **Gestion d'erreur basique** - Echo puis exit
4. ❌ **Pas de documentation** - Aucun commentaire PHPDoc

---

## 3. État Actuel du Framework ADA

### 3.1 Architecture MVC Complète

**Statut** : ✅ Phases 1-6 implémentées (malgré CLAUDE.md qui indique Phase 1)

```
/home/fab/code/ada/src/
├── core/                          # Framework core
│   ├── Router.php                 # Routing avec paramètres dynamiques
│   ├── Request.php                # Abstraction requête HTTP + file handling
│   ├── Response.php               # Abstraction réponse HTTP
│   ├── Controller.php             # Base controller avec validation
│   ├── Model.php                  # Base model avec query builder
│   ├── Database.php               # Singleton PDO
│   ├── Validator.php              # 15+ règles de validation
│   ├── Security.php               # CSRF, XSS, sanitization
│   ├── Session.php                # Gestion session + flash
│   └── View.php                   # Template engine
├── app/
│   ├── Controllers/
│   │   └── DevoirController.php   # Contrôleur devoirs existant
│   ├── Models/
│   │   ├── Devoir.php             # Model devoirs
│   │   └── Depose.php             # Model deposes (à mettre à jour)
│   ├── Middleware/
│   │   ├── CsrfMiddleware.php     # Protection CSRF
│   │   └── SessionMiddleware.php  # Session management
│   └── Views/
│       └── devoirs/
│           └── index.php          # Liste des devoirs
├── config/
│   ├── config.php                 # Configuration générale
│   └── routes.php                 # Définition des routes
└── index.php                      # Front controller
```

### 3.2 Composants Réutilisables

#### 3.2.1 Request Class - Gestion des Fichiers

**Fichier** : `src/core/Request.php`

```php
// Lignes 292-306
public function file(string $key)
{
    return $_FILES[$key] ?? null;
}

public function hasFile(string $key): bool
{
    return isset($_FILES[$key]) && $_FILES[$key]['error'] === UPLOAD_ERR_OK;
}

// Lignes 317-350
public function validateFile(
    string $key,
    int $maxSize = 10485760,
    array $allowedTypes = [],
    array $allowedExtensions = []
): bool {
    if (!$this->hasFile($key)) return false;

    $file = $_FILES[$key];

    // Validation taille
    if ($file['size'] > $maxSize) return false;

    // Validation type MIME
    if (!empty($allowedTypes) && !in_array($file['type'], $allowedTypes)) {
        return false;
    }

    // Validation extension
    if (!empty($allowedExtensions)) {
        $extension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
        if (!in_array($extension, $allowedExtensions)) return false;
    }

    return true;
}

// Lignes 360-390
public function moveFile(
    string $key,
    string $destination,
    ?string $newName = null
): ?string {
    if (!$this->hasFile($key)) return null;

    $file = $_FILES[$key];

    // Créer le dossier si nécessaire
    if (!is_dir($destination)) {
        mkdir($destination, 0755, true);
    }

    // Générer nom unique si non fourni
    if ($newName === null) {
        $extension = pathinfo($file['name'], PATHINFO_EXTENSION);
        $newName = bin2hex(random_bytes(16)) . '.' . $extension;
    }

    $targetPath = rtrim($destination, '/') . '/' . $newName;

    if (move_uploaded_file($file['tmp_name'], $targetPath)) {
        return $newName;
    }

    return null;
}
```

**Avantages** :
- ✅ Abstraction complète de `$_FILES`
- ✅ Validation intégrée (taille, MIME, extension)
- ✅ Génération de nom sécurisé avec `random_bytes()`
- ✅ Création automatique de répertoires
- ✅ Retour du nom de fichier généré

#### 3.2.2 Validator Class

**Fichier** : `src/core/Validator.php`

```php
// Exemple d'utilisation
$validator = new Validator($request->all(), [
    'prenom' => 'required|alpha|min:2|max:50',
    'nom' => 'required|alpha|min:2|max:50',
    'email' => 'required|email|max:100',
    'url' => 'nullable|url',
]);

if ($validator->fails()) {
    return $this->redirect('/submit')
                ->with('errors', $validator->errors())
                ->with('old', $request->all());
}

$validatedData = $validator->validated();
```

**Règles disponibles** :
- `required` : Champ obligatoire
- `email` : Format email valide (lignes 290-297)
- `url` : Format URL valide (lignes 421-428)
- `alpha` : Caractères alphabétiques uniquement
- `min:n` / `max:n` : Longueur minimale/maximale
- `numeric` : Valeur numérique
- `unique:table,column` : Vérification d'unicité en DB
- `exists:table,column` : Vérification d'existence en DB

#### 3.2.3 Security Class - CSRF Protection

**Fichier** : `src/core/Security.php`

```php
// Lignes 15-23 : Génération token
public static function generateCsrfToken(): string
{
    if (!isset($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

// Lignes 41-58 : Validation token
public static function validateCsrfToken(?string $token): bool
{
    if (!isset($_SESSION['csrf_token']) || $token === null) {
        return false;
    }
    return hash_equals($_SESSION['csrf_token'], $token);
}
```

**Utilisation dans les vues** :
```php
<input type="hidden" name="csrf_token" value="<?= Security::generateCsrfToken() ?>">
```

#### 3.2.4 Model Depose - Existant

**Fichier** : `src/app/Models/Depose.php`

```php
class Depose extends Model
{
    protected string $table = 'deposes';
    protected string $primaryKey = 'iddeposes';
    protected array $fillable = [
        'nom',
        'prenom',
        'datedepot',
        'url',
        'nomfichieroriginal',
        'nomfichierstockage',
        'iddevoirs'
    ];

    // Lignes 125-134
    public function createSubmission(array $data): int
    {
        $data['datedepot'] = date('Y-m-d H:i:s');
        return $this->create($data);
    }
}
```

**À mettre à jour** :
- Ajouter `email`, `taille_fichier`, `type_fichier` dans `$fillable`

#### 3.2.5 CsrfMiddleware - Protection Automatique

**Fichier** : `src/app/Middleware/CsrfMiddleware.php`

```php
// Lignes 20-31
public function handle(Request $request): bool
{
    if (in_array($request->method(), ['POST', 'PUT', 'DELETE', 'PATCH'])) {
        $token = $request->input('csrf_token');

        if (!Security::validateCsrfToken($token)) {
            throw new Exception('CSRF token validation failed.');
        }
    }

    return true;
}
```

**Activation** : Middleware automatiquement appliqué via configuration de route

### 3.3 Database Schema Actuel

**Fichier** : `database/01-init.sql`

```sql
CREATE TABLE IF NOT EXISTS devoirs (
    iddevoirs INT AUTO_INCREMENT PRIMARY KEY,
    shortcode VARCHAR(50) NOT NULL UNIQUE,
    datelimite DATETIME NOT NULL,
    INDEX idx_shortcode (shortcode),
    INDEX idx_datelimite (datelimite)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS deposes (
    iddeposes INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    datedepot DATETIME NOT NULL,
    url TEXT,
    nomfichieroriginal VARCHAR(255),
    nomfichierstockage VARCHAR(255),
    iddevoirs INT NOT NULL,
    FOREIGN KEY (iddevoirs) REFERENCES devoirs(iddevoirs) ON DELETE CASCADE,
    INDEX idx_iddevoirs (iddevoirs),
    INDEX idx_datedepot (datedepot)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Colonnes manquantes** :
- ❌ `email` : Email de l'étudiant
- ❌ `taille_fichier` : Taille du fichier en octets
- ❌ `type_fichier` : Type MIME du fichier

### 3.4 Routing System

**Fichier** : `src/config/routes.php`

```php
return [
    ['GET', '/', 'DevoirController@index'],
    ['GET', '/devoirs', 'DevoirController@index'],
    ['GET', '/devoirs/{shortcode}', 'DevoirController@show'],
    // Routes à ajouter pour deposes
];
```

**Pattern de route** :
- Support des paramètres dynamiques : `{shortcode}`, `{id}`
- Middleware par route : `['middleware' => ['CsrfMiddleware']]`
- Nommage des routes : `['name' => 'depose.store']`

---

## 4. Architecture Cible

### 4.1 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                      ARCHITECTURE MVC                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ GET /devoirs/ABC123/submit
       │ POST /devoirs/ABC123/submit + Form Data + File
       ↓
┌──────────────────────────────────────────────────────────────┐
│                    Front Controller                          │
│                   (src/index.php)                            │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────────────────────┐
│                        Router                                │
│              (src/core/Router.php)                           │
│  - Route matching                                            │
│  - Parameter extraction: {shortcode} → ABC123                │
│  - Middleware pipeline                                       │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────────────────────┐
│                   CsrfMiddleware                             │
│        (src/app/Middleware/CsrfMiddleware.php)               │
│  - Validate CSRF token on POST requests                      │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────────────────────┐
│                  DeposeController                            │
│        (src/app/Controllers/DeposeController.php)            │
│                                                              │
│  create(Request $request, string $shortcode)                 │
│    ├─ Find Devoir by shortcode                              │
│    ├─ Check if still open                                   │
│    └─ Render submission form                                │
│                                                              │
│  store(Request $request, string $shortcode)                  │
│    ├─ Validate input (Validator)                            │
│    ├─ Validate file (Request->validateFile())               │
│    ├─ Move file (Request->moveFile())                       │
│    ├─ Save to DB (Depose->createSubmission())               │
│    └─ Redirect with success message                         │
└──────────────────┬───────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ↓                     ↓
┌──────────────┐      ┌──────────────┐
│ Devoir Model │      │ Depose Model │
│ (Devoir.php) │      │ (Depose.php) │
└──────┬───────┘      └──────┬───────┘
       │                     │
       └──────────┬──────────┘
                  ↓
        ┌──────────────────┐
        │   Database PDO   │
        │  (Database.php)  │
        └──────────────────┘
                  ↓
        ┌──────────────────┐
        │   MySQL Server   │
        │  Tables: devoirs │
        │          deposes │
        └──────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      File System                            │
│                                                             │
│  /filestore/submissions/                                    │
│    ├── a1b2c3d4e5f6g7h8i9j0.pdf                           │
│    ├── f9e8d7c6b5a4g3h2i1j0.jpg                           │
│    └── ...                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Flux de Soumission Détaillé

#### 4.2.1 Affichage du Formulaire (GET)

```
1. GET /devoirs/ABC123/submit
   ↓
2. Router → DeposeController@create
   ↓
3. Controller:
   - Devoir::findByShortcode('ABC123')
   - Check if $devoir exists
   - Check if $devoir->isOpen()
   ↓
4. Render view: deposes/create.php
   - Form avec CSRF token
   - Hidden input: iddevoirs
   - Fields: prenom, nom, email, url, fichier
   ↓
5. Return HTML Response
```

#### 4.2.2 Soumission du Formulaire (POST)

```
1. POST /devoirs/ABC123/submit
   - Form data: prenom, nom, email, url, csrf_token
   - File: fichier (optional)
   ↓
2. CsrfMiddleware
   - Validate csrf_token
   - Reject if invalid (403 Forbidden)
   ↓
3. DeposeController@store
   ↓
4. Validation Phase
   - Validator: prenom, nom, email, url
   - Request->validateFile(): size, MIME, extension
   - Business rule: URL OR file required
   ↓
5. File Handling Phase (if file present)
   - Request->moveFile('fichier', '/filestore/submissions/')
   - Returns: unique filename
   ↓
6. Database Phase
   - Prepare data array
   - Depose->createSubmission($data)
   - Returns: new ID
   ↓
7. Response Phase
   - Session->flash('success', 'Soumission enregistrée')
   - Redirect to success page or devoir detail
   ↓
8. Success Page Display
   - Show confirmation message
   - Display submission ID
```

### 4.3 Structure des Fichiers à Créer

```
src/
├── app/
│   ├── Controllers/
│   │   └── DeposeController.php          [NOUVEAU]
│   │       ├── create()                   # Afficher formulaire
│   │       └── store()                    # Traiter soumission
│   └── Views/
│       └── deposes/                       [NOUVEAU]
│           ├── create.php                 # Formulaire de soumission
│           └── success.php                # Page de confirmation

database/
└── migrations/
    └── 02-add-depose-fields.sql          [NOUVEAU]

filestore/
└── submissions/                           [NOUVEAU]
    └── .gitkeep
```

### 4.4 Composants à Modifier

```
src/app/Models/Depose.php
  → Ajouter 'email', 'taille_fichier', 'type_fichier' dans $fillable

src/config/routes.php
  → Ajouter routes GET et POST pour soumission

database/01-init.sql
  → Ajouter colonnes email, taille_fichier, type_fichier (pour futures installations)
```

---

## 5. Migration de la Base de Données

### 5.1 Script de Migration SQL

**Fichier** : `database/migrations/02-add-depose-fields.sql`

```sql
-- ============================================================================
-- Migration 02: Ajout des champs email, taille_fichier, type_fichier
-- Date: 2025-11-05
-- Description: Ajouter les colonnes manquantes pour la soumission de devoirs
-- ============================================================================

USE ADA;

-- Vérifier la structure actuelle de la table deposes
DESC deposes;

-- Ajouter la colonne email après prenom
ALTER TABLE deposes
ADD COLUMN email VARCHAR(100) NULL
AFTER prenom;

-- Ajouter la colonne taille_fichier après nomfichierstockage
ALTER TABLE deposes
ADD COLUMN taille_fichier INT NULL
COMMENT 'Taille du fichier en octets'
AFTER nomfichierstockage;

-- Ajouter la colonne type_fichier après taille_fichier
ALTER TABLE deposes
ADD COLUMN type_fichier VARCHAR(50) NULL
COMMENT 'Type MIME du fichier uploadé'
AFTER taille_fichier;

-- Créer un index sur email pour les recherches
CREATE INDEX idx_email ON deposes(email);

-- Vérifier la nouvelle structure
DESC deposes;

-- Afficher un exemple de la nouvelle structure
SELECT
    iddeposes,
    nom,
    prenom,
    email,
    datedepot,
    url,
    nomfichieroriginal,
    nomfichierstockage,
    taille_fichier,
    type_fichier,
    iddevoirs
FROM deposes
LIMIT 1;

-- ============================================================================
-- Rollback (si nécessaire)
-- ============================================================================
-- ALTER TABLE deposes DROP COLUMN email;
-- ALTER TABLE deposes DROP COLUMN taille_fichier;
-- ALTER TABLE deposes DROP COLUMN type_fichier;
-- DROP INDEX idx_email ON deposes;
```

### 5.2 Commandes d'Exécution

```bash
# Option 1: Exécuter via docker exec
docker exec -i ada_db mysql -uroot -p${DB_ROOT_PASS} ADA < database/migrations/02-add-depose-fields.sql

# Option 2: Exécuter via client MySQL interactif
docker exec -it ada_db mysql -uroot -p
# Puis copier/coller le contenu du script SQL

# Option 3: Via script PHP (si on veut automatiser)
php -r "
\$pdo = new PDO('mysql:host=localhost;dbname=ADA', 'root', getenv('DB_ROOT_PASS'));
\$sql = file_get_contents('database/migrations/02-add-depose-fields.sql');
\$pdo->exec(\$sql);
echo 'Migration executed successfully';
"
```

### 5.3 Validation de la Migration

```sql
-- Vérifier que les colonnes ont été ajoutées
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'ADA'
  AND TABLE_NAME = 'deposes'
  AND COLUMN_NAME IN ('email', 'taille_fichier', 'type_fichier');

-- Résultat attendu:
-- +------------------+-----------+---------------------------+-------------+-------------------------------+
-- | COLUMN_NAME      | DATA_TYPE | CHARACTER_MAXIMUM_LENGTH  | IS_NULLABLE | COLUMN_COMMENT                |
-- +------------------+-----------+---------------------------+-------------+-------------------------------+
-- | email            | varchar   | 100                       | YES         |                               |
-- | taille_fichier   | int       | NULL                      | YES         | Taille du fichier en octets   |
-- | type_fichier     | varchar   | 50                        | YES         | Type MIME du fichier uploadé  |
-- +------------------+-----------+---------------------------+-------------+-------------------------------+
```

### 5.4 Mise à Jour du Schema Initial (Optionnel)

Pour les **nouvelles installations**, mettre à jour `database/01-init.sql` :

```sql
CREATE TABLE IF NOT EXISTS deposes (
    iddeposes INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    email VARCHAR(100) NULL,                           -- AJOUTÉ
    datedepot DATETIME NOT NULL,
    url TEXT,
    nomfichieroriginal VARCHAR(255),
    nomfichierstockage VARCHAR(255),
    taille_fichier INT NULL COMMENT 'Taille du fichier en octets',         -- AJOUTÉ
    type_fichier VARCHAR(50) NULL COMMENT 'Type MIME du fichier uploadé',  -- AJOUTÉ
    iddevoirs INT NOT NULL,
    FOREIGN KEY (iddevoirs) REFERENCES devoirs(iddevoirs) ON DELETE CASCADE,
    INDEX idx_iddevoirs (iddevoirs),
    INDEX idx_datedepot (datedepot),
    INDEX idx_email (email)                            -- AJOUTÉ
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 6. Implémentation Complète

### 6.1 DeposeController.php

**Fichier** : `src/app/Controllers/DeposeController.php`

```php
<?php

namespace App\Controllers;

use Core\Controller;
use Core\Request;
use Core\Response;
use Core\Validator;
use Core\Security;
use Core\Session;
use App\Models\Devoir;
use App\Models\Depose;
use Exception;

/**
 * Contrôleur pour la gestion des soumissions de devoirs (dépôts)
 *
 * Gère l'affichage du formulaire de soumission et le traitement
 * des soumissions d'étudiants (URL ou fichier).
 */
class DeposeController extends Controller
{
    /**
     * Affiche le formulaire de soumission pour un devoir
     *
     * Route: GET /devoirs/{shortcode}/submit
     *
     * @param Request $request
     * @param string $shortcode Code unique du devoir
     * @return Response
     */
    public function create(Request $request, string $shortcode): Response
    {
        // 1. Récupérer le devoir par son shortcode
        $devoirModel = new Devoir();
        $devoir = $devoirModel->findByShortcode($shortcode);

        // 2. Vérifier que le devoir existe
        if (!$devoir) {
            Session::flash('error', "Le devoir avec le code '{$shortcode}' n'existe pas.");
            return $this->redirect('/devoirs');
        }

        // 3. Vérifier que le devoir est encore ouvert (date limite non dépassée)
        if (!$devoirModel->isOpen($devoir['iddevoirs'])) {
            Session::flash('error', "La date limite de soumission est dépassée pour ce devoir.");
            return $this->redirect('/devoirs/' . $shortcode);
        }

        // 4. Générer le token CSRF
        $csrfToken = Security::generateCsrfToken();

        // 5. Récupérer les anciennes valeurs du formulaire (en cas d'erreur de validation)
        $old = Session::get('old', []);

        // 6. Récupérer les erreurs de validation
        $errors = Session::get('errors', []);

        // 7. Rendre la vue avec les données
        return $this->view('deposes/create', [
            'devoir' => $devoir,
            'shortcode' => $shortcode,
            'csrfToken' => $csrfToken,
            'old' => $old,
            'errors' => $errors
        ]);
    }

    /**
     * Traite la soumission du formulaire de dépôt
     *
     * Route: POST /devoirs/{shortcode}/submit
     * Middleware: CsrfMiddleware
     *
     * @param Request $request
     * @param string $shortcode Code unique du devoir
     * @return Response
     */
    public function store(Request $request, string $shortcode): Response
    {
        try {
            // ============================================================
            // ÉTAPE 1: Vérifier que le devoir existe et est ouvert
            // ============================================================

            $devoirModel = new Devoir();
            $devoir = $devoirModel->findByShortcode($shortcode);

            if (!$devoir) {
                Session::flash('error', "Le devoir avec le code '{$shortcode}' n'existe pas.");
                return $this->redirect('/devoirs');
            }

            if (!$devoirModel->isOpen($devoir['iddevoirs'])) {
                Session::flash('error', "La date limite de soumission est dépassée.");
                return $this->redirect('/devoirs/' . $shortcode);
            }

            // ============================================================
            // ÉTAPE 2: Validation des données du formulaire
            // ============================================================

            $validator = new Validator($request->all(), [
                'prenom' => 'required|alpha|min:2|max:50',
                'nom' => 'required|alpha|min:2|max:50',
                'email' => 'required|email|max:100',
                'url' => 'nullable|url',
            ], [
                'prenom.required' => 'Le prénom est obligatoire.',
                'prenom.alpha' => 'Le prénom ne doit contenir que des lettres.',
                'prenom.min' => 'Le prénom doit contenir au moins 2 caractères.',
                'prenom.max' => 'Le prénom ne peut pas dépasser 50 caractères.',
                'nom.required' => 'Le nom est obligatoire.',
                'nom.alpha' => 'Le nom ne doit contenir que des lettres.',
                'nom.min' => 'Le nom doit contenir au moins 2 caractères.',
                'nom.max' => 'Le nom ne peut pas dépasser 50 caractères.',
                'email.required' => "L'adresse email est obligatoire.",
                'email.email' => "L'adresse email n'est pas valide.",
                'email.max' => "L'adresse email ne peut pas dépasser 100 caractères.",
                'url.url' => "L'URL n'est pas valide.",
            ]);

            if ($validator->fails()) {
                Session::flash('errors', $validator->errors());
                Session::flash('old', $request->all());
                return $this->redirect('/devoirs/' . $shortcode . '/submit');
            }

            $validatedData = $validator->validated();

            // ============================================================
            // ÉTAPE 3: Validation et traitement du fichier uploadé
            // ============================================================

            $fileData = [
                'nomfichieroriginal' => null,
                'nomfichierstockage' => null,
                'taille_fichier' => null,
                'type_fichier' => null,
            ];

            $hasFile = $request->hasFile('fichier');
            $hasUrl = !empty($validatedData['url']);

            // Vérifier qu'au moins URL ou Fichier est fourni
            if (!$hasFile && !$hasUrl) {
                Session::flash('errors', [
                    'fichier' => 'Veuillez fournir soit une URL valide, soit un fichier à télécharger.'
                ]);
                Session::flash('old', $request->all());
                return $this->redirect('/devoirs/' . $shortcode . '/submit');
            }

            if ($hasFile) {
                // Configuration de validation du fichier
                $maxSize = 10 * 1024 * 1024; // 10 MB
                $allowedMimeTypes = [
                    'image/jpeg',
                    'image/png',
                    'image/gif',
                    'application/pdf',
                    'text/plain',
                    'application/zip',
                    'application/x-zip-compressed',
                ];
                $allowedExtensions = ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt', 'zip'];

                // Valider le fichier
                if (!$request->validateFile('fichier', $maxSize, $allowedMimeTypes, $allowedExtensions)) {
                    Session::flash('errors', [
                        'fichier' => 'Le fichier est invalide. Formats autorisés: JPG, PNG, GIF, PDF, TXT, ZIP. Taille max: 10 MB.'
                    ]);
                    Session::flash('old', $request->all());
                    return $this->redirect('/devoirs/' . $shortcode . '/submit');
                }

                // Récupérer les informations du fichier original
                $file = $request->file('fichier');
                $fileData['nomfichieroriginal'] = $file['name'];
                $fileData['taille_fichier'] = $file['size'];
                $fileData['type_fichier'] = $file['type'];

                // Déplacer le fichier vers le stockage permanent
                $destination = __DIR__ . '/../../filestore/submissions';
                $storedFileName = $request->moveFile('fichier', $destination);

                if (!$storedFileName) {
                    throw new Exception("Erreur lors de l'enregistrement du fichier sur le serveur.");
                }

                $fileData['nomfichierstockage'] = $storedFileName;
            }

            // ============================================================
            // ÉTAPE 4: Sauvegarde en base de données
            // ============================================================

            $deposeModel = new Depose();

            $deposeData = [
                'nom' => $validatedData['nom'],
                'prenom' => $validatedData['prenom'],
                'email' => $validatedData['email'],
                'url' => $validatedData['url'] ?? null,
                'nomfichieroriginal' => $fileData['nomfichieroriginal'],
                'nomfichierstockage' => $fileData['nomfichierstockage'],
                'taille_fichier' => $fileData['taille_fichier'],
                'type_fichier' => $fileData['type_fichier'],
                'iddevoirs' => $devoir['iddevoirs'],
            ];

            // createSubmission() ajoute automatiquement la date de dépôt
            $newDeposeId = $deposeModel->createSubmission($deposeData);

            // ============================================================
            // ÉTAPE 5: Confirmation et redirection
            // ============================================================

            Session::flash('success', "Votre soumission a été enregistrée avec succès ! (ID: {$newDeposeId})");

            // Rediriger vers la page de succès
            return $this->redirect('/devoirs/' . $shortcode . '/submit/success');

        } catch (Exception $e) {
            // Log de l'erreur (si système de log implémenté)
            // Logger::error('Erreur lors de la soumission: ' . $e->getMessage());

            Session::flash('error', 'Une erreur est survenue lors de la soumission: ' . $e->getMessage());
            Session::flash('old', $request->all());
            return $this->redirect('/devoirs/' . $shortcode . '/submit');
        }
    }

    /**
     * Affiche la page de confirmation de soumission
     *
     * Route: GET /devoirs/{shortcode}/submit/success
     *
     * @param Request $request
     * @param string $shortcode
     * @return Response
     */
    public function success(Request $request, string $shortcode): Response
    {
        // Vérifier qu'il y a bien un message de succès (évite l'accès direct)
        $successMessage = Session::get('success');

        if (!$successMessage) {
            return $this->redirect('/devoirs/' . $shortcode . '/submit');
        }

        // Récupérer le devoir pour affichage
        $devoirModel = new Devoir();
        $devoir = $devoirModel->findByShortcode($shortcode);

        return $this->view('deposes/success', [
            'devoir' => $devoir,
            'shortcode' => $shortcode,
            'message' => $successMessage
        ]);
    }
}
```

### 6.2 Vue : deposes/create.php

**Fichier** : `src/app/Views/deposes/create.php`

```php
<?php
/**
 * Vue: Formulaire de soumission de devoir
 *
 * Variables disponibles:
 * @var array $devoir Informations du devoir
 * @var string $shortcode Code du devoir
 * @var string $csrfToken Token CSRF
 * @var array $old Anciennes valeurs du formulaire
 * @var array $errors Erreurs de validation
 */

use Core\Security;

$pageTitle = 'Soumettre un devoir';
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($pageTitle) ?> - ADA</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 16px;
            opacity: 0.9;
        }

        .content {
            padding: 40px;
        }

        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            font-size: 14px;
        }

        .alert-error {
            background: #fee;
            border: 1px solid #fcc;
            color: #c33;
        }

        .alert-success {
            background: #efe;
            border: 1px solid #cfc;
            color: #3c3;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 14px;
        }

        .form-group label .required {
            color: #e53e3e;
            margin-left: 3px;
        }

        .form-group input[type="text"],
        .form-group input[type="email"],
        .form-group input[type="url"],
        .form-group input[type="file"] {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 15px;
            transition: border-color 0.3s, box-shadow 0.3s;
        }

        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-group.has-error input {
            border-color: #fc8181;
        }

        .error-message {
            color: #e53e3e;
            font-size: 13px;
            margin-top: 6px;
            display: block;
        }

        .form-hint {
            color: #718096;
            font-size: 13px;
            margin-top: 6px;
            display: block;
        }

        .divider {
            text-align: center;
            margin: 30px 0;
            position: relative;
        }

        .divider::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            width: 100%;
            height: 1px;
            background: #e2e8f0;
        }

        .divider span {
            background: white;
            padding: 0 15px;
            position: relative;
            z-index: 1;
            color: #718096;
            font-size: 14px;
            font-weight: 600;
        }

        .submit-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        .submit-btn:active {
            transform: translateY(0);
        }

        .back-link {
            display: inline-block;
            margin-top: 20px;
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
        }

        .back-link:hover {
            text-decoration: underline;
        }

        .file-input-wrapper {
            position: relative;
        }

        .file-input-wrapper input[type="file"] {
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Soumettre un devoir</h1>
            <p>Code: <strong><?= htmlspecialchars($shortcode) ?></strong></p>
            <?php if (isset($devoir['datelimite'])): ?>
                <p style="font-size: 14px; margin-top: 5px;">
                    Date limite: <?= date('d/m/Y à H:i', strtotime($devoir['datelimite'])) ?>
                </p>
            <?php endif; ?>
        </div>

        <div class="content">
            <?php if (isset($errors['fichier'])): ?>
                <div class="alert alert-error">
                    <?= htmlspecialchars($errors['fichier']) ?>
                </div>
            <?php endif; ?>

            <form action="/devoirs/<?= htmlspecialchars($shortcode) ?>/submit"
                  method="POST"
                  enctype="multipart/form-data">

                <!-- CSRF Token (obligatoire pour la sécurité) -->
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($csrfToken) ?>">

                <!-- Informations personnelles -->
                <div class="form-group <?= isset($errors['prenom']) ? 'has-error' : '' ?>">
                    <label for="prenom">
                        Prénom <span class="required">*</span>
                    </label>
                    <input
                        type="text"
                        id="prenom"
                        name="prenom"
                        value="<?= htmlspecialchars($old['prenom'] ?? '') ?>"
                        placeholder="Votre prénom"
                        required
                    >
                    <?php if (isset($errors['prenom'])): ?>
                        <span class="error-message"><?= htmlspecialchars($errors['prenom']) ?></span>
                    <?php endif; ?>
                </div>

                <div class="form-group <?= isset($errors['nom']) ? 'has-error' : '' ?>">
                    <label for="nom">
                        Nom <span class="required">*</span>
                    </label>
                    <input
                        type="text"
                        id="nom"
                        name="nom"
                        value="<?= htmlspecialchars($old['nom'] ?? '') ?>"
                        placeholder="Votre nom"
                        required
                    >
                    <?php if (isset($errors['nom'])): ?>
                        <span class="error-message"><?= htmlspecialchars($errors['nom']) ?></span>
                    <?php endif; ?>
                </div>

                <div class="form-group <?= isset($errors['email']) ? 'has-error' : '' ?>">
                    <label for="email">
                        Email <span class="required">*</span>
                    </label>
                    <input
                        type="email"
                        id="email"
                        name="email"
                        value="<?= htmlspecialchars($old['email'] ?? '') ?>"
                        placeholder="votre.email@example.com"
                        required
                    >
                    <?php if (isset($errors['email'])): ?>
                        <span class="error-message"><?= htmlspecialchars($errors['email']) ?></span>
                    <?php endif; ?>
                </div>

                <div class="divider">
                    <span>Soumission du travail</span>
                </div>

                <p style="text-align: center; color: #718096; font-size: 14px; margin-bottom: 25px;">
                    Fournissez <strong>soit une URL</strong>, <strong>soit un fichier</strong> (ou les deux)
                </p>

                <!-- URL optionnelle -->
                <div class="form-group <?= isset($errors['url']) ? 'has-error' : '' ?>">
                    <label for="url">
                        URL de votre travail (optionnel)
                    </label>
                    <input
                        type="url"
                        id="url"
                        name="url"
                        value="<?= htmlspecialchars($old['url'] ?? '') ?>"
                        placeholder="https://github.com/votrecompte/projet"
                    >
                    <?php if (isset($errors['url'])): ?>
                        <span class="error-message"><?= htmlspecialchars($errors['url']) ?></span>
                    <?php endif; ?>
                    <span class="form-hint">
                        Lien vers votre dépôt Git, Google Drive, etc.
                    </span>
                </div>

                <!-- Upload de fichier optionnel -->
                <div class="form-group file-input-wrapper">
                    <label for="fichier">
                        Fichier à envoyer (optionnel)
                    </label>
                    <input
                        type="file"
                        id="fichier"
                        name="fichier"
                        accept=".jpg,.jpeg,.png,.gif,.pdf,.txt,.zip"
                    >
                    <span class="form-hint">
                        Formats acceptés: JPG, PNG, GIF, PDF, TXT, ZIP • Taille max: 10 MB
                    </span>
                </div>

                <!-- Bouton de soumission -->
                <button type="submit" class="submit-btn">
                    ✓ Soumettre mon devoir
                </button>
            </form>

            <a href="/devoirs/<?= htmlspecialchars($shortcode) ?>" class="back-link">
                ← Retour au devoir
            </a>
        </div>
    </div>

    <script>
        // Validation côté client basique
        document.querySelector('form').addEventListener('submit', function(e) {
            const url = document.getElementById('url').value.trim();
            const file = document.getElementById('fichier').files.length > 0;

            if (!url && !file) {
                e.preventDefault();
                alert('Veuillez fournir soit une URL valide, soit un fichier à télécharger.');
                return false;
            }
        });
    </script>
</body>
</html>
```

### 6.3 Vue : deposes/success.php

**Fichier** : `src/app/Views/deposes/success.php`

```php
<?php
/**
 * Vue: Page de confirmation de soumission
 *
 * Variables disponibles:
 * @var array|null $devoir Informations du devoir
 * @var string $shortcode Code du devoir
 * @var string $message Message de succès
 */

$pageTitle = 'Soumission réussie';
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($pageTitle) ?> - ADA</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            max-width: 600px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
            text-align: center;
        }

        .success-icon {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 50px;
        }

        .success-icon svg {
            width: 100px;
            height: 100px;
            animation: checkmark 0.8s ease-in-out;
        }

        @keyframes checkmark {
            0% {
                transform: scale(0) rotate(-45deg);
                opacity: 0;
            }
            50% {
                transform: scale(1.2) rotate(-45deg);
                opacity: 1;
            }
            100% {
                transform: scale(1) rotate(0deg);
                opacity: 1;
            }
        }

        .content {
            padding: 40px;
        }

        .content h1 {
            color: #2d3748;
            font-size: 28px;
            margin-bottom: 15px;
        }

        .success-message {
            background: #c6f6d5;
            border: 2px solid #9ae6b4;
            color: #22543d;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
            font-size: 16px;
            font-weight: 500;
        }

        .info-box {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
            text-align: left;
        }

        .info-box h3 {
            color: #2d3748;
            font-size: 18px;
            margin-bottom: 15px;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }

        .info-row:last-child {
            border-bottom: none;
        }

        .info-label {
            color: #718096;
            font-weight: 500;
        }

        .info-value {
            color: #2d3748;
            font-weight: 600;
        }

        .actions {
            margin-top: 30px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }

        .btn {
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
            display: inline-block;
        }

        .btn:hover {
            transform: translateY(-2px);
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }

        .btn-secondary {
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
        </div>

        <div class="content">
            <h1>✓ Soumission réussie !</h1>

            <div class="success-message">
                <?= htmlspecialchars($message) ?>
            </div>

            <div class="info-box">
                <h3>📋 Informations</h3>
                <div class="info-row">
                    <span class="info-label">Code du devoir:</span>
                    <span class="info-value"><?= htmlspecialchars($shortcode) ?></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Date de soumission:</span>
                    <span class="info-value"><?= date('d/m/Y à H:i:s') ?></span>
                </div>
                <?php if ($devoir && isset($devoir['datelimite'])): ?>
                <div class="info-row">
                    <span class="info-label">Date limite:</span>
                    <span class="info-value"><?= date('d/m/Y à H:i', strtotime($devoir['datelimite'])) ?></span>
                </div>
                <?php endif; ?>
            </div>

            <p style="color: #718096; font-size: 14px; margin: 20px 0;">
                Votre travail a été enregistré avec succès. Vous recevrez une confirmation par email si vous en avez fourni un.
            </p>

            <div class="actions">
                <a href="/devoirs" class="btn btn-primary">
                    Voir tous les devoirs
                </a>
                <a href="/devoirs/<?= htmlspecialchars($shortcode) ?>" class="btn btn-secondary">
                    Retour au devoir
                </a>
            </div>
        </div>
    </div>
</body>
</html>
```

### 6.4 Mise à Jour : Model Depose.php

**Fichier** : `src/app/Models/Depose.php`

Mettre à jour l'array `$fillable` pour inclure les nouveaux champs :

```php
<?php

namespace App\Models;

use Core\Model;

class Depose extends Model
{
    protected string $table = 'deposes';
    protected string $primaryKey = 'iddeposes';

    /**
     * Champs autorisés pour l'insertion/mise à jour en masse
     */
    protected array $fillable = [
        'nom',
        'prenom',
        'email',                    // AJOUTÉ
        'datedepot',
        'url',
        'nomfichieroriginal',
        'nomfichierstockage',
        'taille_fichier',           // AJOUTÉ
        'type_fichier',             // AJOUTÉ
        'iddevoirs'
    ];

    /**
     * Récupère toutes les soumissions pour un devoir donné
     */
    public function getByDevoir(int $idDevoirs): array
    {
        return $this->where('iddevoirs', '=', $idDevoirs)
                    ->orderBy('datedepot', 'DESC')
                    ->get();
    }

    /**
     * Récupère les soumissions par nom d'étudiant
     */
    public function getByStudent(string $nom, string $prenom): array
    {
        return $this->where('nom', '=', $nom)
                    ->where('prenom', '=', $prenom)
                    ->orderBy('datedepot', 'DESC')
                    ->get();
    }

    /**
     * Récupère les soumissions par email
     * NOUVELLE MÉTHODE
     */
    public function getByEmail(string $email): array
    {
        return $this->where('email', '=', $email)
                    ->orderBy('datedepot', 'DESC')
                    ->get();
    }

    /**
     * Récupère une soumission avec les informations du devoir associé
     */
    public function findWithDevoir(int $id): ?array
    {
        $sql = "SELECT d.*, dv.shortcode, dv.datelimite
                FROM {$this->table} d
                INNER JOIN devoirs dv ON d.iddevoirs = dv.iddevoirs
                WHERE d.{$this->primaryKey} = ?";

        $result = $this->db->query($sql, [$id]);
        return $result[0] ?? null;
    }

    /**
     * Crée une nouvelle soumission avec timestamp automatique
     */
    public function createSubmission(array $data): int
    {
        // Ajouter automatiquement la date de dépôt
        $data['datedepot'] = date('Y-m-d H:i:s');

        return $this->create($data);
    }

    /**
     * Compte le nombre de soumissions pour un devoir
     * NOUVELLE MÉTHODE
     */
    public function countByDevoir(int $idDevoirs): int
    {
        $sql = "SELECT COUNT(*) as count FROM {$this->table} WHERE iddevoirs = ?";
        $result = $this->db->query($sql, [$idDevoirs]);
        return (int)($result[0]['count'] ?? 0);
    }
}
```

### 6.5 Mise à Jour : Routes (routes.php)

**Fichier** : `src/config/routes.php`

Ajouter les routes pour la soumission de devoirs :

```php
<?php

/**
 * Configuration des routes de l'application
 *
 * Format: [METHOD, PATH, CONTROLLER@ACTION, OPTIONS]
 */

return [
    // ================================================================
    // Routes existantes (Devoirs)
    // ================================================================
    ['GET', '/', 'DevoirController@index'],
    ['GET', '/devoirs', 'DevoirController@index'],
    ['GET', '/devoirs/{shortcode}', 'DevoirController@show'],

    // ================================================================
    // Routes pour les soumissions (Dépôts) - NOUVELLES
    // ================================================================

    /**
     * Afficher le formulaire de soumission
     * Route: GET /devoirs/{shortcode}/submit
     */
    [
        'GET',
        '/devoirs/{shortcode}/submit',
        'DeposeController@create',
        ['name' => 'depose.create']
    ],

    /**
     * Traiter la soumission du formulaire
     * Route: POST /devoirs/{shortcode}/submit
     * Middleware: CsrfMiddleware (protection CSRF)
     */
    [
        'POST',
        '/devoirs/{shortcode}/submit',
        'DeposeController@store',
        [
            'name' => 'depose.store',
            'middleware' => ['CsrfMiddleware']
        ]
    ],

    /**
     * Page de confirmation de soumission
     * Route: GET /devoirs/{shortcode}/submit/success
     */
    [
        'GET',
        '/devoirs/{shortcode}/submit/success',
        'DeposeController@success',
        ['name' => 'depose.success']
    ],

    // ================================================================
    // Routes futures (à implémenter)
    // ================================================================
    // ['GET', '/admin/deposes', 'Admin\DeposeController@index'],
    // ['GET', '/admin/deposes/{id}', 'Admin\DeposeController@show'],
];
```

### 6.6 Création du Répertoire de Stockage

```bash
# Créer le répertoire pour les fichiers uploadés
mkdir -p filestore/submissions

# Ajouter un .gitkeep pour tracker le dossier vide
touch filestore/submissions/.gitkeep

# Définir les permissions appropriées
chmod 755 filestore/submissions

# Vérifier la structure
ls -la filestore/
```

**Fichier** : `filestore/submissions/.gitkeep`

```
# Ce fichier permet de tracker le dossier vide dans Git
# Les fichiers uploadés ne sont PAS commités (voir .gitignore)
```

**Mise à jour de `.gitignore`** :

```gitignore
# Fichiers uploadés (ne pas commiter)
filestore/submissions/*
!filestore/submissions/.gitkeep
```

---

## 7. Spécifications de Sécurité

### 7.1 Protection CSRF

**Mécanisme** : Validation automatique via `CsrfMiddleware`

```php
// Le middleware vérifie automatiquement le token CSRF sur toutes les requêtes POST
// Configuration: src/app/Middleware/CsrfMiddleware.php (lignes 20-31)

// Dans le formulaire (create.php)
<input type="hidden" name="csrf_token" value="<?= Security::generateCsrfToken() ?>">

// Validation automatique côté serveur
// Si le token est invalide ou manquant → Exception + 403 Forbidden
```

**Avantages** :
- ✅ Protection contre les attaques CSRF
- ✅ Token régénéré à chaque session
- ✅ Comparaison timing-safe avec `hash_equals()`
- ✅ Pas besoin de validation manuelle dans le contrôleur

### 7.2 Validation des Fichiers Uploadés

**Validations implémentées** :

```php
// 1. Vérification de la présence du fichier
$request->hasFile('fichier')  // Vérifie UPLOAD_ERR_OK

// 2. Validation de la taille (10 MB max)
$maxSize = 10 * 1024 * 1024;

// 3. Validation du type MIME
$allowedMimeTypes = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'text/plain',
    'application/zip',
    'application/x-zip-compressed',
];

// 4. Validation de l'extension réelle
$allowedExtensions = ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt', 'zip'];

// 5. Nom de fichier sécurisé
$storedFileName = bin2hex(random_bytes(16)) . '.' . $extension;
// Exemple: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.pdf
```

**Protection contre les attaques** :

| Attaque | Protection |
|---------|-----------|
| **Upload de fichiers malveillants** | Whitelist MIME types + extensions |
| **Path traversal** | Nom généré aléatoirement, pas d'utilisation du nom original |
| **Overwrite de fichiers** | `random_bytes(16)` garantit l'unicité (2^128 possibilités) |
| **Déni de service (DoS)** | Limite de taille 10 MB par fichier |
| **Spoofing MIME** | Double vérification: MIME + extension |

### 7.3 Validation des Données Utilisateur

**Règles de validation** :

```php
$validator = new Validator($request->all(), [
    'prenom' => 'required|alpha|min:2|max:50',     // Lettres uniquement, 2-50 chars
    'nom' => 'required|alpha|min:2|max:50',        // Lettres uniquement, 2-50 chars
    'email' => 'required|email|max:100',            // Format email RFC 5322
    'url' => 'nullable|url',                        // Format URL RFC 3986 (optionnel)
]);
```

**Protection contre** :
- ✅ **XSS** : Validation stricte des caractères (alpha pour nom/prénom)
- ✅ **SQL Injection** : Utilisation de prepared statements dans Model
- ✅ **Buffer overflow** : Limites de longueur (max:50, max:100)
- ✅ **Script injection** : URLs validées avec `filter_var(FILTER_VALIDATE_URL)`

### 7.4 Échappement des Sorties (XSS Prevention)

**Dans les vues** :

```php
// Toutes les données utilisateur sont échappées avec htmlspecialchars()
<?= htmlspecialchars($shortcode) ?>
<?= htmlspecialchars($devoir['datelimite']) ?>
<?= htmlspecialchars($old['prenom'] ?? '') ?>
<?= htmlspecialchars($errors['nom']) ?>

// Configuration de htmlspecialchars:
// - ENT_QUOTES : Échappe ' et "
// - UTF-8 : Support des caractères multi-octets
// - ENT_SUBSTITUTE : Remplace les séquences invalides
```

**Contextes d'échappement** :

| Contexte | Méthode | Exemple |
|----------|---------|---------|
| HTML | `htmlspecialchars()` | `<p><?= htmlspecialchars($text) ?></p>` |
| Attribut HTML | `htmlspecialchars()` | `<input value="<?= htmlspecialchars($val) ?>">` |
| URL | `urlencode()` | `<a href="/page?id=<?= urlencode($id) ?>">` |
| JavaScript | `json_encode(,JSON_HEX_TAG)` | `var data = <?= json_encode($data, JSON_HEX_TAG) ?>;` |

### 7.5 Gestion Sécurisée des Sessions

**Configuration** (dans `Session::start()`) :

```php
session_start([
    'cookie_httponly' => true,     // Pas d'accès JavaScript
    'cookie_secure' => true,       // HTTPS uniquement (production)
    'cookie_samesite' => 'Strict', // Protection CSRF additionnelle
    'use_strict_mode' => true,     // Rejette les IDs de session non initialisés
]);
```

**Flash messages** :
```php
// Stockage temporaire (1 requête)
Session::flash('success', 'Message');
Session::flash('errors', ['field' => 'Error message']);

// Lecture et suppression automatique
$success = Session::get('success'); // null à la 2e lecture
```

### 7.6 Sécurité du Stockage des Fichiers

**Structure de stockage** :

```
filestore/submissions/
├── a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.pdf
├── f9e8d7c6b5a4g3h2i1j0k9l8m7n6o5p4.jpg
└── ...
```

**Règles de sécurité** :
1. ✅ **Hors de la racine web** : `/filestore/` n'est pas accessible via HTTP direct
2. ✅ **Noms aléatoires** : Impossible de deviner les noms de fichiers
3. ✅ **Pas de liste de répertoire** : Apache `Options -Indexes`
4. ✅ **Permissions restrictives** : `chmod 755` (lecture/écriture propriétaire seulement)
5. ✅ **Tracking du nom original** : Stocké en DB pour affichage/téléchargement

**Serving des fichiers** (à implémenter dans le futur) :

```php
// Contrôleur pour servir les fichiers de manière sécurisée
public function download(Request $request, int $id): Response
{
    $depose = $this->deposeModel->find($id);

    // Vérifier les permissions (authentification, autorisation)
    if (!$this->canAccessDepose($depose)) {
        return $this->error(403, 'Accès refusé');
    }

    $filePath = '/filestore/submissions/' . $depose['nomfichierstockage'];

    // Servir le fichier avec headers sécurisés
    return $this->download($filePath, $depose['nomfichieroriginal']);
}
```

### 7.7 Logging et Audit (Recommandations Futures)

**À implémenter** :

```php
// Logger toutes les soumissions
Logger::info('Nouvelle soumission', [
    'depose_id' => $newDeposeId,
    'devoir_shortcode' => $shortcode,
    'email' => $validatedData['email'],
    'has_file' => $hasFile,
    'has_url' => $hasUrl,
    'ip_address' => $request->ip(),
    'user_agent' => $request->userAgent(),
    'timestamp' => date('Y-m-d H:i:s'),
]);

// Logger les erreurs de validation
Logger::warning('Validation failed', [
    'errors' => $validator->errors(),
    'input' => $request->except(['fichier']), // Ne pas logger les fichiers
]);

// Logger les tentatives de CSRF
Logger::error('CSRF validation failed', [
    'url' => $request->url(),
    'ip_address' => $request->ip(),
]);
```

---

## 8. Plan de Migration (Checklist)

### Phase 1: Préparation de la Base de Données

```
☐ Sauvegarder la base de données actuelle
  └─ docker exec ada_db mysqldump -uroot -p ADA > backup_$(date +%Y%m%d).sql

☐ Exécuter le script de migration SQL
  └─ docker exec -i ada_db mysql -uroot -p ADA < database/migrations/02-add-depose-fields.sql

☐ Vérifier que les colonnes ont été ajoutées
  └─ mysql> DESC deposes;
  └─ Colonnes attendues: email, taille_fichier, type_fichier

☐ Tester une insertion manuelle avec les nouveaux champs
  └─ INSERT INTO deposes (nom, prenom, email, ...) VALUES (...);
```

### Phase 2: Création des Composants MVC

```
☐ Créer le contrôleur DeposeController.php
  └─ Fichier: src/app/Controllers/DeposeController.php
  └─ Méthodes: create(), store(), success()

☐ Créer les vues de soumission
  └─ Fichier: src/app/Views/deposes/create.php
  └─ Fichier: src/app/Views/deposes/success.php

☐ Mettre à jour le modèle Depose.php
  └─ Ajouter 'email', 'taille_fichier', 'type_fichier' dans $fillable
  └─ Ajouter la méthode getByEmail()
  └─ Ajouter la méthode countByDevoir()

☐ Mettre à jour les routes
  └─ Fichier: src/config/routes.php
  └─ Ajouter 3 routes: GET create, POST store, GET success
```

### Phase 3: Configuration du Stockage de Fichiers

```
☐ Créer le répertoire de stockage
  └─ mkdir -p filestore/submissions

☐ Définir les permissions appropriées
  └─ chmod 755 filestore/submissions

☐ Ajouter .gitkeep pour tracker le dossier vide
  └─ touch filestore/submissions/.gitkeep

☐ Mettre à jour .gitignore
  └─ Ajouter: filestore/submissions/*
  └─ Excepter: !filestore/submissions/.gitkeep
```

### Phase 4: Tests Fonctionnels

```
☐ Tester l'affichage du formulaire
  └─ Naviguer vers: http://localhost:8080/devoirs/ABC123/submit
  └─ Vérifier: Formulaire affiché avec token CSRF
  └─ Vérifier: Messages d'information sur date limite

☐ Tester la validation des champs obligatoires
  └─ Soumettre formulaire vide
  └─ Vérifier: Messages d'erreur affichés pour prenom, nom, email

☐ Tester la validation email
  └─ Saisir email invalide (ex: "test@")
  └─ Vérifier: Message "L'email n'est pas valide"

☐ Tester la règle "URL OU Fichier"
  └─ Soumettre sans URL ni fichier
  └─ Vérifier: Message "Veuillez fournir soit une URL..."

☐ Tester l'upload avec fichier valide
  └─ Uploader un fichier PDF < 10MB
  └─ Vérifier: Fichier déplacé dans filestore/submissions/
  └─ Vérifier: Nom de fichier aléatoire (32 chars + extension)
  └─ Vérifier: Données enregistrées en DB

☐ Tester l'upload avec fichier invalide
  └─ Uploader un fichier .exe (non autorisé)
  └─ Vérifier: Message d'erreur type de fichier
  └─ Uploader un fichier > 10MB
  └─ Vérifier: Message d'erreur taille de fichier

☐ Tester la soumission avec URL uniquement
  └─ Saisir URL valide (ex: https://github.com/user/repo)
  └─ Vérifier: Enregistrement en DB sans fichier

☐ Tester la soumission avec URL + Fichier
  └─ Saisir URL + uploader fichier
  └─ Vérifier: Les deux enregistrés correctement

☐ Tester la protection CSRF
  └─ Modifier le token CSRF dans le HTML (DevTools)
  └─ Soumettre le formulaire
  └─ Vérifier: Erreur "CSRF token validation failed"

☐ Tester la page de succès
  └─ Soumettre formulaire valide
  └─ Vérifier: Redirection vers /submit/success
  └─ Vérifier: Message de confirmation avec ID
  └─ Vérifier: Informations du devoir affichées

☐ Tester l'accès direct à la page de succès
  └─ Naviguer directement vers /submit/success
  └─ Vérifier: Redirection vers formulaire (pas de message)
```

### Phase 5: Tests de Sécurité

```
☐ Test XSS dans les champs texte
  └─ Saisir: <script>alert('XSS')</script> dans prénom
  └─ Vérifier: Code échappé, pas d'alerte JavaScript

☐ Test SQL Injection
  └─ Saisir: ' OR '1'='1 dans nom
  └─ Vérifier: Traité comme texte normal, pas d'erreur SQL

☐ Test Path Traversal
  └─ Uploader fichier nommé: ../../../../etc/passwd
  └─ Vérifier: Nom de fichier régénéré, pas de traversal

☐ Test limite de taille fichier
  └─ Uploader fichier de 11 MB
  └─ Vérifier: Rejet avec message approprié

☐ Test MIME type spoofing
  └─ Renommer .exe en .pdf et uploader
  └─ Vérifier: Rejet (validation extension)
```

### Phase 6: Tests de Base de Données

```
☐ Vérifier l'enregistrement complet
  └─ mysql> SELECT * FROM deposes ORDER BY iddeposes DESC LIMIT 1;
  └─ Vérifier présence de toutes les données:
      - nom, prenom, email (nouveau)
      - datedepot (timestamp automatique)
      - url (si fournie)
      - nomfichieroriginal, nomfichierstockage (si fichier)
      - taille_fichier, type_fichier (nouveaux, si fichier)
      - iddevoirs (clé étrangère)

☐ Vérifier l'intégrité référentielle
  └─ mysql> SELECT d.*, dv.shortcode FROM deposes d
             INNER JOIN devoirs dv ON d.iddevoirs = dv.iddevoirs
             WHERE d.iddeposes = [ID];
  └─ Vérifier: JOIN fonctionne correctement

☐ Tester les méthodes du modèle
  └─ Depose::getByEmail('test@example.com')
  └─ Depose::countByDevoir($idDevoirs)
  └─ Depose::findWithDevoir($id)
```

### Phase 7: Vérifications Finales

```
☐ Vérifier les logs d'erreur
  └─ cat src/logs/error.log
  └─ Vérifier: Aucune erreur PHP

☐ Vérifier la structure des fichiers
  └─ ls -la filestore/submissions/
  └─ Vérifier: Fichiers stockés avec noms aléatoires

☐ Tester le flow complet end-to-end
  └─ Liste devoirs → Détail devoir → Formulaire soumission → Succès

☐ Vérifier la compatibilité mobile
  └─ Tester sur viewport mobile (responsive design)

☐ Documentation du code
  └─ Vérifier: Commentaires PHPDoc présents
  └─ Vérifier: Commentaires inline pour logique complexe
```

### Phase 8: Migration de post.php

```
☐ Renommer post.php en post.php.old
  └─ mv src/post.php src/post.php.old

☐ Créer un fichier de redirection (optionnel)
  └─ Créer: src/post.php avec redirection vers nouvelle route

☐ Mettre à jour la documentation
  └─ Mettre à jour CLAUDE.md avec nouvelle architecture
  └─ Documenter les changements dans un fichier CHANGELOG.md

☐ Commit et tag de version
  └─ git add .
  └─ git commit -m "Intégration post.php dans architecture MVC"
  └─ git tag -a v1.0.0 -m "Version 1.0 - MVC complet avec soumissions"
```

### Phase 9: Déploiement (Si applicable)

```
☐ Vérifier la configuration de production
  └─ Vérifier .env (credentials DB, paths)
  └─ Vérifier permissions filestore/ en production

☐ Exécuter les migrations sur le serveur de production
  └─ Backup production DB
  └─ Exécuter 02-add-depose-fields.sql

☐ Déployer le code
  └─ git pull origin main (ou via CI/CD)
  └─ Vérifier permissions et ownership des fichiers

☐ Tests post-déploiement
  └─ Tester une soumission réelle en production
  └─ Vérifier les logs de production
```

---

## 9. Tests et Validation

### 9.1 Tests Unitaires (Recommandations)

**Tests pour DeposeController** :

```php
class DeposeControllerTest extends TestCase
{
    public function test_create_displays_form_for_valid_devoir()
    {
        // Arrange
        $shortcode = 'ABC123';
        // Act
        $response = $this->get("/devoirs/{$shortcode}/submit");
        // Assert
        $this->assertResponseOk($response);
        $this->assertViewIs('deposes/create');
        $this->assertViewHas('csrfToken');
    }

    public function test_create_redirects_for_expired_devoir()
    {
        // Arrange
        $shortcode = 'EXPIRED';
        // Act
        $response = $this->get("/devoirs/{$shortcode}/submit");
        // Assert
        $this->assertRedirect($response);
        $this->assertSessionHas('error');
    }

    public function test_store_validates_required_fields()
    {
        // Arrange
        $data = ['prenom' => '', 'nom' => '', 'email' => ''];
        // Act
        $response = $this->post("/devoirs/ABC123/submit", $data);
        // Assert
        $this->assertRedirect($response);
        $this->assertSessionHas('errors');
    }

    public function test_store_requires_url_or_file()
    {
        // Arrange
        $data = [
            'prenom' => 'Jean',
            'nom' => 'Dupont',
            'email' => 'jean@example.com',
            'csrf_token' => Session::get('csrf_token'),
        ];
        // Act
        $response = $this->post("/devoirs/ABC123/submit", $data);
        // Assert
        $this->assertSessionHasError('fichier');
    }

    public function test_store_saves_submission_with_file()
    {
        // Arrange
        $file = $this->createUploadedFile('test.pdf', 'application/pdf');
        $data = [
            'prenom' => 'Jean',
            'nom' => 'Dupont',
            'email' => 'jean@example.com',
            'fichier' => $file,
            'csrf_token' => Session::get('csrf_token'),
        ];
        // Act
        $response = $this->post("/devoirs/ABC123/submit", $data);
        // Assert
        $this->assertRedirect($response, '/devoirs/ABC123/submit/success');
        $this->assertDatabaseHas('deposes', [
            'nom' => 'Dupont',
            'prenom' => 'Jean',
            'email' => 'jean@example.com',
        ]);
    }
}
```

### 9.2 Tests d'Intégration

**Scénario 1 : Soumission complète avec fichier**

```
1. GET /devoirs/ABC123/submit
   → 200 OK, formulaire affiché

2. POST /devoirs/ABC123/submit
   Données: prenom=Jean, nom=Dupont, email=jean@test.com, fichier=test.pdf
   → 302 Redirect vers /devoirs/ABC123/submit/success

3. Vérification DB:
   SELECT * FROM deposes WHERE email='jean@test.com'
   → 1 ligne trouvée avec toutes les données

4. Vérification fichier:
   ls filestore/submissions/[RANDOM_NAME].pdf
   → Fichier existe

5. GET /devoirs/ABC123/submit/success
   → 200 OK, page de confirmation affichée
```

**Scénario 2 : Validation d'erreur**

```
1. GET /devoirs/ABC123/submit
   → 200 OK

2. POST /devoirs/ABC123/submit
   Données: prenom=, nom=, email=invalid
   → 302 Redirect vers /devoirs/ABC123/submit

3. GET /devoirs/ABC123/submit (après redirect)
   → 200 OK
   → Erreurs affichées: "Le prénom est obligatoire", "Le nom est obligatoire", "L'email n'est pas valide"
   → Champs du formulaire vides
```

**Scénario 3 : Protection CSRF**

```
1. GET /devoirs/ABC123/submit
   → 200 OK, token CSRF généré

2. POST /devoirs/ABC123/submit
   Données: prenom=Jean, nom=Dupont, email=jean@test.com, csrf_token=INVALID_TOKEN
   → 403 Forbidden
   → Exception: "CSRF token validation failed"
```

### 9.3 Tests de Performance

**Métriques cibles** :

```
☐ Temps de réponse GET /submit
  └─ Cible: < 100ms
  └─ Test: ab -n 1000 -c 10 http://localhost:8080/devoirs/ABC123/submit

☐ Temps de traitement POST /submit (avec fichier 5MB)
  └─ Cible: < 2 secondes
  └─ Test: Mesurer avec microtime() dans le contrôleur

☐ Utilisation mémoire
  └─ Cible: < 10MB par requête
  └─ Test: memory_get_peak_usage()

☐ Nombre de requêtes SQL par soumission
  └─ Cible: < 5 requêtes
  └─ Test: Activer le query log MySQL et compter
```

### 9.4 Tests de Sécurité Automatisés

**Outils recommandés** :

```bash
# OWASP ZAP - Scanner de vulnérabilités
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8080/devoirs/ABC123/submit

# PHPStan - Analyse statique du code
./vendor/bin/phpstan analyse src/app/Controllers/DeposeController.php --level=8

# PHP Security Checker - Vérification des dépendances
php security-checker security:check composer.lock
```

### 9.5 Validation Manuelle (Checklist)

```
☐ Tester avec différents navigateurs
  └─ Chrome/Chromium
  └─ Firefox
  └─ Safari
  └─ Edge

☐ Tester avec différents types de fichiers
  └─ PDF: test.pdf
  └─ Image JPG: photo.jpg
  └─ Image PNG: screenshot.png
  └─ ZIP: archive.zip
  └─ Fichier non autorisé: script.exe (doit être rejeté)

☐ Tester avec noms de fichiers spéciaux
  └─ Espaces: "mon fichier.pdf"
  └─ Caractères spéciaux: "éàç-file.pdf"
  └─ Très long: "aaaaa...[250 chars]...aaaaa.pdf"

☐ Tester les cas limites
  └─ Fichier exactement 10MB (limite)
  └─ Fichier 10MB + 1 octet (doit être rejeté)
  └─ Email très long (100 chars)
  └─ Nom/prénom 1 caractère (doit être rejeté, min:2)

☐ Tester la persistance des données
  └─ Soumettre formulaire
  └─ Redémarrer MySQL: docker restart ada_db
  └─ Vérifier que les données sont toujours présentes

☐ Tester la résilience
  └─ Soumettre formulaire pendant un pic de charge
  └─ Vérifier que la soumission réussit malgré la charge
```

---

## 10. Références

### 10.1 Fichiers du Framework

| Fichier | Ligne | Description |
|---------|-------|-------------|
| `src/core/Router.php` | 314-323 | Compilation des patterns de routes dynamiques |
| `src/core/Request.php` | 317-350 | Validation de fichiers uploadés |
| `src/core/Request.php` | 360-390 | Déplacement sécurisé de fichiers |
| `src/core/Validator.php` | 290-297 | Règle de validation email |
| `src/core/Validator.php` | 421-428 | Règle de validation URL |
| `src/core/Security.php` | 15-23 | Génération token CSRF |
| `src/core/Security.php` | 41-58 | Validation token CSRF |
| `src/core/Model.php` | 110-313 | CRUD operations de base |
| `src/app/Models/Depose.php` | 125-134 | Méthode createSubmission() |
| `src/app/Middleware/CsrfMiddleware.php` | 20-31 | Vérification CSRF automatique |

### 10.2 Documentation Externe

**PHP Documentation** :
- [File Uploads](https://www.php.net/manual/fr/features.file-upload.php)
- [filter_var()](https://www.php.net/manual/fr/function.filter-var.php)
- [htmlspecialchars()](https://www.php.net/manual/fr/function.htmlspecialchars.php)
- [PDO Prepared Statements](https://www.php.net/manual/fr/pdo.prepared-statements.php)

**Sécurité** :
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)

**Standards** :
- [PSR-12: Coding Style](https://www.php-fig.org/psr/psr-12/)
- [RFC 5322: Email Format](https://datatracker.ietf.org/doc/html/rfc5322)
- [RFC 3986: URI Generic Syntax](https://datatracker.ietf.org/doc/html/rfc3986)

### 10.3 Ressources du Projet

**Documentation** :
- `ai_prompt/spec.md` : Spécification complète du framework ADA
- `ai_prompt/plan.md` : Plan d'implémentation en 6 phases (80 tâches)
- `CLAUDE.md` : Instructions pour Claude Code (ce fichier)
- `README.md` : Documentation utilisateur

**Database** :
- `database/01-init.sql` : Schéma initial (devoirs, deposes)
- `database/migrations/02-add-depose-fields.sql` : Migration pour nouveaux champs

**Tests** :
- `src/test_crud.php` : Tests des opérations CRUD
- `src/test_phase4.php` : Tests des middlewares
- `src/test_phase5.php` : Tests de validation
- `src/test_security.php` : Tests de sécurité CSRF/XSS

### 10.4 Patterns et Architectures

**MVC Pattern** :
```
Model (Depose.php)
  ↓
Controller (DeposeController.php)
  ↓
View (deposes/create.php)
```

**Request Lifecycle** :
```
Browser → Apache → index.php (Front Controller)
  → Router (route matching)
  → Middleware Pipeline (CsrfMiddleware)
  → Controller Action (DeposeController@store)
  → Model (Depose::createSubmission)
  → Database (MySQL)
  → Response (redirect with flash message)
```

**File Upload Flow** :
```
Browser (multipart/form-data)
  → PHP ($_FILES superglobal)
  → Request::hasFile()
  → Request::validateFile() [size, MIME, extension]
  → Request::moveFile() [generate random name, move to filestore/]
  → Database (store metadata)
  → Response (success or error)
```

---

## Conclusion

Cette spécification fournit tous les éléments nécessaires pour intégrer le fichier `post.php` dans l'architecture MVC du framework ADA. Les composants ont été conçus pour :

1. **Réutiliser au maximum** les composants existants du framework (Request, Validator, Security, Models)
2. **Améliorer la sécurité** avec CSRF protection, validation stricte, et échappement systématique
3. **Respecter les conventions** MVC et les standards PSR
4. **Faciliter la maintenance** avec du code structuré, documenté, et testable

Le code fourni est **complet et implémentable directement** sans modifications majeures. Suivez la checklist de migration (Section 8) pour une intégration progressive et sécurisée.

**Temps estimé d'implémentation** : 2-3 heures
**Difficulté** : Moyenne (nécessite connaissance de base en MVC et SQL)
**Impact** : Migration complète de post.php vers architecture MVC professionnelle

---

**Fin de la spécification technique**

*Pour toute question ou clarification sur cette spécification, consultez les fichiers de référence du projet ou la documentation du framework ADA.*
