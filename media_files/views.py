# ============================================================
# SPORTLINK — Vues Media
# Gère l'upload, la liste et la suppression des photos/vidéos
# ============================================================

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from .models import Media
from .serializers import MediaSerializer
from profiles.models import Profile


class MediaListCreateView(APIView):
    """
    GET  /api/profiles/<slug>/media/ — Liste les médias d'un profil
    POST /api/profiles/<slug>/media/ — Ajoute un média au profil
    """

    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_profile(self, slug):
        """Récupère le profil par son slug."""
        return get_object_or_404(Profile, slug=slug)

    def get(self, request, slug):
        """Retourne tous les médias d'un profil."""
        profile = self.get_profile(slug)
        medias  = Media.objects.filter(profile=profile)
        serializer = MediaSerializer(medias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, slug):
        """
        Ajoute un média au profil.
        Vérifie que c'est bien le propriétaire qui uploade.
        """
        profile = self.get_profile(slug)

        # Seul le propriétaire peut ajouter des médias
        if request.user != profile.user:
            return Response({
                'error': 'Vous ne pouvez ajouter des médias qu\'à votre propre profil.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = MediaSerializer(data=request.data)

        if serializer.is_valid():
            # Lie le média au profil automatiquement
            media = serializer.save(profile=profile)
            return Response(
                MediaSerializer(media).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MediaDeleteView(APIView):
    """
    DELETE /api/media/<id>/ — Supprime un média
    PATCH  /api/media/<id>/ — Modifie l'ordre d'un média
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Media, pk=pk)

    def delete(self, request, pk):
        """Supprime un média. Seul le propriétaire peut supprimer."""
        media = self.get_object(pk)

        # Vérifie que c'est le propriétaire du profil lié
        if request.user != media.profile.user:
            return Response({
                'error': 'Action non autorisée.'
            }, status=status.HTTP_403_FORBIDDEN)

        media.delete()
        return Response({
            'message': 'Média supprimé avec succès.'
        }, status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        """Modifie l'ordre d'affichage d'un média dans la galerie."""
        media = self.get_object(pk)

        if request.user != media.profile.user:
            return Response({
                'error': 'Action non autorisée.'
            }, status=status.HTTP_403_FORBIDDEN)

        # partial=True : seul order_index est modifié
        serializer = MediaSerializer(media, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)