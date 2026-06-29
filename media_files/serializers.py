# ============================================================
# SPORTLINK — Serializers Media
# Gère la conversion des photos et vidéos
# entre le format Python (Django) et le format JSON (Flutter)
# ============================================================

from rest_framework import serializers
from .models import Media


class MediaSerializer(serializers.ModelSerializer):
    """
    Serializer pour les médias (photos et vidéos).
    Utilisé pour l'upload, l'affichage et la suppression des médias.
    """

    class Meta:
        model  = Media
        fields = (
            'id', 'type', 'url', 'fichier',
            'thumbnail_url', 'order_index', 'created_at'
        )
        # Ces champs sont générés automatiquement — pas modifiables par l'app
        read_only_fields = ('thumbnail_url', 'created_at')

    def validate(self, data):
        """
        Vérifie que le média a bien soit une URL soit un fichier,
        selon son type.
        """
        media_type = data.get('type')
        url        = data.get('url')
        fichier    = data.get('fichier')

        # Un lien vidéo doit avoir une URL YouTube
        if media_type == 'video_link':
            if not url:
                raise serializers.ValidationError({
                    'url': 'Un lien YouTube est obligatoire pour ce type de média.'
                })
            # Vérifie que c'est bien YouTube
            if 'youtube.com' not in url and 'youtu.be' not in url:
                raise serializers.ValidationError({
                    'url': 'Le lien doit être une URL YouTube valide.'
                })

        # Une photo ou une vidéo locale doit avoir un fichier
        if media_type in ('photo', 'video_file'):
            if not fichier and not url:
                raise serializers.ValidationError({
                    'fichier': 'Un fichier est obligatoire pour ce type de média.'
                })

        return data

    def validate_fichier(self, value):
        """
        Vérifie que le fichier uploadé ne dépasse pas 10 Mo.
        """
        # 10 Mo = 10 * 1024 * 1024 octets
        taille_max = 10 * 1024 * 1024

        if value and value.size > taille_max:
            raise serializers.ValidationError(
                f'Le fichier est trop lourd : {round(value.size / 1024 / 1024, 1)} Mo. '
                f'Maximum autorisé : 10 Mo. '
                f'Conseil : utilise plutôt un lien YouTube pour les vidéos lourdes.'
            )
        return value