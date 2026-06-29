# ============================================================
# SPORTLINK — Administration des profils
# Rend les modèles visibles dans le panneau admin Django
# ============================================================

from django.contrib import admin
from .models import Sport, Position, Profile, RecruiterProfile


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    # Colonnes visibles dans la liste
    list_display  = ('nom_sport', 'is_active', 'created_at')
    # Filtre par statut actif/inactif
    list_filter   = ('is_active',)
    # Permet de modifier is_active directement depuis la liste
    list_editable = ('is_active',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display  = ('sport', 'categorie', 'nom_poste', 'code_poste')
    list_filter   = ('sport', 'categorie')
    search_fields = ('nom_poste', 'code_poste')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = (
        'nom_complet', 'ville', 'is_published',
        'is_verified', 'is_minor', 'is_minor_consent_validated', 'created_at'
    )
    list_filter   = (
        'is_published', 'is_verified', 'is_minor',
        'is_minor_consent_validated', 'statut_club', 'pied_fort'
    )
    search_fields = ('nom_complet', 'ville', 'nom_club', 'slug')
    # Champs modifiables directement depuis la liste
    list_editable = ('is_published', 'is_verified', 'is_minor_consent_validated')
    readonly_fields = ('slug', 'profile_views', 'created_at', 'updated_at')


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display  = ('nom_complet', 'organisation', 'is_validated', 'created_at')
    list_filter   = ('is_validated',)
    search_fields = ('nom_complet', 'organisation')
    # Permet de valider les recruteurs directement depuis la liste
    list_editable = ('is_validated',)