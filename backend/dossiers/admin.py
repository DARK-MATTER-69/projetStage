from django.contrib import admin
from .models import Client, Dossier, DocumentDossier, ValidationDossier


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'prenom', 'type_employeur', 'salaire_net', 'cree_par', 'cree_le']
    list_filter   = ['type_employeur', 'nationalite']
    search_fields = ['nom', 'prenom', 'numero_cni', 'telephone']
    ordering      = ['-cree_le']


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display  = ['id', 'client', 'commercial', 'montant_sollicite', 'statut', 'necessite_comite', 'cree_le']
    list_filter   = ['statut', 'type_credit', 'necessite_comite']
    search_fields = ['client__nom', 'client__prenom', 'commercial__username']
    ordering      = ['-cree_le']


@admin.register(DocumentDossier)
class DocumentDossierAdmin(admin.ModelAdmin):
    list_display = ['dossier', 'type_document', 'nom_fichier', 'uploade_par', 'uploade_le']
    list_filter  = ['type_document']


@admin.register(ValidationDossier)
class ValidationDossierAdmin(admin.ModelAdmin):
    list_display = ['dossier', 'validateur', 'decision', 'date']
    list_filter  = ['decision']