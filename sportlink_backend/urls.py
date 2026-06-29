# ============================================================
# SPORTLINK — URLs Principales
# Point d'entrée de toutes les URLs du projet.
# Regroupe les URLs de chaque application.
# ============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panneau d'administration Django
    # Accessible sur : http://127.0.0.1:8000/admin/
    path('admin/', admin.site.urls),

    # URLs des applications SportLink
    # Toutes les routes API commencent par /api/
    path('api/auth/',  include('accounts.urls')),   # /api/auth/register/, login/, etc.
    path('api/',       include('profiles.urls')),   # /api/profiles/, /api/sports/, etc.
    path('api/',       include('media.urls')),      # /api/profiles/<slug>/media/
    path('api/',       include('feed.urls')),       # /api/feed/
]

# En développement : sert les fichiers média uploadés localement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)