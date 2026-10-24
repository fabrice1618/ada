"""Mots de passe, sessions (table sessions de ada.db) et contrôle d'accès des vues."""
import base64
import hashlib
import hmac
import secrets
from functools import wraps
from urllib.parse import urlsplit

from flask import current_app, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ada import db
from ada.modeles import Utilisateur
from ada.temps import iso, maintenant

# Haché de comparaison : une adresse inconnue coûte le même temps qu'un mauvais mot de passe.
_HACHE_FACTICE = generate_password_hash('ada', method='pbkdf2:sha256:1000')


def hacher(mot_de_passe):
    return generate_password_hash(mot_de_passe, method=current_app.config['METHODE_HACHAGE'])


def _verifier_django(hache, mot_de_passe):
    # Comptes repris de Django : pbkdf2_sha256$<itérations>$<sel>$<base64>
    try:
        _algo, iterations, sel, attendu = hache.split('$', 3)
        calcule = hashlib.pbkdf2_hmac(
            'sha256', mot_de_passe.encode('utf-8'), sel.encode('utf-8'), int(iterations),
        )
    except ValueError:
        return False
    return hmac.compare_digest(base64.b64encode(calcule).decode('ascii'), attendu)


def verifier_mot_de_passe(hache, mot_de_passe):
    if not hache or hache.startswith('!'):
        check_password_hash(_HACHE_FACTICE, mot_de_passe)
        return False
    if hache.startswith('pbkdf2_sha256$'):
        return _verifier_django(hache, mot_de_passe)
    return check_password_hash(hache, mot_de_passe)


def creer_utilisateur(cx, email, nom_complet, role='etudiant', mot_de_passe=None):
    """Dans une transaction ouverte sur ada.db ; sans mot de passe, connexion impossible."""
    return cx.execute(
        'INSERT INTO utilisateurs (email, nom_complet, role, mot_de_passe, inscrit_le) '
        'VALUES (?, ?, ?, ?, ?)',
        (email.strip().lower(), nom_complet, role, hacher(mot_de_passe) if mot_de_passe else '',
         iso(maintenant())),
    ).lastrowid


def changer_mot_de_passe(utilisateur_id, mot_de_passe):
    cx = db.commun()
    with db.transaction(cx):
        cx.execute(
            'UPDATE utilisateurs SET mot_de_passe = ? WHERE id = ?',
            (hacher(mot_de_passe), utilisateur_id),
        )


def authentifier(email, mot_de_passe):
    cx = db.commun()
    ligne = cx.execute(
        'SELECT * FROM utilisateurs WHERE email = ?', ((email or '').strip(),),
    ).fetchone()
    if ligne is None:
        check_password_hash(_HACHE_FACTICE, mot_de_passe)
        return None
    if not verifier_mot_de_passe(ligne['mot_de_passe'], mot_de_passe) or not ligne['actif']:
        return None
    if ligne['mot_de_passe'].startswith('pbkdf2_sha256$'):
        changer_mot_de_passe(ligne['id'], mot_de_passe)
    return Utilisateur.depuis(ligne)


# ── Sessions ────────────────────────────────────────────────────

def _cle(jeton):
    return hashlib.sha256(jeton.encode('ascii')).hexdigest()


def ouvrir_session(utilisateur):
    jeton = secrets.token_urlsafe(32)
    debut = maintenant()
    fin = debut + current_app.config['PERMANENT_SESSION_LIFETIME']
    cx = db.commun()
    with db.transaction(cx):
        cx.execute('DELETE FROM sessions WHERE expire_le < ?', (iso(debut),))
        cx.execute(
            'INSERT INTO sessions (cle, utilisateur_id, cree_le, expire_le) VALUES (?, ?, ?, ?)',
            (_cle(jeton), utilisateur.id, iso(debut), iso(fin)),
        )
        cx.execute(
            'UPDATE utilisateurs SET derniere_connexion = ? WHERE id = ?', (iso(debut), utilisateur.id),
        )
    # Nouveau cookie : un jeton fixé avant la connexion ne sert à rien.
    session.clear()
    session.permanent = True
    session['jeton'] = jeton
    session['csrf'] = secrets.token_urlsafe(32)
    g.utilisateur = utilisateur


def fermer_session():
    jeton = session.get('jeton')
    if jeton:
        cx = db.commun()
        with db.transaction(cx):
            cx.execute('DELETE FROM sessions WHERE cle = ?', (_cle(jeton),))
    session.clear()
    g.utilisateur = None


def fermer_autres_sessions(utilisateur_id):
    jeton = session.get('jeton', '')
    cx = db.commun()
    with db.transaction(cx):
        cx.execute(
            'DELETE FROM sessions WHERE utilisateur_id = ? AND cle <> ?',
            (utilisateur_id, _cle(jeton)),
        )


def utilisateur_courant():
    if 'utilisateur' not in g:
        g.utilisateur = None
        jeton = session.get('jeton')
        if jeton:
            ligne = db.commun().execute(
                'SELECT u.* FROM sessions s JOIN utilisateurs u ON u.id = s.utilisateur_id '
                'WHERE s.cle = ? AND s.expire_le > ? AND u.actif = 1',
                (_cle(jeton), iso(maintenant())),
            ).fetchone()
            if ligne:
                g.utilisateur = Utilisateur.depuis(ligne)
    return g.utilisateur


def jeton_csrf():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']


def csrf_valide():
    attendu = session.get('csrf')
    recu = request.form.get('csrf', '')
    return bool(attendu) and hmac.compare_digest(attendu, recu)


# ── Contrôle d'accès ───────────────────────────────────────────

def adresse_ip():
    return request.remote_addr or '-'


def chemin_complet():
    chaine = request.query_string.decode('latin-1')
    return request.path + (f'?{chaine}' if chaine else '')


def vers_connexion():
    return redirect(url_for('connexion.connexion', next=chemin_complet()))


def redirection_sure(cible):
    """Chemin local seulement : pas d'URL absolue ni de //hote."""
    if not cible or not cible.startswith('/') or cible.startswith('//') or '\\' in cible:
        return False
    if any(ord(c) < 32 for c in cible):
        return False
    morceaux = urlsplit(cible)
    return not morceaux.scheme and not morceaux.netloc


def destination(utilisateur):
    if utilisateur.role == 'admin':
        return url_for('admin.gestion')
    if utilisateur.role == 'enseignant':
        return url_for('enseignant.gestion_devoirs')
    return url_for('devoirs.liste')


def connexion_requise(vue):
    @wraps(vue)
    def enveloppe(*args, **kwargs):
        if utilisateur_courant() is None:
            return vers_connexion()
        return vue(*args, **kwargs)
    return enveloppe


def personnel_requis(vue):
    @wraps(vue)
    def enveloppe(*args, **kwargs):
        utilisateur = utilisateur_courant()
        if utilisateur is None:
            return vers_connexion()
        if not utilisateur.personnel:
            return redirect(url_for('devoirs.liste'))
        return vue(*args, **kwargs)
    return enveloppe


def admin_requis(vue):
    @wraps(vue)
    def enveloppe(*args, **kwargs):
        utilisateur = utilisateur_courant()
        if utilisateur is None:
            return vers_connexion()
        if utilisateur.role != 'admin':
            return redirect(url_for('connexion.connexion'))
        return vue(*args, **kwargs)
    return enveloppe
