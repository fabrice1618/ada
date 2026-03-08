from django.urls import path

from core import views, views_admin

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
]
