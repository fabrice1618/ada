import io
import json
import zipfile

from ada import db
from ada.archivage import calculer_empreinte, donnees_classe
from tests.base import BaseTests


class ArchivageTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.ciel = self.classe('CIEL')
        self.eisi = self.classe('EISI')
        self.admin = self._compte('admin@example.com', 'admin')
        self.prof = self._compte('prof@example.com', 'enseignant', self.ciel)
        self.eleve = self._compte('eleve@example.com', 'etudiant', self.ciel)
        self.binome = self._compte('binome@example.com', 'etudiant', self.ciel)
        self.double = self._compte('double@example.com', 'etudiant', self.ciel, self.eisi)
        self.ailleurs = self._compte('ailleurs@example.com', 'etudiant', self.eisi)

        self.devoir_id = self.devoir(self.ciel, 'TP 1', self.prof)
        self.projet_id = self.devoir(self.ciel, 'Projet', self.prof, type_rendu='fichiers', mode='groupe',
                                     taille_groupe_max=3)
        self.devoir_eisi = self.devoir(self.eisi, 'TP EISI', self.prof)

        self._deposer(self.eleve, self.ciel, self.devoir_id, 'compte-rendu.pdf', b'%PDF eleve')
        self.groupe_id = self.groupe(self.ciel, self.projet_id, 'Les Ours', self.eleve, self.binome)
        self._deposer(self.binome, self.ciel, self.projet_id, 'main.py', b'print(1)')
        self._deposer(self.binome, self.ciel, self.projet_id, 'notes.txt', b'notes')
        self._deposer(self.ailleurs, self.eisi, self.devoir_eisi, 'eisi.pdf', b'%PDF eisi')

    def _compte(self, email, role, *classes):
        return self.compte(email, role, *classes, nom=email.split('@')[0].title())

    def _deposer(self, etudiant, classe, devoir_id, nom, contenu):
        self.connecter(etudiant)
        self.post(f'/devoirs/{classe.id}/{devoir_id}/', {'fichier': self.fichier(nom, contenu)})

    def _empreinte(self):
        with self.contexte():
            return calculer_empreinte(donnees_classe(self.recharger_classe(self.ciel)))

    def _exporter(self):
        self.connecter(self.admin)
        reponse = self.get(f'/admin/classes/{self.ciel.id}/archive/')
        self.assertEqual(reponse.status_code, 200)
        return reponse.data, reponse

    def _existe(self, classe):
        return self.un(None, 'SELECT * FROM classes WHERE id = ?', classe.id) is not None

    def test_contenu_de_l_archive(self):
        contenu, reponse = self._exporter()
        self.assertIn('ada-ciel-2026-', reponse.headers['Content-Disposition'])
        archive = zipfile.ZipFile(io.BytesIO(contenu))
        noms = set(archive.namelist())
        for attendu in ('classe.json', 'LISEZMOI.txt', 'etudiants.csv', 'devoirs.csv', 'groupes.csv', 'rendus.csv'):
            self.assertIn(attendu, noms)
        self.assertIn(f'fichiers/{self.devoir_id}-tp-1/eleve-{self.eleve.id}/compte-rendu.pdf', noms)
        dossier = f'fichiers/{self.projet_id}-projet/groupe-{self.groupe_id}-les-ours'
        self.assertEqual(archive.read(f'{dossier}/main.py'), b'print(1)')
        self.assertIn(f'{dossier}/notes.txt', noms)
        self.assertFalse(any('eisi' in nom for nom in noms))

        manifeste = json.loads(archive.read('classe.json'))
        self.assertEqual(manifeste['empreinte'], self._empreinte())
        membres = {m['email']: m for m in manifeste['donnees']['membres']}
        self.assertTrue(membres['eleve@example.com']['compte_supprime'])
        self.assertFalse(membres['double@example.com']['compte_supprime'])
        self.assertEqual(membres['double@example.com']['autres_classes'], ['EISI (2026)'])
        self.assertFalse(membres['prof@example.com']['compte_supprime'])
        brut = archive.read('classe.json').decode() + archive.read('etudiants.csv').decode('utf-8-sig')
        self.assertNotIn('pbkdf2', brut)
        self.assertNotIn('mot_de_passe', brut)
        self.assertIn('Les Ours;Eleve', archive.read('groupes.csv').decode('utf-8-sig'))

    def test_page_classe(self):
        self.connecter(self.admin)
        reponse = self.get(f'/admin/classes/{self.ciel.id}/')
        self.assertContient(reponse, 'Exporter l')
        self.assertContient(reponse, self._empreinte())

    def test_suppression(self):
        empreinte = self._empreinte()
        self.connecter(self.admin)
        reponse = self.post(f'/admin/classes/{self.ciel.id}/supprimer/', {
            'confirmation': 'CIEL', 'archive_verifiee': 'on', 'empreinte': empreinte,
        })
        self.assertRedirige(reponse, '/admin/')

        self.assertFalse(self._existe(self.ciel))
        self.assertFalse((self.racine / 'classes' / str(self.ciel.id)).exists())
        emails = {u['email'] for u in self.sql(None, 'SELECT email FROM utilisateurs')}
        self.assertNotIn('eleve@example.com', emails)
        self.assertNotIn('binome@example.com', emails)
        self.assertIn('prof@example.com', emails)
        self.assertEqual(
            [i['classe_id'] for i in self.sql(None, 'SELECT classe_id FROM inscriptions WHERE utilisateur_id = ?',
                                              self.double.id)],
            [self.eisi.id],
        )
        self.assertEqual(self.sql(None, 'SELECT * FROM sessions WHERE utilisateur_id = ?', self.eleve.id), [])

        reste = self.un(self.eisi, 'SELECT * FROM fichiers_rendus')
        self.assertTrue((self.fichiers_de(self.eisi) / reste['chemin']).is_file())

    def test_suppression_refusee(self):
        empreinte = self._empreinte()
        url = f'/admin/classes/{self.ciel.id}/supprimer/'
        self.connecter(self.admin)
        self.post(url, {'confirmation': 'ciel', 'archive_verifiee': 'on', 'empreinte': empreinte})
        self.post(url, {'confirmation': 'CIEL', 'empreinte': empreinte})

        self._deposer(self.eleve, self.ciel, self.devoir_id, 'v2.pdf', b'%PDF v2')
        self.connecter(self.admin)
        reponse = self.post(url, {'confirmation': 'CIEL', 'archive_verifiee': 'on', 'empreinte': empreinte},
                            follow_redirects=True)
        self.assertContient(reponse, 'ont changé')

        self.connecter(self.prof)
        self.post(url, {'confirmation': 'CIEL', 'archive_verifiee': 'on', 'empreinte': self._empreinte()})
        self.assertEqual(self.get(f'/admin/classes/{self.ciel.id}/archive/').status_code, 302)
        self.assertTrue(self._existe(self.ciel))

    def _commande(self, *args, entree=None):
        return self.app.test_cli_runner().invoke(args=['archiver-classe', *map(str, args)], input=entree)

    def test_commande(self):
        sortie = self.racine / 'export.zip'
        resultat = self._commande(self.ciel.id, '--sortie', sortie)
        self.assertEqual(resultat.exit_code, 0, resultat.output)
        self.assertTrue(zipfile.is_zipfile(sortie))

        self._deposer(self.eleve, self.ciel, self.devoir_id, 'v2.pdf', b'%PDF v2')
        resultat = self._commande(self.ciel.id, '--supprimer', sortie)
        self.assertNotEqual(resultat.exit_code, 0)
        self.assertIn('ont changé', resultat.output)
        resultat = self._commande(self.eisi.id, '--supprimer', sortie)
        self.assertIn('pas celle de la classe', resultat.output)

        # Par défaut, l'archive va dans /data/exports.
        resultat = self._commande(self.ciel.id)
        self.assertEqual(resultat.exit_code, 0, resultat.output)
        (export,) = (self.racine / 'exports').glob('ada-ciel-2026-*.zip')
        resultat = self._commande(self.ciel.id, '--supprimer', '-', entree=export.read_bytes())
        self.assertEqual(resultat.exit_code, 0, resultat.output)
        self.assertIn('supprimée', resultat.output)
        self.assertFalse(self._existe(self.ciel))

    def test_archive_corrompue(self):
        abime = self.racine / 'abime.zip'
        abime.write_bytes(b'pas un zip')
        resultat = self._commande(self.ciel.id, '--supprimer', abime)
        self.assertIn('pas une archive zip', resultat.output)
        self.assertTrue(self._existe(self.ciel))

    def test_identifiants_jamais_reutilises(self):
        # Les bases de classe gardent des identifiants d'utilisateurs : pas de réattribution,
        # même pour le dernier identifiant supprimé.
        dernier = self.compte('dernier@example.com', 'etudiant')
        temporaire = self.classe('TEMP')
        with self.contexte():
            cx = db.commun()
            cx.execute('DELETE FROM utilisateurs WHERE id = ?', (dernier.id,))
            cx.execute('DELETE FROM classes WHERE id = ?', (temporaire.id,))
            db.supprimer_dossier_classe(temporaire.id)
        self.assertGreater(self.compte('nouveau@example.com', 'etudiant').id, dernier.id)
        self.assertGreater(self.classe('NOUVELLE').id, temporaire.id)
