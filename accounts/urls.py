# ============================================================
# SPORTLINK — URLs Authentification
# Définit les chemins d'accès aux endpoints d'authentification
# ============================================================

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, LogoutView, MeView

urlpatterns = [
    # POST — Créer un nouveau compte
    path('register/', RegisterView.as_view(), name='auth-register'),

    # POST — Se connecter (retourne les tokens JWT)
    path('login/', LoginView.as_view(), name='auth-login'),

    # POST — Se déconnecter (invalide le refresh token)
    path('logout/', LogoutView.as_view(), name='auth-logout'),

    # POST — Renouveler l'access token avec le refresh token
    # Fourni directement par SimpleJWT — pas besoin de créer la vue
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # GET — Informations de l'utilisateur connecté
    path('me/', MeView.as_view(), name='auth-me'),
]