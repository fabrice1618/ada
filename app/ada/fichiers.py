import os
import re
from pathlib import Path

from flask import current_app

from ada.db import dossier_fichiers

TAILLE_BLOC = 64 * 1024


class FichierRefuse(Exception):
    pass


def extension_autorisee(nom):
    nom = Path(str(nom or '')).name.lower()
    for ext in sorted(current_app.config['ALLOWED_EXTENSIONS'], key=len, reverse=True):
        suffixe = '.' + ext.lower().lstrip('.')
        if nom.endswith(suffixe):
            return suffixe
    return None


def nom_affichage(nom):
    nom = Path(str(nom or '')).name.replace('\x00', '')
    nom = re.sub(r'[\r\n"]', '', nom).strip()
    if not nom or nom in ('.', '..'):
        return 'fichier'
    return nom[:200]


def _racine(classe_id):
    return dossier_fichiers(classe_id).resolve()


def ouvrir(classe_id, relatif):
    if not relatif or relatif.startswith(('/', '\\')) or '..' in Path(relatif).parts:
        raise FichierRefuse("Fichier introuvable.")
    racine = _racine(classe_id)
    cible = (racine / relatif).resolve()
    if not cible.is_relative_to(racine) or not cible.is_file():
        raise FichierRefuse("Fichier introuvable.")
    return cible


def supprimer(classe_id, relatif):
    if not relatif:
        return
    try:
        ouvrir(classe_id, relatif).unlink()
    except (FichierRefuse, FileNotFoundError):
        return


_NOM_GENERE = re.compile(r'[0-9A-Za-z_-]+(/[0-9A-Za-z_-]+)?')


def enregistrer(upload, classe_id, devoir_id, nom_genere):
    # upload : FileStorage de werkzeug.
    # nom_genere : '12' (étudiant), 'g3' (groupe), '12/<uuid>' (rendu en plusieurs fichiers)
    nom_genere = str(nom_genere)
    if not _NOM_GENERE.fullmatch(nom_genere):
        raise ValueError(f"nom généré invalide : {nom_genere!r}")
    if upload is None or not upload.filename:
        raise FichierRefuse("Choisissez un fichier.")
    ext = extension_autorisee(upload.filename)
    if ext is None:
        raise FichierRefuse("Ce type de fichier n'est pas accepté.")
    max_mo = current_app.config['MAX_UPLOAD_SIZE_MB']
    max_octets = int(max_mo) * 1024 * 1024

    relatif = f"{int(devoir_id)}/{nom_genere}{ext}"
    racine = _racine(classe_id)
    dest = (racine / relatif).resolve()
    if not dest.is_relative_to(racine):
        raise FichierRefuse("Fichier introuvable.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporaire = dest.with_name(dest.name + '.part')
    total = 0
    try:
        with temporaire.open('wb') as sortie:
            while bloc := upload.stream.read(TAILLE_BLOC):
                total += len(bloc)
                if total > max_octets:
                    raise FichierRefuse(
                        f"Le fichier dépasse la taille maximale de {max_mo} Mo."
                    )
                sortie.write(bloc)
        if total == 0:
            raise FichierRefuse("Le fichier est vide.")
        os.replace(temporaire, dest)
    except Exception:
        temporaire.unlink(missing_ok=True)
        raise
    return relatif, nom_affichage(upload.filename), total
