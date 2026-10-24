from datetime import timedelta

from ada.temps import iso, maintenant
from tests.base import BaseTests


class CoursTests(BaseTests):
    page = '/cours/math-101/chapitre1.html'

    def setUp(self):
        super().setUp()
        cours = self.racine / 'cours'
        for chemin, contenu in {
            'math-101/index.html': 'sommaire math',
            'math-101/chapitre1.html': 'chapitre 1',
            'info-201/index.html': 'sommaire info',
            'info-201/img/schema.png': 'png',
            'info-2010/index.html': 'autre cours',
            'secret/index.html': 'secret',
        }.items():
            (cours / chemin).parent.mkdir(parents=True, exist_ok=True)
            (cours / chemin).write_text(contenu)
        self.ciel = self.classe('CIEL')
        self.eleve = self.compte('eleve@example.com', 'etudiant', self.ciel)
        self.creneau(self.page)
        self.connecter(self.eleve)

    def creneau(self, chemin, debut=-1, fin=1):
        self.sql(
            self.ciel,
            "INSERT INTO creneaux (type_ressource, chemin_page, ouverture, fermeture) VALUES ('page', ?, ?, ?)",
            chemin, iso(maintenant() + timedelta(hours=debut)), iso(maintenant() + timedelta(hours=fin)),
        )

    def statut(self, url):
        return self.get(url).status_code

    def test_creneau_ouvert(self):
        reponse = self.get(self.page)
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data, b'chapitre 1')

    def test_parametres_ignores(self):
        self.assertEqual(self.statut(self.page + '?v=2'), 200)

    def test_dossier_couvre_ses_fichiers(self):
        self.creneau('/cours/info-201/')
        reponse = self.get('/cours/info-201/')
        self.assertEqual(reponse.data, b'sommaire info')
        self.assertEqual(self.statut('/cours/info-201/img/schema.png'), 200)
        self.assertEqual(self.statut('/cours/info-2010/index.html'), 403)
        self.assertRedirige(self.get('/cours/info-201'), '/cours/info-201/')

    def test_dossier_sans_barre_finale(self):
        self.creneau('/cours/info-201')
        self.assertEqual(self.statut('/cours/info-201/index.html'), 200)
        self.assertEqual(self.statut('/cours/info-2010/index.html'), 403)

    def test_remontee_refusee(self):
        self.creneau('/cours/info-201/')
        self.assertEqual(self.statut('/cours/info-201/../secret/index.html'), 403)
        self.assertEqual(self.statut('/cours/info-201/%2e%2e/secret/index.html'), 403)
        self.assertEqual(self.statut('/cours/info-201//index.html'), 200)

    def test_autre_page_et_creneau_ferme(self):
        self.assertEqual(self.statut('/cours/info-201/index.html'), 403)
        self.creneau('/cours/info-201/', debut=-3, fin=-2)
        self.assertEqual(self.statut('/cours/info-201/index.html'), 403)
        self.assertContient(self.get('/cours/info-201/index.html'), 'créneau horaire est fermé')

    def test_chemin_vide_ne_couvre_rien(self):
        self.creneau('')
        self.assertEqual(self.statut('/cours/secret/index.html'), 403)

    def test_page_absente(self):
        self.creneau('/cours/')
        self.assertEqual(self.statut('/cours/absent.html'), 404)

    def test_personnel_sans_creneau(self):
        prof = self.compte('prof@example.com', 'enseignant')
        self.connecter(prof)
        self.assertEqual(self.statut('/cours/secret/index.html'), 200)

    def test_non_connecte(self):
        self.deconnecter()
        reponse = self.get(self.page)
        self.assertRedirige(reponse, f'/auth/login/?next={self.page}')
