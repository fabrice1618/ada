import os
import re
from pathlib import Path

from django.conf import settings


class FichierRefuse(Exception):
    pass


def extension_autorisee(nom):
    nom = Path(str(nom or '')).name.lower()
    for ext in sorted(settings.ALLOWED_EXTENSIONS, key=len, reverse=True):
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


def _racine():
    return Path(settings.UPLOAD_ROOT).resolve()


def ouvrir(relatif):
    if not relatif or relatif.startswith(('/', '\\')) or '..' in Path(relatif).parts:
        raise FichierRefuse("Fichier introuvable.")
    racine = _racine()
    cible = (racine / relatif).resolve()
    if not cible.is_relative_to(racine) or not cible.is_file():
        raise FichierRefuse("Fichier introuvable.")
    return cible


def supprimer(relatif):
    if not relatif:
        return
    try:
        ouvrir(relatif).unlink()
    except (FichierRefuse, FileNotFoundError):
        return


_NOM_GENERE = re.compile(r'[0-9A-Za-z_-]+(/[0-9A-Za-z_-]+)?')


def enregistrer(upload, devoir_id, nom_genere):
    # nom_genere : '12' (étudiant), 'g3' (groupe), '12/<uuid>' (rendu en plusieurs fichiers)
    nom_genere = str(nom_genere)
    if not _NOM_GENERE.fullmatch(nom_genere):
        raise ValueError(f"nom généré invalide : {nom_genere!r}")
    if upload is None or not getattr(upload, 'name', ''):
        raise FichierRefuse("Choisissez un fichier.")
    ext = extension_autorisee(upload.name)
    if ext is None:
        raise FichierRefuse("Ce type de fichier n'est pas accepté.")
    max_octets = int(settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
    if upload.size == 0:
        raise FichierRefuse("Le fichier est vide.")
    if upload.size is not None and upload.size > max_octets:
        raise FichierRefuse(
            f"Le fichier dépasse la taille maximale de {settings.MAX_UPLOAD_SIZE_MB} Mo."
        )

    relatif = f"{int(devoir_id)}/{nom_genere}{ext}"
    racine = _racine()
    dest = (racine / relatif).resolve()
    if not dest.is_relative_to(racine):
        raise FichierRefuse("Fichier introuvable.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporaire = dest.with_name(dest.name + '.part')
    total = 0
    try:
        with temporaire.open('wb') as sortie:
            for bloc in upload.chunks():
                total += len(bloc)
                if total > max_octets:
                    raise FichierRefuse(
                        f"Le fichier dépasse la taille maximale de {settings.MAX_UPLOAD_SIZE_MB} Mo."
                    )
                sortie.write(bloc)
        if total == 0:
            raise FichierRefuse("Le fichier est vide.")
        os.replace(temporaire, dest)
    except Exception:
        temporaire.unlink(missing_ok=True)
        raise
    return relatif, nom_affichage(upload.name), total
