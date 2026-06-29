# ============================================================
# SPORTLINK — Modèle Utilisateur personnalisé
# On remplace le User par défaut de Django par le nôtre
# pour pouvoir ajouter les champs dont on a besoin (role, etc.)
# ============================================================

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# ── MANAGER PERSONNALISÉ ─────────────────────────────────────
# Le Manager est la classe qui gère la création des utilisateurs
# Django en a besoin pour savoir comment créer un user et un superuser
class UserManager(BaseUserManager):

    def create_user(self, email, username, password=None, **extra_fields):
        """
        Crée un utilisateur normal (joueur ou recruteur).
        Appelé lors de l'inscription via l'API.
        """
        if not email:
            raise ValueError('L\'email est obligatoire')

        # Normalise l'email : met le domaine en minuscules
        # Ex: Omar@Gmail.COM devient Omar@gmail.com
        email = self.normalize_email(email)

        # Crée l'objet user sans encore le sauvegarder
        user = self.model(email=email, username=username, **extra_fields)

        # Hash le mot de passe — jamais stocké en clair dans la BDD
        user.set_password(password)

        # Sauvegarde dans la base de données
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        Crée un administrateur (accès au panneau Django Admin).
        Appelé via la commande : python manage.py createsuperuser
        """
        # Force les permissions admin à True
        extra_fields.setdefault('is_staff', True)       # Accès à l'admin Django
        extra_fields.setdefault('is_superuser', True)   # Toutes les permissions
        extra_fields.setdefault('is_active', True)      # Compte actif immédiatement

        return self.create_user(email, username, password, **extra_fields)


# ── MODÈLE USER ──────────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur principal de SportLink.
    Remplace le User par défaut de Django.
    Utilisé pour : joueurs, recruteurs et admins.
    """

    # Choix possibles pour le rôle de l'utilisateur
    ROLE_CHOICES = [
        ('talent',    'Talent'),      # Joueur qui crée un profil
        ('recruteur', 'Recruteur'),   # Recruteur qui cherche des joueurs
        ('admin',     'Admin'),       # Administrateur de la plateforme
    ]

    # ── CHAMPS DE LA TABLE users ─────────────────────────────
    email = models.EmailField(
        unique=True,
        # unique=True : deux utilisateurs ne peuvent pas avoir le même email
    )

    username = models.CharField(
        max_length=50,
        unique=True,
        # unique=True : deux utilisateurs ne peuvent pas avoir le même pseudo
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='talent',
        # Par défaut, tout nouvel inscrit est un talent (joueur)
    )

    is_active = models.BooleanField(
        default=False,
        # False par défaut : le compte est inactif jusqu'à confirmation de l'email
    )

    is_email_verified = models.BooleanField(
        default=False,
        # Passe à True quand l'utilisateur clique sur le lien dans son email
    )

    is_staff = models.BooleanField(
        default=False,
        # True = accès au panneau d'administration Django
    )

    failed_login_attempts = models.PositiveSmallIntegerField(
        default=0,
        # Compteur de tentatives de connexion échouées
        # Bloqué après 5 tentatives pour éviter le brute force
    )

    last_login = models.DateTimeField(
        null=True,
        blank=True,
        # null=True : peut être vide (jamais connecté)
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        # auto_now_add : rempli automatiquement à la création, jamais modifié
    )

    # On dit à Django d'utiliser notre UserManager
    objects = UserManager()

    # Le champ utilisé pour se connecter (à la place du username par défaut)
    USERNAME_FIELD = 'email'

    # Champs obligatoires en plus de l'email et du mot de passe
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name        = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        # Ce qui s'affiche dans l'admin Django pour identifier un user
        return f'{self.username} ({self.role})'

    def is_recruiter(self):
        """Retourne True si l'utilisateur est un recruteur."""
        return self.role == 'recruteur'

    def is_talent(self):
        """Retourne True si l'utilisateur est un joueur."""
        return self.role == 'talent'

    def increment_failed_login(self):
        """Incrémente le compteur de tentatives échouées."""
        self.failed_login_attempts += 1
        self.save(update_fields=['failed_login_attempts'])

    def reset_failed_login(self):
        """Remet le compteur à zéro après une connexion réussie."""
        self.failed_login_attempts = 0
        self.save(update_fields=['failed_login_attempts'])

    def is_blocked(self):
        """Retourne True si le compte est bloqué après trop de tentatives."""
        return self.failed_login_attempts >= 5