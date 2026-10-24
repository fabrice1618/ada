import json
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from ada import db, sauvegardes
from tests.base import BaseTests


class SauvegardesTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.ciel = self.classe('CIEL')
        self.eleve = self.compte('eleve@example.com', 'etudiant', self.ciel)
        self.devoir_id = self.devoir(self.ciel, 'TP 1')
        self.url = f'/devoirs/{self.ciel.id}/{self.devoir_id}/'
        (self.racine / 'cours' / 'math').mkdir(parents=True)
        (self.racine / 'cours' / 'math' / 'index.html').write_text('v1')
        self.connecter(self.eleve)
        self.post(self.url, {'fichier': self.fichier('rapport.pdf', b'%PDF v1')})

    def _rendu(self):
        fichier = self.un(self.ciel, 'SELECT * FROM fichiers_rendus')
        return fichier, self.fichiers_de(self.ciel) / fichier['chemin']

    def _creer(self, motif='essai'):
        with self.contexte():
            return sauvegardes.creer(motif)

    def test_contenu(self):
        dossier = self._creer()
        self.assertTrue(dossier.name.endswith('-essai'))
        manifeste = json.loads((dossier / 'MANIFESTE.json').read_text())
        self.assertEqual(manifeste['classes'][str(self.ciel.id)]['fichiers'], 1)
        self.assertEqual(manifeste['commun']['schema'], 1)
        fichier, original = self._rendu()
        copie = dossier / 'classes' / str(self.ciel.id) / 'fichiers' / fichier['chemin']
        self.assertEqual(copie.stat().st_ino, original.stat().st_ino)
        self.assertEqual((dossier / 'cours' / 'math' / 'index.html').read_text(), 'v1')
        self.assertFalse(list(dossier.rglob('*-wal')))

        # La copie est une base complète et lisible.
        import sqlite3
        cx = sqlite3.connect(dossier / 'classes' / str(self.ciel.id) / 'classe.db')
        self.assertEqual(cx.execute('SELECT count(*) FROM soumissions').fetchone()[0], 1)
        cx.close()

    def test_un_nouveau_depot_ne_touche_pas_la_sauvegarde(self):
        dossier = self._creer()
        fichier, _ = self._rendu()
        self.post(self.url, {'fichier': self.fichier('rapport.pdf', b'%PDF v2')})
        copie = dossier / 'classes' / str(self.ciel.id) / 'fichiers' / fichier['chemin']
        self.assertEqual(copie.read_bytes(), b'%PDF v1')
        self.assertEqual(self._rendu()[1].read_bytes(), b'%PDF v2')

    def test_restaurer(self):
        dossier = self._creer()
        self.post(self.url, {'fichier': self.fichier('rapport.pdf', b'%PDF v2')})
        autre = self.classe('EISI')
        (self.racine / 'cours' / 'math' / 'index.html').write_text('v2')

        resultat = self.app.test_cli_runner().invoke(args=['restaurer', dossier.name, '--oui'])
        self.assertEqual(resultat.exit_code, 0, resultat.output)
        self.assertEqual(self._rendu()[1].read_bytes(), b'%PDF v1')
        self.assertIsNone(self.un(None, 'SELECT * FROM classes WHERE id = ?', autre.id))
        self.assertFalse((self.racine / 'classes' / str(autre.id)).exists())
        self.assertEqual((self.racine / 'cours' / 'math' / 'index.html').read_text(), 'v1')
        # L'état remplacé est gardé.
        with self.contexte():
            noms = [nom for nom, _ in sauvegardes.lister()]
        self.assertTrue(any(nom.endswith('-avant-restauration') for nom in noms))
        # L'application fonctionne sur les données restaurées.
        self.connecter(self.eleve)
        self.assertEqual(self.get(f'{self.url}fichiers/{self._rendu()[0]["id"]}/').data, b'%PDF v1')

    def test_restaurer_inconnue(self):
        resultat = self.app.test_cli_runner().invoke(args=['restaurer', '../ailleurs', '--oui'])
        self.assertNotEqual(resultat.exit_code, 0)
        self.assertIn('introuvable', resultat.output)

    def test_commandes(self):
        runner = self.app.test_cli_runner()
        resultat = runner.invoke(args=['sauvegarder', '--motif', 'fin de trimestre'])
        self.assertEqual(resultat.exit_code, 0, resultat.output)
        self.assertIn('fin-de-trimestre', resultat.output)
        self.assertIn('1 classes, 1 fichiers', runner.invoke(args=['sauvegardes']).output)


class MigrationSchemaTests(BaseTests):
    def setUp(self):
        super().setUp()
        self.ciel = self.classe('CIEL')
        self.schemas = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.schemas)
        shutil.copytree(db.SCHEMAS, self.schemas, dirs_exist_ok=True)
        (self.schemas / 'classe' / '002_essai.sql').write_text(
            "ALTER TABLE devoirs ADD COLUMN bareme INTEGER NOT NULL DEFAULT 20;"
        )
        patch = mock.patch.object(db, 'SCHEMAS', self.schemas)
        patch.start()
        self.addCleanup(patch.stop)

    def test_sauvegarde_puis_migration(self):
        with self.contexte():
            with self.assertRaises(db.VersionIncorrecte):
                db.classe(self.ciel.id)
            sauvegarde = db.migrer()
            self.assertTrue(sauvegarde.name.endswith('-avant-migration'))
            cx = db.classe(self.ciel.id)
            self.assertEqual(db.version(cx), 2)
            self.assertIn('bareme', [c[1] for c in cx.execute('PRAGMA table_info(devoirs)')])
            copie = sauvegarde / 'classes' / str(self.ciel.id) / 'classe.db'
            import sqlite3
            self.assertEqual(sqlite3.connect(copie).execute('PRAGMA user_version').fetchone()[0], 1)
            self.assertIsNone(db.migrer())

    def test_nouvelle_classe_au_dernier_schema(self):
        with self.contexte():
            db.migrer()
        autre = self.classe('EISI')
        with self.contexte():
            self.assertEqual(db.version(db.classe(autre.id)), 2)

    def test_echec_annule(self):
        (self.schemas / 'classe' / '002_essai.sql').write_text(
            "ALTER TABLE devoirs ADD COLUMN bareme INTEGER; INSERT INTO table_absente VALUES (1);"
        )
        with self.contexte():
            with self.assertRaises(Exception):
                db.migrer()
            import sqlite3
            cx = sqlite3.connect(db.chemin_classe(self.ciel.id))
            self.assertEqual(cx.execute('PRAGMA user_version').fetchone()[0], 1)
            self.assertNotIn('bareme', [c[1] for c in cx.execute('PRAGMA table_info(devoirs)')])
            cx.close()

    def test_base_plus_recente_que_le_code(self):
        with self.contexte():
            db.migrer()
        (self.schemas / 'classe' / '002_essai.sql').unlink()
        with self.contexte():
            with self.assertRaises(db.VersionIncorrecte):
                db.migrer()
