import functools
from datetime import datetime

from flask import request, abort
from sqlalchemy import text

from shared.db import SessionLocal


def verifier_creneau(type_ressource, ressource_id=None, chemin_page=None, classe_id=None):
    """Vérifie qu'un créneau est ouvert pour la ressource et la classe donnée."""
    db = SessionLocal()
    try:
        now = datetime.now()
        query = """
            SELECT id FROM core_creneau
            WHERE type_ressource = :type_ressource
              AND classe_id = :classe_id
              AND ouverture <= :now
              AND fermeture >= :now
        """
        params = {
            'type_ressource': type_ressource,
            'classe_id': classe_id,
            'now': now,
        }
        if ressource_id is not None:
            query += " AND ressource_id = :ressource_id"
            params['ressource_id'] = ressource_id
        if chemin_page is not None:
            query += " AND chemin_page = :chemin_page"
            params['chemin_page'] = chemin_page

        result = db.execute(text(query), params).fetchone()
        return result is not None
    finally:
        db.close()


def creneau_requis(type_ressource, param_ressource_id=None, param_chemin_page=None):
    """Décorateur Flask : refuse l'accès (403) si aucun créneau ouvert.

    Args:
        type_ressource: 'quiz', 'devoir' ou 'page'
        param_ressource_id: nom du paramètre URL contenant l'id de la ressource
        param_chemin_page: nom du paramètre URL contenant le chemin de la page
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            utilisateur = getattr(request, 'utilisateur', None)
            if not utilisateur:
                abort(403)

            ressource_id = kwargs.get(param_ressource_id) if param_ressource_id else None
            chemin_page = kwargs.get(param_chemin_page) if param_chemin_page else None

            # Vérifier pour chaque classe de l'utilisateur
            acces = False
            for classe in utilisateur.get('classes', []):
                if verifier_creneau(type_ressource, ressource_id, chemin_page, classe['id']):
                    acces = True
                    break

            if not acces:
                abort(403, description="Créneau fermé")

            return f(*args, **kwargs)
        return wrapper
    return decorator
