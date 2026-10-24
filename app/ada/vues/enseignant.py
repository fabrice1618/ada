"""Côté enseignant et admin : création des devoirs, suivi des rendus, téléchargements."""
import logging
import tempfile
import zipfile
from pathlib import Path

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for

from ada import db
from ada.comptes import personnel_requis, utilisateur_courant
from ada.fichiers import FichierRefuse, ouvrir
from ada.formulaires import FormulaireDevoir, initial_devoir
from ada.modeles import (
    FichierRendu, devoirs_de, get_classe, get_devoir, groupes, membres_classe, soumissions,
    toutes_les_classes,
)
from ada.temps import iso
from ada.texte import slugify
from ada.vues.devoirs import reponse_fichier

bp = Blueprint('enseignant', __name__, url_prefix='/admin/devoirs')
journal = logging.getLogger('ada')


def _devoir(classe_id, devoir_id):
    classe = get_classe(classe_id)
    devoir = get_devoir(classe, devoir_id) if classe else None
    if devoir is None:
        abort(404)
    return devoir


def _liste_devoirs(classes):
    liste = []
    for classe in classes:
        cx = db.classe(classe.id)
        nb_etudiants = len(membres_classe(classe.id, role='etudiant'))
        comptes = {
            ligne['id']: ligne
            for ligne in cx.execute(
                'SELECT d.id, '
                '(SELECT count(*) FROM soumissions s WHERE s.devoir_id = d.id) AS nb_rendus, '
                '(SELECT count(*) FROM groupes g WHERE g.devoir_id = d.id) AS nb_groupes '
                'FROM devoirs d'
            )
        }
        for devoir in devoirs_de(classe):
            liste.append({
                'devoir': devoir,
                'nb_rendus': comptes[devoir.id]['nb_rendus'],
                'nb_groupes': comptes[devoir.id]['nb_groupes'],
                'nb_etudiants': nb_etudiants,
            })
    liste.sort(key=lambda ligne: ligne['devoir'].date_limite, reverse=True)
    return liste


@bp.route('/', methods=['GET', 'POST'])
@personnel_requis
def gestion_devoirs():
    utilisateur = utilisateur_courant()
    classes = toutes_les_classes()
    if request.method == 'POST':
        form = FormulaireDevoir(request.form, classes=classes)
        if form.valider():
            d = form.donnees_valides
            cx = db.classe(d['classe'])
            with db.transaction(cx):
                devoir_id = cx.execute(
                    'INSERT INTO devoirs (titre, description, date_limite, cree_par, type_rendu, mode, taille_groupe_max) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (d['titre'], d['description'], iso(d['date_limite']), utilisateur.id,
                     d['type_rendu'], d['mode'], d['taille_groupe_max']),
                ).lastrowid
            flash("Devoir créé.", 'success')
            journal.info(
                "Devoir créé classe=%s id=%s type=%s mode=%s par=%s",
                d['classe'], devoir_id, d['type_rendu'], d['mode'], utilisateur.id,
            )
            return redirect(url_for('enseignant.suivi', classe_id=d['classe'], devoir_id=devoir_id))
    else:
        classe = request.args.get('classe', '')
        form = FormulaireDevoir(classes=classes, initial={'classe': int(classe)} if classe.isdigit() else None)

    return render_template(
        'devoirs_gestion.html', active_page='devoirs', form=form, lignes=_liste_devoirs(classes),
    )


@bp.route('/<int:classe_id>/<int:devoir_id>/', methods=['GET', 'POST'])
@personnel_requis
def suivi(classe_id, devoir_id):
    utilisateur = utilisateur_courant()
    devoir = _devoir(classe_id, devoir_id)
    cx = db.classe(classe_id)
    rendus = soumissions(devoir)
    taille_min = cx.execute(
        'SELECT max(n) FROM (SELECT count(*) AS n FROM membres_groupe WHERE devoir_id = ? GROUP BY groupe_id)',
        (devoir.id,),
    ).fetchone()[0]
    options = {
        'verrouille': bool(rendus),
        'taille_min': taille_min,
        'initial': initial_devoir(devoir),
    }
    if request.method == 'POST':
        form = FormulaireDevoir(request.form, **options)
        if form.valider():
            d = form.donnees_valides
            with db.transaction(cx):
                cx.execute(
                    'UPDATE devoirs SET titre = ?, description = ?, date_limite = ?, type_rendu = ?, '
                    'mode = ?, taille_groupe_max = ? WHERE id = ?',
                    (d['titre'], d['description'], iso(d['date_limite']), d['type_rendu'],
                     d['mode'], d['taille_groupe_max'], devoir.id),
                )
            flash("Devoir mis à jour.", 'success')
            journal.info(
                "Devoir modifié classe=%s id=%s type=%s mode=%s par=%s",
                classe_id, devoir.id, d['type_rendu'], d['mode'], utilisateur.id,
            )
            return redirect(url_for('enseignant.suivi', classe_id=classe_id, devoir_id=devoir.id))
    else:
        form = FormulaireDevoir(**options)

    etudiants = membres_classe(classe_id, role='etudiant')
    contexte = {'active_page': 'devoirs', 'devoir': devoir, 'form': form}
    if devoir.en_groupe:
        par_groupe = {s.groupe_id: s for s in rendus if s.groupe_id}
        liste_groupes = groupes(devoir)
        lignes = [{'groupe': g, 'soumission': par_groupe.get(g.id)} for g in liste_groupes]
        dans_un_groupe = {m.id for g in liste_groupes for m in g.membres}
        contexte['sans_groupe'] = [e for e in etudiants if e.id not in dans_un_groupe]
    else:
        par_etudiant = {s.etudiant_id: s for s in rendus if s.etudiant_id}
        lignes = [{'etudiant': e, 'soumission': par_etudiant.get(e.id)} for e in etudiants]
    contexte['lignes'] = lignes
    contexte['nb_rendus'] = sum(1 for ligne in lignes if ligne['soumission'])
    return render_template('devoir_suivi.html', **contexte)


@bp.get('/<int:classe_id>/<int:devoir_id>/fichiers/<int:fichier_id>/')
@personnel_requis
def telecharger(classe_id, devoir_id, fichier_id):
    devoir = _devoir(classe_id, devoir_id)
    ligne = db.classe(classe_id).execute(
        'SELECT f.* FROM fichiers_rendus f JOIN soumissions s ON s.id = f.soumission_id '
        'WHERE f.id = ? AND s.devoir_id = ?',
        (fichier_id, devoir.id),
    ).fetchone()
    if ligne is None:
        abort(404)
    try:
        return reponse_fichier(classe_id, FichierRendu.depuis(ligne))
    except FichierRefuse:
        flash("Fichier introuvable.", 'danger')
        return redirect(url_for('enseignant.suivi', classe_id=classe_id, devoir_id=devoir.id))


def _nom_archive(nom):
    nom = Path(nom or 'fichier').name.replace('\x00', '')
    return nom.replace('/', '_').replace('\\', '_') or 'fichier'


@bp.get('/<int:classe_id>/<int:devoir_id>/archive/')
@personnel_requis
def archive(classe_id, devoir_id):
    devoir = _devoir(classe_id, devoir_id)
    noms_groupes = {g.id: g.nom for g in groupes(devoir)}
    temporaire = tempfile.NamedTemporaryFile(suffix='.zip')
    ecrits = 0
    with zipfile.ZipFile(temporaire, 'w', compression=zipfile.ZIP_DEFLATED) as zip_rendus:
        for soumission in soumissions(devoir):
            if soumission.groupe_id:
                nom = noms_groupes.get(soumission.groupe_id, '')
                prefixe = f"groupe-{soumission.groupe_id}-{slugify(nom) or 'sans-nom'}"
            else:
                prefixe = str(soumission.etudiant_id)
            # Un fichier : <prefixe>_<nom> ; plusieurs : un dossier <prefixe>/.
            dossier = soumission.type == 'fichiers'
            vus = set()
            for fichier in soumission.fichiers:
                try:
                    chemin = ouvrir(classe_id, fichier.chemin)
                except FichierRefuse:
                    continue
                nom = _nom_archive(fichier.nom_original)
                if nom in vus:
                    nom = f"{fichier.id}_{nom}"
                vus.add(nom)
                zip_rendus.write(chemin, arcname=f"{prefixe}/{nom}" if dossier else f"{prefixe}_{nom}")
                ecrits += 1
    if ecrits == 0:
        temporaire.close()
        flash("Aucun fichier à archiver.", 'danger')
        return redirect(url_for('enseignant.suivi', classe_id=classe_id, devoir_id=devoir.id))
    temporaire.seek(0)
    return send_file(
        temporaire, as_attachment=True, download_name=f"devoir-{devoir.id}.zip", mimetype='application/zip',
    )
