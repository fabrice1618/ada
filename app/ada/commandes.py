"""Commandes : docker compose exec ada flask <commande> (FLASK_APP=ada dans l'image)."""
import logging
import os
import shutil
import sys
import tempfile

import click
from flask.cli import with_appcontext

from ada import archivage, db, sauvegardes
from ada.comptes import creer_utilisateur
from ada.modeles import get_classe, toutes_les_classes

journal = logging.getLogger('ada')


def enregistrer(app):
    for commande in (migrer, creer_admin, archiver_classe, sauvegarder, lister_sauvegardes, restaurer,
                     importer_mysql):
        app.cli.add_command(commande)


@click.command('migrer')
@with_appcontext
def migrer():
    """Crée le volume au premier lancement, sinon met les bases au dernier schéma (sauvegarde avant)."""
    sauvegarde = db.migrer()
    if sauvegarde:
        journal.info("Schéma mis à jour après sauvegarde %s", sauvegarde.name)
    else:
        journal.info("Schéma à jour (%s)", db.racine())


@click.command('creer-admin')
@with_appcontext
@click.option('--email', prompt=True)
@click.option('--nom', prompt='Nom complet')
@click.password_option('--mot-de-passe', prompt='Mot de passe')
def creer_admin(email, nom, mot_de_passe):
    """Crée un compte administrateur."""
    cx = db.commun()
    with db.transaction(cx):
        if cx.execute('SELECT 1 FROM utilisateurs WHERE email = ?', (email.strip(),)).fetchone():
            raise click.ClickException(f"{email} existe déjà.")
        utilisateur_id = creer_utilisateur(cx, email, nom, 'admin', mot_de_passe)
    journal.info("Administrateur créé id=%s par=commande", utilisateur_id)
    click.echo(f"Administrateur {email} créé.", err=True)


@click.command('archiver-classe')
@with_appcontext
@click.argument('classe_id', type=int, required=False)
@click.option('--sortie', help="Fichier de l'archive (défaut : /data/exports/<nom> ; - : sortie standard).")
@click.option('--supprimer', 'archive', metavar='ARCHIVE',
              help="Vérifie ARCHIVE (- : entrée standard) contre les données, puis supprime la classe.")
def archiver_classe(classe_id, sortie, archive):
    """Archive une classe puis la supprime. Sans argument : liste les classes."""
    if classe_id is None:
        effectifs = dict(db.commun().execute(
            'SELECT classe_id, count(*) FROM inscriptions GROUP BY classe_id'
        ).fetchall())
        for classe in toutes_les_classes():
            click.echo(f"{classe.id:>5}  {classe}  {effectifs.get(classe.id, 0)} membres", err=True)
        return
    classe = get_classe(classe_id)
    if classe is None:
        raise click.ClickException(f"Classe {classe_id} introuvable.")
    if archive:
        _supprimer(classe, archive)
    else:
        _exporter(classe, sortie)


def _exporter(classe, sortie):
    if sortie == '-' and sys.stdout.isatty():
        raise click.ClickException("Redirigez la sortie vers un fichier : archiver-classe ID --sortie - > archive.zip")
    with tempfile.TemporaryFile() as temporaire:
        resultat = archivage.ecrire_archive(classe, temporaire)
        temporaire.seek(0)
        archivage.verifier_archive(classe, temporaire)
        temporaire.seek(0)
        if sortie == '-':
            shutil.copyfileobj(temporaire, sys.stdout.buffer)
            sys.stdout.buffer.flush()
        else:
            if not sortie:
                db.dossier_exports().mkdir(parents=True, exist_ok=True)
                sortie = db.dossier_exports() / archivage.nom_archive(classe, resultat['empreinte'])
            with open(sortie, 'wb') as fichier:
                shutil.copyfileobj(temporaire, fichier)
    journal.info(
        "Classe exportée id=%s empreinte=%s fichiers=%s manquants=%s par=commande",
        classe.id, resultat['empreinte'][:8], resultat['fichiers'], resultat['manquants'],
    )
    click.echo(
        f"Archive de {classe} : {resultat['devoirs']} devoirs, {resultat['rendus']} rendus, "
        f"{resultat['fichiers']} fichiers ({resultat['manquants']} manquants). "
        f"Empreinte {resultat['empreinte'][:8]}"
        + (f" ; écrite dans {sortie}" if sortie != '-' else
           f" ; nom suggéré : {archivage.nom_archive(classe, resultat['empreinte'])}"),
        err=True,
    )


def _supprimer(classe, chemin):
    with tempfile.TemporaryFile() as temporaire:
        if chemin == '-':
            shutil.copyfileobj(sys.stdin.buffer, temporaire)
        else:
            try:
                with open(chemin, 'rb') as fichier:
                    shutil.copyfileobj(fichier, temporaire)
            except OSError as exc:
                raise click.ClickException(f"Archive illisible : {exc}")
        temporaire.seek(0)
        try:
            manifeste = archivage.verifier_archive(classe, temporaire)
        except archivage.ArchiveInvalide as exc:
            raise click.ClickException(f"Suppression refusée : {exc}")
    nom = str(classe)
    resultat = archivage.supprimer_classe(classe)
    journal.info(
        "Classe supprimée id=%s nom=%s empreinte=%s devoirs=%s fichiers=%s comptes_supprimes=%s par=commande",
        classe.id, nom, manifeste['empreinte'][:8],
        resultat['devoirs'], resultat['fichiers'], resultat['etudiants_supprimes'],
    )
    click.echo(
        f"Classe {nom} supprimée (archive {manifeste['empreinte'][:8]} vérifiée) : "
        f"{resultat['devoirs']} devoirs, {resultat['fichiers']} fichiers, "
        f"{resultat['etudiants_supprimes']} comptes supprimés, "
        f"{resultat['etudiants_conserves']} conservés.",
        err=True,
    )


@click.command('sauvegarder')
@with_appcontext
@click.option('--motif', default='manuelle', show_default=True)
def sauvegarder(motif):
    """Sauvegarde complète (bases + fichiers + cours) dans /data/sauvegardes/."""
    dossier = sauvegardes.creer(motif)
    journal.info("Sauvegarde créée %s", dossier.name)
    click.echo(dossier.name)


@click.command('sauvegardes')
@with_appcontext
def lister_sauvegardes():
    """Liste les sauvegardes, de la plus récente à la plus ancienne."""
    for nom, manifeste in sauvegardes.lister():
        classes = manifeste.get('classes', {})
        fichiers = sum(c.get('fichiers', 0) for c in classes.values())
        click.echo(f"{nom}  {len(classes)} classes, {fichiers} fichiers")


@click.command('restaurer')
@with_appcontext
@click.argument('nom')
@click.option('--oui', is_flag=True, help="Ne pas demander confirmation.")
def restaurer(nom, oui):
    """Remplace les données par la sauvegarde NOM (service ada arrêté)."""
    if not oui:
        click.confirm(f"Remplacer toutes les données par {nom} ?", abort=True)
    try:
        secours = sauvegardes.restaurer(nom)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc))
    db.migrer()
    journal.info("Restauration de %s ; état précédent dans %s", nom, secours.name)
    click.echo(f"Données restaurées depuis {nom} ; état précédent sauvegardé dans {secours.name}.", err=True)


@click.command('importer-mysql')
@with_appcontext
@click.option('--uploads', default='/ancien-uploads', show_default=True,
              help="Ancien volume uploads, monté en lecture seule.")
@click.option('--avant-migration', default='/avant-migration', show_default=True,
              help="Dossier produit par migration/1-sauvegarder-mysql.sh.")
def importer_mysql(uploads, avant_migration):
    """Reprend la base MySQL et les fichiers de la version Django (variables MYSQL_*)."""
    from ada.import_mysql import MigrationRefusee, importer

    parametres = {
        'host': os.environ.get('MYSQL_HOST', 'ada-mysql'),
        'port': int(os.environ.get('MYSQL_PORT', '3306')),
        'user': os.environ.get('MYSQL_USER', ''),
        'password': os.environ.get('MYSQL_PASSWORD', ''),
        'database': os.environ.get('MYSQL_DATABASE', ''),
    }
    try:
        resultat = importer(parametres, uploads, avant_migration, journal=journal.info)
    except MigrationRefusee as exc:
        raise click.ClickException(f"Migration annulée : {exc}")
    for classe_id, absents in resultat['manquants'].items():
        journal.warning("Classe %s : fichiers absents de l'ancien volume : %s", classe_id, ', '.join(absents))
    journal.info("Migration terminée ; sauvegarde de l'ancienne version : %s", resultat['sauvegarde'])
