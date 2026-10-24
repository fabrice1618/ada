"""Côté étudiant : devoirs de ses classes, rendu (fichier, fichiers, lien GitHub), groupes."""
import logging
import sqlite3
import uuid

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_file, url_for

from ada import db
from ada.comptes import connexion_requise, utilisateur_courant
from ada.fichiers import FichierRefuse, enregistrer, nom_affichage, ouvrir, supprimer
from ada.formulaires import valider_lien, valider_nom_groupe
from ada.modeles import (
    FichierRendu, Groupe, classes_de, devoirs_de, est_inscrit, get_classe, get_devoir, groupes,
    soumissions,
)
from ada.temps import iso, maintenant

bp = Blueprint('devoirs', __name__, url_prefix='/devoirs')
journal = logging.getLogger('ada')


def reponse_fichier(classe_id, fichier):
    return send_file(
        ouvrir(classe_id, fichier.chemin),
        as_attachment=True,
        download_name=fichier.nom_original or 'fichier',
    )


def contexte_depot():
    config = current_app.config
    return {
        'extensions': ','.join(f'.{ext}' for ext in config['ALLOWED_EXTENSIONS']),
        'taille_max': config['MAX_UPLOAD_SIZE_MB'],
        'max_fichiers': config['MAX_UPLOAD_FILES'],
    }


def _devoir_de_letudiant(utilisateur, classe_id, devoir_id):
    if not est_inscrit(utilisateur.id, classe_id):
        abort(404)
    classe = get_classe(classe_id)
    devoir = get_devoir(classe, devoir_id) if classe else None
    if devoir is None:
        abort(404)
    return devoir


def _groupe_de(devoir, etudiant_id):
    ligne = db.classe(devoir.classe_id).execute(
        'SELECT g.* FROM groupes g JOIN membres_groupe m ON m.groupe_id = g.id '
        'WHERE m.devoir_id = ? AND m.etudiant_id = ?',
        (devoir.id, etudiant_id),
    ).fetchone()
    return Groupe.depuis(ligne) if ligne else None


def _proprietaire(devoir, etudiant_id):
    # Le rendu appartient à l'étudiant, ou à son groupe ; None : pas encore de groupe.
    if not devoir.en_groupe:
        return {'etudiant_id': etudiant_id}
    groupe = _groupe_de(devoir, etudiant_id)
    if groupe is None:
        return None
    return {'groupe_id': groupe.id}


def _filtre(proprietaire, table=''):
    (colonne, valeur), = proprietaire.items()
    return f'AND {table}{colonne} = ?', (valeur,)


def _ma_soumission(devoir, proprietaire):
    if proprietaire is None:
        return None
    where, parametres = _filtre(proprietaire)
    trouvees = soumissions(devoir, where, parametres)
    return trouvees[0] if trouvees else None


def _nom_genere(proprietaire):
    if 'groupe_id' in proprietaire:
        return f"g{proprietaire['groupe_id']}"
    return str(proprietaire['etudiant_id'])


def _qui(proprietaire, utilisateur):
    if 'groupe_id' in proprietaire:
        return f"groupe={proprietaire['groupe_id']} etudiant={utilisateur.id}"
    return f"etudiant={utilisateur.id}"


def _enregistrer_soumission(cx, devoir, proprietaire, utilisateur, type_rendu, lien=None):
    """Crée ou met à jour le rendu du propriétaire ; renvoie son id. Dans une transaction."""
    where, parametres = _filtre(proprietaire)
    ligne = cx.execute(
        f'SELECT id FROM soumissions WHERE devoir_id = ? {where}', (devoir.id, *parametres),
    ).fetchone()
    instant = iso(maintenant())
    if ligne:
        cx.execute(
            'UPDATE soumissions SET type = ?, lien_github = COALESCE(?, lien_github), '
            'deposee_par = ?, date_soumission = ? WHERE id = ?',
            (type_rendu, lien, utilisateur.id, instant, ligne['id']),
        )
        return ligne['id']
    return cx.execute(
        'INSERT INTO soumissions (devoir_id, etudiant_id, groupe_id, deposee_par, type, lien_github, date_soumission) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (devoir.id, proprietaire.get('etudiant_id'), proprietaire.get('groupe_id'), utilisateur.id,
         type_rendu, lien, instant),
    ).lastrowid


@bp.get('/')
@connexion_requise
def liste():
    utilisateur = utilisateur_courant()
    classes = classes_de(utilisateur.id)
    lignes = []
    for classe in classes:
        cx = db.classe(classe.id)
        groupes_ids = {
            a['devoir_id']: a['groupe_id']
            for a in cx.execute(
                'SELECT devoir_id, groupe_id FROM membres_groupe WHERE etudiant_id = ?', (utilisateur.id,),
            )
        }
        rendus = cx.execute(
            'SELECT devoir_id, etudiant_id, groupe_id FROM soumissions WHERE etudiant_id = ? OR groupe_id IN '
            '(SELECT groupe_id FROM membres_groupe WHERE etudiant_id = ?)',
            (utilisateur.id, utilisateur.id),
        ).fetchall()
        par_etudiant = {r['devoir_id'] for r in rendus if r['etudiant_id']}
        par_groupe = {r['groupe_id'] for r in rendus if r['groupe_id']}
        for devoir in devoirs_de(classe):
            if devoir.en_groupe:
                rendu = groupes_ids.get(devoir.id) in par_groupe
            else:
                rendu = devoir.id in par_etudiant
            lignes.append({
                'devoir': devoir,
                'rendu': rendu,
                'sans_groupe': devoir.en_groupe and devoir.id not in groupes_ids,
            })
    lignes.sort(key=lambda ligne: ligne['devoir'].date_limite, reverse=True)
    return render_template('devoirs.html', active_page='devoirs', lignes=lignes, classes=classes)


def _deposer_fichier(devoir, proprietaire, soumission, utilisateur):
    upload = request.files.get('fichier')
    plusieurs = devoir.type_rendu == 'fichiers'
    existants = soumission.fichiers if soumission else []
    max_fichiers = current_app.config['MAX_UPLOAD_FILES']
    if plusieurs:
        # Un fichier du même nom remplace l'ancien ; sinon il s'ajoute.
        nom = nom_affichage(upload.filename) if upload and upload.filename else ''
        remplaces = [f for f in existants if f.nom_original == nom]
        if not remplaces and len(existants) >= max_fichiers:
            flash(f"{max_fichiers} fichiers maximum : supprimez-en un avant d'en ajouter.", 'danger')
            return
    else:
        remplaces = existants

    base = _nom_genere(proprietaire)
    if plusieurs:
        base = f"{base}/{uuid.uuid4().hex}"
    try:
        relatif, nom, taille = enregistrer(upload, devoir.classe_id, devoir.id, base)
    except FichierRefuse as exc:
        flash(str(exc), 'danger')
        journal.warning(
            "Dépôt refusé classe=%s devoir=%s %s raison=%s",
            devoir.classe_id, devoir.id, _qui(proprietaire, utilisateur), exc,
        )
        return

    anciens = [f.chemin for f in remplaces]
    cx = db.classe(devoir.classe_id)
    try:
        with db.transaction(cx):
            soumission_id = _enregistrer_soumission(cx, devoir, proprietaire, utilisateur, devoir.type_rendu)
            if remplaces:
                marques = ','.join('?' * len(remplaces))
                cx.execute(
                    f'DELETE FROM fichiers_rendus WHERE id IN ({marques})', [f.id for f in remplaces],
                )
            cx.execute(
                'INSERT INTO fichiers_rendus (soumission_id, chemin, nom_original, taille, date_depot) '
                'VALUES (?, ?, ?, ?, ?)',
                (soumission_id, relatif, nom, taille, iso(maintenant())),
            )
    except Exception:
        if relatif not in anciens:
            supprimer(devoir.classe_id, relatif)
        raise
    for ancien in anciens:
        if ancien != relatif:
            supprimer(devoir.classe_id, ancien)
    flash("Fichier reçu.", 'success')
    journal.info(
        "Dépôt classe=%s devoir=%s %s fichier=%s",
        devoir.classe_id, devoir.id, _qui(proprietaire, utilisateur), nom,
    )


def _deposer_lien(devoir, proprietaire, utilisateur):
    lien, erreur = valider_lien(request.form.get('lien'))
    if erreur:
        flash(erreur, 'danger')
        journal.warning(
            "Lien refusé classe=%s devoir=%s %s", devoir.classe_id, devoir.id, _qui(proprietaire, utilisateur),
        )
        return
    cx = db.classe(devoir.classe_id)
    with db.transaction(cx):
        _enregistrer_soumission(cx, devoir, proprietaire, utilisateur, 'github', lien)
    flash("Lien enregistré.", 'success')
    journal.info(
        "Dépôt classe=%s devoir=%s %s lien=%s",
        devoir.classe_id, devoir.id, _qui(proprietaire, utilisateur), lien,
    )


@bp.route('/<int:classe_id>/<int:devoir_id>/', methods=['GET', 'POST'])
@connexion_requise
def detail(classe_id, devoir_id):
    utilisateur = utilisateur_courant()
    devoir = _devoir_de_letudiant(utilisateur, classe_id, devoir_id)
    proprietaire = _proprietaire(devoir, utilisateur.id)
    soumission = _ma_soumission(devoir, proprietaire)

    if request.method == 'POST':
        if not devoir.est_ouvert:
            flash("La date limite est dépassée.", 'danger')
        elif proprietaire is None:
            flash("Rejoignez ou créez un groupe pour rendre ce devoir.", 'danger')
        elif devoir.type_rendu == 'github':
            _deposer_lien(devoir, proprietaire, utilisateur)
        else:
            _deposer_fichier(devoir, proprietaire, soumission, utilisateur)
        return redirect(url_for('devoirs.detail', classe_id=classe_id, devoir_id=devoir.id))

    contexte = {
        'active_page': 'devoirs',
        'devoir': devoir,
        'soumission': soumission,
        'fichiers': soumission.fichiers if soumission else [],
    }
    if devoir.en_groupe:
        tous = groupes(devoir)
        mien = proprietaire['groupe_id'] if proprietaire else None
        contexte['mon_groupe'] = next((g for g in tous if g.id == mien), None)
        contexte['groupes'] = tous
    contexte.update(contexte_depot())
    return render_template('devoir.html', **contexte)


def _mon_fichier(devoir, utilisateur, fichier_id):
    proprietaire = _proprietaire(devoir, utilisateur.id)
    if proprietaire is None:
        abort(404)
    where, parametres = _filtre(proprietaire, 's.')
    ligne = db.classe(devoir.classe_id).execute(
        f'SELECT f.* FROM fichiers_rendus f JOIN soumissions s ON s.id = f.soumission_id '
        f'WHERE f.id = ? AND s.devoir_id = ? {where}',
        (fichier_id, devoir.id, *parametres),
    ).fetchone()
    if ligne is None:
        abort(404)
    return FichierRendu.depuis(ligne)


@bp.get('/<int:classe_id>/<int:devoir_id>/fichiers/<int:fichier_id>/')
@connexion_requise
def telecharger(classe_id, devoir_id, fichier_id):
    utilisateur = utilisateur_courant()
    devoir = _devoir_de_letudiant(utilisateur, classe_id, devoir_id)
    fichier = _mon_fichier(devoir, utilisateur, fichier_id)
    try:
        return reponse_fichier(classe_id, fichier)
    except FichierRefuse:
        flash("Fichier introuvable.", 'danger')
        return redirect(url_for('devoirs.detail', classe_id=classe_id, devoir_id=devoir.id))


@bp.post('/<int:classe_id>/<int:devoir_id>/fichiers/<int:fichier_id>/supprimer/')
@connexion_requise
def supprimer_fichier(classe_id, devoir_id, fichier_id):
    utilisateur = utilisateur_courant()
    devoir = _devoir_de_letudiant(utilisateur, classe_id, devoir_id)
    fichier = _mon_fichier(devoir, utilisateur, fichier_id)
    if not devoir.est_ouvert:
        flash("La date limite est dépassée.", 'danger')
    elif devoir.type_rendu != 'fichiers':
        flash("Ce fichier se remplace, il ne se supprime pas.", 'danger')
    else:
        cx = db.classe(classe_id)
        with db.transaction(cx):
            cx.execute('DELETE FROM fichiers_rendus WHERE id = ?', (fichier.id,))
            # Sans fichier, le rendu n'existe plus.
            cx.execute(
                'DELETE FROM soumissions WHERE id = ? AND NOT EXISTS '
                '(SELECT 1 FROM fichiers_rendus WHERE soumission_id = ?)',
                (fichier.soumission_id, fichier.soumission_id),
            )
        supprimer(classe_id, fichier.chemin)
        flash("Fichier supprimé.", 'success')
        journal.info(
            "Fichier supprimé classe=%s devoir=%s etudiant=%s fichier=%s",
            classe_id, devoir.id, utilisateur.id, fichier.nom_original,
        )
    return redirect(url_for('devoirs.detail', classe_id=classe_id, devoir_id=devoir.id))


def _creer_groupe(devoir, utilisateur):
    nom, erreur = valider_nom_groupe(request.form.get('nom'))
    if erreur:
        flash(erreur, 'danger')
        return
    cx = db.classe(devoir.classe_id)
    try:
        with db.transaction(cx):
            pris = cx.execute(
                'SELECT 1 FROM groupes WHERE devoir_id = ? AND lower(nom) = lower(?)', (devoir.id, nom),
            ).fetchone()
            if pris:
                flash("Ce nom de groupe est déjà pris.", 'danger')
                return
            instant = iso(maintenant())
            groupe_id = cx.execute(
                'INSERT INTO groupes (devoir_id, nom, cree_par, date_creation) VALUES (?, ?, ?, ?)',
                (devoir.id, nom, utilisateur.id, instant),
            ).lastrowid
            cx.execute(
                'INSERT INTO membres_groupe (groupe_id, devoir_id, etudiant_id, date_adhesion) VALUES (?, ?, ?, ?)',
                (groupe_id, devoir.id, utilisateur.id, instant),
            )
    except sqlite3.IntegrityError:
        flash("Groupe non créé : nom déjà pris ou groupe déjà rejoint.", 'danger')
        return
    flash(f"Groupe « {nom} » créé.", 'success')
    journal.info(
        "Groupe créé classe=%s devoir=%s groupe=%s etudiant=%s",
        devoir.classe_id, devoir.id, groupe_id, utilisateur.id,
    )


def _rejoindre_groupe(devoir, utilisateur):
    groupe_id = request.form.get('groupe', '')
    if not groupe_id.isdigit():
        flash("Groupe introuvable.", 'danger')
        return
    cx = db.classe(devoir.classe_id)
    try:
        # BEGIN IMMEDIATE : deux adhésions simultanées ne dépassent pas la taille maximale.
        with db.transaction(cx):
            groupe = cx.execute(
                'SELECT * FROM groupes WHERE devoir_id = ? AND id = ?', (devoir.id, int(groupe_id)),
            ).fetchone()
            if groupe is None:
                flash("Groupe introuvable.", 'danger')
                return
            effectif = cx.execute(
                'SELECT count(*) FROM membres_groupe WHERE groupe_id = ?', (groupe['id'],),
            ).fetchone()[0]
            if devoir.taille_groupe_max and effectif >= devoir.taille_groupe_max:
                flash("Ce groupe est complet.", 'danger')
                return
            cx.execute(
                'INSERT INTO membres_groupe (groupe_id, devoir_id, etudiant_id, date_adhesion) VALUES (?, ?, ?, ?)',
                (groupe['id'], devoir.id, utilisateur.id, iso(maintenant())),
            )
    except sqlite3.IntegrityError:
        flash("Vous êtes déjà dans un groupe.", 'danger')
        return
    flash(f"Vous avez rejoint « {groupe['nom']} ».", 'success')
    journal.info(
        "Groupe rejoint classe=%s devoir=%s groupe=%s etudiant=%s",
        devoir.classe_id, devoir.id, groupe['id'], utilisateur.id,
    )


def _quitter_groupe(devoir, groupe, utilisateur):
    cx = db.classe(devoir.classe_id)
    with db.transaction(cx):
        cx.execute(
            'DELETE FROM membres_groupe WHERE devoir_id = ? AND etudiant_id = ?', (devoir.id, utilisateur.id),
        )
        # Un groupe vide sans rendu disparaît ; avec un rendu, il reste visible du professeur.
        supprime = cx.execute(
            'DELETE FROM groupes WHERE id = ? '
            'AND NOT EXISTS (SELECT 1 FROM membres_groupe WHERE groupe_id = ?) '
            'AND NOT EXISTS (SELECT 1 FROM soumissions WHERE groupe_id = ?)',
            (groupe.id, groupe.id, groupe.id),
        ).rowcount > 0
    flash(f"Vous avez quitté « {groupe.nom} ».", 'success')
    journal.info(
        "Groupe quitté classe=%s devoir=%s groupe=%s etudiant=%s supprime=%s",
        devoir.classe_id, devoir.id, groupe.id, utilisateur.id, supprime,
    )


@bp.post('/<int:classe_id>/<int:devoir_id>/groupe/')
@connexion_requise
def groupe(classe_id, devoir_id):
    utilisateur = utilisateur_courant()
    devoir = _devoir_de_letudiant(utilisateur, classe_id, devoir_id)
    if not devoir.en_groupe:
        abort(404)
    if utilisateur.role != 'etudiant':
        flash("Seuls les étudiants forment des groupes.", 'danger')
    elif not devoir.est_ouvert:
        flash("La date limite est dépassée.", 'danger')
    else:
        action = request.form.get('action')
        actuel = _groupe_de(devoir, utilisateur.id)
        if action == 'quitter':
            if actuel is not None:
                _quitter_groupe(devoir, actuel, utilisateur)
        elif actuel is not None:
            flash("Quittez d'abord votre groupe.", 'danger')
        elif action == 'creer':
            _creer_groupe(devoir, utilisateur)
        elif action == 'rejoindre':
            _rejoindre_groupe(devoir, utilisateur)
    return redirect(url_for('devoirs.detail', classe_id=classe_id, devoir_id=devoir.id))
