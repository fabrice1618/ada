from django.urls import path, include

from core.urls import urlpatterns_admin
from core.views import accueil

urlpatterns = [
    path('', accueil, name='accueil'),
    path('auth/', include('core.urls')),
    path('admin/', include(urlpatterns_admin)),
    path('devoirs/', include('core.urls_devoirs')),
]
