import io
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from core.fichiers import FichierRefuse, enregistrer, extension_autorisee, ouvrir
from core.models import Classe, Devoir, Soumission, Utilisateur


class FichiersTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dehors = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.dehors.cleanup)
        self.override = override_settings(UPLOAD_ROOT=self.tmp.name)
        self.override.enable()
        self.addCleanup(self.override.disable)

    def test_extensions(self):
        self.assertEqual(extension_autorisee('Compte Rendu.PDF'), '.pdf')
        self.assertEqual(extension_autorisee('archive.tar.gz'), '.tar.gz')
        self.assertIsNone(extension_autorisee('page.php'))
        self.assertIsNone(extension_autorisee('note.pdf.exe'))

    def test_nom_avec_chemin(self):
        upload = SimpleUploadedFile('../../secret.pdf', b'%PDF')
        relatif, nom, taille = enregistrer(upload, 4, 9)
        self.assertEqual(nom, 'secret.pdf')
        self.assertEqual(relatif, '4/9.pdf')
        self.assertEqual(taille, 4)
        self.assertTrue((Path(self.tmp.name) / relatif).is_file())

    def test_echappement(self):
        with self.assertRaises(FichierRefuse):
            ouvrir('../../etc/passwd')
        with self.assertRaises(FichierRefuse):
            ouvrir('/etc/passwd')

    def test_lien_symbolique_hors_racine(self):
        secret = Path(self.dehors.name) / 'secret.txt'
        secret.write_text('secret')
        dossier = Path(self.tmp.name) / '1'
        dossier.mkdir()
        (dossier / '2.pdf').symlink_to(secret)
        with self.assertRaises(FichierRefuse):
            ouvrir('1/2.pdf')


class RenduTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.override = override_settings(UPLOAD_ROOT=self.tmp.name)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.classe = Classe.objects.create(nom='CIEL', annee='2026')
        self.autre_classe = Classe.objects.create(nom='EISI', annee='2026')
        self.admin = self._compte('admin@example.com', 'admin')
        self.eleve = self._compte('eleve@example.com', 'etudiant', self.classe)
        self.autre = self._compte('autre@example.com', 'etudiant', self.autre_classe)
        self.devoir = Devoir.objects.create(
            classe=self.classe,
            titre='TP 1',
            description='Compte rendu',
            date_limite=timezone.now() + timedelta(days=1),
            cree_par=self.admin,
        )

    def _compte(self, email, role, classe=None):
        user = Utilisateur.objects.create_user(
            email=email,
            password='secret-12',
            nom_complet=email,
            role=role,
        )
        if classe is not None:
            user.classes.add(classe)
        return user

    def _pdf(self, nom='compte-rendu.pdf', contenu=b'%PDF-1.4 contenu'):
        return SimpleUploadedFile(nom, contenu)

    def test_creation_et_depot(self):
        self.client.force_login(self.admin)
        reponse = self.client.post('/admin/devoirs/', {
            'classe': self.classe.id,
            'titre': 'TP 2',
            'description': 'A rendre',
            'date_limite': '2026-10-23T18:00',
        })
        devoir = Devoir.objects.get(titre='TP 2')
        self.assertRedirects(reponse, f'/admin/devoirs/{devoir.id}/')

        self.client.force_login(self.eleve)
        reponse = self.client.post(
            f'/devoirs/{self.devoir.id}/',
            {'fichier': self._pdf()},
        )
        self.assertRedirects(reponse, f'/devoirs/{self.devoir.id}/')
        soumission = Soumission.objects.get(devoir=self.devoir, etudiant=self.eleve)
        fichier = soumission.fichiers.get()
        self.assertEqual(fichier.nom_original, 'compte-rendu.pdf')

        reponse = self.client.get(f'/devoirs/{self.devoir.id}/fichiers/{fichier.id}/')
        self.assertEqual(b''.join(reponse.streaming_content), b'%PDF-1.4 contenu')
        self.assertIn('attachment', reponse['Content-Disposition'])

    def test_remplacement_et_unicite(self):
        self.client.force_login(self.eleve)
        self.client.post(f'/devoirs/{self.devoir.id}/', {'fichier': self._pdf()})
        self.client.post(
            f'/devoirs/{self.devoir.id}/',
            {'fichier': self._pdf('sources.tar.gz', b'archive')},
        )
        self.assertEqual(Soumission.objects.filter(devoir=self.devoir).count(), 1)
        soumission = Soumission.objects.get(devoir=self.devoir, etudiant=self.eleve)
        fichier = soumission.fichiers.get()
        self.assertEqual(fichier.chemin, f'{self.devoir.id}/{self.eleve.id}.tar.gz')
        self.assertFalse((Path(self.tmp.name) / f'{self.devoir.id}/{self.eleve.id}.pdf').exists())
        self.assertEqual((Path(self.tmp.name) / fichier.chemin).read_bytes(), b'archive')

    def test_type_refuse_et_date_depassee(self):
        self.client.force_login(self.eleve)
        reponse = self.client.post(
            f'/devoirs/{self.devoir.id}/',
            {'fichier': self._pdf('page.php', b'<?php')},
            follow=True,
        )
        self.assertContains(reponse, "pas accept")
        self.assertEqual(Soumission.objects.count(), 0)

        self.devoir.date_limite = timezone.now() - timedelta(hours=1)
        self.devoir.save()
        reponse = self.client.post(
            f'/devoirs/{self.devoir.id}/',
            {'fichier': self._pdf()},
            follow=True,
        )
        self.assertContains(reponse, 'date limite')
        self.assertEqual(Soumission.objects.count(), 0)

    def test_eleve_hors_classe(self):
        self.client.force_login(self.autre)
        reponse = self.client.get(f'/devoirs/{self.devoir.id}/')
        self.assertEqual(reponse.status_code, 404)
        reponse = self.client.get('/admin/devoirs/')
        self.assertRedirects(reponse, '/devoirs/')

    def test_suivi_et_archive(self):
        self.client.force_login(self.eleve)
        self.client.post(f'/devoirs/{self.devoir.id}/', {'fichier': self._pdf()})
        fichier = Soumission.objects.get(devoir=self.devoir).fichiers.get()

        self.client.force_login(self.autre)
        reponse = self.client.get(f'/devoirs/{self.devoir.id}/fichiers/{fichier.id}/')
        self.assertEqual(reponse.status_code, 404)
        reponse = self.client.get(
            f'/admin/devoirs/{self.devoir.id}/fichiers/{fichier.id}/'
        )
        self.assertRedirects(reponse, '/devoirs/')

        autre_devoir = Devoir.objects.create(
            classe=self.autre_classe,
            titre='Autre',
            date_limite=timezone.now() + timedelta(days=1),
            cree_par=self.admin,
        )
        self.client.force_login(self.admin)
        reponse = self.client.get(
            f'/admin/devoirs/{autre_devoir.id}/fichiers/{fichier.id}/'
        )
        self.assertEqual(reponse.status_code, 404)

        reponse = self.client.get(f'/admin/devoirs/{self.devoir.id}/archive/')
        self.assertEqual(reponse.status_code, 200)
        archive = zipfile.ZipFile(io.BytesIO(b''.join(reponse.streaming_content)))
        self.assertEqual(archive.read(archive.namelist()[0]), b'%PDF-1.4 contenu')
        self.assertTrue(archive.namelist()[0].startswith(f'{self.eleve.id}_'))

    def test_redirection_apres_connexion(self):
        reponse = self.client.post('/auth/login/?next=https://evil.example/phish', {
            'email': self.eleve.email,
            'mot_de_passe': 'secret-12',
        })
        self.assertEqual(reponse.status_code, 302)
        self.assertNotIn('evil.example', reponse['Location'])
        self.assertEqual(reponse['Location'], '/devoirs/')

        self.client.logout()
        reponse = self.client.post('/auth/login/?next=/auth/profil/', {
            'email': self.eleve.email,
            'mot_de_passe': 'secret-12',
        })
        self.assertEqual(reponse['Location'], '/auth/profil/')
