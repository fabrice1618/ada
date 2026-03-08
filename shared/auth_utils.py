import base64
import json
import functools
from datetime import datetime

from flask import request, redirect
from sqlalchemy import text

from shared.db import SessionLocal


def _get_session_data(session_key):
    """Lit et décode la session Django depuis MySQL."""
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT session_data, expire_date FROM django_session WHERE session_key = :key"),
            {'key': session_key}
        ).fetchone()
        if not result:
            return None
        session_data, expire_date = result
        if expire_date < datetime.now():
            return None
        # Django encode : base64(salt:json_payload)
        # Le format est : base64 → "salt:json"
        decoded = base64.b64decode(session_data).decode('utf-8')
        # Trouver le premier ':' qui sépare le salt du JSON
        colon_idx = decoded.index(':')
        payload = json.loads(decoded[colon_idx + 1:])
        return payload
    finally:
        db.close()


def _get_utilisateur(user_id):
    """Récupère l'utilisateur et ses classes depuis MySQL."""
    db = SessionLocal()
    try:
        user = db.execute(
            text("SELECT id, email, nom_complet, role FROM core_utilisateur WHERE id = :id"),
            {'id': user_id}
        ).fetchone()
        if not user:
            return None
        classes = db.execute(
            text("""
                SELECT c.id, c.nom FROM core_classe c
                JOIN core_utilisateur_classes uc ON c.id = uc.classe_id
                WHERE uc.utilisateur_id = :uid
            """),
            {'uid': user_id}
        ).fetchall()
        return {
            'id': user[0],
            'email': user[1],
            'nom_complet': user[2],
            'role': user[3],
            'classes': [{'id': c[0], 'nom': c[1]} for c in classes],
        }
    finally:
        db.close()


def get_utilisateur_courant():
    """Retourne l'utilisateur courant depuis le cookie sessionid, ou None."""
    session_key = request.cookies.get('sessionid')
    if not session_key:
        return None
    payload = _get_session_data(session_key)
    if not payload:
        return None
    user_id = payload.get('_auth_user_id')
    if not user_id:
        return None
    return _get_utilisateur(int(user_id))


def login_requis(f):
    """Décorateur Flask : redirige vers /auth/login/ si non connecté."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        utilisateur = get_utilisateur_courant()
        if not utilisateur:
            return redirect('/auth/login/')
        request.utilisateur = utilisateur
        return f(*args, **kwargs)
    return wrapper
