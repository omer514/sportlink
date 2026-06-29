# ============================================================
# SPORTLINK — Vues Authentification
# Gère toutes les requêtes liées aux comptes utilisateurs :
# inscription, connexion, déconnexion, confirmation email
# ============================================================

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings
import uuid

from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


# ── INSCRIPTION ───────────────────────────────────────────────
class RegisterView(APIView):
    """
    Endpoint : POST /api/auth/register/
    Crée un nouveau compte utilisateur.
    Accessible sans être connecté (AllowAny).
    """

    # AllowAny = tout le monde peut accéder à cet endpoint
    # même sans token JWT — normal pour l'inscription
    permission_classes = [AllowAny]

    def post(self, request):
        # Passe les données JSON de Flutter au serializer
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            # Crée l'utilisateur en base de données
            user = serializer.save()

            # Pour le MVP : on active le compte directement
            # sans attendre la confirmation email
            # À changer en production pour plus de sécurité
            user.is_active         = True
            user.is_email_verified = True
            user.save()

            # Génère les tokens JWT pour connecter l'utilisateur
            # directement après l'inscription
            refresh = RefreshToken.for_user(user)

            return Response({
                'message'       : 'Compte créé avec succès.',
                'user'          : UserSerializer(user).data,
                # access_token : durée 1h — envoyé dans chaque requête API
                'access_token'  : str(refresh.access_token),
                # refresh_token : durée 7 jours — pour renouveler l'access_token
                'refresh_token' : str(refresh),
            }, status=status.HTTP_201_CREATED)

        # Si le serializer a trouvé des erreurs, les retourner à Flutter
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ── CONNEXION ─────────────────────────────────────────────────
class LoginView(APIView):
    """
    Endpoint : POST /api/auth/login/
    Connecte un utilisateur existant.
    Retourne les tokens JWT si les identifiants sont corrects.
    Accessible sans être connecté (AllowAny).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            # L'utilisateur validé est disponible dans validated_data
            # grâce à la méthode validate() du LoginSerializer
            user = serializer.validated_data['user']

            # Génère de nouveaux tokens JWT pour cette session
            refresh = RefreshToken.for_user(user)

            return Response({
                'message'       : 'Connexion réussie.',
                'user'          : UserSerializer(user).data,
                'access_token'  : str(refresh.access_token),
                'refresh_token' : str(refresh),
            }, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ── DÉCONNEXION ───────────────────────────────────────────────
class LogoutView(APIView):
    """
    Endpoint : POST /api/auth/logout/
    Invalide le refresh token de l'utilisateur.
    Après ça, l'utilisateur doit se reconnecter pour obtenir
    de nouveaux tokens.
    Nécessite d'être connecté (IsAuthenticated).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Récupère le refresh token envoyé par Flutter
            refresh_token = request.data.get('refresh_token')

            if not refresh_token:
                return Response({
                    'error': 'Le refresh token est requis.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Met le token en liste noire — il ne pourra plus être utilisé
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'message': 'Déconnexion réussie.'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Token invalide ou déjà expiré.'
            }, status=status.HTTP_400_BAD_REQUEST)


# ── PROFIL UTILISATEUR CONNECTÉ ───────────────────────────────
class MeView(APIView):
    """
    Endpoint : GET /api/auth/me/
    Retourne les informations de l'utilisateur actuellement connecté.
    Flutter utilise cet endpoint au démarrage de l'app pour
    vérifier si le token est encore valide et récupérer le profil.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user est automatiquement rempli par Django
        # grâce au token JWT envoyé dans le header Authorization
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)