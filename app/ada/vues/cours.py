"""Pages de cours de /data/cours, servies sous /cours/ après contrôle :
personnel toujours, étudiant si un créneau « page » ouvert de l'une de ses classes couvre le chemin."""
import logging
import posixpath
import re

from flask import Blueprint, abort, redirect, request, send_from_directory
from werkzeug.security import safe_join

from ada import db
from ada.comptes import adresse_ip, utilisateur_courant, vers_connexion
from ada.modeles import classes_de
from ada.temps import iso, maintenant

bp = Blueprint('cours', __name__)
journal = logging.getLogger('ada')
PREFIXE = '/cours/'


def chemin_demande(brut):
    """Chemin ramené à ce qui sera servi : sans '..' ni '//'. Vide s'il n'est pas absolu."""
    if not brut.startswith('/') or '\x00' in brut:
        return ''
    normalise = posixpath.normpath(re.sub('/+', '/', brut))
    if brut.endswith('/') and normalise != '/':
        normalise += '/'
    return normalise


def couvre(chemin_page, chemin):
    """Un créneau sur /cours/math-101/ (ou /cours/math-101) couvre tout ce dossier,
    mais pas /cours/math-1010/."""
    base = chemin_page.rstrip('/')
    return chemin == chemin_page or chemin == base or chemin.startswith(base + '/')


def acces_autorise(utilisateur, chemin):
    if utilisateur.personnel:
        return True
    instant = iso(maintenant())
    for classe in classes_de(utilisateur.id):
        ouverts = db.classe(classe.id).execute(
            "SELECT chemin_page FROM creneaux WHERE type_ressource = 'page' "
            "AND ouverture <= ? AND fermeture >= ? AND chemin_page IS NOT NULL AND chemin_page <> ''",
            (instant, instant),
        )
        if any(couvre(ligne['chemin_page'], chemin) for ligne in ouverts):
            return True
    return False


@bp.get(PREFIXE, defaults={'reste': ''})
@bp.get(f'{PREFIXE}<path:reste>')
def page(reste):
    utilisateur = utilisateur_courant()
    if utilisateur is None:
        return vers_connexion()
    chemin = chemin_demande(request.path)
    if not chemin.startswith(PREFIXE):
        abort(404)
    if not acces_autorise(utilisateur, chemin):
        journal.warning(
            "Cours refusé utilisateur=%s chemin=%s ip=%s", utilisateur.id, chemin, adresse_ip(),
        )
        abort(403)

    racine = db.dossier_cours()
    relatif = chemin[len(PREFIXE):]
    cible = safe_join(str(racine), relatif) if relatif else str(racine)
    if cible is None:
        abort(404)
    if posixpath.isdir(cible):
        if not chemin.endswith('/'):
            return redirect(chemin + '/')
        relatif = posixpath.join(relatif, 'index.html')
    return send_from_directory(racine, relatif)
