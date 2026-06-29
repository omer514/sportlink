# ============================================================
# SPORTLINK — Administration des médias
# ============================================================

from django.contrib import admin
from .models import Media


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display  = ('profile', 'type', 'order_index', 'created_at')
    list_filter   = ('type',)
    search_fields = ('profile__nom_complet',)
    # profile__nom_complet : recherche dans le nom du profil lié