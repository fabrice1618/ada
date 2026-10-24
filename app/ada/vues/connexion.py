import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ada.comptes import (
    adresse_ip, authentifier, changer_mot_de_passe, connexion_requise, destination,
    fermer_autres_sessions, fermer_session, ouvrir_session, redirection_sure, utilisateur_courant,
    verifier_mot_de_passe,
)
from ada import db
from ada.modeles import classes_de

bp = Blueprint('connexion', __name__)
journal = logging.getLogger('ada')


@bp.get('/')
def accueil():
    utilisateur = utilisateur_courant()
    if utilisateur is None:
        return redirect(url_for('connexion.connexion'))
    return redirect(destination(utilisateur))


@bp.route('/auth/login/', methods=['GET', 'POST'])
def connexion():
    utilisateur = utilisateur_courant()
    if utilisateur is not None:
        return redirect(destination(utilisateur))

    erreur = None
    email = ''
    suivant = request.values.get('next', '')
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        mot_de_passe = request.form.get('mot_de_passe', '')
        utilisateur = authentifier(email, mot_de_passe) if email and mot_de_passe else None
        if utilisateur is not None:
            ouvrir_session(utilisateur)
            journal.info("Connexion réussie utilisateur=%s ip=%s", utilisateur.id, adresse_ip())
            return redirect(suivant if redirection_sure(suivant) else destination(utilisateur))
        erreur = "Email ou mot de passe incorrect."
        journal.warning("Connexion échouée email=%s ip=%s", email, adresse_ip())
    return render_template('login.html', erreur=erreur, email=email, suivant=suivant)


@bp.get('/auth/logout/')
def deconnexion():
    utilisateur = utilisateur_courant()
    fermer_session()
    journal.info("Déconnexion utilisateur=%s ip=%s", utilisateur.id if utilisateur else '-', adresse_ip())
    return redirect(url_for('connexion.connexion'))


@bp.route('/auth/profil/', methods=['GET', 'POST'])
@connexion_requise
def profil():
    utilisateur = utilisateur_courant()
    if request.method == 'POST':
        ancien = request.form.get('ancien_mdp', '')
        nouveau = request.form.get('nouveau_mdp', '')
        confirmation = request.form.get('confirmation_mdp', '')
        hache = db.commun().execute(
            'SELECT mot_de_passe FROM utilisateurs WHERE id = ?', (utilisateur.id,),
        ).fetchone()['mot_de_passe']

        if not verifier_mot_de_passe(hache, ancien):
            flash("Mot de passe actuel incorrect.", 'danger')
        elif len(nouveau) < 8:
            flash("Le nouveau mot de passe doit contenir au moins 8 caractères.", 'danger')
        elif nouveau != confirmation:
            flash("Les mots de passe ne correspondent pas.", 'danger')
        else:
            changer_mot_de_passe(utilisateur.id, nouveau)
            # Les autres appareils connectés doivent se reconnecter.
            fermer_autres_sessions(utilisateur.id)
            flash("Mot de passe modifié avec succès.", 'success')
            journal.info("Mot de passe modifié utilisateur=%s", utilisateur.id)

    return render_template('profil.html', active_page='profil', classes=classes_de(utilisateur.id))
