from django.urls import path

from core import views_devoirs

urlpatterns = [
    path('', views_devoirs.liste_devoirs, name='devoirs_liste'),
    path('<int:devoir_id>/', views_devoirs.detail_devoir, name='devoir_detail'),
    path('<int:devoir_id>/groupe/', views_devoirs.groupe_devoir, name='devoir_groupe'),
    path(
        '<int:devoir_id>/fichiers/<int:fichier_id>/',
        views_devoirs.telecharger_mon_fichier,
        name='devoir_fichier',
    ),
    path(
        '<int:devoir_id>/fichiers/<int:fichier_id>/supprimer/',
        views_devoirs.supprimer_mon_fichier,
        name='devoir_fichier_supprimer',
    ),
]
