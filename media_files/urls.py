# ============================================================
# SPORTLINK — URLs Media
# ============================================================

from django.urls import path
from .views import MediaListCreateView, MediaDeleteView

urlpatterns = [
    # GET  — Liste les médias d'un profil
    # POST — Ajoute un média au profil
    path('profiles/<slug:slug>/media/', MediaListCreateView.as_view(), name='media-list-create'),

    # DELETE — Supprime un média
    # PATCH  — Modifie l'ordre d'un média
    path('media/<int:pk>/', MediaDeleteView.as_view(), name='media-detail'),
]