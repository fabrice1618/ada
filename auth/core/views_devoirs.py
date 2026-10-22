import logging
import tempfile
import uuid
import zipfile
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.fichiers import FichierRefuse, enregistrer, nom_affichage, ouvrir, supprimer
from core.forms import FormulaireDevoir, FormulaireGroupe, FormulaireLienGithub
from core.models import Devoir, FichierRendu, Groupe, MembreGroupe, Soumission

logger = logging.getLogger('auth')


def personnel_requis(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ('admin', 'enseignant'):
            return redirect('devoirs_liste')
        return view(request, *args, **kwargs)
    return wrapper


def _devoir_de_letudiant(request, devoir_id):
    return get_object_or_404(
        Devoir.objects.select_related('classe'),
        id=devoir_id,
        classe__in=request.user.classes.all(),
    )


def _groupe_de(devoir, etudiant):
    return Groupe.objects.filter(devoir=devoir, adhesions__etudiant=etudiant).first()


def _proprietaire(devoir, etudiant):
    # Le rendu appartient à l'étudiant, ou à son groupe ; None : pas encore de groupe.
    if not devoir.en_groupe():
        return {'etudiant': etudiant}
    groupe = _groupe_de(devoir, etudiant)
    if groupe is None:
        return None
    return {'groupe': groupe}


def _nom_genere(proprietaire):
    if 'groupe' in proprietaire:
        return f"g{proprietaire['groupe'].id}"
    return str(proprietaire['etudiant'].id)


def _qui(proprietaire, utilisateur):
    if 'groupe' in proprietaire:
        return f"groupe={proprietaire['groupe'].id} etudiant={utilisateur.id}"
    return f"etudiant={utilisateur.id}"


def _reponse_fichier(fichier):
    chemin = ouvrir(fichier.chemin)
    return FileResponse(
        chemin.open('rb'),
        as_attachment=True,
        filename=fichier.nom_original or 'fichier',
    )


def _contexte_depot():
    return {
        'extensions': ','.join(f'.{ext}' for ext in settings.ALLOWED_EXTENSIONS),
        'taille_max': settings.MAX_UPLOAD_SIZE_MB,
        'max_fichiers': settings.MAX_UPLOAD_FILES,
    }


@login_required
@require_GET
def liste_devoirs(request):
    devoirs = list(
        Devoir.objects.filter(classe__in=request.user.classes.all())
        .select_related('classe')
        .order_by('-date_limite')
    )
    groupes = {
        a.devoir_id: a.groupe_id
        for a in MembreGroupe.objects.filter(etudiant=request.user, devoir__in=devoirs)
    }
    soumissions = Soumission.objects.filter(devoir__in=devoirs).filter(
        Q(etudiant=request.user) | Q(groupe_id__in=groupes.values())
    )
    par_etudiant = {s.devoir_id: s for s in soumissions if s.etudiant_id}
    par_groupe = {s.groupe_id: s for s in soumissions if s.groupe_id}
    lignes = []
    for devoir in devoirs:
        if devoir.en_groupe():
            soumission = par_groupe.get(groupes.get(devoir.id))
        else:
            soumission = par_etudiant.get(devoir.id)
        lignes.append({
            'devoir': devoir,
            'soumission': soumission,
            'sans_groupe': devoir.en_groupe() and devoir.id not in groupes,
        })
    return render(request, 'devoirs.html', {
        'active_page': 'devoirs',
        'lignes': lignes,
    })


def _deposer_fichier(request, devoir, proprietaire, soumission):
    upload = request.FILES.get('fichier')
    plusieurs = devoir.type_rendu == 'fichiers'
    existants = list(soumission.fichiers.all()) if soumission else []
    if plusieurs:
        # Un fichier du même nom remplace l'ancien ; sinon il s'ajoute.
        nom = nom_affichage(upload.name) if upload else ''
        remplaces = [f for f in existants if f.nom_original == nom]
        if not remplaces and len(existants) >= settings.MAX_UPLOAD_FILES:
            messages.error(
                request,
                f"{settings.MAX_UPLOAD_FILES} fichiers maximum : supprimez-en un avant d'en ajouter.",
            )
            return
    else:
        remplaces = existants

    base = _nom_genere(proprietaire)
    if plusieurs:
        base = f"{base}/{uuid.uuid4().hex}"
    try:
        relatif, nom, taille = enregistrer(upload, devoir.id, base)
    except FichierRefuse as exc:
        messages.error(request, str(exc))
        logger.warning(
            "Dépôt refusé devoir=%s %s raison=%s",
            devoir.id, _qui(proprietaire, request.user), exc,
        )
        return

    anciens = [f.chemin for f in remplaces]
    try:
        with transaction.atomic():
            soumission, _cree = Soumission.objects.update_or_create(
                devoir=devoir,
                **proprietaire,
                defaults={
                    'type': devoir.type_rendu,
                    'deposee_par': request.user,
                    'date_soumission': timezone.now(),
                },
            )
            FichierRendu.objects.filter(id__in=[f.id for f in remplaces]).delete()
            FichierRendu.objects.create(
                soumission=soumission,
                chemin=relatif,
                nom_original=nom,
                taille=taille,
            )
    except Exception:
        if relatif not in anciens:
            supprimer(relatif)
        raise
    for ancien in anciens:
        if ancien != relatif:
            supprimer(ancien)
    messages.success(request, "Fichier reçu.")
    logger.info(
        "Dépôt devoir=%s %s fichier=%s",
        devoir.id, _qui(proprietaire, request.user), nom,
    )


def _deposer_lien(request, devoir, proprietaire):
    form = FormulaireLienGithub(request.POST)
    if not form.is_valid():
        for erreur in form.errors.get('lien', []):
            messages.error(request, erreur)
        logger.warning(
            "Lien refusé devoir=%s %s",
            devoir.id, _qui(proprietaire, request.user),
        )
        return
    Soumission.objects.update_or_create(
        devoir=devoir,
        **proprietaire,
        defaults={
            'type': 'github',
            'lien_github': form.cleaned_data['lien'],
            'deposee_par': request.user,
            'date_soumission': timezone.now(),
        },
    )
    messages.success(request, "Lien enregistré.")
    logger.info(
        "Dépôt devoir=%s %s lien=%s",
        devoir.id, _qui(proprietaire, request.user), form.cleaned_data['lien'],
    )


@login_required
@require_http_methods(["GET", "POST"])
def detail_devoir(request, devoir_id):
    devoir = _devoir_de_letudiant(request, devoir_id)
    proprietaire = _proprietaire(devoir, request.user)
    soumission = None
    if proprietaire is not None:
        soumission = (
            Soumission.objects.filter(devoir=devoir, **proprietaire)
            .select_related('deposee_par')
            .prefetch_related('fichiers')
            .first()
        )

    if request.method == 'POST':
        if not devoir.est_ouvert():
            messages.error(request, "La date limite est dépassée.")
        elif proprietaire is None:
            messages.error(request, "Rejoignez ou créez un groupe pour rendre ce devoir.")
        elif devoir.type_rendu == 'github':
            _deposer_lien(request, devoir, proprietaire)
        else:
            _deposer_fichier(request, devoir, proprietaire, soumission)
        return redirect('devoir_detail', devoir_id=devoir.id)

    contexte = {
        'active_page': 'devoirs',
        'devoir': devoir,
        'soumission': soumission,
        'fichiers': list(soumission.fichiers.all()) if soumission else [],
        'form_lien': FormulaireLienGithub(
            initial={'lien': soumission.lien_github} if soumission else None
        ),
    }
    if devoir.en_groupe():
        contexte['mon_groupe'] = proprietaire['groupe'] if proprietaire else None
        contexte['groupes'] = (
            devoir.groupes.annotate(nb_membres=Count('adhesions'))
            .prefetch_related('membres')
            .order_by('nom')
        )
        contexte['form_groupe'] = FormulaireGroupe()
    contexte.update(_contexte_depot())
    return render(request, 'devoir.html', contexte)


def _mon_fichier(request, devoir, fichier_id):
    proprietaire = _proprietaire(devoir, request.user)
    if proprietaire is None:
        raise Http404
    filtres = {f'soumission__{cle}': valeur for cle, valeur in proprietaire.items()}
    return get_object_or_404(
        FichierRendu.objects.select_related('soumission'),
        id=fichier_id,
        soumission__devoir=devoir,
        **filtres,
    )


@login_required
@require_GET
def telecharger_mon_fichier(request, devoir_id, fichier_id):
    devoir = _devoir_de_letudiant(request, devoir_id)
    fichier = _mon_fichier(request, devoir, fichier_id)
    try:
        return _reponse_fichier(fichier)
    except FichierRefuse:
        messages.error(request, "Fichier introuvable.")
        return redirect('devoir_detail', devoir_id=devoir.id)


@login_required
@require_POST
def supprimer_mon_fichier(request, devoir_id, fichier_id):
    devoir = _devoir_de_letudiant(request, devoir_id)
    fichier = _mon_fichier(request, devoir, fichier_id)
    if not devoir.est_ouvert():
        messages.error(request, "La date limite est dépassée.")
    elif devoir.type_rendu != 'fichiers':
        messages.error(request, "Ce fichier se remplace, il ne se supprime pas.")
    else:
        with transaction.atomic():
            soumission = fichier.soumission
            fichier.delete()
            # Sans fichier, le rendu n'existe plus.
            if not soumission.fichiers.exists():
                soumission.delete()
        supprimer(fichier.chemin)
        messages.success(request, "Fichier supprimé.")
        logger.info(
            "Fichier supprimé devoir=%s etudiant=%s fichier=%s",
            devoir.id, request.user.id, fichier.nom_original,
        )
    return redirect('devoir_detail', devoir_id=devoir.id)


def _creer_groupe(request, devoir):
    form = FormulaireGroupe(request.POST)
    if not form.is_valid():
        for erreur in form.errors.get('nom', []):
            messages.error(request, erreur)
        return
    nom = form.cleaned_data['nom']
    if Groupe.objects.filter(devoir=devoir, nom__iexact=nom).exists():
        messages.error(request, "Ce nom de groupe est déjà pris.")
        return
    try:
        with transaction.atomic():
            groupe = Groupe.objects.create(devoir=devoir, nom=nom, cree_par=request.user)
            MembreGroupe.objects.create(groupe=groupe, devoir=devoir, etudiant=request.user)
    except IntegrityError:
        messages.error(request, "Groupe non créé : nom déjà pris ou groupe déjà rejoint.")
        return
    messages.success(request, f"Groupe « {nom} » créé.")
    logger.info(
        "Groupe créé devoir=%s groupe=%s etudiant=%s",
        devoir.id, groupe.id, request.user.id,
    )


def _rejoindre_groupe(request, devoir):
    groupe_id = request.POST.get('groupe', '')
    if not groupe_id.isdigit():
        messages.error(request, "Groupe introuvable.")
        return
    try:
        with transaction.atomic():
            groupe = Groupe.objects.select_for_update().filter(devoir=devoir, id=groupe_id).first()
            if groupe is None:
                messages.error(request, "Groupe introuvable.")
                return
            taille_max = devoir.taille_groupe_max
            if taille_max and groupe.adhesions.count() >= taille_max:
                messages.error(request, "Ce groupe est complet.")
                return
            MembreGroupe.objects.create(groupe=groupe, devoir=devoir, etudiant=request.user)
    except IntegrityError:
        messages.error(request, "Vous êtes déjà dans un groupe.")
        return
    messages.success(request, f"Vous avez rejoint « {groupe.nom} ».")
    logger.info(
        "Groupe rejoint devoir=%s groupe=%s etudiant=%s",
        devoir.id, groupe.id, request.user.id,
    )


def _quitter_groupe(request, devoir, groupe):
    with transaction.atomic():
        MembreGroupe.objects.filter(devoir=devoir, etudiant=request.user).delete()
        # Un groupe vide sans rendu disparaît ; avec un rendu, il reste visible du professeur.
        supprime = not groupe.adhesions.exists() and not groupe.soumissions.exists()
        if supprime:
            groupe.delete()
    messages.success(request, f"Vous avez quitté « {groupe.nom} ».")
    logger.info(
        "Groupe quitté devoir=%s groupe=%s etudiant=%s supprime=%s",
        devoir.id, groupe.id, request.user.id, supprime,
    )


@login_required
@require_POST
def groupe_devoir(request, devoir_id):
    devoir = _devoir_de_letudiant(request, devoir_id)
    if not devoir.en_groupe():
        raise Http404
    if request.user.role != 'etudiant':
        messages.error(request, "Seuls les étudiants forment des groupes.")
    elif not devoir.est_ouvert():
        messages.error(request, "La date limite est dépassée.")
    else:
        action = request.POST.get('action')
        actuel = _groupe_de(devoir, request.user)
        if action == 'quitter':
            if actuel is not None:
                _quitter_groupe(request, devoir, actuel)
        elif actuel is not None:
            messages.error(request, "Quittez d'abord votre groupe.")
        elif action == 'creer':
            _creer_groupe(request, devoir)
        elif action == 'rejoindre':
            _rejoindre_groupe(request, devoir)
    return redirect('devoir_detail', devoir_id=devoir.id)


def _initial_devoir(devoir):
    return {
        'titre': devoir.titre,
        'description': devoir.description,
        'date_limite': timezone.localtime(devoir.date_limite),
        'type_rendu': devoir.type_rendu,
        'mode': devoir.mode,
        'taille_groupe_max': devoir.taille_groupe_max or 3,
    }


@personnel_requis
@require_http_methods(["GET", "POST"])
def gestion_devoirs(request):
    if request.method == 'POST':
        form = FormulaireDevoir(request.POST)
        if form.is_valid():
            devoir = Devoir.objects.create(
                classe=form.cleaned_data['classe'],
                titre=form.cleaned_data['titre'],
                description=form.cleaned_data['description'],
                date_limite=form.cleaned_data['date_limite'],
                type_rendu=form.cleaned_data['type_rendu'],
                mode=form.cleaned_data['mode'],
                taille_groupe_max=form.cleaned_data['taille_groupe_max'],
                cree_par=request.user,
            )
            messages.success(request, "Devoir créé.")
            logger.info(
                "Devoir créé id=%s classe=%s type=%s mode=%s par=%s",
                devoir.id, devoir.classe_id, devoir.type_rendu, devoir.mode, request.user.id,
            )
            return redirect('devoir_suivi', devoir_id=devoir.id)
    else:
        initial = {}
        classe = request.GET.get('classe', '')
        if classe.isdigit():
            initial['classe'] = int(classe)
        form = FormulaireDevoir(initial=initial)

    devoirs = (
        Devoir.objects.select_related('classe')
        .annotate(
            nb_rendus=Count('soumissions', distinct=True),
            nb_groupes=Count('groupes', distinct=True),
            nb_etudiants=Count(
                'classe__utilisateurs',
                filter=Q(classe__utilisateurs__role='etudiant'),
                distinct=True,
            ),
        )
        .order_by('-date_limite')
    )
    return render(request, 'devoirs_gestion.html', {
        'active_page': 'devoirs',
        'form': form,
        'devoirs': devoirs,
    })


@personnel_requis
@require_http_methods(["GET", "POST"])
def suivi_devoir(request, devoir_id):
    devoir = get_object_or_404(Devoir.objects.select_related('classe'), id=devoir_id)
    options = {
        'avec_classe': False,
        'verrouille': devoir.soumissions.exists(),
        'taille_min': devoir.groupes.annotate(n=Count('adhesions')).aggregate(m=Max('n'))['m'],
        'initial': _initial_devoir(devoir),
    }
    if request.method == 'POST':
        form = FormulaireDevoir(request.POST, **options)
        if form.is_valid():
            for champ in ('titre', 'description', 'date_limite', 'type_rendu', 'mode', 'taille_groupe_max'):
                setattr(devoir, champ, form.cleaned_data[champ])
            devoir.save()
            messages.success(request, "Devoir mis à jour.")
            logger.info(
                "Devoir modifié id=%s type=%s mode=%s par=%s",
                devoir.id, devoir.type_rendu, devoir.mode, request.user.id,
            )
            return redirect('devoir_suivi', devoir_id=devoir.id)
    else:
        form = FormulaireDevoir(**options)

    soumissions = list(
        devoir.soumissions.select_related('deposee_par').prefetch_related('fichiers')
    )
    etudiants = devoir.classe.utilisateurs.filter(role='etudiant').order_by('nom_complet')
    contexte = {
        'active_page': 'devoirs',
        'devoir': devoir,
        'form': form,
    }
    if devoir.en_groupe():
        par_groupe = {s.groupe_id: s for s in soumissions if s.groupe_id}
        groupes = devoir.groupes.prefetch_related('membres').order_by('nom')
        lignes = [{'groupe': g, 'soumission': par_groupe.get(g.id)} for g in groupes]
        contexte['sans_groupe'] = etudiants.exclude(adhesions__devoir=devoir)
    else:
        par_etudiant = {s.etudiant_id: s for s in soumissions if s.etudiant_id}
        lignes = [{'etudiant': e, 'soumission': par_etudiant.get(e.id)} for e in etudiants]
    contexte['lignes'] = lignes
    contexte['nb_rendus'] = sum(1 for ligne in lignes if ligne['soumission'])
    return render(request, 'devoir_suivi.html', contexte)


@personnel_requis
@require_GET
def telecharger_soumission(request, devoir_id, fichier_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    fichier = get_object_or_404(FichierRendu, id=fichier_id, soumission__devoir=devoir)
    try:
        return _reponse_fichier(fichier)
    except FichierRefuse:
        messages.error(request, "Fichier introuvable.")
        return redirect('devoir_suivi', devoir_id=devoir.id)


def _nom_archive(nom):
    nom = Path(nom or 'fichier').name.replace('\x00', '')
    return nom.replace('/', '_').replace('\\', '_') or 'fichier'


@personnel_requis
@require_GET
def archive_devoir(request, devoir_id):
    devoir = get_object_or_404(Devoir, id=devoir_id)
    temporaire = tempfile.NamedTemporaryFile(suffix='.zip')
    ecrits = 0
    soumissions = devoir.soumissions.select_related('groupe').prefetch_related('fichiers')
    with zipfile.ZipFile(temporaire, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for soumission in soumissions:
            if soumission.groupe_id:
                prefixe = f"groupe-{soumission.groupe_id}-{slugify(soumission.groupe.nom) or 'sans-nom'}"
            else:
                prefixe = str(soumission.etudiant_id)
            # Un fichier : <prefixe>_<nom> ; plusieurs : un dossier <prefixe>/.
            dossier = soumission.type == 'fichiers'
            vus = set()
            for fichier in soumission.fichiers.all():
                try:
                    chemin = ouvrir(fichier.chemin)
                except FichierRefuse:
                    continue
                nom = _nom_archive(fichier.nom_original)
                if nom in vus:
                    nom = f"{fichier.id}_{nom}"
                vus.add(nom)
                archive.write(chemin, arcname=f"{prefixe}/{nom}" if dossier else f"{prefixe}_{nom}")
                ecrits += 1
    if ecrits == 0:
        temporaire.close()
        messages.error(request, "Aucun fichier à archiver.")
        return redirect('devoir_suivi', devoir_id=devoir.id)
    temporaire.seek(0)
    return FileResponse(
        temporaire,
        as_attachment=True,
        filename=f"devoir-{devoir.id}.zip",
        content_type='application/zip',
    )
