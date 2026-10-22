from django.urls import path

from core import views, views_admin, views_devoirs

# Routes sous /auth/
urlpatterns = [
    path('login/', views.connexion, name='connexion'),
    path('logout/', views.deconnexion, name='deconnexion'),
    path('verify/', views.verifier, name='verifier'),
    path('profil/', views_admin.profil, name='profil'),
]

# Routes sous /admin/
urlpatterns_admin = [
    path('', views_admin.gestion, name='gestion'),
    path('classes/<int:classe_id>/', views_admin.detail_classe, name='detail_classe'),
    path('classes/<int:classe_id>/archive/', views_admin.archive_classe, name='classe_archive'),
    path('classes/<int:classe_id>/supprimer/', views_admin.supprimer_classe, name='classe_supprimer'),
    path('devoirs/', views_devoirs.gestion_devoirs, name='devoirs_gestion'),
    path('devoirs/<int:devoir_id>/', views_devoirs.suivi_devoir, name='devoir_suivi'),
    path('devoirs/<int:devoir_id>/archive/', views_devoirs.archive_devoir, name='devoir_archive'),
    path(
        'devoirs/<int:devoir_id>/fichiers/<int:fichier_id>/',
        views_devoirs.telecharger_soumission,
        name='soumission_fichier',
    ),
]
