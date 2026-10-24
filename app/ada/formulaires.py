import re

from ada.modeles import LIBELLES_MODE, LIBELLES_TYPE, MODE_CHOICES, TYPE_RENDU_CHOICES
from ada.temps import depuis_saisie, local

LIEN_GITHUB = re.compile(r'https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9._-]+(/[^\s]*)?')
OBLIGATOIRE = 'Ce champ est obligatoire.'


def valider_lien(texte):
    """(lien, erreur) ; sans schéma, https:// est ajouté."""
    lien = (texte or '').strip()
    if not lien:
        return None, OBLIGATOIRE
    if '://' not in lien:
        lien = 'https://' + lien
    if len(lien) > 500 or not LIEN_GITHUB.fullmatch(lien):
        return None, 'Indiquez un dépôt GitHub : https://github.com/compte/depot'
    return lien, None


def valider_nom_groupe(texte):
    nom = ' '.join((texte or '').split())
    if not nom:
        return None, 'Indiquez un nom.'
    if len(nom) > 100:
        return None, 'Nom trop long (100 caractères au plus).'
    return nom, None


class FormulaireDevoir:
    """Création (avec la classe) et modification d'un devoir.

    verrouille : des rendus existent, type et mode restent ceux de la création.
    taille_min : effectif du plus grand groupe déjà formé.
    """

    CHAMPS = ('classe', 'titre', 'description', 'date_limite', 'type_rendu', 'mode', 'taille_groupe_max')

    def __init__(self, donnees=None, *, classes=None, initial=None, verrouille=False, taille_min=None):
        self.classes = classes
        self.verrouille = verrouille
        self.taille_min = taille_min
        self.choix_type = TYPE_RENDU_CHOICES
        self.choix_mode = MODE_CHOICES
        self.libelles_type = LIBELLES_TYPE
        self.libelles_mode = LIBELLES_MODE
        self.initial = {
            'titre': '', 'description': '', 'date_limite': '',
            'type_rendu': 'fichier', 'mode': 'individuel', 'taille_groupe_max': 3,
            **(initial or {}),
        }
        self.erreurs = {}
        self.donnees_valides = {}
        self.valeurs = dict(self.initial)
        if donnees is not None:
            for nom in self.CHAMPS:
                if nom in donnees and not (verrouille and nom in ('type_rendu', 'mode')):
                    self.valeurs[nom] = donnees.get(nom, '')

    @property
    def avec_classe(self):
        return self.classes is not None

    def _erreur(self, champ, message):
        self.erreurs.setdefault(champ, []).append(message)

    def valider(self):
        v, d = self.valeurs, self.donnees_valides
        if self.avec_classe:
            classe = str(v.get('classe', '')).strip()
            ids = {c.id for c in self.classes}
            if not classe:
                self._erreur('classe', OBLIGATOIRE)
            elif not classe.isdigit() or int(classe) not in ids:
                self._erreur('classe', 'Sélectionnez une classe de la liste.')
            else:
                d['classe'] = int(classe)

        titre = str(v.get('titre', '')).strip()
        if not titre:
            self._erreur('titre', OBLIGATOIRE)
        elif len(titre) > 255:
            self._erreur('titre', 'Titre trop long (255 caractères au plus).')
        d['titre'] = titre
        d['description'] = str(v.get('description', '')).strip()

        saisie = str(v.get('date_limite', '')).strip()
        date_limite = depuis_saisie(saisie)
        if not saisie:
            self._erreur('date_limite', OBLIGATOIRE)
        elif date_limite is None:
            self._erreur('date_limite', 'Saisissez une date et une heure valides.')
        d['date_limite'] = date_limite

        if self.verrouille:
            d['type_rendu'], d['mode'] = self.initial['type_rendu'], self.initial['mode']
        else:
            d['type_rendu'] = v.get('type_rendu') or 'fichier'
            d['mode'] = v.get('mode') or 'individuel'
            if d['type_rendu'] not in LIBELLES_TYPE:
                self._erreur('type_rendu', 'Choix invalide.')
            if d['mode'] not in LIBELLES_MODE:
                self._erreur('mode', 'Choix invalide.')

        d['taille_groupe_max'] = None
        if d['mode'] == 'groupe':
            texte = str(v.get('taille_groupe_max', '') or '').strip()
            if not texte:
                self._erreur('taille_groupe_max', 'Indiquez la taille maximale des groupes.')
            elif not texte.isdigit() or not 2 <= int(texte) <= 20:
                self._erreur('taille_groupe_max', 'Entre 2 et 20.')
            elif self.taille_min and int(texte) < self.taille_min:
                self._erreur('taille_groupe_max', f'Un groupe compte déjà {self.taille_min} membres.')
            else:
                d['taille_groupe_max'] = int(texte)
        return not self.erreurs


def initial_devoir(devoir):
    return {
        'titre': devoir.titre,
        'description': devoir.description,
        'date_limite': local(devoir.date_limite).strftime('%Y-%m-%dT%H:%M'),
        'type_rendu': devoir.type_rendu,
        'mode': devoir.mode,
        'taille_groupe_max': devoir.taille_groupe_max or 3,
    }
