import io
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path

from werkzeug.datastructures import FileStorage

from ada.fichiers import FichierRefuse, enregistrer, extension_autorisee, ouvrir
from ada.temps import iso, maintenant
from tests.base import BaseTests


class FichiersTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.classe_ = self.classe('CIEL')
        self.dehors = tempfile.TemporaryDirectory()
        self.addCleanup(self.dehors.cleanup)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.addCleanup(self.ctx.pop)

    def test_extensions(self):
        self.assertEqual(extension_autorisee('Compte Rendu.PDF'), '.pdf')
        self.assertEqual(extension_autorisee('archive.tar.gz'), '.tar.gz')
        self.assertIsNone(extension_autorisee('page.php'))
        self.assertIsNone(extension_autorisee('note.pdf.exe'))

    def test_nom_avec_chemin(self):
        upload = FileStorage(io.BytesIO(b'%PDF'), filename='../../secret.pdf')
        relatif, nom, taille = enregistrer(upload, self.classe_.id, 4, 9)
        self.assertEqual(nom, 'secret.pdf')
        self.assertEqual(relatif, '4/9.pdf')
        self.assertEqual(taille, 4)
        self.assertTrue((self.fichiers_de(self.classe_) / relatif).is_file())

    def test_vide_et_trop_gros(self):
        with self.assertRaises(FichierRefuse):
            enregistrer(FileStorage(io.BytesIO(b''), filename='a.pdf'), self.classe_.id, 1, 2)
        gros = b'x' * (self.app.config['MAX_UPLOAD_SIZE_MB'] * 1024 * 1024 + 1)
        with self.assertRaises(FichierRefuse):
            enregistrer(FileStorage(io.BytesIO(gros), filename='a.pdf'), self.classe_.id, 1, 2)
        self.assertEqual(list(self.fichiers_de(self.classe_).rglob('*')), [self.fichiers_de(self.classe_) / '1'])

    def test_echappement(self):
        with self.assertRaises(FichierRefuse):
            ouvrir(self.classe_.id, '../../etc/passwd')
        with self.assertRaises(FichierRefuse):
            ouvrir(self.classe_.id, '/etc/passwd')

    def test_lien_symbolique_hors_racine(self):
        secret = Path(self.dehors.name) / 'secret.txt'
        secret.write_text('secret')
        dossier = self.fichiers_de(self.classe_) / '1'
        dossier.mkdir()
        (dossier / '2.pdf').symlink_to(secret)
        with self.assertRaises(FichierRefuse):
            ouvrir(self.classe_.id, '1/2.pdf')

    def test_autre_classe(self):
        autre = self.classe('EISI')
        upload = FileStorage(io.BytesIO(b'%PDF'), filename='a.pdf')
        relatif, _nom, _taille = enregistrer(upload, autre.id, 1, 2)
        self.assertTrue(ouvrir(autre.id, relatif).is_file())
        with self.assertRaises(FichierRefuse):
            ouvrir(self.classe_.id, relatif)


class RenduTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.ciel = self.classe('CIEL')
        self.eisi = self.classe('EISI')
        self.admin = self.compte('admin@example.com', 'admin')
        self.eleve = self.compte('eleve@example.com', 'etudiant', self.ciel)
        self.autre = self.compte('autre@example.com', 'etudiant', self.eisi)
        self.devoir_id = self.devoir(self.ciel, 'TP 1', self.admin)
        self.url = f'/devoirs/{self.ciel.id}/{self.devoir_id}/'

    def _pdf(self, nom='compte-rendu.pdf', contenu=b'%PDF-1.4 contenu'):
        return self.fichier(nom, contenu)

    def test_creation_et_depot(self):
        self.connecter(self.admin)
        reponse = self.post('/admin/devoirs/', {
            'classe': self.ciel.id,
            'titre': 'TP 2',
            'description': 'A rendre',
            'date_limite': '2026-10-23T18:00',
        })
        devoir = self.un(self.ciel, "SELECT * FROM devoirs WHERE titre = 'TP 2'")
        self.assertRedirige(reponse, f'/admin/devoirs/{self.ciel.id}/{devoir["id"]}/')
        # Saisie à l'heure de Paris (été : UTC+2), stockée en UTC.
        self.assertEqual(devoir['date_limite'], '2026-10-23T16:00:00.000000+00:00')

        self.connecter(self.eleve)
        reponse = self.post(self.url, {'fichier': self._pdf()})
        self.assertRedirige(reponse, self.url)
        fichier = self.un(self.ciel, 'SELECT f.* FROM fichiers_rendus f JOIN soumissions s ON s.id = f.soumission_id '
                                     'WHERE s.etudiant_id = ?', self.eleve.id)
        self.assertEqual(fichier['nom_original'], 'compte-rendu.pdf')

        reponse = self.get(f'{self.url}fichiers/{fichier["id"]}/')
        self.assertEqual(reponse.data, b'%PDF-1.4 contenu')
        self.assertIn('attachment', reponse.headers['Content-Disposition'])

    def test_remplacement_et_unicite(self):
        self.connecter(self.eleve)
        self.post(self.url, {'fichier': self._pdf()})
        self.post(self.url, {'fichier': self._pdf('sources.tar.gz', b'archive')})
        self.assertEqual(len(self.sql(self.ciel, 'SELECT * FROM soumissions')), 1)
        fichiers = self.sql(self.ciel, 'SELECT * FROM fichiers_rendus')
        self.assertEqual(len(fichiers), 1)
        self.assertEqual(fichiers[0]['chemin'], f'{self.devoir_id}/{self.eleve.id}.tar.gz')
        self.assertFalse((self.fichiers_de(self.ciel) / f'{self.devoir_id}/{self.eleve.id}.pdf').exists())
        self.assertEqual((self.fichiers_de(self.ciel) / fichiers[0]['chemin']).read_bytes(), b'archive')

    def test_type_refuse_et_date_depassee(self):
        self.connecter(self.eleve)
        reponse = self.post(self.url, {'fichier': self._pdf('page.php', b'<?php')}, follow_redirects=True)
        self.assertContient(reponse, "pas accept")
        self.assertEqual(self.sql(self.ciel, 'SELECT * FROM soumissions'), [])

        self.sql(self.ciel, 'UPDATE devoirs SET date_limite = ?', iso(maintenant() - timedelta(hours=1)))
        reponse = self.post(self.url, {'fichier': self._pdf()}, follow_redirects=True)
        self.assertContient(reponse, 'date limite')
        self.assertEqual(self.sql(self.ciel, 'SELECT * FROM soumissions'), [])

    def test_trop_gros(self):
        self.connecter(self.eleve)
        gros = b'x' * ((self.app.config['MAX_UPLOAD_SIZE_MB'] + 1) * 1024 * 1024 + 10)
        reponse = self.post(self.url, {'fichier': self._pdf('gros.pdf', gros)})
        self.assertRedirige(reponse, self.url)
        self.assertContient(self.get(self.url), 'taille maximale')

    def test_eleve_hors_classe(self):
        self.connecter(self.autre)
        self.assertEqual(self.get(self.url).status_code, 404)
        self.assertRedirige(self.get('/admin/devoirs/'), '/devoirs/')

    def test_suivi_et_archive(self):
        self.connecter(self.eleve)
        self.post(self.url, {'fichier': self._pdf()})
        fichier = self.un(self.ciel, 'SELECT * FROM fichiers_rendus')

        self.connecter(self.autre)
        self.assertEqual(self.get(f'{self.url}fichiers/{fichier["id"]}/').status_code, 404)
        reponse = self.get(f'/admin/devoirs/{self.ciel.id}/{self.devoir_id}/fichiers/{fichier["id"]}/')
        self.assertRedirige(reponse, '/devoirs/')

        autre_devoir = self.devoir(self.eisi, 'Autre', self.admin)
        self.connecter(self.admin)
        reponse = self.get(f'/admin/devoirs/{self.eisi.id}/{autre_devoir}/fichiers/{fichier["id"]}/')
        self.assertEqual(reponse.status_code, 404)

        reponse = self.get(f'/admin/devoirs/{self.ciel.id}/{self.devoir_id}/archive/')
        self.assertEqual(reponse.status_code, 200)
        archive = zipfile.ZipFile(io.BytesIO(reponse.data))
        self.assertEqual(archive.read(archive.namelist()[0]), b'%PDF-1.4 contenu')
        self.assertTrue(archive.namelist()[0].startswith(f'{self.eleve.id}_'))

    def test_redirection_apres_connexion(self):
        self.deconnecter()
        reponse = self.post('/auth/login/?next=https://evil.example/phish', {
            'email': 'eleve@example.com', 'mot_de_passe': 'secret-12',
        })
        self.assertEqual(reponse.status_code, 302)
        self.assertNotIn('evil.example', reponse.headers['Location'])
        self.assertRedirige(reponse, '/devoirs/')

        self.deconnecter()
        reponse = self.post('/auth/login/?next=/auth/profil/', {
            'email': 'ELEVE@example.com', 'mot_de_passe': 'secret-12',
        })
        self.assertRedirige(reponse, '/auth/profil/')

        self.deconnecter()
        for cible in ('//evil.example/x', '/\\evil.example'):
            reponse = self.post('/auth/login/', {
                'email': 'eleve@example.com', 'mot_de_passe': 'secret-12', 'next': cible,
            })
            self.assertRedirige(reponse, '/devoirs/')
            self.deconnecter()
