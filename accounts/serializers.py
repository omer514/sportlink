# ============================================================
# SPORTLINK — Serializers Authentification
# Convertit les données JSON de Flutter en objets Django
# et inversement pour tout ce qui concerne les utilisateurs
# ============================================================

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User


# ── INSCRIPTION ───────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'un nouveau compte.
    Appelé quand Flutter envoie une requête POST sur /api/auth/register/
    """

    # Ce champ existe dans le serializer mais pas dans le modèle
    # write_only=True : jamais renvoyé dans la réponse JSON
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            'min_length': 'Le mot de passe doit contenir au moins 8 caractères.'
        }
    )

    password_confirm = serializers.CharField(
        write_only=True,
        # Champ de confirmation — vérifié puis ignoré
    )

    class Meta:
        model  = User
        fields = ('email', 'username', 'password', 'password_confirm', 'role')
        extra_kwargs = {
            'role': {'required': False}
            # Le rôle est optionnel à l'inscription
            # Par défaut : 'talent' (défini dans le modèle)
        }

    def validate_email(self, value):
        """
        Vérifie que l'email n'est pas déjà utilisé.
        Cette méthode est appelée automatiquement par DRF.
        """
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                'Un compte avec cet email existe déjà.'
            )
        return value.lower()  # Stocke l'email en minuscules

    def validate_username(self, value):
        """
        Vérifie que le nom d'utilisateur est valide et disponible.
        """
        # Pas d'espaces dans le username
        if ' ' in value:
            raise serializers.ValidationError(
                'Le nom d\'utilisateur ne peut pas contenir d\'espaces.'
            )
        # Vérifie la disponibilité
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Ce nom d\'utilisateur est déjà pris.'
            )
        return value

    def validate(self, data):
        """
        Validation croisée : vérifie que les deux mots de passe correspondent.
        Cette méthode reçoit toutes les données à la fois.
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Les mots de passe ne correspondent pas.'
            })
        return data

    def create(self, validated_data):
        """
        Crée l'utilisateur après validation.
        Supprime password_confirm car ce champ n'existe pas dans le modèle.
        """
        # On retire password_confirm avant de créer le user
        validated_data.pop('password_confirm')

        # create_user hash automatiquement le mot de passe
        user = User.objects.create_user(**validated_data)
        return user


# ── CONNEXION ─────────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion.
    Accepte email OU username + mot de passe.
    """

    # On accepte email ou username dans le même champ
    email_or_username = serializers.CharField()
    password          = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Vérifie les identifiants et retourne l'utilisateur si valide.
        """
        email_or_username = data.get('email_or_username')
        password          = data.get('password')

        # Détermine si c'est un email ou un username
        # Un email contient forcément un '@'
        if '@' in email_or_username:
            # Connexion par email
            try:
                user = User.objects.get(email=email_or_username.lower())
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    'Aucun compte trouvé avec cet email.'
                )
        else:
            # Connexion par username
            try:
                user = User.objects.get(username=email_or_username)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    'Aucun compte trouvé avec ce nom d\'utilisateur.'
                )

        # Vérifie si le compte est bloqué après trop de tentatives
        if user.is_blocked():
            raise serializers.ValidationError(
                'Compte temporairement bloqué après 5 tentatives échouées. '
                'Contactez l\'administration.'
            )

        # Vérifie le mot de passe
        if not user.check_password(password):
            # Incrémente le compteur d'échecs
            user.increment_failed_login()
            raise serializers.ValidationError(
                'Mot de passe incorrect.'
            )

        # Vérifie que l'email est confirmé
        if not user.is_email_verified:
            raise serializers.ValidationError(
                'Veuillez confirmer votre adresse email avant de vous connecter.'
            )

        # Vérifie que le compte est actif
        if not user.is_active:
            raise serializers.ValidationError(
                'Ce compte est désactivé. Contactez l\'administration.'
            )

        # Tout est bon — remet le compteur d'échecs à zéro
        user.reset_failed_login()

        # Met à jour la date de dernière connexion
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Ajoute l'objet user aux données validées
        data['user'] = user
        return data


# ── INFORMATIONS UTILISATEUR ──────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour afficher les informations d'un utilisateur.
    Utilisé dans les réponses API après connexion ou inscription.
    """

    class Meta:
        model  = User
        fields = (
            'id', 'email', 'username', 'role',
            'is_active', 'is_email_verified', 'created_at'
        )
        # Tous ces champs sont en lecture seule dans ce serializer
        read_only_fields = fields