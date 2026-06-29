# ============================================================
# SPORTLINK — Vues Feed
# Le feed de découverte style TikTok
# Visible par tout le monde : joueurs, recruteurs, visiteurs
# ============================================================

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from profiles.models import Profile
from profiles.serializers import ProfileReadSerializer


class FeedView(APIView):
    """
    Endpoint : GET /api/feed/
    Retourne les profils publiés pour le feed TikTok.
    Accessible sans connexion — visible par tout le monde.
    Les profils Premium (futur) seront prioritaires dans l'ordre.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        # Ne retourne que les profils publiés
        queryset = Profile.objects.filter(is_published=True)

        # ── Filtres rapides du feed ───────────────────────────
        # Disponibles via la barre de filtre en haut du feed Flutter

        poste = request.query_params.get('poste')
        if poste:
            queryset = queryset.filter(
                position__nom_poste__icontains=poste
            )

        ville = request.query_params.get('ville')
        if ville:
            queryset = queryset.filter(ville__icontains=ville)

        categorie_age = request.query_params.get('categorie_age')
        if categorie_age:
            # Filtre par catégorie d'âge calculée
            ids = [
                p.id for p in queryset
                if p.get_categorie_age() == categorie_age
            ]
            queryset = queryset.filter(id__in=ids)

        # ── Ordre d'affichage ─────────────────────────────────
        # MVP : les plus récents en premier
        # Phase 2 : les profils Premium seront mis en avant
        queryset = queryset.order_by('-created_at')

        # ── Pagination ────────────────────────────────────────
        # 10 profils par page pour le feed (moins que la recherche)
        # Optimisé pour le scroll vertical sur mobile
        page      = int(request.query_params.get('page', 1))
        page_size = 10
        start     = (page - 1) * page_size
        end       = start + page_size
        total     = queryset.count()

        serializer = ProfileReadSerializer(
            queryset[start:end],
            many=True,
            context={'request': request}
        )

        return Response({
            'total'         : total,
            'page'          : page,
            'has_next_page' : end < total,
            # has_next_page : Flutter utilise ça pour savoir
            # s'il doit charger la prochaine page quand on arrive en bas
            'results'       : serializer.data,
        }, status=status.HTTP_200_OK)