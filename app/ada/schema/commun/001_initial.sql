-- Base commune /data/ada.db : comptes, classes, inscriptions, sessions.
-- Dates : texte ISO 8601 en UTC (ada/temps.py).

-- AUTOINCREMENT : un identifiant supprimé n'est jamais réattribué (les bases de classe
-- gardent des identifiants d'utilisateurs).
CREATE TABLE utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nom_complet TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'etudiant' CHECK (role IN ('etudiant', 'enseignant', 'admin')),
    -- Vide, ou commençant par '!' (compte Django sans mot de passe) : connexion impossible.
    mot_de_passe TEXT NOT NULL DEFAULT '',
    actif INTEGER NOT NULL DEFAULT 1,
    inscrit_le TEXT NOT NULL,
    derniere_connexion TEXT
);

-- Chaque classe a son dossier /data/classes/<id>/ (classe.db et fichiers rendus).
CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    annee TEXT NOT NULL,
    debut_autorisation TEXT,
    fin_autorisation TEXT
);

CREATE TABLE inscriptions (
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs (id) ON DELETE CASCADE,
    classe_id INTEGER NOT NULL REFERENCES classes (id) ON DELETE CASCADE,
    PRIMARY KEY (utilisateur_id, classe_id)
);
CREATE INDEX inscriptions_classe ON inscriptions (classe_id);

-- cle : sha256 du jeton gardé dans le cookie signé.
CREATE TABLE sessions (
    cle TEXT PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs (id) ON DELETE CASCADE,
    cree_le TEXT NOT NULL,
    expire_le TEXT NOT NULL
);
CREATE INDEX sessions_utilisateur ON sessions (utilisateur_id);
