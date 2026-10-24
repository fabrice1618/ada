"""Sauvegardes complètes du volume : bases SQLite et fichiers.

/data/sauvegardes/<AAAAMMJJ-HHMMSS>-<motif>/
├── MANIFESTE.json
├── ada.db
├── classes/<id>/classe.db
├── classes/<id>/fichiers/...   liens physiques : un fichier rendu n'est jamais réécrit
│                               sur place (os.replace), la copie ne coûte presque rien
└── cours/                      copie réelle (les pages peuvent être réécrites sur place)

Les bases sont copiées avec l'API de sauvegarde de SQLite : copie cohérente, même service lancé.
Une sauvegarde reste sur le même disque : la copier ailleurs (tar, voir install.md).
"""
import json
import os
import shutil
import sqlite3
from pathlib import Path

from ada import db
from ada.temps import local, maintenant
from ada.texte import slugify


def _copier_base(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(f'file:{source}?mode=ro', uri=True)
    dst = sqlite3.connect(destination)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    # Une copie autonome : pas de -wal à côté.
    cx = sqlite3.connect(destination)
    try:
        cx.execute('PRAGMA journal_mode = DELETE')
    finally:
        cx.close()


def _lier_arbre(source, destination):
    """Recopie l'arborescence en liens physiques (copie si le lien est impossible)."""
    nb, octets = 0, 0
    for dossier, _sous, fichiers in os.walk(source):
        cible = destination / Path(dossier).relative_to(source)
        cible.mkdir(parents=True, exist_ok=True)
        for nom in fichiers:
            if nom.endswith('.part'):
                continue
            origine = Path(dossier) / nom
            try:
                os.link(origine, cible / nom)
            except OSError:
                shutil.copy2(origine, cible / nom)
            nb += 1
            octets += origine.stat().st_size
    return nb, octets


def _version(chemin):
    cx = sqlite3.connect(f'file:{chemin}?mode=ro', uri=True)
    try:
        return db.version(cx)
    finally:
        cx.close()


def creer(motif='manuelle'):
    """Sauvegarde complète ; renvoie son dossier."""
    racine = db.dossier_sauvegardes()
    racine.mkdir(parents=True, exist_ok=True)
    nom = f"{local(maintenant()).strftime('%Y%m%d-%H%M%S')}-{slugify(motif) or 'sauvegarde'}"
    dossier = racine / nom
    suffixe = 1
    while dossier.exists():
        suffixe += 1
        dossier = racine / f'{nom}-{suffixe}'
    partiel = racine / f'.{dossier.name}.part'
    shutil.rmtree(partiel, ignore_errors=True)
    partiel.mkdir()

    manifeste = {
        'application': 'ada',
        'motif': motif,
        'cree_le': local(maintenant()).isoformat(),
        'commun': None,
        'classes': {},
        'cours': None,
    }
    try:
        if db.chemin_commun().is_file():
            _copier_base(db.chemin_commun(), partiel / 'ada.db')
            manifeste['commun'] = {'schema': _version(partiel / 'ada.db')}
        for classe_id in db.ids_bases_classes():
            cible = partiel / 'classes' / str(classe_id)
            _copier_base(db.chemin_classe(classe_id), cible / 'classe.db')
            nb, octets = 0, 0
            if db.dossier_fichiers(classe_id).is_dir():
                nb, octets = _lier_arbre(db.dossier_fichiers(classe_id), cible / 'fichiers')
            manifeste['classes'][str(classe_id)] = {
                'schema': _version(cible / 'classe.db'), 'fichiers': nb, 'octets': octets,
            }
        if db.dossier_cours().is_dir():
            shutil.copytree(db.dossier_cours(), partiel / 'cours')
            manifeste['cours'] = sum(1 for p in (partiel / 'cours').rglob('*') if p.is_file())
        (partiel / 'MANIFESTE.json').write_text(
            json.dumps(manifeste, indent=2, ensure_ascii=False), encoding='utf-8',
        )
        partiel.rename(dossier)
    except BaseException:
        shutil.rmtree(partiel, ignore_errors=True)
        raise
    return dossier


def lister():
    """[(nom, manifeste)] de la plus récente à la plus ancienne."""
    racine = db.dossier_sauvegardes()
    if not racine.is_dir():
        return []
    resultat = []
    for dossier in sorted(racine.iterdir(), reverse=True):
        fichier = dossier / 'MANIFESTE.json'
        if dossier.name.startswith('.') or not fichier.is_file():
            continue
        resultat.append((dossier.name, json.loads(fichier.read_text(encoding='utf-8'))))
    return resultat


def restaurer(nom):
    """Remplace bases, fichiers et cours par ceux de la sauvegarde `nom`, après une sauvegarde
    de l'état actuel. Service arrêté : rien ne doit écrire pendant la restauration."""
    source = db.dossier_sauvegardes() / nom
    if '/' in nom or nom.startswith('.') or not (source / 'MANIFESTE.json').is_file():
        raise FileNotFoundError(f"Sauvegarde introuvable : {nom}")
    if not (source / 'ada.db').is_file():
        raise FileNotFoundError(f"{source}/ada.db absent : sauvegarde incomplète.")
    db.fermer()
    secours = creer('avant-restauration')

    racine = db.racine()
    for suffixe in ('', '-wal', '-shm'):
        Path(f'{db.chemin_commun()}{suffixe}').unlink(missing_ok=True)
    for dossier in (db.dossier_classes(), db.dossier_cours()):
        if dossier.exists():
            shutil.rmtree(dossier)

    shutil.copy2(source / 'ada.db', db.chemin_commun())
    db.dossier_classes().mkdir()
    if (source / 'classes').is_dir():
        for dossier in sorted((source / 'classes').iterdir()):
            cible = db.dossier_classes() / dossier.name
            cible.mkdir()
            # Les bases sont réécrites sur place : copie réelle. Les fichiers : liens physiques.
            shutil.copy2(dossier / 'classe.db', cible / 'classe.db')
            if (dossier / 'fichiers').is_dir():
                _lier_arbre(dossier / 'fichiers', cible / 'fichiers')
            else:
                (cible / 'fichiers').mkdir()
    if (source / 'cours').is_dir():
        shutil.copytree(source / 'cours', db.dossier_cours())
    else:
        db.dossier_cours().mkdir()
    (racine / 'exports').mkdir(exist_ok=True)
    return secours
