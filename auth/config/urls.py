from django.urls import path, include

from core.urls import urlpatterns_admin

urlpatterns = [
    path('auth/', include('core.urls')),
    path('admin/', include(urlpatterns_admin)),
]
