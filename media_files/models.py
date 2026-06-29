# ============================================================
# SPORTLINK — Modèle Media
# Gère les photos et vidéos associées aux profils joueurs.
# Chaque profil peut avoir :
#   - Maximum 5 photos d'action / d'entraînement
#   - 1 lien YouTube pour les highlights
#   - 1 vidéo uploadée localement (max 10 Mo)
# ============================================================

from django.db import models
from django.core.exceptions import ValidationError
from profiles.models import Profile


class Media(models.Model):
    """
    Table des médias (photos et vidéos) liés aux profils joueurs.
    Stockés sur Cloudinary pour compression et optimisation automatique.
    Critique pour les connexions lentes au Bénin.
    """

    # Types de médias possibles
    TYPE_CHOICES = [
        ('photo',       'Photo'),
        # Photo d'action ou d'entraînement — uploadée directement

        ('video_link',  'Lien Vidéo'),
        # Lien YouTube ou YouTube Shorts — recommandé pour les connexions lentes
        # Le lecteur YouTube est intégré directement dans l'app Flutter

        ('video_file',  'Fichier Vidéo'),
        # Vidéo uploadée directement — max 10 Mo
        # Compressée automatiquement par Cloudinary
    ]

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='medias',
        # Si le profil est supprimé, tous ses médias le sont aussi
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        # Détermine comment le média sera affiché dans l'app Flutter
    )

    url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        # URL Cloudinary pour les photos et vidéos uploadées
        # URL YouTube pour les liens vidéo
    )

    fichier = models.FileField(
        upload_to='videos/',
        null=True,
        blank=True,
        # Fichier vidéo uploadé directement
        # Cloudinary le compresse et retourne une URL dans le champ 'url'
    )

    thumbnail_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        # Miniature générée automatiquement par Cloudinary (pour les photos)
        # ou extraite de YouTube via l'API YouTube (pour les liens vidéo)
        # Utilisée dans le feed TikTok et la galerie pour charger vite
    )

    order_index = models.PositiveSmallIntegerField(
        default=1,
        # Ordre d'affichage dans la galerie du profil (1 à 5 pour les photos)
        # Le joueur peut réorganiser ses photos depuis l'app
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Media'
        verbose_name_plural = 'Medias'
        # Trie les médias par ordre d'affichage défini par le joueur
        ordering            = ['order_index', 'created_at']

    def __str__(self):
        return f'{self.profile.nom_complet} — {self.type} #{self.order_index}'

    def clean(self):
        """
        Validation avant sauvegarde :
        1. Un profil ne peut pas avoir plus de 5 photos
        2. Un lien vidéo doit contenir youtube.com ou youtu.be
        """
        # Limite de 5 photos par profil
        if self.type == 'photo':
            # Compte les photos existantes de ce profil
            # Exclut le média actuel si c'est une modification (self.pk exist)
            photos_count = Media.objects.filter(
                profile=self.profile,
                type='photo'
            ).exclude(pk=self.pk).count()

            if photos_count >= 5:
                raise ValidationError(
                    'Un profil ne peut pas avoir plus de 5 photos.'
                )

        # Validation du lien YouTube
        if self.type == 'video_link':
            if self.url:
                # Vérifie que c'est bien un lien YouTube
                if 'youtube.com' not in self.url and 'youtu.be' not in self.url:
                    raise ValidationError(
                        'Le lien vidéo doit être un lien YouTube valide. '
                        'Ex : https://www.youtube.com/watch?v=...'
                    )