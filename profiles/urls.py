# ============================================================
# SPORTLINK — URLs Profils
# ============================================================

from django.urls import path
from .views import (
    SportListView, PositionListView,
    ProfileListCreateView, ProfileDetailView, ProfilePublishView,MyProfileView
)

urlpatterns = [
    # GET — Liste des sports disponibles
    path('sports/', SportListView.as_view(), name='sport-list'),

    # GET — Liste des postes (filtrable par ?sport_id=1)
    path('positions/', PositionListView.as_view(), name='position-list'),

    # GET  — Liste des profils publiés avec filtres
    # POST — Créer son profil joueur
    path('profiles/', ProfileListCreateView.as_view(), name='profile-list-create'),


    # GET   — Profil public d'un joueur par son slug
    # PATCH — Modifier son profil
    path('profiles/me/', MyProfileView.as_view(), name='my-profile'),
    path('profiles/<slug:slug>/', ProfileDetailView.as_view(), name='profile-detail'),

    # POST — Publier son profil
    path('profiles/<slug:slug>/publish/', ProfilePublishView.as_view(), name='profile-publish'),
]