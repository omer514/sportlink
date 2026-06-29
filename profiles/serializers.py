# ============================================================
# SPORTLINK — Serializers Profils
# Gère la conversion des profils joueurs et recruteurs
# entre le format Python (Django) et le format JSON (Flutter)
# ============================================================

from rest_framework import serializers
from datetime import date
from .models import Sport, Position, Profile, RecruiterProfile


# ── SPORT ─────────────────────────────────────────────────────
class SportSerializer(serializers.ModelSerializer):
    """
    Serializer simple pour les sports.
    Flutter l'utilise pour afficher la liste des disciplines.
    """
    class Meta:
        model  = Sport
        fields = ('id', 'nom_sport', 'is_active')


# ── POSITION ──────────────────────────────────────────────────
class PositionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les postes de jeu.
    Flutter l'utilise pour construire le menu dynamique
    Catégorie → Poste dans le formulaire d'inscription.
    """

    # Affiche le nom du sport au lieu de son id
    sport_nom = serializers.CharField(
        source='sport.nom_sport',
        read_only=True
    )

    class Meta:
        model  = Position
        fields = ('id', 'sport_nom', 'categorie', 'nom_poste', 'code_poste')


# ── PROFIL JOUEUR (LECTURE) ───────────────────────────────────
class ProfileReadSerializer(serializers.ModelSerializer):
    """
    Serializer pour AFFICHER un profil joueur.
    Utilisé pour la page publique et la liste des joueurs.
    Ajoute des champs calculés : age, categorie_age, contact_whatsapp.
    """

    # Champs calculés — générés par des méthodes Python, pas stockés en BDD
    age            = serializers.SerializerMethodField()
    categorie_age  = serializers.SerializerMethodField()
    contact_whatsapp = serializers.SerializerMethodField()

    # Affiche les détails complets du poste au lieu de juste l'id
    position            = PositionSerializer(read_only=True)
    position_secondaire = PositionSerializer(read_only=True)
    sport               = SportSerializer(read_only=True)

    # Affiche le nom d'utilisateur lié au profil
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = Profile
        fields = (
            'id', 'username', 'slug', 'nom_complet', 'age', 'categorie_age',
            'ville', 'sport', 'position', 'position_secondaire',
            'pied_fort', 'taille', 'poids',
            'statut_club', 'nom_club',
            'photo_profil', 'is_verified', 'is_minor',
            'contact_whatsapp', 'profile_views', 'created_at',
        )

    def get_age(self, obj):
        """
        Calcule l'âge du joueur à partir de sa date de naissance.
        Retourne un entier — Ex : 19
        """
        return obj.get_age()

    def get_categorie_age(self, obj):
        """
        Retourne la catégorie d'âge du joueur.
        Ex : U17, U20, Senior
        """
        return obj.get_categorie_age()

    def get_contact_whatsapp(self, obj):
        """
        Retourne le bon numéro WhatsApp selon le statut du joueur.
        - Si mineur : retourne le numéro du TUTEUR
        - Si majeur : retourne le numéro du JOUEUR
        Le numéro n'est jamais affiché en clair dans l'URL.
        Flutter génère le lien WhatsApp côté app avec ce numéro.
        """
        if obj.is_minor and obj.tuteur_whatsapp:
            return obj.tuteur_whatsapp
        return obj.whatsapp


# ── PROFIL JOUEUR (ÉCRITURE) ──────────────────────────────────
class ProfileWriteSerializer(serializers.ModelSerializer):
    """
    Serializer pour CRÉER ou MODIFIER un profil joueur.
    Inclut les validations métier importantes.
    """

    class Meta:
        model  = Profile
        fields = (
            'nom_complet', 'date_naissance', 'ville',
            'sport', 'position', 'position_secondaire',
            'pied_fort', 'taille', 'poids',
            'statut_club', 'nom_club', 'whatsapp',
            'photo_profil', 'identity_doc',
            'tuteur_nom', 'tuteur_lien', 'tuteur_whatsapp', 'consent_doc',
        )

    def validate_date_naissance(self, value):
        """
        Vérifie que le joueur a au moins 10 ans.
        Calcule l'âge à partir de la date de naissance soumise.
        """
        today = date.today()
        age   = today.year - value.year

        # Ajustement si l'anniversaire n'est pas encore passé cette année
        if (today.month, today.day) < (value.month, value.day):
            age -= 1

        if age < 10:
            raise serializers.ValidationError(
                'L\'inscription n\'est pas autorisée pour les moins de 10 ans.'
            )
        return value

    def validate(self, data):
        """
        Validation croisée : vérifie les données du tuteur si le joueur est mineur.
        """
        # Calcule si le joueur est mineur
        date_naissance = data.get('date_naissance')
        if date_naissance:
            today = date.today()
            age = today.year - date_naissance.year
            if (today.month, today.day) < (date_naissance.month, date_naissance.day):
                age -= 1

            # Si mineur : les infos du tuteur sont obligatoires
            if age < 16:
                if not data.get('tuteur_nom'):
                    raise serializers.ValidationError({
                        'tuteur_nom': 'Le nom du tuteur est obligatoire pour un joueur de moins de 16 ans.'
                    })
                if not data.get('tuteur_whatsapp'):
                    raise serializers.ValidationError({
                        'tuteur_whatsapp': 'Le WhatsApp du tuteur est obligatoire pour un joueur de moins de 16 ans.'
                    })
        return data

    def create(self, validated_data):
        """
        Crée le profil et le lie automatiquement à l'utilisateur connecté.
        L'utilisateur est passé depuis la vue via le contexte.
        """
        # Récupère l'utilisateur connecté depuis le contexte de la requête
        user = self.context['request'].user
        profile = Profile.objects.create(user=user, **validated_data)
        return profile


# ── PROFIL RECRUTEUR ──────────────────────────────────────────
class RecruiterProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les profils recruteurs.
    Lecture et écriture dans le même serializer car
    les recruteurs ont peu de champs.
    """

    # Affiche le statut de validation — lecture seule
    # Le recruteur ne peut pas se valider lui-même
    is_validated = serializers.BooleanField(read_only=True)

    class Meta:
        model  = RecruiterProfile
        fields = (
            'id', 'nom_complet', 'organisation',
            'poste_occupe', 'telephone', 'is_validated', 'created_at'
        )
        read_only_fields = ('is_validated', 'created_at')