import logging
from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from core.forms import FormulaireConnexion
from core.models import Creneau

logger = logging.getLogger('auth')


def destination(user):
    if user.role == 'admin':
        return 'gestion'
    if user.role == 'enseignant':
        return 'devoirs_gestion'
    return 'devoirs_liste'


def _redirige_apres_connexion(request, user):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(destination(user))


def accueil(request):
    if not request.user.is_authenticated:
        return redirect('connexion')
    return redirect(destination(request.user))


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@require_http_methods(["GET", "POST"])
def connexion(request):
    if request.user.is_authenticated:
        return redirect(destination(request.user))

    if request.method == 'POST':
        form = FormulaireConnexion(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            mot_de_passe = form.cleaned_data['mot_de_passe']
            user = authenticate(request, username=email, password=mot_de_passe)
            if user is not None:
                login(request, user)
                ip = _get_client_ip(request)
                logger.info(
                    "Connexion réussie",
                    extra={'user': user.id, 'classe': '-', 'ip': ip,
                           'method': 'POST', 'path': '/auth/login/', 'status': 200}
                )
                return _redirige_apres_connexion(request, user)
            else:
                form.add_error(None, "Email ou mot de passe incorrect.")
                logger.warning(
                    "Tentative de connexion échouée",
                    extra={'user': email, 'classe': '-', 'ip': _get_client_ip(request),
                           'method': 'POST', 'path': '/auth/login/', 'status': 401}
                )
    else:
        form = FormulaireConnexion()

    return render(request, 'login.html', {'form': form})


def deconnexion(request):
    ip = _get_client_ip(request)
    user_id = request.user.id if request.user.is_authenticated else '-'
    logout(request)
    logger.info(
        "Déconnexion",
        extra={'user': user_id, 'classe': '-', 'ip': ip,
               'method': 'GET', 'path': '/auth/logout/', 'status': 200}
    )
    return redirect('/auth/login/')


def verifier(request):
    """Endpoint Forward Auth pour Traefik.
    Retourne 200 si l'utilisateur est authentifié et a un créneau ouvert,
    403 sinon.
    """
    ip = _get_client_ip(request)

    if not request.user.is_authenticated:
        logger.warning(
            "Vérification échouée : non authentifié",
            extra={'user': '-', 'classe': '-', 'ip': ip,
                   'method': request.method, 'path': request.get_full_path(), 'status': 403}
        )
        return HttpResponse(status=403)

    # Récupérer le chemin original depuis les headers Traefik
    original_path = request.META.get('HTTP_X_FORWARDED_URI', '')
    user = request.user
    now = datetime.now()

    # Vérifier si un créneau est ouvert pour au moins une classe de l'utilisateur
    # Les admins et enseignants passent sans vérification de créneau
    if user.role in ('admin', 'enseignant'):
        return HttpResponse(status=200)

    classes_ids = list(user.classes.values_list('id', flat=True))
    if not classes_ids:
        logger.warning(
            "Vérification échouée : aucune classe",
            extra={'user': user.id, 'classe': '-', 'ip': ip,
                   'method': request.method, 'path': original_path, 'status': 403}
        )
        return HttpResponse(status=403)

    creneau_ouvert = Creneau.objects.filter(
        classe_id__in=classes_ids,
        type_ressource='page',
        chemin_page=original_path,
        ouverture__lte=now,
        fermeture__gte=now,
    ).exists()

    if creneau_ouvert:
        return HttpResponse(status=200)

    logger.warning(
        "Créneau fermé",
        extra={'user': user.id, 'classe': '-', 'ip': ip,
               'method': request.method, 'path': original_path, 'status': 403}
    )
    return HttpResponse(status=403)
