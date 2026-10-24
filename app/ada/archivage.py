"""Archive zip d'une classe (données de ada.db et de classe.db, fichiers rendus), vérification,
puis suppression. Le format est celui des archives produites par la version Django : une archive
exportée avant la migration se compare aux données migrées (ada/import_mysql.py)."""
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

from ada import db
from ada.fichiers import FichierRefuse, ouvrir
from ada.modeles import LIBELLES_MODE, LIBELLES_TYPE, classes_de, membres_classe, utilisateurs_par_id
from ada.temps import lire, local, maintenant
from ada.texte import slugify

FORMAT = 1


class ArchiveInvalide(Exception):
    pass


def _date(valeur):
    # Texte stocké -> même rendu que Django : microsecondes omises quand elles sont nulles.
    if isinstance(valeur, str):
        valeur = lire(valeur) if 'T' in valeur else valeur
        if isinstance(valeur, str):
            return valeur
    return valeur.isoformat() if valeur else None


def _personne(utilisateur):
    if utilisateur is None:
        return None
    return {'id': utilisateur.id, 'nom_complet': utilisateur.nom_complet, 'email': utilisateur.email}


def ids_etudiants_a_supprimer(classe):
    # Étudiants de cette seule classe.
    return [ligne[0] for ligne in db.commun().execute(
        "SELECT u.id FROM utilisateurs u JOIN inscriptions i ON i.utilisateur_id = u.id "
        "WHERE i.classe_id = ? AND u.role = 'etudiant' "
        "AND (SELECT count(*) FROM inscriptions j WHERE j.utilisateur_id = u.id) = 1 ORDER BY u.id",
        (classe.id,),
    )]


def _rendu(cx, soumission, dossier, personnes, noms_groupes):
    etudiant = personnes.get(soumission['etudiant_id'])
    if soumission['groupe_id']:
        nom_groupe = noms_groupes.get(soumission['groupe_id'], '')
        prefixe = f"groupe-{soumission['groupe_id']}-{slugify(nom_groupe) or 'sans-nom'}"
    else:
        nom = etudiant.nom_complet if etudiant else ''
        prefixe = f"{slugify(nom) or 'etudiant'}-{soumission['etudiant_id']}"
    vus = set()
    fichiers = []
    for fichier in cx.execute(
        'SELECT * FROM fichiers_rendus WHERE soumission_id = ? ORDER BY id', (soumission['id'],),
    ):
        nom = Path(fichier['nom_original'] or 'fichier').name.replace('\x00', '') or 'fichier'
        if nom in vus:
            nom = f"{fichier['id']}_{nom}"
        vus.add(nom)
        fichiers.append({
            'id': fichier['id'],
            'nom': fichier['nom_original'],
            'taille': fichier['taille'],
            'date_depot': _date(fichier['date_depot']),
            'archive': f"{dossier}/{prefixe}/{nom}",
        })
    groupe_id = soumission['groupe_id']
    return {
        'id': soumission['id'],
        'etudiant': _personne(etudiant),
        'groupe': {'id': groupe_id, 'nom': noms_groupes.get(groupe_id, '')} if groupe_id else None,
        'type': soumission['type'],
        'lien_github': soumission['lien_github'],
        'date_soumission': _date(soumission['date_soumission']),
        'deposee_par': _personne(personnes.get(soumission['deposee_par'])),
        'fichiers': fichiers,
    }


def _ids_personnes(cx):
    requetes = (
        'SELECT cree_par FROM devoirs', 'SELECT etudiant_id FROM membres_groupe',
        'SELECT etudiant_id FROM soumissions', 'SELECT deposee_par FROM soumissions',
        'SELECT cree_par FROM quiz', 'SELECT etudiant_id FROM tentatives',
    )
    return {ligne[0] for requete in requetes for ligne in cx.execute(requete)}


def donnees_classe(classe):
    """Tout ce qui sera supprimé avec la classe, sans mot de passe ni chemin de stockage."""
    cx = db.classe(classe.id)
    a_supprimer = set(ids_etudiants_a_supprimer(classe))
    membres = []
    for utilisateur in membres_classe(classe.id):
        membres.append({
            'id': utilisateur.id,
            'nom_complet': utilisateur.nom_complet,
            'email': utilisateur.email,
            'role': utilisateur.role,
            'actif': utilisateur.actif,
            'inscrit_le': _date(utilisateur.inscrit_le),
            'autres_classes': sorted(str(c) for c in classes_de(utilisateur.id) if c.id != classe.id),
            'compte_supprime': utilisateur.id in a_supprimer,
        })

    personnes = utilisateurs_par_id(_ids_personnes(cx))
    liste_devoirs = []
    for devoir in cx.execute('SELECT * FROM devoirs ORDER BY id').fetchall():
        dossier = f"fichiers/{devoir['id']}-{slugify(devoir['titre']) or 'devoir'}"
        groupes = cx.execute(
            'SELECT * FROM groupes WHERE devoir_id = ? ORDER BY id', (devoir['id'],),
        ).fetchall()
        noms_groupes = {g['id']: g['nom'] for g in groupes}
        liste_devoirs.append({
            'id': devoir['id'],
            'titre': devoir['titre'],
            'description': devoir['description'],
            'date_limite': _date(devoir['date_limite']),
            'type_rendu': devoir['type_rendu'],
            'mode': devoir['mode'],
            'taille_groupe_max': devoir['taille_groupe_max'],
            'cree_par': _personne(personnes.get(devoir['cree_par'])),
            'groupes': [{
                'id': groupe['id'],
                'nom': groupe['nom'],
                'date_creation': _date(groupe['date_creation']),
                'membres': [
                    dict(_personne(personnes[a['etudiant_id']]), date_adhesion=_date(a['date_adhesion']))
                    for a in cx.execute(
                        'SELECT * FROM membres_groupe WHERE groupe_id = ? ORDER BY id', (groupe['id'],),
                    )
                    if a['etudiant_id'] in personnes
                ],
            } for groupe in groupes],
            'rendus': [
                _rendu(cx, s, dossier, personnes, noms_groupes)
                for s in cx.execute(
                    'SELECT * FROM soumissions WHERE devoir_id = ? ORDER BY id', (devoir['id'],),
                ).fetchall()
            ],
        })

    creneaux = [{
        'type_ressource': c['type_ressource'],
        'ressource_id': c['ressource_id'],
        'chemin_page': c['chemin_page'],
        'ouverture': _date(c['ouverture']),
        'fermeture': _date(c['fermeture']),
    } for c in cx.execute('SELECT * FROM creneaux ORDER BY id')]

    quiz = [{
        'id': q['id'],
        'titre': q['titre'],
        'duree_max_minutes': q['duree_max_minutes'],
        'tentative_unique': bool(q['tentative_unique']),
        'cree_par': _personne(personnes.get(q['cree_par'])),
        'questions': [{
            'enonce': question['enonce'],
            'choix': json.loads(question['choix']),
            'reponse_correcte': question['reponse_correcte'],
            'points': question['points'],
        } for question in cx.execute('SELECT * FROM questions WHERE quiz_id = ? ORDER BY id', (q['id'],))],
        'tentatives': [{
            'etudiant': _personne(personnes.get(t['etudiant_id'])),
            'reponses': json.loads(t['reponses']) if t['reponses'] is not None else None,
            'score': t['score'],
            'debut': _date(t['debut']),
            'fin': _date(t['fin']),
        } for t in cx.execute('SELECT * FROM tentatives WHERE quiz_id = ? ORDER BY id', (q['id'],))],
    } for q in cx.execute('SELECT * FROM quiz ORDER BY id').fetchall()]

    return {
        'classe': {
            'id': classe.id,
            'nom': classe.nom,
            'annee': classe.annee,
            'debut_autorisation': _date(classe.debut_autorisation),
            'fin_autorisation': _date(classe.fin_autorisation),
        },
        'membres': membres,
        'devoirs': liste_devoirs,
        'creneaux': creneaux,
        'quiz': quiz,
    }


def calculer_empreinte(donnees):
    texte = json.dumps(donnees, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(texte.encode('utf-8')).hexdigest()


def bilan(donnees):
    fichiers = [f for d in donnees['devoirs'] for r in d['rendus'] for f in r['fichiers']]
    return {
        'etudiants_supprimes': sum(1 for m in donnees['membres'] if m['compte_supprime']),
        'etudiants_conserves': sum(
            1 for m in donnees['membres'] if m['role'] == 'etudiant' and not m['compte_supprime']
        ),
        'devoirs': len(donnees['devoirs']),
        'rendus': sum(len(d['rendus']) for d in donnees['devoirs']),
        'fichiers': len(fichiers),
        'octets': sum(f['taille'] for f in fichiers),
    }


def nom_archive(classe, empreinte):
    nom = slugify(f"{classe.nom}-{classe.annee}") or 'classe'
    return f"ada-{nom}-{empreinte[:8]}.zip"


def _csv(entetes, lignes):
    # Point-virgule et BOM : s'ouvre directement dans un tableur français.
    tampon = io.StringIO()
    tampon.write('﻿')
    ecrivain = csv.writer(tampon, delimiter=';')
    ecrivain.writerow(entetes)
    ecrivain.writerows(lignes)
    return tampon.getvalue()


def _tableaux(donnees):
    etudiants = [
        [m['nom_complet'], m['email'], m['role'], 'oui' if m['actif'] else 'non',
         ', '.join(m['autres_classes']), 'oui' if m['compte_supprime'] else 'non']
        for m in donnees['membres']
    ]
    devoirs, groupes, rendus = [], [], []
    for d in donnees['devoirs']:
        devoirs.append([
            d['id'], d['titre'], LIBELLES_TYPE.get(d['type_rendu'], d['type_rendu']),
            LIBELLES_MODE.get(d['mode'], d['mode']), d['taille_groupe_max'] or '',
            d['date_limite'], (d['cree_par'] or {}).get('nom_complet', ''), len(d['rendus']),
        ])
        for g in d['groupes']:
            for m in g['membres']:
                groupes.append([d['id'], d['titre'], g['nom'], m['nom_complet'], m['email']])
        membres_groupe = {g['id']: g['membres'] for g in d['groupes']}
        for r in d['rendus']:
            if r['groupe']:
                auteur = r['groupe']['nom']
                membres = ', '.join(m['nom_complet'] for m in membres_groupe.get(r['groupe']['id'], []))
            else:
                auteur = r['etudiant']['nom_complet']
                membres = r['etudiant']['email']
            rendus.append([
                d['id'], d['titre'], auteur, membres, LIBELLES_TYPE.get(r['type'], r['type']),
                r['lien_github'] or '', ' | '.join(f['archive'] for f in r['fichiers']),
                r['date_soumission'], (r['deposee_par'] or {}).get('nom_complet', ''),
            ])
    return {
        'etudiants.csv': _csv(
            ['nom', 'email', 'role', 'actif', 'autres_classes', 'compte_supprime'], etudiants),
        'devoirs.csv': _csv(
            ['id', 'titre', 'type_rendu', 'mode', 'taille_groupe_max', 'date_limite',
             'cree_par', 'rendus'], devoirs),
        'groupes.csv': _csv(['devoir_id', 'devoir', 'groupe', 'membre', 'email'], groupes),
        'rendus.csv': _csv(
            ['devoir_id', 'devoir', 'rendu_par', 'membres', 'type', 'lien_github', 'fichiers',
             'date', 'depose_par'], rendus),
    }


def _lisezmoi(manifeste, chiffres):
    classe = manifeste['donnees']['classe']
    lignes = [
        f"Archive Ada — classe {classe['nom']} ({classe['annee']})",
        f"Exportée le {manifeste['exporte_le']}",
        f"Empreinte des données : {manifeste['empreinte']}",
        '',
        f"{chiffres['etudiants_supprimes'] + chiffres['etudiants_conserves']} étudiants, "
        f"{chiffres['devoirs']} devoirs, {chiffres['rendus']} rendus, {chiffres['fichiers']} fichiers.",
        '',
        "classe.json   toutes les données (membres, devoirs, groupes, rendus, créneaux, quiz)",
        "etudiants.csv, devoirs.csv, groupes.csv, rendus.csv   les mêmes, pour un tableur",
        "fichiers/<devoir>/<étudiant ou groupe>/   les fichiers rendus, sous leur nom d'origine",
        '',
        "Aucun mot de passe n'est archivé.",
    ]
    if manifeste['fichiers_manquants']:
        lignes += ['', "Fichiers absents du serveur au moment de l'export :"]
        lignes += [f"  {nom}" for nom in manifeste['fichiers_manquants']]
    return '\n'.join(lignes) + '\n'


def ecrire_archive(classe, sortie):
    donnees = donnees_classe(classe)
    empreinte = calculer_empreinte(donnees)
    chemins = dict(db.classe(classe.id).execute('SELECT id, chemin FROM fichiers_rendus').fetchall())
    manquants = []
    with zipfile.ZipFile(sortie, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for devoir in donnees['devoirs']:
            for rendu in devoir['rendus']:
                for fichier in rendu['fichiers']:
                    try:
                        source = ouvrir(classe.id, chemins.get(fichier['id']))
                    except FichierRefuse:
                        manquants.append(fichier['archive'])
                        continue
                    archive.write(source, arcname=fichier['archive'])
        manifeste = {
            'application': 'ada',
            'format': FORMAT,
            'exporte_le': local(maintenant()).isoformat(),
            'empreinte': empreinte,
            'fichiers_manquants': manquants,
            'donnees': donnees,
        }
        archive.writestr('classe.json', json.dumps(manifeste, indent=2, ensure_ascii=False))
        for nom, contenu in _tableaux(donnees).items():
            archive.writestr(nom, contenu)
        chiffres = bilan(donnees)
        archive.writestr('LISEZMOI.txt', _lisezmoi(manifeste, chiffres))
    return dict(chiffres, empreinte=empreinte, manquants=len(manquants))


def verifier_archive(classe, source):
    """L'archive est lisible, complète, et décrit l'état actuel de la classe."""
    try:
        archive = zipfile.ZipFile(source)
    except zipfile.BadZipFile:
        raise ArchiveInvalide("Ce fichier n'est pas une archive zip.")
    with archive:
        corrompu = archive.testzip()
        if corrompu is not None:
            raise ArchiveInvalide(f"Archive corrompue : {corrompu}.")
        try:
            manifeste = json.loads(archive.read('classe.json'))
            donnees = manifeste['donnees']
            empreinte = manifeste['empreinte']
            identifiant = donnees['classe']['id']
        except (KeyError, TypeError, ValueError):
            raise ArchiveInvalide("classe.json absent ou illisible.")
        if manifeste.get('application') != 'ada' or identifiant != classe.id:
            raise ArchiveInvalide(f"Cette archive n'est pas celle de la classe {classe}.")
        if calculer_empreinte(donnees) != empreinte:
            raise ArchiveInvalide("classe.json ne correspond pas à son empreinte.")
        if calculer_empreinte(donnees_classe(classe)) != empreinte:
            raise ArchiveInvalide(
                "Les données de la classe ont changé depuis l'export : exportez à nouveau."
            )
        presents = set(archive.namelist())
        manquants = set(manifeste.get('fichiers_manquants', []))
        for devoir in donnees['devoirs']:
            for rendu in devoir['rendus']:
                for fichier in rendu['fichiers']:
                    if fichier['archive'] not in presents and fichier['archive'] not in manquants:
                        raise ArchiveInvalide(f"Fichier absent de l'archive : {fichier['archive']}.")
    return manifeste


def supprimer_classe(classe):
    """Supprime la classe (ligne, base, fichiers) et ses étudiants sans autre classe."""
    cx = db.classe(classe.id)
    devoirs = cx.execute('SELECT count(*) FROM devoirs').fetchone()[0]
    fichiers = cx.execute('SELECT count(*) FROM fichiers_rendus').fetchone()[0]
    cx_commun = db.commun()
    with db.transaction(cx_commun):
        a_supprimer = ids_etudiants_a_supprimer(classe)
        conserves = len(membres_classe(classe.id, role='etudiant')) - len(a_supprimer)
        cx_commun.executemany('DELETE FROM utilisateurs WHERE id = ?', [(i,) for i in a_supprimer])
        cx_commun.execute('DELETE FROM classes WHERE id = ?', (classe.id,))
    # Après la transaction : un échec plus haut laisse la classe intacte.
    db.supprimer_dossier_classe(classe.id)
    return {
        'etudiants_supprimes': len(a_supprimer),
        'etudiants_conserves': conserves,
        'devoirs': devoirs,
        'fichiers': fichiers,
    }
