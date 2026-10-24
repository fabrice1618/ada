from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.models import Classe, Creneau, Utilisateur


class VerifierTests(TestCase):
    url = '/auth/verify/'
    page = '/cours/math-101/chapitre1.html'

    def setUp(self):
        self.classe = Classe.objects.create(nom='CIEL', annee='2026')
        self.eleve = Utilisateur.objects.create_user(
            email='eleve@example.com', password='secret-12', nom_complet='Eleve', role='etudiant',
        )
        self.eleve.classes.add(self.classe)
        maintenant = timezone.now()
        Creneau.objects.create(
            classe=self.classe, type_ressource='page', chemin_page=self.page,
            ouverture=maintenant - timedelta(hours=1), fermeture=maintenant + timedelta(hours=1),
        )
        self.client.force_login(self.eleve)

    def _creneau(self, chemin):
        maintenant = timezone.now()
        Creneau.objects.create(
            classe=self.classe, type_ressource='page', chemin_page=chemin,
            ouverture=maintenant - timedelta(hours=1), fermeture=maintenant + timedelta(hours=1),
        )

    def _statut(self, uri):
        return self.client.get(self.url, HTTP_X_ORIGINAL_URI=uri).status_code

    def test_creneau_ouvert(self):
        reponse = self.client.get(self.url, HTTP_X_ORIGINAL_URI=self.page)
        self.assertEqual(reponse.status_code, 200)

    def test_parametres_ignores(self):
        self.assertEqual(self._statut(self.page + '?v=2'), 200)

    def test_dossier_couvre_ses_fichiers(self):
        self._creneau('/cours/info-201/')
        self.assertEqual(self._statut('/cours/info-201/'), 200)
        self.assertEqual(self._statut('/cours/info-201/img/schema.png'), 200)
        self.assertEqual(self._statut('/cours/info-2010/index.html'), 403)

    def test_dossier_sans_barre_finale(self):
        self._creneau('/cours/info-201')
        self.assertEqual(self._statut('/cours/info-201/index.html'), 200)
        self.assertEqual(self._statut('/cours/info-2010/index.html'), 403)

    def test_remontee_refusee(self):
        self._creneau('/cours/info-201/')
        self.assertEqual(self._statut('/cours/info-201/../secret/index.html'), 403)
        self.assertEqual(self._statut('/cours/info-201/%2e%2e/secret/index.html'), 403)
        self.assertEqual(self._statut('/cours/info-201//index.html'), 200)

    def test_autre_page(self):
        reponse = self.client.get(self.url, HTTP_X_ORIGINAL_URI='/cours/info-201/index.html')
        self.assertEqual(reponse.status_code, 403)

    def test_entete_absent(self):
        Creneau.objects.create(
            classe=self.classe, type_ressource='page', chemin_page='',
            ouverture=timezone.now() - timedelta(hours=1), fermeture=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_ancien_entete_traefik_ignore(self):
        reponse = self.client.get(self.url, HTTP_X_FORWARDED_URI=self.page)
        self.assertEqual(reponse.status_code, 403)

    def test_non_connecte(self):
        self.client.logout()
        reponse = self.client.get(self.url, HTTP_X_ORIGINAL_URI=self.page)
        self.assertEqual(reponse.status_code, 401)
