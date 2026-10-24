-- Base d'une classe /data/classes/<id>/classe.db.
-- Les utilisateurs (cree_par, etudiant_id, deposee_par) sont ceux de ada.db :
-- pas de clé étrangère entre deux fichiers SQLite.

CREATE TABLE creneaux (
    id INTEGER PRIMARY KEY,
    type_ressource TEXT NOT NULL CHECK (type_ressource IN ('quiz', 'devoir', 'page')),
    ressource_id INTEGER,
    chemin_page TEXT,
    ouverture TEXT NOT NULL,
    fermeture TEXT NOT NULL
);

CREATE TABLE devoirs (
    id INTEGER PRIMARY KEY,
    titre TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    date_limite TEXT NOT NULL,
    cree_par INTEGER,
    type_rendu TEXT NOT NULL DEFAULT 'fichier' CHECK (type_rendu IN ('fichier', 'fichiers', 'github')),
    mode TEXT NOT NULL DEFAULT 'individuel' CHECK (mode IN ('individuel', 'groupe')),
    taille_groupe_max INTEGER
);

CREATE TABLE groupes (
    id INTEGER PRIMARY KEY,
    devoir_id INTEGER NOT NULL REFERENCES devoirs (id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    cree_par INTEGER,
    date_creation TEXT NOT NULL,
    UNIQUE (devoir_id, nom)
);

-- devoir_id est recopié du groupe : l'unicité garantit un groupe par étudiant et par devoir.
CREATE TABLE membres_groupe (
    id INTEGER PRIMARY KEY,
    groupe_id INTEGER NOT NULL REFERENCES groupes (id) ON DELETE CASCADE,
    devoir_id INTEGER NOT NULL REFERENCES devoirs (id) ON DELETE CASCADE,
    etudiant_id INTEGER NOT NULL,
    date_adhesion TEXT NOT NULL,
    UNIQUE (devoir_id, etudiant_id)
);
CREATE INDEX membres_groupe_groupe ON membres_groupe (groupe_id);

CREATE TABLE soumissions (
    id INTEGER PRIMARY KEY,
    devoir_id INTEGER NOT NULL REFERENCES devoirs (id) ON DELETE CASCADE,
    etudiant_id INTEGER,
    groupe_id INTEGER REFERENCES groupes (id) ON DELETE CASCADE,
    deposee_par INTEGER,
    type TEXT NOT NULL CHECK (type IN ('fichier', 'fichiers', 'github')),
    lien_github TEXT,
    date_soumission TEXT NOT NULL,
    UNIQUE (devoir_id, etudiant_id),
    UNIQUE (devoir_id, groupe_id),
    CHECK ((etudiant_id IS NULL) <> (groupe_id IS NULL))
);

-- chemin : relatif à /data/classes/<id>/fichiers/
CREATE TABLE fichiers_rendus (
    id INTEGER PRIMARY KEY,
    soumission_id INTEGER NOT NULL REFERENCES soumissions (id) ON DELETE CASCADE,
    chemin TEXT NOT NULL,
    nom_original TEXT NOT NULL,
    taille INTEGER NOT NULL DEFAULT 0,
    date_depot TEXT NOT NULL
);
CREATE INDEX fichiers_rendus_soumission ON fichiers_rendus (soumission_id);

CREATE TABLE quiz (
    id INTEGER PRIMARY KEY,
    titre TEXT NOT NULL,
    duree_max_minutes INTEGER NOT NULL,
    tentative_unique INTEGER NOT NULL DEFAULT 1,
    cree_par INTEGER
);

CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    quiz_id INTEGER NOT NULL REFERENCES quiz (id) ON DELETE CASCADE,
    enonce TEXT NOT NULL,
    choix TEXT NOT NULL,           -- JSON
    reponse_correcte TEXT NOT NULL,
    points INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE tentatives (
    id INTEGER PRIMARY KEY,
    quiz_id INTEGER NOT NULL REFERENCES quiz (id) ON DELETE CASCADE,
    etudiant_id INTEGER NOT NULL,
    reponses TEXT,                 -- JSON
    score INTEGER,
    debut TEXT NOT NULL,
    fin TEXT
);
