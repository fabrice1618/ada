import logging
import shutil
import sys
import tempfile

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from core import archivage
from core.models import Classe

logger = logging.getLogger('auth')


class Command(BaseCommand):
    help = (
        "Archive une classe puis la supprime. Sans argument : liste les classes. "
        "Exporter : archiver_classe ID > archive.zip ; "
        "supprimer : archiver_classe ID --supprimer archive.zip (ou - pour stdin)."
    )

    def add_arguments(self, parser):
        parser.add_argument('classe_id', nargs='?', type=int)
        parser.add_argument(
            '--sortie', default='-',
            help="Fichier de l'archive exportée (défaut : - , la sortie standard).",
        )
        parser.add_argument(
            '--supprimer', metavar='ARCHIVE',
            help="Vérifie ARCHIVE (- : entrée standard) contre la base, puis supprime la classe.",
        )

    def handle(self, *args, classe_id=None, sortie='-', supprimer=None, **options):
        if classe_id is None:
            self._lister()
            return
        try:
            classe = Classe.objects.get(id=classe_id)
        except Classe.DoesNotExist:
            raise CommandError(f"Classe {classe_id} introuvable.")
        if supprimer:
            self._supprimer(classe, supprimer)
        else:
            self._exporter(classe, sortie)

    def _lister(self):
        classes = Classe.objects.annotate(nb=Count('utilisateurs')).order_by('-annee', 'nom')
        for classe in classes:
            self.stderr.write(f"{classe.id:>5}  {classe}  {classe.nb} membres")

    def _exporter(self, classe, sortie):
        if sortie == '-' and sys.stdout.isatty():
            raise CommandError("Redirigez la sortie vers un fichier : archiver_classe ID > archive.zip")
        with tempfile.TemporaryFile() as temporaire:
            resultat = archivage.ecrire_archive(classe, temporaire)
            temporaire.seek(0)
            archivage.verifier_archive(classe, temporaire)
            temporaire.seek(0)
            if sortie == '-':
                shutil.copyfileobj(temporaire, sys.stdout.buffer)
                sys.stdout.buffer.flush()
            else:
                with open(sortie, 'wb') as fichier:
                    shutil.copyfileobj(temporaire, fichier)
        self.stderr.write(
            f"Archive de {classe} : {resultat['devoirs']} devoirs, {resultat['rendus']} rendus, "
            f"{resultat['fichiers']} fichiers ({resultat['manquants']} manquants). "
            f"Empreinte {resultat['empreinte'][:8]} ; nom suggéré : "
            f"{archivage.nom_archive(classe, resultat['empreinte'])}"
        )

    def _supprimer(self, classe, chemin):
        with tempfile.TemporaryFile() as temporaire:
            if chemin == '-':
                shutil.copyfileobj(sys.stdin.buffer, temporaire)
            else:
                try:
                    with open(chemin, 'rb') as fichier:
                        shutil.copyfileobj(fichier, temporaire)
                except OSError as exc:
                    raise CommandError(f"Archive illisible : {exc}")
            temporaire.seek(0)
            try:
                manifeste = archivage.verifier_archive(classe, temporaire)
            except archivage.ArchiveInvalide as exc:
                raise CommandError(f"Suppression refusée : {exc}")
        nom = str(classe)
        resultat = archivage.supprimer_classe(classe)
        logger.info(
            "Classe supprimée id=%s nom=%s empreinte=%s devoirs=%s fichiers=%s comptes_supprimes=%s par=commande",
            manifeste['donnees']['classe']['id'], nom, manifeste['empreinte'][:8],
            resultat['devoirs'], resultat['fichiers'], resultat['etudiants_supprimes'],
        )
        self.stderr.write(
            f"Classe {nom} supprimée (archive {manifeste['empreinte'][:8]} vérifiée) : "
            f"{resultat['devoirs']} devoirs, {resultat['fichiers']} fichiers, "
            f"{resultat['etudiants_supprimes']} comptes supprimés, "
            f"{resultat['etudiants_conserves']} conservés."
        )
