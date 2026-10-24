import io
import logging
import re
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from ada import create_app, db
from ada.comptes import creer_utilisateur, ouvrir_session
from ada.modeles import Utilisateur, creer_classe, get_classe
from ada.temps import iso, maintenant

CSRF = 'jeton-de-test'


class BaseTests(unittest.TestCase):
    config = {}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.racine = Path(self.tmp.name)
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test',
            'DATA_ROOT': self.tmp.name,
            'SESSION_COOKIE_SECURE': False,
            'TRUSTED_HOSTS': None,
            'METHODE_HACHAGE': 'pbkdf2:sha256:1000',
            **self.config,
        })
        self.client = self.app.test_client()
        logging.getLogger('ada').disabled = True
        with self.app.app_context():
            db.migrer()

    # ── Données ──

    def contexte(self):
        return self.app.app_context()

    def classe(self, nom, annee='2026'):
        with self.contexte():
            return creer_classe(nom, annee)[0]

    def compte(self, email, role, *classes, nom=None):
        with self.contexte():
            cx = db.commun()
            with db.transaction(cx):
                uid = creer_utilisateur(cx, email, nom or email, role, 'secret-12')
                for classe in classes:
                    cx.execute('INSERT INTO inscriptions (utilisateur_id, classe_id) VALUES (?, ?)', (uid, classe.id))
            return Utilisateur.depuis(cx.execute('SELECT * FROM utilisateurs WHERE id = ?', (uid,)).fetchone())

    def devoir(self, classe, titre='TP', cree_par=None, **champs):
        champs.setdefault('date_limite', maintenant() + timedelta(days=1))
        champs['date_limite'] = iso(champs['date_limite'])
        champs.setdefault('type_rendu', 'fichier')
        champs.setdefault('mode', 'individuel')
        champs.setdefault('taille_groupe_max', None)
        with self.contexte():
            cx = db.classe(classe.id)
            with db.transaction(cx):
                return cx.execute(
                    'INSERT INTO devoirs (titre, cree_par, date_limite, type_rendu, mode, taille_groupe_max) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (titre, cree_par.id if cree_par else None, champs['date_limite'], champs['type_rendu'],
                     champs['mode'], champs['taille_groupe_max']),
                ).lastrowid

    def groupe(self, classe, devoir_id, nom, *membres):
        with self.contexte():
            cx = db.classe(classe.id)
            with db.transaction(cx):
                gid = cx.execute(
                    'INSERT INTO groupes (devoir_id, nom, cree_par, date_creation) VALUES (?, ?, ?, ?)',
                    (devoir_id, nom, membres[0].id, iso(maintenant())),
                ).lastrowid
                for membre in membres:
                    cx.execute(
                        'INSERT INTO membres_groupe (groupe_id, devoir_id, etudiant_id, date_adhesion) '
                        'VALUES (?, ?, ?, ?)',
                        (gid, devoir_id, membre.id, iso(maintenant())),
                    )
            return gid

    def sql(self, classe, requete, *parametres):
        """Lignes d'une requête sur la base de la classe (None : base commune) ; écritures en autocommit."""
        with self.contexte():
            cx = db.commun() if classe is None else db.classe(classe.id)
            return [dict(ligne) for ligne in cx.execute(requete, parametres)]

    def un(self, classe, requete, *parametres):
        lignes = self.sql(classe, requete, *parametres)
        return lignes[0] if lignes else None

    def fichiers_de(self, classe):
        return self.racine / 'classes' / str(classe.id) / 'fichiers'

    # ── Requêtes ──

    def connecter(self, utilisateur):
        with self.app.test_request_context():
            ouvrir_session(utilisateur)
            from flask import session
            jeton = session['jeton']
        with self.client.session_transaction() as s:
            s.clear()
            s['jeton'] = jeton
            s['csrf'] = CSRF

    def deconnecter(self):
        with self.client.session_transaction() as s:
            s.clear()
            s['csrf'] = CSRF

    def post(self, url, donnees=None, **options):
        donnees = dict(donnees or {})
        donnees.setdefault('csrf', CSRF)
        with self.client.session_transaction() as s:
            s['csrf'] = CSRF
        return self.client.post(url, data=donnees, buffered=True, **options)

    def get(self, url, **options):
        return self.client.get(url, buffered=True, **options)

    def fichier(self, nom='a.py', contenu=b'print(1)'):
        return (io.BytesIO(contenu), nom)

    def texte(self, reponse):
        return reponse.get_data(as_text=True)

    def assertContient(self, reponse, morceau):
        self.assertIn(morceau, self.texte(reponse))

    def assertRedirige(self, reponse, cible):
        self.assertIn(reponse.status_code, (301, 302, 303, 307, 308))
        self.assertEqual(re.sub('^https?://[^/]+', '', reponse.headers['Location']), cible)

    def recharger_classe(self, classe):
        with self.contexte():
            return get_classe(classe.id)
