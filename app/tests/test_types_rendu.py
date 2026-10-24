import io
import zipfile
from datetime import timedelta

from ada.temps import iso, maintenant
from tests.base import BaseTests


class Base(BaseTests):
    config = {'MAX_UPLOAD_FILES': 3}

    def setUp(self):
        super().setUp()
        self.ciel = self.classe('CIEL')
        self.admin = self.compte('admin@example.com', 'admin')
        self.eleve = self.compte('eleve@example.com', 'etudiant', self.ciel)
        self.binome = self.compte('binome@example.com', 'etudiant', self.ciel)
        self.tiers = self.compte('tiers@example.com', 'etudiant', self.ciel)

    def url_devoir(self, devoir_id):
        return f'/devoirs/{self.ciel.id}/{devoir_id}/'


class PlusieursFichiersTests(Base):
    def setUp(self):
        super().setUp()
        self.devoir_id = self.devoir(self.ciel, type_rendu='fichiers')
        self.url = self.url_devoir(self.devoir_id)
        self.connecter(self.eleve)

    def test_ajout_remplacement_et_suppression(self):
        self.post(self.url, {'fichier': self.fichier('a.py', b'v1')})
        self.post(self.url, {'fichier': self.fichier('b.py')})
        self.post(self.url, {'fichier': self.fichier('a.py', b'v2')})
        fichiers = self.sql(self.ciel, 'SELECT * FROM fichiers_rendus ORDER BY nom_original')
        self.assertEqual([f['nom_original'] for f in fichiers], ['a.py', 'b.py'])
        self.assertEqual((self.fichiers_de(self.ciel) / fichiers[0]['chemin']).read_bytes(), b'v2')
        self.assertEqual(len(list((self.fichiers_de(self.ciel) / str(self.devoir_id)).rglob('*.py'))), 2)

        self.post(f'{self.url}fichiers/{fichiers[0]["id"]}/supprimer/')
        self.assertFalse((self.fichiers_de(self.ciel) / fichiers[0]['chemin']).exists())
        self.post(f'{self.url}fichiers/{fichiers[1]["id"]}/supprimer/')
        self.assertEqual(self.sql(self.ciel, 'SELECT * FROM soumissions'), [])

    def test_nombre_maximal(self):
        for nom in ('a.py', 'b.py', 'c.py'):
            self.post(self.url, {'fichier': self.fichier(nom)})
        reponse = self.post(self.url, {'fichier': self.fichier('d.py')}, follow_redirects=True)
        self.assertContient(reponse, '3 fichiers maximum')
        self.assertEqual(len(self.sql(self.ciel, 'SELECT * FROM fichiers_rendus')), 3)

    def test_archive_en_dossier(self):
        self.post(self.url, {'fichier': self.fichier('a.py')})
        self.post(self.url, {'fichier': self.fichier('b.py')})
        self.connecter(self.admin)
        reponse = self.get(f'/admin/devoirs/{self.ciel.id}/{self.devoir_id}/archive/')
        archive = zipfile.ZipFile(io.BytesIO(reponse.data))
        self.assertEqual(sorted(archive.namelist()), [f'{self.eleve.id}/a.py', f'{self.eleve.id}/b.py'])

    def test_un_fichier_ne_se_supprime_pas(self):
        devoir_id = self.devoir(self.ciel, type_rendu='fichier')
        self.post(self.url_devoir(devoir_id), {'fichier': self.fichier()})
        fichier = self.un(self.ciel, 'SELECT * FROM fichiers_rendus')
        self.post(f'{self.url_devoir(devoir_id)}fichiers/{fichier["id"]}/supprimer/')
        self.assertIsNotNone(self.un(self.ciel, 'SELECT * FROM fichiers_rendus WHERE id = ?', fichier['id']))


class LienGithubTests(Base):
    def setUp(self):
        super().setUp()
        self.devoir_id = self.devoir(self.ciel, type_rendu='github')
        self.url = self.url_devoir(self.devoir_id)
        self.connecter(self.eleve)

    def test_lien_valide_puis_remplace(self):
        self.post(self.url, {'lien': 'https://github.com/eleve/tp1'})
        self.post(self.url, {'lien': 'github.com/eleve/tp1-bis/tree/main'})
        soumission = self.un(self.ciel, 'SELECT * FROM soumissions WHERE etudiant_id = ?', self.eleve.id)
        self.assertEqual(soumission['type'], 'github')
        self.assertEqual(soumission['lien_github'], 'https://github.com/eleve/tp1-bis/tree/main')
        self.assertContient(self.get(self.url), 'https://github.com/eleve/tp1-bis/tree/main')

    def test_lien_refuse(self):
        for lien in ('https://gitlab.com/eleve/tp1', 'https://github.com/eleve', 'javascript:alert(1)'):
            reponse = self.post(self.url, {'lien': lien}, follow_redirects=True)
            self.assertContient(reponse, 'alert-danger')
        self.assertEqual(self.sql(self.ciel, 'SELECT * FROM soumissions'), [])

    def test_fichier_ignore(self):
        self.post(self.url, {'fichier': self.fichier()})
        self.assertEqual(self.sql(self.ciel, 'SELECT * FROM soumissions'), [])


class GroupeTests(Base):
    def setUp(self):
        super().setUp()
        self.devoir_id = self.devoir(self.ciel, mode='groupe', taille_groupe_max=2)
        self.url = self.url_devoir(self.devoir_id)

    def _action(self, etudiant, **donnees):
        self.connecter(etudiant)
        return self.post(f'{self.url}groupe/', donnees, follow_redirects=True)

    def _membres(self, groupe_id):
        return [m['etudiant_id'] for m in self.sql(
            self.ciel, 'SELECT etudiant_id FROM membres_groupe WHERE groupe_id = ? ORDER BY id', groupe_id,
        )]

    def test_creer_rejoindre_complet(self):
        self._action(self.eleve, action='creer', nom='  Les   Ours ')
        groupe = self.un(self.ciel, 'SELECT * FROM groupes')
        self.assertEqual(groupe['nom'], 'Les Ours')
        self.assertEqual(self._membres(groupe['id']), [self.eleve.id])

        self._action(self.binome, action='rejoindre', groupe=groupe['id'])
        reponse = self._action(self.tiers, action='rejoindre', groupe=groupe['id'])
        self.assertContient(reponse, 'complet')
        self.assertEqual(len(self._membres(groupe['id'])), 2)

        reponse = self._action(self.tiers, action='creer', nom='les ours')
        self.assertContient(reponse, 'déjà pris')

    def test_un_seul_groupe_par_devoir(self):
        self._action(self.eleve, action='creer', nom='A')
        reponse = self._action(self.eleve, action='creer', nom='B')
        self.assertContient(reponse, "Quittez d&#39;abord")
        self.assertEqual(len(self.sql(self.ciel, 'SELECT * FROM groupes')), 1)

        autre = self.devoir(self.ciel, mode='groupe', taille_groupe_max=2)
        self.post(f'{self.url_devoir(autre)}groupe/', {'action': 'creer', 'nom': 'A'})
        self.assertEqual(
            len(self.sql(self.ciel, 'SELECT * FROM membres_groupe WHERE etudiant_id = ?', self.eleve.id)), 2,
        )

    def test_rendu_partage_par_le_groupe(self):
        self.connecter(self.eleve)
        self.post(self.url, {'fichier': self.fichier()})
        self.assertEqual(self.sql(self.ciel, 'SELECT * FROM soumissions'), [])

        groupe_id = self.groupe(self.ciel, self.devoir_id, 'A', self.eleve, self.binome)
        self.connecter(self.eleve)
        self.post(self.url, {'fichier': self.fichier('rapport.pdf', b'%PDF v1')})
        soumission = self.un(self.ciel, 'SELECT * FROM soumissions')
        self.assertEqual(soumission['groupe_id'], groupe_id)
        self.assertIsNone(soumission['etudiant_id'])
        fichier = self.un(self.ciel, 'SELECT * FROM fichiers_rendus')
        self.assertEqual(fichier['chemin'], f'{self.devoir_id}/g{groupe_id}.pdf')

        self.connecter(self.binome)
        self.assertEqual(self.get(f'{self.url}fichiers/{fichier["id"]}/').data, b'%PDF v1')
        self.post(self.url, {'fichier': self.fichier('rapport.pdf', b'%PDF v2')})
        soumissions = self.sql(self.ciel, 'SELECT * FROM soumissions')
        self.assertEqual(len(soumissions), 1)
        self.assertEqual(soumissions[0]['deposee_par'], self.binome.id)
        self.assertContient(self.get(self.url), f'par {self.binome.nom_complet}')

        self.connecter(self.tiers)
        fichier = self.un(self.ciel, 'SELECT * FROM fichiers_rendus')
        self.assertEqual(self.get(f'{self.url}fichiers/{fichier["id"]}/').status_code, 404)

    def test_quitter(self):
        self._action(self.eleve, action='creer', nom='A')
        self._action(self.eleve, action='quitter')
        self.assertEqual(self.sql(self.ciel, 'SELECT * FROM groupes'), [])

        groupe_id = self.groupe(self.ciel, self.devoir_id, 'B', self.eleve)
        self.connecter(self.eleve)
        self.post(self.url, {'fichier': self.fichier('rapport.pdf', b'%PDF')})
        self._action(self.eleve, action='quitter')
        self.assertIsNotNone(self.un(self.ciel, 'SELECT * FROM groupes WHERE id = ?', groupe_id))
        self.assertEqual(self.sql(self.ciel, 'SELECT * FROM membres_groupe'), [])

    def test_date_depassee(self):
        self.sql(self.ciel, 'UPDATE devoirs SET date_limite = ?', iso(maintenant() - timedelta(hours=1)))
        reponse = self._action(self.eleve, action='creer', nom='A')
        self.assertContient(reponse, 'date limite')
        self.assertEqual(self.sql(self.ciel, 'SELECT * FROM groupes'), [])

    def test_devoir_individuel(self):
        devoir_id = self.devoir(self.ciel)
        self.connecter(self.eleve)
        reponse = self.post(f'{self.url_devoir(devoir_id)}groupe/', {'action': 'creer', 'nom': 'A'})
        self.assertEqual(reponse.status_code, 404)

    def test_suivi_et_archive(self):
        groupe_id = self.groupe(self.ciel, self.devoir_id, 'Les Ours', self.eleve, self.binome)
        self.connecter(self.eleve)
        self.post(self.url, {'fichier': self.fichier('rapport.pdf', b'%PDF')})

        self.connecter(self.admin)
        reponse = self.get(f'/admin/devoirs/{self.ciel.id}/{self.devoir_id}/')
        self.assertContient(reponse, 'Les Ours')
        self.assertContient(reponse, 'Sans groupe (1)')
        self.assertContient(reponse, 'Rendus (1 / 1 groupes)')
        reponse = self.get(f'/admin/devoirs/{self.ciel.id}/{self.devoir_id}/archive/')
        archive = zipfile.ZipFile(io.BytesIO(reponse.data))
        self.assertEqual(archive.namelist(), [f'groupe-{groupe_id}-les-ours_rapport.pdf'])


class ConfigurationDevoirTests(Base):
    def setUp(self):
        super().setUp()
        self.connecter(self.admin)

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

    def _devoir(self, titre):
        return self.un(self.ciel, 'SELECT * FROM devoirs WHERE titre = ?', titre)

    def test_creation(self):
        self.post('/admin/devoirs/', self._donnees(classe=self.ciel.id))
        devoir = self._devoir('Projet')
        self.assertEqual((devoir['type_rendu'], devoir['mode'], devoir['taille_groupe_max']), ('fichiers', 'groupe', 3))

        reponse = self.post('/admin/devoirs/', self._donnees(classe=self.ciel.id, titre='Sans taille', taille_groupe_max=''))
        self.assertContient(reponse, 'Indiquez la taille')
        self.assertIsNone(self._devoir('Sans taille'))

        self.post('/admin/devoirs/', self._donnees(classe=self.ciel.id, titre='Seul', mode='individuel'))
        self.assertIsNone(self._devoir('Seul')['taille_groupe_max'])

        reponse = self.post('/admin/devoirs/', self._donnees(classe=999, titre='Sans classe'))
        self.assertContient(reponse, 'Sélectionnez une classe')
        self.assertContient(self.get('/admin/devoirs/'), 'Projet')

    def test_modifiable_sans_rendu(self):
        devoir_id = self.devoir(self.ciel)
        self.post(f'/admin/devoirs/{self.ciel.id}/{devoir_id}/', self._donnees(type_rendu='github'))
        devoir = self.un(self.ciel, 'SELECT * FROM devoirs WHERE id = ?', devoir_id)
        self.assertEqual((devoir['type_rendu'], devoir['mode']), ('github', 'groupe'))

    def test_verrouille_avec_rendu(self):
        devoir_id = self.devoir(self.ciel, type_rendu='fichier')
        self.connecter(self.eleve)
        self.post(self.url_devoir(devoir_id), {'fichier': self.fichier()})

        self.connecter(self.admin)
        url = f'/admin/devoirs/{self.ciel.id}/{devoir_id}/'
        self.assertContient(self.get(url), 'Verrouillé')
        self.post(url, self._donnees(titre='Nouveau titre'))
        devoir = self.un(self.ciel, 'SELECT * FROM devoirs WHERE id = ?', devoir_id)
        self.assertEqual(devoir['titre'], 'Nouveau titre')
        self.assertEqual((devoir['type_rendu'], devoir['mode']), ('fichier', 'individuel'))

    def test_taille_pas_sous_un_groupe_existant(self):
        devoir_id = self.devoir(self.ciel, mode='groupe', taille_groupe_max=3)
        self.groupe(self.ciel, devoir_id, 'A', self.eleve, self.binome, self.tiers)
        reponse = self.post(f'/admin/devoirs/{self.ciel.id}/{devoir_id}/', self._donnees(
            type_rendu='fichier', taille_groupe_max=2,
        ))
        self.assertContient(reponse, 'compte déjà 3 membres')
        devoir = self.un(self.ciel, 'SELECT * FROM devoirs WHERE id = ?', devoir_id)
        self.assertEqual(devoir['taille_groupe_max'], 3)
