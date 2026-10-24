"""Bases SQLite et arborescence du volume de données.

/data/
├── ada.db                     base commune : comptes, classes, inscriptions, sessions
├── classes/<id>/classe.db     une base par classe : créneaux, devoirs, groupes, rendus, quiz
├── classes/<id>/fichiers/     fichiers rendus de la classe : <devoir>/<étudiant>.ext ...
├── cours/                     pages de cours, servies sous /cours/
├── sauvegardes/<date>-<motif>/
└── exports/                   archives zip des classes

Schéma : scripts schema/<commun|classe>/NNN_*.sql, numéro appliqué dans PRAGMA user_version.
"""
import shutil
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g

SCHEMAS = Path(__file__).parent / 'schema'


class BaseAbsente(Exception):
    pass


class VersionIncorrecte(Exception):
    pass


def racine():
    return Path(current_app.config['DATA_ROOT'])


def chemin_commun():
    return racine() / 'ada.db'


def dossier_classes():
    return racine() / 'classes'


def dossier_classe(classe_id):
    return dossier_classes() / str(int(classe_id))


def chemin_classe(classe_id):
    return dossier_classe(classe_id) / 'classe.db'


def dossier_fichiers(classe_id):
    return dossier_classe(classe_id) / 'fichiers'


def dossier_cours():
    return racine() / 'cours'


def dossier_sauvegardes():
    return racine() / 'sauvegardes'


def dossier_exports():
    return racine() / 'exports'


def ids_bases_classes():
    """Classes qui ont un dossier sur le disque, avec ou sans ligne dans ada.db."""
    if not dossier_classes().is_dir():
        return []
    return sorted(
        int(d.name) for d in dossier_classes().iterdir()
        if d.name.isdigit() and (d / 'classe.db').is_file()
    )


# ── Connexions ──────────────────────────────────────────────────

def connecter(chemin):
    # Autocommit : les écritures passent par transaction().
    cx = sqlite3.connect(chemin, timeout=15, isolation_level=None)
    cx.row_factory = sqlite3.Row
    cx.execute('PRAGMA foreign_keys = ON')
    cx.execute('PRAGMA journal_mode = WAL')
    return cx


@contextmanager
def transaction(cx):
    cx.execute('BEGIN IMMEDIATE')
    try:
        yield cx
    except BaseException:
        cx.execute('ROLLBACK')
        raise
    cx.execute('COMMIT')


def _verifier_version(cx, type_base, chemin):
    actuelle, attendue = version(cx), version_cible(type_base)
    if actuelle != attendue:
        cx.close()
        raise VersionIncorrecte(
            f"{chemin} : schéma {actuelle}, attendu {attendue} — lancer « flask migrer »."
        )


def commun():
    """Connexion à ada.db, gardée le temps de la requête (ou de la commande)."""
    if 'base_commune' not in g:
        chemin = chemin_commun()
        if not chemin.is_file():
            raise BaseAbsente(f"{chemin} absent — lancer « flask migrer ».")
        cx = connecter(chemin)
        _verifier_version(cx, 'commun', chemin)
        g.base_commune = cx
    return g.base_commune


def classe(classe_id):
    bases = g.setdefault('bases_classes', {})
    classe_id = int(classe_id)
    if classe_id not in bases:
        chemin = chemin_classe(classe_id)
        if not chemin.is_file():
            raise BaseAbsente(f"{chemin} absent.")
        cx = connecter(chemin)
        _verifier_version(cx, 'classe', chemin)
        bases[classe_id] = cx
    return bases[classe_id]


def fermer_classe(classe_id):
    cx = g.get('bases_classes', {}).pop(int(classe_id), None)
    if cx is not None:
        cx.close()


def fermer(_exc=None):
    cx = g.pop('base_commune', None)
    if cx is not None:
        cx.close()
    for cx in g.pop('bases_classes', {}).values():
        cx.close()


# ── Schéma ──────────────────────────────────────────────────────

def _scripts(type_base):
    return sorted(
        (int(f.name[:3]), f) for f in (SCHEMAS / type_base).glob('[0-9][0-9][0-9]_*.sql')
    )


def version_cible(type_base):
    return _scripts(type_base)[-1][0]


def version(cx):
    return cx.execute('PRAGMA user_version').fetchone()[0]


def appliquer_schema(cx, type_base):
    for numero, script in _scripts(type_base):
        if numero <= version(cx):
            continue
        try:
            cx.executescript(
                f"BEGIN IMMEDIATE;\n{script.read_text(encoding='utf-8')}\n"
                f"PRAGMA user_version = {numero};\nCOMMIT;"
            )
        except BaseException:
            if cx.in_transaction:
                cx.execute('ROLLBACK')
            raise


def creer_base_classe(classe_id):
    """Dossier et base d'une nouvelle classe, au dernier schéma."""
    dossier = dossier_classe(classe_id)
    if (dossier / 'classe.db').exists():
        raise FileExistsError(f"{dossier / 'classe.db'} existe déjà.")
    (dossier / 'fichiers').mkdir(parents=True, exist_ok=True)
    cx = connecter(dossier / 'classe.db')
    try:
        appliquer_schema(cx, 'classe')
    finally:
        cx.close()


def supprimer_dossier_classe(classe_id):
    fermer_classe(classe_id)
    dossier = dossier_classe(classe_id)
    if dossier.is_symlink() or not dossier.is_dir():
        return
    # Renommer d'abord : une suppression interrompue ne laisse pas une classe à moitié lisible.
    corbeille = dossier.with_name(f'.supprime-{dossier.name}')
    shutil.rmtree(corbeille, ignore_errors=True)
    dossier.rename(corbeille)
    shutil.rmtree(corbeille)


def bases_a_migrer():
    """[(type_base, chemin, version)] des bases en retard ; erreur si une base est plus récente que le code."""
    a_migrer = []
    bases = [('commun', chemin_commun())] + [('classe', chemin_classe(i)) for i in ids_bases_classes()]
    for type_base, chemin in bases:
        if not chemin.is_file():
            continue
        cx = connecter(chemin)
        try:
            actuelle = version(cx)
        finally:
            cx.close()
        if actuelle > version_cible(type_base):
            raise VersionIncorrecte(
                f"{chemin} : schéma {actuelle}, plus récent que le code ({version_cible(type_base)})."
            )
        if actuelle < version_cible(type_base):
            a_migrer.append((type_base, chemin, actuelle))
    return a_migrer


def migrer():
    """Crée l'arborescence et ada.db au premier lancement ; sinon met les bases au dernier
    schéma, après une sauvegarde complète (bases + fichiers). Retourne la sauvegarde ou None."""
    from ada import sauvegardes

    for dossier in (dossier_classes(), dossier_cours(), dossier_sauvegardes(), dossier_exports()):
        dossier.mkdir(parents=True, exist_ok=True)
    if not chemin_commun().exists():
        cx = connecter(chemin_commun())
        try:
            appliquer_schema(cx, 'commun')
        finally:
            cx.close()
    a_migrer = bases_a_migrer()
    if not a_migrer:
        return None
    sauvegarde = sauvegardes.creer('avant-migration')
    for type_base, chemin, _version in a_migrer:
        cx = connecter(chemin)
        try:
            appliquer_schema(cx, type_base)
        finally:
            cx.close()
    return sauvegarde
