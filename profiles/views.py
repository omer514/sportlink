# ============================================================
# SPORTLINK — Vues Profils
# Gère toutes les requêtes liées aux profils joueurs,
# recruteurs, sports et positions
# ============================================================

from rest_framework import status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from .models import Sport, Position, Profile, RecruiterProfile
from .serializers import (
    SportSerializer, PositionSerializer,
    ProfileReadSerializer, ProfileWriteSerializer,
    RecruiterProfileSerializer
)


# ── PERMISSION PERSONNALISÉE ──────────────────────────────────
class IsRecruiterValidated(IsAuthenticated):
    """
    Permission personnalisée : vérifie que l'utilisateur est
    un recruteur validé par l'admin.
    Utilisée pour protéger les endpoints de recherche avancée.
    """
    def has_permission(self, request, view):
        # Vérifie d'abord que l'utilisateur est connecté
        if not super().has_permission(request, view):
            return False
        # Ensuite vérifie qu'il est recruteur et validé
        if request.user.role == 'recruteur':
            try:
                return request.user.recruiter_profile.is_validated
            except RecruiterProfile.DoesNotExist:
                return False
        # Les admins ont toujours accès
        return request.user.is_staff


# ── SPORTS ────────────────────────────────────────────────────
class SportListView(generics.ListAPIView):
    """
    Endpoint : GET /api/sports/
    Retourne la liste de tous les sports.
    Flutter utilise ça pour afficher les disciplines disponibles
    (Football actif, autres grisés).
    Accessible sans connexion.
    """
    queryset         = Sport.objects.all()
    serializer_class = SportSerializer
    permission_classes = [AllowAny]


# ── POSITIONS ─────────────────────────────────────────────────
class PositionListView(generics.ListAPIView):
    """
    Endpoint : GET /api/positions/?sport_id=1
    Retourne les postes disponibles pour un sport donné.
    Flutter utilise ça pour construire le menu dynamique
    Catégorie → Poste dans le formulaire de profil.
    Accessible sans connexion.
    """
    serializer_class   = PositionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Position.objects.all()
        # Filtre par sport si le paramètre sport_id est fourni
        # Ex : /api/positions/?sport_id=1 retourne tous les postes de football
        sport_id = self.request.query_params.get('sport_id')
        if sport_id:
            queryset = queryset.filter(sport_id=sport_id)
        return queryset


# ── LISTE ET CRÉATION DE PROFILS ──────────────────────────────
class ProfileListCreateView(APIView):
    """
    GET  /api/profiles/ — Liste tous les profils publiés avec filtres
    POST /api/profiles/ — Crée le profil du joueur connecté
    """

    # Pour les uploads de fichiers (photos, documents)
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        """
        GET : accessible à tous (recruteurs, joueurs, visiteurs)
        POST : réservé aux utilisateurs connectés
        """
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        """
        Liste les profils publiés avec filtres optionnels.
        Tous les paramètres de filtre sont optionnels.
        """
        # Ne retourne que les profils publiés
        queryset = Profile.objects.filter(is_published=True)

        # ── Filtres disponibles ───────────────────────────────
        # Chaque filtre est appliqué seulement si le paramètre est présent

        # Filtre par poste principal
        poste = request.query_params.get('poste')
        if poste:
            queryset = queryset.filter(position__nom_poste__icontains=poste)
            # icontains = insensible à la casse

        # Filtre par poste secondaire
        poste_sec = request.query_params.get('poste_secondaire')
        if poste_sec:
            queryset = queryset.filter(
                position_secondaire__nom_poste__icontains=poste_sec
            )

        # Filtre par ville
        ville = request.query_params.get('ville')
        if ville:
            queryset = queryset.filter(ville__icontains=ville)

        # Filtre par pied fort
        pied = request.query_params.get('pied_fort')
        if pied:
            queryset = queryset.filter(pied_fort=pied)

        # Filtre par statut de club
        statut_club = request.query_params.get('statut_club')
        if statut_club:
            queryset = queryset.filter(statut_club=statut_club)

        # Filtre profils vérifiés uniquement
        is_verified = request.query_params.get('is_verified')
        if is_verified == 'true':
            queryset = queryset.filter(is_verified=True)

        # Filtre par catégorie d'âge
        # Calcul fait en Python car SQL ne calcule pas l'âge facilement
        categorie_age = request.query_params.get('categorie_age')
        if categorie_age:
            # Filtre les profils dont la catégorie correspond
            ids = [
                p.id for p in queryset
                if p.get_categorie_age() == categorie_age
            ]
            queryset = queryset.filter(id__in=ids)

        # Recherche full-text sur nom, ville et club
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(nom_complet__icontains=search) |
                Q(ville__icontains=search)        |
                Q(nom_club__icontains=search)
            )

        # ── Tri ───────────────────────────────────────────────
        ordering = request.query_params.get('ordering', '-created_at')
        # Valeurs autorisées pour éviter les injections
        orderings_autorises = [
            'created_at', '-created_at',
            'profile_views', '-profile_views'
        ]
        if ordering in orderings_autorises:
            queryset = queryset.order_by(ordering)

        # ── Pagination manuelle ───────────────────────────────
        # 20 profils par page
        page      = int(request.query_params.get('page', 1))
        page_size = 20
        start     = (page - 1) * page_size
        end       = start + page_size
        total     = queryset.count()

        serializer = ProfileReadSerializer(
            queryset[start:end],
            many=True,
            context={'request': request}
        )

        return Response({
            'total'    : total,
            'page'     : page,
            'pages'    : (total + page_size - 1) // page_size,
            'results'  : serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Crée le profil du joueur connecté.
        Un joueur ne peut avoir qu'un seul profil.
        """
        # Vérifie que l'utilisateur est bien un talent (joueur)
        if request.user.role != 'talent':
            return Response({
                'error': 'Seuls les joueurs peuvent créer un profil.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Vérifie qu'il n'a pas déjà un profil
        if hasattr(request.user, 'profile'):
            return Response({
                'error': 'Vous avez déjà un profil. Utilisez PATCH pour le modifier.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProfileWriteSerializer(
            data=request.data,
            # Le contexte passe la requête au serializer
            # pour qu'il puisse accéder à request.user
            context={'request': request}
        )

        if serializer.is_valid():
            profile = serializer.save()
            return Response(
                ProfileReadSerializer(profile, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── DÉTAIL, MODIFICATION ET PUBLICATION D'UN PROFIL ──────────
class ProfileDetailView(APIView):
    """
    GET   /api/profiles/<slug>/ — Profil public d'un joueur
    PATCH /api/profiles/<slug>/ — Modification partielle du profil
    """

    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self, slug):
        """
        Récupère le profil par son slug.
        Retourne 404 automatiquement si le slug n'existe pas.
        """
        return get_object_or_404(Profile, slug=slug)

    def get(self, request, slug):
        """
        Affiche le profil public d'un joueur.
        Incrémente le compteur de vues à chaque consultation.
        """
        profile = self.get_object(slug)

        # Vérifie que le profil est publié
        # Sauf si c'est le propriétaire ou un admin qui consulte
        if not profile.is_published:
            if not request.user.is_authenticated:
                return Response({
                    'error': 'Ce profil n\'est pas encore publié.'
                }, status=status.HTTP_404_NOT_FOUND)
            if request.user != profile.user and not request.user.is_staff:
                return Response({
                    'error': 'Ce profil n\'est pas encore publié.'
                }, status=status.HTTP_404_NOT_FOUND)

        # Incrémente le compteur de vues
        # update_fields évite de sauvegarder tout le profil inutilement
        Profile.objects.filter(slug=slug).update(
            profile_views=profile.profile_views + 1
        )

        serializer = ProfileReadSerializer(
            profile,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, slug):
        """
        Modifie partiellement le profil.
        Seul le propriétaire peut modifier son propre profil.
        """
        profile = self.get_object(slug)

        # Vérifie que c'est bien le propriétaire
        if request.user != profile.user:
            return Response({
                'error': 'Vous ne pouvez modifier que votre propre profil.'
            }, status=status.HTTP_403_FORBIDDEN)

        # partial=True : seuls les champs envoyés sont modifiés
        # Pas besoin d'envoyer tout le profil pour changer une seule info
        serializer = ProfileWriteSerializer(
            profile,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            profile = serializer.save()
            return Response(
                ProfileReadSerializer(profile, context={'request': request}).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── PUBLICATION DU PROFIL ─────────────────────────────────────
class ProfilePublishView(APIView):
    """
    Endpoint : POST /api/profiles/<slug>/publish/
    Rend le profil visible publiquement dans le feed et la recherche.
    Vérifie que toutes les conditions sont remplies avant de publier.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        profile = get_object_or_404(Profile, slug=slug)

        # Seul le propriétaire peut publier son profil
        if request.user != profile.user:
            return Response({
                'error': 'Action non autorisée.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Un profil mineur ne peut pas être publié sans consentement validé
        if profile.is_minor and not profile.is_minor_consent_validated:
            return Response({
                'error': (
                    'Votre profil ne peut pas être publié. '
                    'Le consentement parental est en attente de validation '
                    'par l\'administration SportLink.'
                )
            }, status=status.HTTP_403_FORBIDDEN)

        # Publie le profil
        profile.is_published = True
        profile.save(update_fields=['is_published'])

        return Response({
            'message' : 'Profil publié avec succès. Il est maintenant visible dans le feed.',
            'slug'    : profile.slug,
        }, status=status.HTTP_200_OK)
        
        
# ── MON PROFIL (UTILISATEUR CONNECTÉ) ─────────────────────────
class MyProfileView(APIView):
    """
    Endpoint : GET /api/profiles/me/
    Retourne le profil de l'utilisateur connecté.
    Si l'utilisateur n'a pas encore de profil, retourne 404
    avec un message explicite (Flutter affichera un écran
    "créer mon profil" dans ce cas).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Vérifie que l'utilisateur a bien un profil lié
        if not hasattr(request.user, 'profile'):
            return Response({
                'error': 'Vous n\'avez pas encore créé de profil.',
                'has_profile': False,
            }, status=status.HTTP_404_NOT_FOUND)

        profile = request.user.profile
        serializer = ProfileReadSerializer(
            profile,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
        
        