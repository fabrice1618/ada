from django.urls import path

from core import views

urlpatterns = [
    path('login/', views.connexion, name='connexion'),
    path('logout/', views.deconnexion, name='deconnexion'),
    path('verify/', views.verifier, name='verifier'),
]
