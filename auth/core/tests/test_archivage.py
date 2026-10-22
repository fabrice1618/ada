import io
import json
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from core.archivage import calculer_empreinte, donnees_classe
from core.models import (
    Classe, Devoir, FichierRendu, Groupe, MembreGroupe, Soumission, Utilisateur,
)


class ArchivageTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.override = override_settings(UPLOAD_ROOT=self.tmp.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.racine = Path(self.tmp.name)

        self.classe = Classe.objects.create(nom='CIEL', annee='2026')
        self.autre_classe = Classe.objects.create(nom='EISI', annee='2026')
        self.admin = self._compte('admin@example.com', 'admin')
        self.prof = self._compte('prof@example.com', 'enseignant', self.classe)
        self.eleve = self._compte('eleve@example.com', 'etudiant', self.classe)
        self.binome = self._compte('binome@example.com', 'etudiant', self.classe)
        self.double = self._compte('double@example.com', 'etudiant', self.classe, self.autre_classe)
        self.ailleurs = self._compte('ailleurs@example.com', 'etudiant', self.autre_classe)

        self.devoir = self._devoir(self.classe, 'TP 1')
        self.projet = self._devoir(self.classe, 'Projet', type_rendu='fichiers', mode='groupe', taille_groupe_max=3)
        self.devoir_autre = self._devoir(self.autre_classe, 'TP EISI')

        self._deposer(self.eleve, self.devoir, 'compte-rendu.pdf', b'%PDF eleve')
        groupe = Groupe.objects.create(devoir=self.projet, nom='Les Ours', cree_par=self.eleve)
        for membre in (self.eleve, self.binome):
            MembreGroupe.objects.create(groupe=groupe, devoir=self.projet, etudiant=membre)
        self._deposer(self.binome, self.projet, 'main.py', b'print(1)')
        self._deposer(self.binome, self.projet, 'notes.txt', b'notes')
        self._deposer(self.ailleurs, self.devoir_autre, 'eisi.pdf', b'%PDF eisi')

    def _compte(self, email, role, *classes):
        user = Utilisateur.objects.create_user(
            email=email, password='secret-12', nom_complet=email.split('@')[0].title(), role=role,
        )
        user.classes.add(*classes)
        return user

    def _devoir(self, classe, titre, **champs):
        return Devoir.objects.create(
            classe=classe, titre=titre, cree_par=self.prof,
            date_limite=timezone.now() + timedelta(days=1), **champs,
        )

    def _deposer(self, etudiant, devoir, nom, contenu):
        self.client.force_login(etudiant)
        self.client.post(f'/devoirs/{devoir.id}/', {'fichier': SimpleUploadedFile(nom, contenu)})

    def _exporter(self):
        self.client.force_login(self.admin)
        reponse = self.client.get(f'/admin/classes/{self.classe.id}/archive/')
        self.assertEqual(reponse.status_code, 200)
        return b''.join(reponse.streaming_content), reponse

    def test_contenu_de_l_archive(self):
        contenu, reponse = self._exporter()
        self.assertIn('ada-ciel-2026-', reponse['Content-Disposition'])
        archive = zipfile.ZipFile(io.BytesIO(contenu))
        noms = set(archive.namelist())
        for attendu in ('classe.json', 'LISEZMOI.txt', 'etudiants.csv', 'devoirs.csv',
                        'groupes.csv', 'rendus.csv'):
            self.assertIn(attendu, noms)
        self.assertIn(f'fichiers/{self.devoir.id}-tp-1/eleve-{self.eleve.id}/compte-rendu.pdf', noms)
        groupe = Groupe.objects.get()
        dossier = f'fichiers/{self.projet.id}-projet/groupe-{groupe.id}-les-ours'
        self.assertEqual(archive.read(f'{dossier}/main.py'), b'print(1)')
        self.assertIn(f'{dossier}/notes.txt', noms)
        self.assertFalse(any('eisi' in nom for nom in noms))

        manifeste = json.loads(archive.read('classe.json'))
        self.assertEqual(manifeste['empreinte'], calculer_empreinte(donnees_classe(self.classe)))
        membres = {m['email']: m for m in manifeste['donnees']['membres']}
        self.assertTrue(membres['eleve@example.com']['compte_supprime'])
        self.assertFalse(membres['double@example.com']['compte_supprime'])
        self.assertFalse(membres['prof@example.com']['compte_supprime'])
        brut = archive.read('classe.json').decode() + archive.read('etudiants.csv').decode('utf-8-sig')
        self.assertNotIn('md5$', brut)
        self.assertNotIn('password', brut)
        self.assertIn('Les Ours;Eleve', archive.read('groupes.csv').decode('utf-8-sig'))

    def test_page_classe(self):
        self.client.force_login(self.admin)
        reponse = self.client.get(f'/admin/classes/{self.classe.id}/')
        self.assertContains(reponse, 'Exporter l')
        self.assertContains(reponse, calculer_empreinte(donnees_classe(self.classe)))

    def test_suppression(self):
        empreinte = calculer_empreinte(donnees_classe(self.classe))
        fichiers_classe = list(
            FichierRendu.objects.filter(soumission__devoir__classe=self.classe).values_list('chemin', flat=True)
        )
        self.client.force_login(self.admin)
        reponse = self.client.post(f'/admin/classes/{self.classe.id}/supprimer/', {
            'confirmation': 'CIEL', 'archive_verifiee': 'on', 'empreinte': empreinte,
        })
        self.assertRedirects(reponse, '/admin/')

        self.assertFalse(Classe.objects.filter(id=self.classe.id).exists())
        self.assertFalse(Devoir.objects.filter(classe_id=self.classe.id).exists())
        self.assertFalse(Utilisateur.objects.filter(email__in=['eleve@example.com', 'binome@example.com']).exists())
        self.assertEqual(list(self.double.classes.all()), [self.autre_classe])
        self.assertTrue(Utilisateur.objects.filter(id=self.prof.id).exists())
        self.assertEqual(Groupe.objects.count(), 0)
        for chemin in fichiers_classe:
            self.assertFalse((self.racine / chemin).exists())
        self.assertFalse((self.racine / str(self.devoir.id)).exists())
        self.assertFalse((self.racine / str(self.projet.id)).exists())

        reste = Soumission.objects.get(devoir=self.devoir_autre)
        self.assertTrue((self.racine / reste.fichiers.get().chemin).is_file())

    def test_suppression_refusee(self):
        empreinte = calculer_empreinte(donnees_classe(self.classe))
        url = f'/admin/classes/{self.classe.id}/supprimer/'
        self.client.force_login(self.admin)
        self.client.post(url, {'confirmation': 'ciel', 'archive_verifiee': 'on', 'empreinte': empreinte})
        self.client.post(url, {'confirmation': 'CIEL', 'empreinte': empreinte})

        self._deposer(self.eleve, self.devoir, 'v2.pdf', b'%PDF v2')
        self.client.force_login(self.admin)
        reponse = self.client.post(
            url, {'confirmation': 'CIEL', 'archive_verifiee': 'on', 'empreinte': empreinte}, follow=True,
        )
        self.assertContains(reponse, 'ont changé')

        self.client.force_login(self.prof)
        self.client.post(url, {
            'confirmation': 'CIEL', 'archive_verifiee': 'on',
            'empreinte': calculer_empreinte(donnees_classe(self.classe)),
        })
        self.assertEqual(self.client.get(f'/admin/classes/{self.classe.id}/archive/').status_code, 302)
        self.assertTrue(Classe.objects.filter(id=self.classe.id).exists())

    def test_commande(self):
        sortie = self.racine / 'export.zip'
        call_command('archiver_classe', self.classe.id, sortie=str(sortie), stderr=io.StringIO())
        self.assertTrue(zipfile.is_zipfile(sortie))

        self._deposer(self.eleve, self.devoir, 'v2.pdf', b'%PDF v2')
        with self.assertRaisesMessage(CommandError, 'ont changé'):
            call_command('archiver_classe', self.classe.id, supprimer=str(sortie), stderr=io.StringIO())
        with self.assertRaisesMessage(CommandError, "pas celle de la classe"):
            call_command('archiver_classe', self.autre_classe.id, supprimer=str(sortie), stderr=io.StringIO())

        call_command('archiver_classe', self.classe.id, sortie=str(sortie), stderr=io.StringIO())
        journal = io.StringIO()
        call_command('archiver_classe', self.classe.id, supprimer=str(sortie), stderr=journal)
        self.assertIn('supprimée', journal.getvalue())
        self.assertFalse(Classe.objects.filter(id=self.classe.id).exists())

    def test_archive_corrompue(self):
        abime = self.racine / 'abime.zip'
        abime.write_bytes(b'pas un zip')
        with self.assertRaisesMessage(CommandError, 'pas une archive zip'):
            call_command('archiver_classe', self.classe.id, supprimer=str(abime), stderr=io.StringIO())
        self.assertTrue(Classe.objects.filter(id=self.classe.id).exists())
