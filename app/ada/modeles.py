"""Objets lus en base (ada.db et classe.db) et requêtes partagées entre les vues."""
from dataclasses import dataclass, field
from datetime import date, datetime

from ada import db
from ada.temps import lire, lire_jour, maintenant

ROLE_CHOICES = [
    ('etudiant', 'Étudiant'),
    ('enseignant', 'Enseignant'),
    ('admin', 'Administrateur'),
]
TYPE_RENDU_CHOICES = [
    ('fichier', 'Un fichier'),
    ('fichiers', 'Plusieurs fichiers'),
    ('github', 'Lien GitHub'),
]
MODE_CHOICES = [
    ('individuel', 'Individuel'),
    ('groupe', 'En groupe'),
]
LIBELLES_ROLE = dict(ROLE_CHOICES)
LIBELLES_TYPE = dict(TYPE_RENDU_CHOICES)
LIBELLES_MODE = dict(MODE_CHOICES)


@dataclass
class Utilisateur:
    id: int
    email: str
    nom_complet: str
    role: str
    actif: bool
    inscrit_le: datetime

    @classmethod
    def depuis(cls, ligne):
        return cls(
            id=ligne['id'], email=ligne['email'], nom_complet=ligne['nom_complet'],
            role=ligne['role'], actif=bool(ligne['actif']), inscrit_le=lire(ligne['inscrit_le']),
        )

    @property
    def personnel(self):
        return self.role in ('admin', 'enseignant')

    @property
    def libelle_role(self):
        return LIBELLES_ROLE.get(self.role, self.role)

    def __str__(self):
        return self.nom_complet


@dataclass
class Classe:
    id: int
    nom: str
    annee: str
    debut_autorisation: date | None
    fin_autorisation: date | None

    @classmethod
    def depuis(cls, ligne):
        return cls(
            id=ligne['id'], nom=ligne['nom'], annee=ligne['annee'],
            debut_autorisation=lire_jour(ligne['debut_autorisation']),
            fin_autorisation=lire_jour(ligne['fin_autorisation']),
        )

    def __str__(self):
        return f"{self.nom} ({self.annee})"


@dataclass
class Devoir:
    id: int
    classe: Classe
    titre: str
    description: str
    date_limite: datetime
    cree_par: int | None
    type_rendu: str
    mode: str
    taille_groupe_max: int | None

    @classmethod
    def depuis(cls, ligne, classe):
        return cls(
            id=ligne['id'], classe=classe, titre=ligne['titre'], description=ligne['description'],
            date_limite=lire(ligne['date_limite']), cree_par=ligne['cree_par'],
            type_rendu=ligne['type_rendu'], mode=ligne['mode'],
            taille_groupe_max=ligne['taille_groupe_max'],
        )

    @property
    def classe_id(self):
        return self.classe.id

    @property
    def est_ouvert(self):
        return maintenant() <= self.date_limite

    @property
    def en_groupe(self):
        return self.mode == 'groupe'

    @property
    def libelle_type(self):
        return LIBELLES_TYPE.get(self.type_rendu, self.type_rendu)

    @property
    def libelle_mode(self):
        return LIBELLES_MODE.get(self.mode, self.mode)


@dataclass
class Groupe:
    id: int
    devoir_id: int
    nom: str
    cree_par: int | None
    date_creation: datetime
    membres: list = field(default_factory=list)

    @classmethod
    def depuis(cls, ligne):
        return cls(
            id=ligne['id'], devoir_id=ligne['devoir_id'], nom=ligne['nom'],
            cree_par=ligne['cree_par'], date_creation=lire(ligne['date_creation']),
        )

    @property
    def nb_membres(self):
        return len(self.membres)


@dataclass
class FichierRendu:
    id: int
    soumission_id: int
    chemin: str
    nom_original: str
    taille: int
    date_depot: datetime

    @classmethod
    def depuis(cls, ligne):
        return cls(
            id=ligne['id'], soumission_id=ligne['soumission_id'], chemin=ligne['chemin'],
            nom_original=ligne['nom_original'], taille=ligne['taille'],
            date_depot=lire(ligne['date_depot']),
        )


@dataclass
class Soumission:
    id: int
    devoir_id: int
    etudiant_id: int | None
    groupe_id: int | None
    deposee_par: int | None
    type: str
    lien_github: str | None
    date_soumission: datetime
    fichiers: list = field(default_factory=list)
    deposant: Utilisateur | None = None

    @classmethod
    def depuis(cls, ligne):
        return cls(
            id=ligne['id'], devoir_id=ligne['devoir_id'], etudiant_id=ligne['etudiant_id'],
            groupe_id=ligne['groupe_id'], deposee_par=ligne['deposee_par'], type=ligne['type'],
            lien_github=ligne['lien_github'], date_soumission=lire(ligne['date_soumission']),
        )


# ── Base commune ────────────────────────────────────────────────

def utilisateurs_par_id(ids):
    ids = sorted({i for i in ids if i is not None})
    if not ids:
        return {}
    marques = ','.join('?' * len(ids))
    lignes = db.commun().execute(f'SELECT * FROM utilisateurs WHERE id IN ({marques})', ids)
    return {ligne['id']: Utilisateur.depuis(ligne) for ligne in lignes}


def get_classe(classe_id):
    ligne = db.commun().execute('SELECT * FROM classes WHERE id = ?', (classe_id,)).fetchone()
    return Classe.depuis(ligne) if ligne else None


def toutes_les_classes():
    lignes = db.commun().execute('SELECT * FROM classes ORDER BY annee DESC, nom')
    return [Classe.depuis(ligne) for ligne in lignes]


def classes_de(utilisateur_id):
    lignes = db.commun().execute(
        'SELECT c.* FROM classes c JOIN inscriptions i ON i.classe_id = c.id '
        'WHERE i.utilisateur_id = ? ORDER BY c.annee DESC, c.nom',
        (utilisateur_id,),
    )
    return [Classe.depuis(ligne) for ligne in lignes]


def est_inscrit(utilisateur_id, classe_id):
    return db.commun().execute(
        'SELECT 1 FROM inscriptions WHERE utilisateur_id = ? AND classe_id = ?',
        (utilisateur_id, classe_id),
    ).fetchone() is not None


def membres_classe(classe_id, role=None):
    requete = (
        'SELECT u.* FROM utilisateurs u JOIN inscriptions i ON i.utilisateur_id = u.id '
        'WHERE i.classe_id = ?'
    )
    parametres = [classe_id]
    if role:
        requete += ' AND u.role = ?'
        parametres.append(role)
    lignes = db.commun().execute(requete + ' ORDER BY u.nom_complet, u.id', parametres)
    return [Utilisateur.depuis(ligne) for ligne in lignes]


def creer_classe(nom, annee):
    """Ligne dans ada.db et base de la classe ; renvoie (Classe, créée ?)."""
    cx = db.commun()
    with db.transaction(cx):
        ligne = cx.execute(
            'SELECT * FROM classes WHERE nom = ? AND annee = ? ORDER BY id LIMIT 1', (nom, annee),
        ).fetchone()
        if ligne:
            return Classe.depuis(ligne), False
        classe_id = cx.execute(
            'INSERT INTO classes (nom, annee) VALUES (?, ?)', (nom, annee),
        ).lastrowid
        db.creer_base_classe(classe_id)
    return get_classe(classe_id), True


# ── Base d'une classe ───────────────────────────────────────────

def get_devoir(classe, devoir_id):
    ligne = db.classe(classe.id).execute(
        'SELECT * FROM devoirs WHERE id = ?', (devoir_id,),
    ).fetchone()
    return Devoir.depuis(ligne, classe) if ligne else None


def devoirs_de(classe):
    lignes = db.classe(classe.id).execute('SELECT * FROM devoirs ORDER BY date_limite DESC, id')
    return [Devoir.depuis(ligne, classe) for ligne in lignes]


def fichiers_de(cx, soumission_ids):
    """{soumission_id: [FichierRendu]} triés par nom puis id."""
    resultat = {i: [] for i in soumission_ids}
    if not soumission_ids:
        return resultat
    marques = ','.join('?' * len(soumission_ids))
    lignes = cx.execute(
        f'SELECT * FROM fichiers_rendus WHERE soumission_id IN ({marques}) ORDER BY nom_original, id',
        list(soumission_ids),
    )
    for ligne in lignes:
        resultat[ligne['soumission_id']].append(FichierRendu.depuis(ligne))
    return resultat


def soumissions(devoir, where='', parametres=()):
    """Rendus du devoir avec leurs fichiers et leur déposant."""
    cx = db.classe(devoir.classe_id)
    lignes = cx.execute(
        f'SELECT * FROM soumissions WHERE devoir_id = ? {where} ORDER BY id',
        (devoir.id, *parametres),
    )
    liste = [Soumission.depuis(ligne) for ligne in lignes]
    fichiers = fichiers_de(cx, [s.id for s in liste])
    deposants = utilisateurs_par_id(s.deposee_par for s in liste)
    for s in liste:
        s.fichiers = fichiers[s.id]
        s.deposant = deposants.get(s.deposee_par)
    return liste


def groupes(devoir):
    """Groupes du devoir, par nom, avec leurs membres (Utilisateur) dans l'ordre d'adhésion."""
    cx = db.classe(devoir.classe_id)
    liste = [
        Groupe.depuis(ligne)
        for ligne in cx.execute('SELECT * FROM groupes WHERE devoir_id = ? ORDER BY nom, id', (devoir.id,))
    ]
    adhesions = cx.execute(
        'SELECT groupe_id, etudiant_id FROM membres_groupe WHERE devoir_id = ? ORDER BY id',
        (devoir.id,),
    ).fetchall()
    personnes = utilisateurs_par_id(a['etudiant_id'] for a in adhesions)
    par_id = {g.id: g for g in liste}
    for a in adhesions:
        if a['groupe_id'] in par_id and a['etudiant_id'] in personnes:
            par_id[a['groupe_id']].membres.append(personnes[a['etudiant_id']])
    return liste
