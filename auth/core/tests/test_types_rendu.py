import io
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from core.models import Classe, Devoir, FichierRendu, Groupe, MembreGroupe, Soumission, Utilisateur


class BaseTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.override = override_settings(UPLOAD_ROOT=self.tmp.name, MAX_UPLOAD_FILES=3)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.classe = Classe.objects.create(nom='CIEL', annee='2026')
        self.admin = self._compte('admin@example.com', 'admin')
        self.eleve = self._compte('eleve@example.com', 'etudiant', self.classe)
        self.binome = self._compte('binome@example.com', 'etudiant', self.classe)
        self.tiers = self._compte('tiers@example.com', 'etudiant', self.classe)

    def _compte(self, email, role, classe=None):
        user = Utilisateur.objects.create_user(
            email=email, password='secret-12', nom_complet=email, role=role,
        )
        if classe is not None:
            user.classes.add(classe)
        return user

    def _devoir(self, **champs):
        champs.setdefault('date_limite', timezone.now() + timedelta(days=1))
        return Devoir.objects.create(
            classe=self.classe, titre='TP', cree_par=self.admin, **champs,
        )

    def _fichier(self, nom='a.py', contenu=b'print(1)'):
        return SimpleUploadedFile(nom, contenu)

    def _groupe(self, devoir, nom, *membres):
        groupe = Groupe.objects.create(devoir=devoir, nom=nom, cree_par=membres[0])
        for membre in membres:
            MembreGroupe.objects.create(groupe=groupe, devoir=devoir, etudiant=membre)
        return groupe


class PlusieursFichiersTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.devoir = self._devoir(type_rendu='fichiers')
        self.url = f'/devoirs/{self.devoir.id}/'
        self.client.force_login(self.eleve)

    def test_ajout_remplacement_et_suppression(self):
        self.client.post(self.url, {'fichier': self._fichier('a.py', b'v1')})
        self.client.post(self.url, {'fichier': self._fichier('b.py')})
        self.client.post(self.url, {'fichier': self._fichier('a.py', b'v2')})
        soumission = Soumission.objects.get(devoir=self.devoir, etudiant=self.eleve)
        fichiers = list(soumission.fichiers.all())
        self.assertEqual([f.nom_original for f in fichiers], ['a.py', 'b.py'])
        self.assertEqual((Path(self.tmp.name) / fichiers[0].chemin).read_bytes(), b'v2')
        self.assertEqual(len(list((Path(self.tmp.name) / str(self.devoir.id)).rglob('*.py'))), 2)

        self.client.post(f'{self.url}fichiers/{fichiers[0].id}/supprimer/')
        self.assertFalse((Path(self.tmp.name) / fichiers[0].chemin).exists())
        self.client.post(f'{self.url}fichiers/{fichiers[1].id}/supprimer/')
        self.assertFalse(Soumission.objects.filter(devoir=self.devoir).exists())

    def test_nombre_maximal(self):
        for nom in ('a.py', 'b.py', 'c.py'):
            self.client.post(self.url, {'fichier': self._fichier(nom)})
        reponse = self.client.post(self.url, {'fichier': self._fichier('d.py')}, follow=True)
        self.assertContains(reponse, '3 fichiers maximum')
        self.assertEqual(FichierRendu.objects.count(), 3)

    def test_archive_en_dossier(self):
        self.client.post(self.url, {'fichier': self._fichier('a.py')})
        self.client.post(self.url, {'fichier': self._fichier('b.py')})
        self.client.force_login(self.admin)
        reponse = self.client.get(f'/admin/devoirs/{self.devoir.id}/archive/')
        archive = zipfile.ZipFile(io.BytesIO(b''.join(reponse.streaming_content)))
        self.assertEqual(
            sorted(archive.namelist()),
            [f'{self.eleve.id}/a.py', f'{self.eleve.id}/b.py'],
        )

    def test_un_fichier_ne_se_supprime_pas(self):
        devoir = self._devoir(type_rendu='fichier')
        self.client.post(f'/devoirs/{devoir.id}/', {'fichier': self._fichier()})
        fichier = FichierRendu.objects.get(soumission__devoir=devoir)
        self.client.post(f'/devoirs/{devoir.id}/fichiers/{fichier.id}/supprimer/')
        self.assertTrue(FichierRendu.objects.filter(id=fichier.id).exists())


class LienGithubTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.devoir = self._devoir(type_rendu='github')
        self.url = f'/devoirs/{self.devoir.id}/'
        self.client.force_login(self.eleve)

    def test_lien_valide_puis_remplace(self):
        self.client.post(self.url, {'lien': 'https://github.com/eleve/tp1'})
        self.client.post(self.url, {'lien': 'https://github.com/eleve/tp1-bis/tree/main'})
        soumission = Soumission.objects.get(devoir=self.devoir, etudiant=self.eleve)
        self.assertEqual(soumission.type, 'github')
        self.assertEqual(soumission.lien_github, 'https://github.com/eleve/tp1-bis/tree/main')

    def test_lien_refuse(self):
        for lien in ('https://gitlab.com/eleve/tp1', 'https://github.com/eleve', 'javascript:alert(1)'):
            reponse = self.client.post(self.url, {'lien': lien}, follow=True)
            self.assertContains(reponse, 'alert-danger')
        self.assertFalse(Soumission.objects.exists())

    def test_fichier_ignore(self):
        self.client.post(self.url, {'fichier': self._fichier()})
        self.assertFalse(Soumission.objects.exists())


class GroupeTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.devoir = self._devoir(mode='groupe', taille_groupe_max=2)
        self.url = f'/devoirs/{self.devoir.id}/'

    def _action(self, etudiant, **donnees):
        self.client.force_login(etudiant)
        return self.client.post(f'{self.url}groupe/', donnees, follow=True)

    def test_creer_rejoindre_complet(self):
        self._action(self.eleve, action='creer', nom='  Les   Ours ')
        groupe = Groupe.objects.get(devoir=self.devoir)
        self.assertEqual(groupe.nom, 'Les Ours')
        self.assertEqual(list(groupe.membres.all()), [self.eleve])

        self._action(self.binome, action='rejoindre', groupe=groupe.id)
        reponse = self._action(self.tiers, action='rejoindre', groupe=groupe.id)
        self.assertContains(reponse, 'complet')
        self.assertEqual(groupe.adhesions.count(), 2)

        reponse = self._action(self.tiers, action='creer', nom='les ours')
        self.assertContains(reponse, 'déjà pris')

    def test_un_seul_groupe_par_devoir(self):
        self._action(self.eleve, action='creer', nom='A')
        reponse = self._action(self.eleve, action='creer', nom='B')
        self.assertContains(reponse, "Quittez d&#x27;abord")
        self.assertEqual(Groupe.objects.count(), 1)

        autre = self._devoir(mode='groupe', taille_groupe_max=2)
        self.client.post(f'/devoirs/{autre.id}/groupe/', {'action': 'creer', 'nom': 'A'})
        self.assertEqual(MembreGroupe.objects.filter(etudiant=self.eleve).count(), 2)

    def test_rendu_partage_par_le_groupe(self):
        self.client.force_login(self.eleve)
        self.client.post(self.url, {'fichier': self._fichier()})
        self.assertFalse(Soumission.objects.exists())

        groupe = self._groupe(self.devoir, 'A', self.eleve, self.binome)
        self.client.force_login(self.eleve)
        self.client.post(self.url, {'fichier': self._fichier('rapport.pdf', b'%PDF v1')})
        soumission = Soumission.objects.get(devoir=self.devoir)
        self.assertEqual(soumission.groupe, groupe)
        self.assertIsNone(soumission.etudiant)
        fichier = soumission.fichiers.get()
        self.assertEqual(fichier.chemin, f'{self.devoir.id}/g{groupe.id}.pdf')

        self.client.force_login(self.binome)
        reponse = self.client.get(f'{self.url}fichiers/{fichier.id}/')
        self.assertEqual(b''.join(reponse.streaming_content), b'%PDF v1')
        self.client.post(self.url, {'fichier': self._fichier('rapport.pdf', b'%PDF v2')})
        soumission.refresh_from_db()
        self.assertEqual(soumission.deposee_par, self.binome)
        self.assertEqual(Soumission.objects.count(), 1)

        self.client.force_login(self.tiers)
        reponse = self.client.get(f'{self.url}fichiers/{soumission.fichiers.get().id}/')
        self.assertEqual(reponse.status_code, 404)

    def test_quitter(self):
        self._action(self.eleve, action='creer', nom='A')
        self._action(self.eleve, action='quitter')
        self.assertFalse(Groupe.objects.exists())

        groupe = self._groupe(self.devoir, 'B', self.eleve)
        self.client.force_login(self.eleve)
        self.client.post(self.url, {'fichier': self._fichier('rapport.pdf', b'%PDF')})
        self._action(self.eleve, action='quitter')
        self.assertTrue(Groupe.objects.filter(id=groupe.id).exists())
        self.assertFalse(MembreGroupe.objects.exists())

    def test_date_depassee(self):
        self.devoir.date_limite = timezone.now() - timedelta(hours=1)
        self.devoir.save()
        reponse = self._action(self.eleve, action='creer', nom='A')
        self.assertContains(reponse, 'date limite')
        self.assertFalse(Groupe.objects.exists())

    def test_devoir_individuel(self):
        devoir = self._devoir()
        self.client.force_login(self.eleve)
        reponse = self.client.post(f'/devoirs/{devoir.id}/groupe/', {'action': 'creer', 'nom': 'A'})
        self.assertEqual(reponse.status_code, 404)

    def test_suivi_et_archive(self):
        groupe = self._groupe(self.devoir, 'Les Ours', self.eleve, self.binome)
        self.client.force_login(self.eleve)
        self.client.post(self.url, {'fichier': self._fichier('rapport.pdf', b'%PDF')})

        self.client.force_login(self.admin)
        reponse = self.client.get(f'/admin/devoirs/{self.devoir.id}/')
        self.assertContains(reponse, 'Les Ours')
        self.assertContains(reponse, 'Sans groupe (1)')
        self.assertContains(reponse, 'Rendus (1 / 1 groupes)')
        reponse = self.client.get(f'/admin/devoirs/{self.devoir.id}/archive/')
        archive = zipfile.ZipFile(io.BytesIO(b''.join(reponse.streaming_content)))
        self.assertEqual(archive.namelist(), [f'groupe-{groupe.id}-les-ours_rapport.pdf'])


class ConfigurationDevoirTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def _donnees(self, **champs):
        donnees = {
            'titre': 'Projet',
            'description': '',
            'date_limite': '2026-12-01T18:00',
            'type_rendu': 'fichiers',
            'mode': 'groupe',
            'taille_groupe_max': 3,
        }
        donnees.update(champs)
        return donnees

    def test_creation(self):
        self.client.post('/admin/devoirs/', self._donnees(classe=self.classe.id))
        devoir = Devoir.objects.get(titre='Projet')
        self.assertEqual((devoir.type_rendu, devoir.mode, devoir.taille_groupe_max), ('fichiers', 'groupe', 3))

        reponse = self.client.post('/admin/devoirs/', self._donnees(
            classe=self.classe.id, titre='Sans taille', taille_groupe_max='',
        ))
        self.assertContains(reponse, 'Indiquez la taille')
        self.assertFalse(Devoir.objects.filter(titre='Sans taille').exists())

        self.client.post('/admin/devoirs/', self._donnees(
            classe=self.classe.id, titre='Seul', mode='individuel',
        ))
        self.assertIsNone(Devoir.objects.get(titre='Seul').taille_groupe_max)

    def test_modifiable_sans_rendu(self):
        devoir = self._devoir()
        self.client.post(f'/admin/devoirs/{devoir.id}/', self._donnees(type_rendu='github'))
        devoir.refresh_from_db()
        self.assertEqual((devoir.type_rendu, devoir.mode), ('github', 'groupe'))

    def test_verrouille_avec_rendu(self):
        devoir = self._devoir(type_rendu='fichier')
        self.client.force_login(self.eleve)
        self.client.post(f'/devoirs/{devoir.id}/', {'fichier': self._fichier()})

        self.client.force_login(self.admin)
        reponse = self.client.get(f'/admin/devoirs/{devoir.id}/')
        self.assertContains(reponse, 'Verrouillé')
        self.client.post(f'/admin/devoirs/{devoir.id}/', self._donnees(titre='Nouveau titre'))
        devoir.refresh_from_db()
        self.assertEqual(devoir.titre, 'Nouveau titre')
        self.assertEqual((devoir.type_rendu, devoir.mode), ('fichier', 'individuel'))

    def test_taille_pas_sous_un_groupe_existant(self):
        devoir = self._devoir(mode='groupe', taille_groupe_max=3)
        self._groupe(devoir, 'A', self.eleve, self.binome, self.tiers)
        reponse = self.client.post(f'/admin/devoirs/{devoir.id}/', self._donnees(
            type_rendu='fichier', taille_groupe_max=2,
        ))
        self.assertContains(reponse, 'compte déjà 3 membres')
        devoir.refresh_from_db()
        self.assertEqual(devoir.taille_groupe_max, 3)
