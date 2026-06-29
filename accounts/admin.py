# ============================================================
# SPORTLINK — Administration des utilisateurs
# Ce fichier rend le modèle User visible dans le panneau admin Django
# Accessible sur : http://127.0.0.1:8000/admin/
# ============================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuration de l'affichage des utilisateurs dans l'admin Django.
    """

    # Colonnes affichées dans la liste des utilisateurs
    list_display  = ('email', 'username', 'role', 'is_active', 'is_email_verified', 'created_at')

    # Filtres disponibles dans la colonne de droite
    list_filter   = ('role', 'is_active', 'is_email_verified', 'is_staff')

    # Champs sur lesquels on peut faire une recherche
    search_fields = ('email', 'username')

    # Ordre d'affichage par défaut : les plus récents en premier
    ordering      = ('-created_at',)

    # Champs affichés quand on ouvre un utilisateur
    fieldsets = (
        ('Identifiants',   {'fields': ('email', 'username', 'password')}),
        ('Role',           {'fields': ('role',)}),
        ('Statut',         {'fields': ('is_active', 'is_email_verified', 'failed_login_attempts')}),
        ('Permissions',    {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates',          {'fields': ('created_at', 'last_login')}),
    )

    # Champs en lecture seule (ne peuvent pas être modifiés dans l'admin)
    readonly_fields = ('created_at', 'last_login')

    # Champs affichés quand on crée un nouvel utilisateur depuis l'admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'role', 'password1', 'password2'),
        }),
    )