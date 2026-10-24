import base64
import hashlib
import io

import openpyxl

from tests.base import BaseTests


def hache_django(mot_de_passe, sel='selDjango', iterations=1000):
    calcule = hashlib.pbkdf2_hmac('sha256', mot_de_passe.encode(), sel.encode(), iterations)
    return f"pbkdf2_sha256${iterations}${sel}${base64.b64encode(calcule).decode()}"


class ComptesTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.ciel = self.classe('CIEL')
        self.eleve = self.compte('eleve@example.com', 'etudiant', self.ciel)
        self.deconnecter()

    def _connexion(self, email='eleve@example.com', mot_de_passe='secret-12'):
        return self.post('/auth/login/', {'email': email, 'mot_de_passe': mot_de_passe})

    def test_mot_de_passe_django_puis_rehache(self):
        self.sql(None, 'UPDATE utilisateurs SET mot_de_passe = ? WHERE id = ?', hache_django('ancien-mdp'), self.eleve.id)
        self.assertRedirige(self._connexion(mot_de_passe='ancien-mdp'), '/devoirs/')
        hache = self.un(None, 'SELECT mot_de_passe FROM utilisateurs WHERE id = ?', self.eleve.id)['mot_de_passe']
        self.assertTrue(hache.startswith('pbkdf2:sha256:'))
        self.deconnecter()
        self.assertRedirige(self._connexion(mot_de_passe='ancien-mdp'), '/devoirs/')
        self.deconnecter()
        self.assertEqual(self._connexion(mot_de_passe='autre').status_code, 200)

    def test_refus(self):
        self.assertContient(self._connexion(mot_de_passe='faux'), 'incorrect')
        self.assertContient(self._connexion(email='inconnu@example.com'), 'incorrect')
        self.sql(None, "UPDATE utilisateurs SET mot_de_passe = '!inutilisable' WHERE id = ?", self.eleve.id)
        self.assertContient(self._connexion(mot_de_passe='!inutilisable'), 'incorrect')
        self.sql(None, "UPDATE utilisateurs SET mot_de_passe = '' WHERE id = ?", self.eleve.id)
        self.assertContient(self._connexion(mot_de_passe=''), 'incorrect')

    def test_compte_inactif(self):
        self.assertEqual(self._connexion().status_code, 302)
        self.sql(None, 'UPDATE utilisateurs SET actif = 0 WHERE id = ?', self.eleve.id)
        # La session ouverte ne vaut plus rien, et une nouvelle connexion est refusée.
        self.assertRedirige(self.get('/devoirs/'), '/auth/login/?next=/devoirs/')
        self.assertContient(self._connexion(), 'incorrect')

    def test_deconnexion_revoque_la_session(self):
        self._connexion()
        with self.client.session_transaction() as s:
            ancien = dict(s)
        self.get('/auth/logout/')
        self.assertEqual(self.sql(None, 'SELECT * FROM sessions'), [])
        with self.client.session_transaction() as s:
            s.update(ancien)
        self.assertEqual(self.get('/devoirs/').status_code, 302)

    def test_changement_de_mot_de_passe_ferme_les_autres_sessions(self):
        autre_appareil = self.app.test_client()
        self.connecter(self.eleve)
        with self.client.session_transaction() as s:
            premier = dict(s)
        self.connecter(self.eleve)
        with autre_appareil.session_transaction() as s:
            s.update(premier)
        self.assertEqual(autre_appareil.get('/devoirs/').status_code, 200)

        reponse = self.post('/auth/profil/', {
            'ancien_mdp': 'secret-12', 'nouveau_mdp': 'nouveau-mdp', 'confirmation_mdp': 'nouveau-mdp',
        })
        self.assertContient(reponse, 'Mot de passe modifié')
        self.assertEqual(self.get('/devoirs/').status_code, 200)
        self.assertEqual(autre_appareil.get('/devoirs/').status_code, 302)
        self.deconnecter()
        self.assertRedirige(self._connexion(mot_de_passe='nouveau-mdp'), '/devoirs/')

    def test_csrf(self):
        self.connecter(self.eleve)
        reponse = self.client.post('/auth/profil/', data={'ancien_mdp': 'secret-12'})
        self.assertEqual(reponse.status_code, 400)
        reponse = self.client.post('/auth/profil/', data={'ancien_mdp': 'secret-12', 'csrf': 'faux'})
        self.assertEqual(reponse.status_code, 400)

    def test_session_fixee_avant_connexion(self):
        with self.client.session_transaction() as s:
            s['jeton'] = 'impose-par-un-tiers'
        self._connexion()
        with self.client.session_transaction() as s:
            self.assertNotEqual(s['jeton'], 'impose-par-un-tiers')

    def test_creer_admin(self):
        resultat = self.app.test_cli_runner().invoke(
            args=['creer-admin', '--email', 'Chef@Example.com', '--nom', 'Chef', '--mot-de-passe', 'tres-secret'],
        )
        self.assertEqual(resultat.exit_code, 0, resultat.output)
        self.assertRedirige(self._connexion('chef@example.com', 'tres-secret'), '/admin/')
        resultat = self.app.test_cli_runner().invoke(
            args=['creer-admin', '--email', 'chef@example.com', '--nom', 'Chef', '--mot-de-passe', 'x'],
        )
        self.assertIn('existe déjà', resultat.output)


class ImportTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.admin = self.compte('admin@example.com', 'admin')
        self.connecter(self.admin)

    def _classeur(self, feuilles):
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for nom, lignes in feuilles.items():
            ws = wb.create_sheet(nom)
            ws.append(['NOM Prénom', 'Email'])
            for ligne in lignes:
                ws.append(ligne)
        tampon = io.BytesIO()
        wb.save(tampon)
        tampon.seek(0)
        return tampon

    def test_import(self):
        deja = self.compte('deja@example.com', 'etudiant')
        reponse = self.post('/admin/', {
            'fichier': (self._classeur({
                'CIEL': [('DUPONT Jean', 'Jean.Dupont@example.com'), ('DEJA Là', 'deja@example.com')],
                'EISI': [('MARTIN Léa', 'lea@example.com')],
            }), 'classes.xlsx'),
            'annee': '2026-2027',
            'generer_mdp': 'on',
            'debut_autorisation': '2026-09-01',
        })
        self.assertContient(reponse, 'Import terminé')
        classes = self.sql(None, 'SELECT * FROM classes ORDER BY nom')
        self.assertEqual([(c['nom'], c['annee'], c['debut_autorisation']) for c in classes],
                         [('CIEL', '2026-2027', '2026-09-01'), ('EISI', '2026-2027', '2026-09-01')])
        for classe in classes:
            self.assertTrue((self.racine / 'classes' / str(classe['id']) / 'classe.db').is_file())
        jean = self.un(None, "SELECT * FROM utilisateurs WHERE email = 'jean.dupont@example.com'")
        self.assertTrue(jean['mot_de_passe'])
        inscrits = self.sql(None, 'SELECT utilisateur_id FROM inscriptions WHERE classe_id = ?', classes[0]['id'])
        self.assertEqual({i['utilisateur_id'] for i in inscrits}, {jean['id'], deja.id})

        # Réimport : rien n'est dupliqué.
        self.post('/admin/', {
            'fichier': (self._classeur({'CIEL': [('DUPONT Jean', 'jean.dupont@example.com')]}), 'classes.xlsx'),
            'annee': '2026-2027',
        })
        self.assertEqual(len(self.sql(None, 'SELECT * FROM classes')), 2)
        self.assertEqual(len(self.sql(None, "SELECT * FROM utilisateurs WHERE email LIKE 'jean%'")), 1)
        self.assertContient(self.get('/admin/'), 'CIEL')
