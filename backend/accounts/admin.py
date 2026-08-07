from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """Administration des utilisateurs de la plateforme SCE."""

    list_display  = ['username', 'get_full_name', 'role', 'agence', 'is_active']
    list_filter   = ['role', 'agence', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering      = ['last_name']

    fieldsets = UserAdmin.fieldsets + (
        ('Informations SCE', {
            'fields': ('role', 'agence', 'telephone')
        }),
    )