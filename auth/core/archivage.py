import csv
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from django.utils.text import slugify

from core.fichiers import FichierRefuse, ouvrir, supprimer
from core.models import (
    TYPE_RENDU_CHOICES, Devoir, FichierRendu, Groupe, MembreGroupe, Soumission, Utilisateur,
)

FORMAT = 1
LIBELLES_TYPE = dict(TYPE_RENDU_CHOICES)
LIBELLES_MODE = dict(Devoir.MODE_CHOICES)


class ArchiveInvalide(Exception):
    pass


def _date(valeur):
    return valeur.isoformat() if valeur else None


def _personne(utilisateur):
    if utilisateur is None:
        return None
    return {'id': utilisateur.id, 'nom_complet': utilisateur.nom_complet, 'email': utilisateur.email}


def ids_etudiants_a_supprimer(classe):
    # Étudiants de cette seule classe. Sous-requête : un filtre sur `classes` suivi de
    # Count('classes') réutiliserait la jointure et compterait toujours 1.
    return list(
        Utilisateur.objects.filter(
            id__in=classe.utilisateurs.filter(role='etudiant').values('id'),
        )
        .annotate(nb_classes=Count('classes'))
        .filter(nb_classes=1)
        .values_list('id', flat=True)
    )


def _rendu(soumission, dossier):
    if soumission.groupe_id:
        prefixe = f"groupe-{soumission.groupe_id}-{slugify(soumission.groupe.nom) or 'sans-nom'}"
    else:
        prefixe = f"{slugify(soumission.etudiant.nom_complet) or 'etudiant'}-{soumission.etudiant_id}"
    vus = set()
    fichiers = []
    for fichier in soumission.fichiers.all():
        nom = Path(fichier.nom_original or 'fichier').name.replace('\x00', '') or 'fichier'
        if nom in vus:
            nom = f"{fichier.id}_{nom}"
        vus.add(nom)
        fichiers.append({
            'id': fichier.id,
            'nom': fichier.nom_original,
            'taille': fichier.taille,
            'date_depot': _date(fichier.date_depot),
            'archive': f"{dossier}/{prefixe}/{nom}",
        })
    return {
        'id': soumission.id,
        'etudiant': _personne(soumission.etudiant),
        'groupe': {'id': soumission.groupe.id, 'nom': soumission.groupe.nom} if soumission.groupe_id else None,
        'type': soumission.type,
        'lien_github': soumission.lien_github,
        'date_soumission': _date(soumission.date_soumission),
        'deposee_par': _personne(soumission.deposee_par),
        'fichiers': fichiers,
    }


def donnees_classe(classe):
    """Tout ce qui sera supprimé avec la classe, sans mot de passe ni chemin de stockage."""
    a_supprimer = set(ids_etudiants_a_supprimer(classe))
    membres = []
    for utilisateur in classe.utilisateurs.prefetch_related('classes').order_by('nom_complet', 'id'):
        membres.append({
            'id': utilisateur.id,
            'nom_complet': utilisateur.nom_complet,
            'email': utilisateur.email,
            'role': utilisateur.role,
            'actif': utilisateur.is_active,
            'inscrit_le': _date(utilisateur.date_joined),
            'autres_classes': sorted(str(c) for c in utilisateur.classes.all() if c.id != classe.id),
            'compte_supprime': utilisateur.id in a_supprimer,
        })

    devoirs = (
        classe.devoirs.select_related('cree_par')
        .prefetch_related(
            Prefetch('groupes', queryset=Groupe.objects.order_by('id').prefetch_related(
                Prefetch('adhesions', queryset=MembreGroupe.objects.select_related('etudiant').order_by('id')),
            )),
            Prefetch('soumissions', queryset=Soumission.objects.select_related(
                'etudiant', 'groupe', 'deposee_par',
            ).prefetch_related(
                Prefetch('fichiers', queryset=FichierRendu.objects.order_by('id')),
            ).order_by('id')),
        )
        .order_by('id')
    )
    liste_devoirs = []
    for devoir in devoirs:
        dossier = f"fichiers/{devoir.id}-{slugify(devoir.titre) or 'devoir'}"
        liste_devoirs.append({
            'id': devoir.id,
            'titre': devoir.titre,
            'description': devoir.description,
            'date_limite': _date(devoir.date_limite),
            'type_rendu': devoir.type_rendu,
            'mode': devoir.mode,
            'taille_groupe_max': devoir.taille_groupe_max,
            'cree_par': _personne(devoir.cree_par),
            'groupes': [{
                'id': groupe.id,
                'nom': groupe.nom,
                'date_creation': _date(groupe.date_creation),
                'membres': [
                    dict(_personne(a.etudiant), date_adhesion=_date(a.date_adhesion))
                    for a in groupe.adhesions.all()
                ],
            } for groupe in devoir.groupes.all()],
            'rendus': [_rendu(s, dossier) for s in devoir.soumissions.all()],
        })

    creneaux = [{
        'type_ressource': c.type_ressource,
        'ressource_id': c.ressource_id,
        'chemin_page': c.chemin_page,
        'ouverture': _date(c.ouverture),
        'fermeture': _date(c.fermeture),
    } for c in classe.creneaux.order_by('id')]

    quiz = [{
        'id': q.id,
        'titre': q.titre,
        'duree_max_minutes': q.duree_max_minutes,
        'tentative_unique': q.tentative_unique,
        'cree_par': _personne(q.cree_par),
        'questions': [{
            'enonce': question.enonce,
            'choix': question.choix,
            'reponse_correcte': question.reponse_correcte,
            'points': question.points,
        } for question in q.questions.order_by('id')],
        'tentatives': [{
            'etudiant': _personne(t.etudiant),
            'reponses': t.reponses,
            'score': t.score,
            'debut': _date(t.debut),
            'fin': _date(t.fin),
        } for t in q.tentatives.select_related('etudiant').order_by('id')],
    } for q in classe.quiz.select_related('cree_par').order_by('id')]

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
    chemins = dict(
        FichierRendu.objects.filter(soumission__devoir__classe=classe).values_list('id', 'chemin')
    )
    manquants = []
    with zipfile.ZipFile(sortie, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for devoir in donnees['devoirs']:
            for rendu in devoir['rendus']:
                for fichier in rendu['fichiers']:
                    try:
                        source = ouvrir(chemins.get(fichier['id']))
                    except FichierRefuse:
                        manquants.append(fichier['archive'])
                        continue
                    archive.write(source, arcname=fichier['archive'])
        manifeste = {
            'application': 'ada',
            'format': FORMAT,
            'exporte_le': _date(timezone.localtime()),
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


def _supprimer_dossier_devoir(devoir_id):
    racine = Path(settings.UPLOAD_ROOT).resolve()
    dossier = racine / str(int(devoir_id))
    if dossier.is_symlink() or not dossier.is_dir():
        return
    shutil.rmtree(dossier)


def supprimer_classe(classe):
    """Supprime la classe, ses devoirs, rendus, groupes, fichiers et ses étudiants sans autre classe."""
    with transaction.atomic():
        a_supprimer = ids_etudiants_a_supprimer(classe)
        devoir_ids = list(classe.devoirs.values_list('id', flat=True))
        chemins = list(
            FichierRendu.objects.filter(
                Q(soumission__devoir__classe=classe) | Q(soumission__etudiant_id__in=a_supprimer)
            ).values_list('chemin', flat=True)
        )
        conserves = classe.utilisateurs.filter(role='etudiant').exclude(id__in=a_supprimer).count()
        Utilisateur.objects.filter(id__in=a_supprimer).delete()
        classe.delete()
    # Après la transaction : un échec plus haut ne laisse pas de rendu sans son fichier.
    for chemin in chemins:
        supprimer(chemin)
    for devoir_id in devoir_ids:
        _supprimer_dossier_devoir(devoir_id)
    return {
        'etudiants_supprimes': len(a_supprimer),
        'etudiants_conserves': conserves,
        'devoirs': len(devoir_ids),
        'fichiers': len(chemins),
    }
