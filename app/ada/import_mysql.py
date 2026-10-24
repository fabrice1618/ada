"""Reprise des données de la version Django (MySQL + volume uploads) dans le volume SQLite.

Préalable (migration/1-sauvegarder-mysql.sh, ancienne pile encore lancée) : dump MySQL, archive
du volume uploads et export zip de chaque classe par l'ancien `archiver_classe`. Ce dossier est
recopié dans /data/sauvegardes/, puis chaque classe migrée est comparée à son export : mêmes
données (classe.json) et mêmes fichiers (sha256). Au moindre écart, ce qui a été créé est retiré.

Identifiants conservés (utilisateurs, classes, devoirs, groupes, rendus, fichiers) ; mots de passe
Django conservés, rehachés à la première connexion (ada/comptes.py).
"""
import hashlib
import json
import shutil
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

from ada import archivage, db
from ada.modeles import get_classe
from ada.temps import iso, local, maintenant


class MigrationRefusee(Exception):
    pass


TABLES = {
    'utilisateurs': 'core_utilisateur',
    'classes': 'core_classe',
    'inscriptions': 'core_utilisateur_classes',
    'creneaux': 'core_creneau',
    'devoirs': 'devoirs',
    'groupes': 'groupes',
    'membres_groupe': 'groupes_membres',
    'soumissions': 'soumissions',
    'fichiers_rendus': 'soumissions_fichiers',
    'quiz': 'quiz',
    'questions': 'questions',
    'tentatives': 'tentatives',
}


def _dt(valeur):
    # Django (USE_TZ) écrit l'heure UTC, sans fuseau, dans MySQL.
    if valeur is None:
        return None
    if isinstance(valeur, datetime):
        return iso(valeur.replace(tzinfo=timezone.utc))
    raise ValueError(f"date inattendue : {valeur!r}")


def _jour(valeur):
    return valeur.isoformat() if isinstance(valeur, date) else valeur


def _json(valeur):
    if valeur is None:
        return None
    if isinstance(valeur, (bytes, str)):
        valeur = json.loads(valeur)
    return json.dumps(valeur, ensure_ascii=False)


def lire_mysql(parametres):
    import pymysql

    cx = pymysql.connect(
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor, **parametres,
    )
    try:
        with cx.cursor() as cur:
            donnees = {}
            for cle, table in TABLES.items():
                cur.execute(f'SELECT * FROM `{table}` ORDER BY id')
                donnees[cle] = list(cur.fetchall())
            return donnees
    finally:
        cx.close()


def _sha256(chemin):
    empreinte = hashlib.sha256()
    with open(chemin, 'rb') as f:
        while bloc := f.read(1024 * 1024):
            empreinte.update(bloc)
    return empreinte.hexdigest()


def _verifier_sommes(dossier, journal):
    sommes = dossier / 'SHA256SUMS'
    if not sommes.is_file():
        raise MigrationRefusee(f"{sommes} absent : relancer migration/1-sauvegarder-mysql.sh.")
    for ligne in sommes.read_text(encoding='utf-8').splitlines():
        attendu, nom = ligne.split(None, 1)
        nom = nom.lstrip('*')
        if _sha256(dossier / nom) != attendu:
            raise MigrationRefusee(f"{nom} : somme sha256 incorrecte, sauvegarde abîmée.")
    journal(f"Sauvegarde vérifiée : {dossier} (SHA256SUMS)")


def _exports(dossier):
    """{classe_id: Path} des exports zip de l'ancienne version."""
    trouves = {}
    for chemin in sorted((dossier / 'exports').glob('*.zip')):
        with zipfile.ZipFile(chemin) as archive:
            manifeste = json.loads(archive.read('classe.json'))
        trouves[manifeste['donnees']['classe']['id']] = chemin
    return trouves


def _ecrire_commun(donnees):
    cx = db.commun()
    with db.transaction(cx):
        for u in donnees['utilisateurs']:
            cx.execute(
                'INSERT INTO utilisateurs (id, email, nom_complet, role, mot_de_passe, actif, inscrit_le, '
                'derniere_connexion) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (u['id'], u['email'], u['nom_complet'], u['role'], u['password'] or '',
                 int(bool(u['is_active'])), _dt(u['date_joined']), _dt(u['last_login'])),
            )
        for c in donnees['classes']:
            cx.execute(
                'INSERT INTO classes (id, nom, annee, debut_autorisation, fin_autorisation) VALUES (?, ?, ?, ?, ?)',
                (c['id'], c['nom'], c['annee'], _jour(c['debut_autorisation']), _jour(c['fin_autorisation'])),
            )
        for i in donnees['inscriptions']:
            cx.execute(
                'INSERT INTO inscriptions (utilisateur_id, classe_id) VALUES (?, ?)',
                (i['utilisateur_id'], i['classe_id']),
            )


def _ecrire_classe(classe_id, donnees):
    db.creer_base_classe(classe_id)
    cx = db.classe(classe_id)
    devoirs = [d for d in donnees['devoirs'] if d['classe_id'] == classe_id]
    ids_devoirs = {d['id'] for d in devoirs}
    soumissions = [s for s in donnees['soumissions'] if s['devoir_id'] in ids_devoirs]
    ids_soumissions = {s['id'] for s in soumissions}
    quiz = [q for q in donnees['quiz'] if q['classe_id'] == classe_id]
    ids_quiz = {q['id'] for q in quiz}
    fichiers = [f for f in donnees['fichiers_rendus'] if f['soumission_id'] in ids_soumissions]
    with db.transaction(cx):
        for c in donnees['creneaux']:
            if c['classe_id'] == classe_id:
                cx.execute(
                    'INSERT INTO creneaux (id, type_ressource, ressource_id, chemin_page, ouverture, fermeture) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (c['id'], c['type_ressource'], c['ressource_id'], c['chemin_page'],
                     _dt(c['ouverture']), _dt(c['fermeture'])),
                )
        for d in devoirs:
            cx.execute(
                'INSERT INTO devoirs (id, titre, description, date_limite, cree_par, type_rendu, mode, '
                'taille_groupe_max) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (d['id'], d['titre'], d['description'], _dt(d['date_limite']), d['cree_par_id'],
                 d['type_rendu'], d['mode'], d['taille_groupe_max']),
            )
        for g in donnees['groupes']:
            if g['devoir_id'] in ids_devoirs:
                cx.execute(
                    'INSERT INTO groupes (id, devoir_id, nom, cree_par, date_creation) VALUES (?, ?, ?, ?, ?)',
                    (g['id'], g['devoir_id'], g['nom'], g['cree_par_id'], _dt(g['date_creation'])),
                )
        for m in donnees['membres_groupe']:
            if m['devoir_id'] in ids_devoirs:
                cx.execute(
                    'INSERT INTO membres_groupe (id, groupe_id, devoir_id, etudiant_id, date_adhesion) '
                    'VALUES (?, ?, ?, ?, ?)',
                    (m['id'], m['groupe_id'], m['devoir_id'], m['etudiant_id'], _dt(m['date_adhesion'])),
                )
        for s in soumissions:
            cx.execute(
                'INSERT INTO soumissions (id, devoir_id, etudiant_id, groupe_id, deposee_par, type, lien_github, '
                'date_soumission) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (s['id'], s['devoir_id'], s['etudiant_id'], s['groupe_id'], s['deposee_par_id'],
                 s['type'], s['lien_github'], _dt(s['date_soumission'])),
            )
        for f in fichiers:
            cx.execute(
                'INSERT INTO fichiers_rendus (id, soumission_id, chemin, nom_original, taille, date_depot) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (f['id'], f['soumission_id'], f['chemin'], f['nom_original'], f['taille'], _dt(f['date_depot'])),
            )
        for q in quiz:
            cx.execute(
                'INSERT INTO quiz (id, titre, duree_max_minutes, tentative_unique, cree_par) VALUES (?, ?, ?, ?, ?)',
                (q['id'], q['titre'], q['duree_max_minutes'], int(bool(q['tentative_unique'])), q['cree_par_id']),
            )
        for q in donnees['questions']:
            if q['quiz_id'] in ids_quiz:
                cx.execute(
                    'INSERT INTO questions (id, quiz_id, enonce, choix, reponse_correcte, points) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (q['id'], q['quiz_id'], q['enonce'], _json(q['choix']), q['reponse_correcte'], q['points']),
                )
        for t in donnees['tentatives']:
            if t['quiz_id'] in ids_quiz:
                cx.execute(
                    'INSERT INTO tentatives (id, quiz_id, etudiant_id, reponses, score, debut, fin) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (t['id'], t['quiz_id'], t['etudiant_id'], _json(t['reponses']), t['score'],
                     _dt(t['debut']), _dt(t['fin'])),
                )
    return fichiers


def _copier_fichiers(classe_id, fichiers, uploads):
    """Copie depuis l'ancien volume ; renvoie la liste des chemins absents."""
    manquants = []
    racine_source = uploads.resolve()
    for f in fichiers:
        relatif = f['chemin']
        source = (racine_source / relatif).resolve()
        if not relatif or '..' in Path(relatif).parts or not source.is_relative_to(racine_source) \
                or not source.is_file():
            manquants.append(relatif)
            continue
        cible = db.dossier_fichiers(classe_id) / relatif
        cible.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, cible)
        if _sha256(source) != _sha256(cible):
            raise MigrationRefusee(f"Copie altérée : {relatif}")
    return manquants


def _normaliser(donnees):
    # L'ordre des membres suivait la collation MySQL ; ici l'ordre binaire de SQLite.
    copie = json.loads(json.dumps(donnees))
    copie['membres'].sort(key=lambda m: m['id'])
    return copie


def _comparer_export(classe, chemin_export, journal):
    donnees = archivage.donnees_classe(classe)
    with zipfile.ZipFile(chemin_export) as archive:
        manifeste = json.loads(archive.read('classe.json'))
        avant = manifeste['donnees']
        if _normaliser(avant) != _normaliser(donnees):
            raise MigrationRefusee(
                f"Classe {classe.id} : données migrées différentes de l'export {chemin_export.name} "
                "(un rendu déposé après l'export ?)."
            )
        chemins = dict(db.classe(classe.id).execute('SELECT id, chemin FROM fichiers_rendus').fetchall())
        presents = set(archive.namelist())
        verifies = 0
        for devoir in avant['devoirs']:
            for rendu in devoir['rendus']:
                for fichier in rendu['fichiers']:
                    if fichier['archive'] not in presents:
                        continue
                    contenu = archive.read(fichier['archive'])
                    cible = db.dossier_fichiers(classe.id) / chemins[fichier['id']]
                    if not cible.is_file() or hashlib.sha256(contenu).hexdigest() != _sha256(cible):
                        raise MigrationRefusee(f"Classe {classe.id} : {fichier['archive']} différent de l'export.")
                    verifies += 1
    identique = archivage.calculer_empreinte(donnees) == manifeste['empreinte']
    journal(
        f"Classe {classe} : conforme à {chemin_export.name} ({verifies} fichiers comparés"
        f"{', empreinte identique' if identique else ', même contenu, ordre des membres différent'})."
    )


def _compter_sqlite(ids_classes):
    cx = db.commun()
    comptes = {t: cx.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
               for t in ('utilisateurs', 'classes', 'inscriptions')}
    for table in ('creneaux', 'devoirs', 'groupes', 'membres_groupe', 'soumissions',
                  'fichiers_rendus', 'quiz', 'questions', 'tentatives'):
        comptes[table] = sum(
            db.classe(i).execute(f'SELECT count(*) FROM {table}').fetchone()[0] for i in ids_classes
        )
    return comptes


def _annuler():
    db.fermer()
    for suffixe in ('', '-wal', '-shm'):
        Path(f'{db.chemin_commun()}{suffixe}').unlink(missing_ok=True)
    if db.dossier_classes().is_dir():
        shutil.rmtree(db.dossier_classes())
    db.dossier_classes().mkdir()


def importer(parametres_mysql, uploads, avant_migration, journal=print):
    uploads, avant_migration = Path(uploads), Path(avant_migration)
    if db.chemin_commun().exists() or db.ids_bases_classes():
        raise MigrationRefusee(
            f"{db.racine()} contient déjà des données : la migration part d'un volume vide."
        )
    if not uploads.is_dir():
        raise MigrationRefusee(f"{uploads} absent : monter l'ancien volume uploads.")

    # 1. Sauvegarde et exports de l'ancienne version : contrôlés, puis gardés dans le volume.
    _verifier_sommes(avant_migration, journal)
    exports = _exports(avant_migration)
    db.migrer()
    copie = db.dossier_sauvegardes() / (
        f"{local(maintenant()).strftime('%Y%m%d-%H%M%S')}-avant-migration-mysql"
    )
    shutil.copytree(avant_migration, copie)
    journal(f"Sauvegarde MySQL et exports recopiés dans {copie}")

    # 2. Lecture de MySQL.
    donnees = lire_mysql(parametres_mysql)
    attendus = {cle: len(lignes) for cle, lignes in donnees.items()}
    ids_classes = [c['id'] for c in donnees['classes']]
    sans_export = [i for i in ids_classes if i not in exports]
    if sans_export:
        raise MigrationRefusee(f"Classes sans export avant migration : {sans_export}.")

    try:
        # 3. Écriture : base commune, puis une base et un dossier de fichiers par classe.
        _ecrire_commun(donnees)
        manquants = {}
        for classe_id in ids_classes:
            fichiers = _ecrire_classe(classe_id, donnees)
            absents = _copier_fichiers(classe_id, fichiers, uploads)
            if absents:
                manquants[classe_id] = absents
            journal(f"Classe {classe_id} : {len(fichiers)} fichiers rendus, {len(absents)} absents de uploads.")

        # 4. Contrôles : effectifs table par table, puis chaque classe contre son export.
        obtenus = _compter_sqlite(ids_classes)
        ecarts = {t: (attendus[t], obtenus[t]) for t in attendus if attendus[t] != obtenus[t]}
        if ecarts:
            raise MigrationRefusee(f"Lignes perdues (MySQL, SQLite) : {ecarts}")
        journal("Effectifs identiques : " + ', '.join(f"{t}={n}" for t, n in obtenus.items()))
        for classe_id in ids_classes:
            _comparer_export(get_classe(classe_id), exports[classe_id], journal)
    except BaseException:
        _annuler()
        raise
    return {'comptes': obtenus, 'manquants': manquants, 'sauvegarde': copie}
