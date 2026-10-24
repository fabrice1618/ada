"""Ada : connexion, classes, devoirs, pages de cours. Flask + une base SQLite par classe."""
import logging
import sys

from flask import Flask, abort, flash, redirect, render_template, request
from markupsafe import Markup, escape
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from ada import config, db
from ada.comptes import csrf_valide, jeton_csrf, utilisateur_courant
from ada.temps import local


def configurer_journal():
    # stdout seulement : le driver syslog du conteneur l'envoie à argos.
    journal = logging.getLogger('ada')
    if not journal.handlers:
        sortie = logging.StreamHandler(sys.stdout)
        sortie.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S'))
        journal.addHandler(sortie)
        journal.setLevel(logging.INFO)
        journal.propagate = False
    return journal


def _date_fr(valeur, format='%d/%m/%Y %H:%M'):
    if not valeur:
        return ''
    if hasattr(valeur, 'tzinfo'):
        valeur = local(valeur)
    return valeur.strftime(format)


def _pluriel(nombre, suffixe='s'):
    return suffixe if nombre != 1 else ''


def _paragraphes(texte):
    blocs = [b for b in str(texte or '').replace('\r\n', '\n').split('\n\n') if b.strip()]
    return Markup(''.join(
        f"<p>{Markup('<br>').join(escape(ligne) for ligne in bloc.strip().split(chr(10)))}</p>"
        for bloc in blocs
    ))


def _taille(octets):
    taille = float(octets or 0)
    for unite in ('octets', 'Ko', 'Mo', 'Go'):
        if taille < 1024 or unite == 'Go':
            return f"{int(taille)} {unite}" if unite == 'octets' else f"{taille:.1f} {unite}".replace('.', ',')
        taille /= 1024


def create_app(surcharges=None):
    app = Flask(__name__)
    app.config.from_mapping(config.depuis_environnement())
    if surcharges:
        app.config.from_mapping(surcharges)
    if not app.config['SECRET_KEY']:
        raise RuntimeError("SECRET_KEY absent : le définir dans .env.")
    # Derrière le reverse proxy d'argos : schéma, hôte et IP du client viennent des en-têtes.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    configurer_journal()

    app.teardown_appcontext(db.fermer)
    app.jinja_env.filters.update(
        date_fr=_date_fr, pluriel=_pluriel, paragraphes=_paragraphes, taille=_taille,
    )

    @app.context_processor
    def _contexte():
        return {'utilisateur': utilisateur_courant(), 'csrf_jeton': jeton_csrf}

    @app.before_request
    def _csrf():
        if request.method == 'POST' and not csrf_valide():
            abort(400, "Formulaire expiré : rechargez la page.")

    @app.errorhandler(RequestEntityTooLarge)
    def _trop_gros(_exc):
        flash("Le fichier dépasse la taille maximale.", 'danger')
        return redirect(request.path)

    @app.errorhandler(403)
    def _interdit(_exc):
        return render_template('forbidden.html'), 403

    from ada.vues import admin, connexion, cours, devoirs, enseignant
    for module in (connexion, cours, devoirs, enseignant, admin):
        app.register_blueprint(module.bp)

    from ada import commandes
    commandes.enregistrer(app)
    return app
