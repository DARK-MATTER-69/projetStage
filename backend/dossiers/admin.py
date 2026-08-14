from django.contrib import admin
from .models import Client, Dossier, DocumentDossier, ValidationDossier
from .models import HistoriqueSalaire, ImpayeSCE


@admin.register(HistoriqueSalaire)
class HistoriqueSalaireAdmin(admin.ModelAdmin):
    list_display  = ['client', 'salaire', 'date_effet', 'note', 'enregistre_par']
    list_filter   = ['date_effet']
    search_fields = ['client__nom', 'client__prenom']
    ordering      = ['-date_effet']

@admin.register(ImpayeSCE)
class ImpayeSCEAdmin(admin.ModelAdmin):
    list_display  = ['client', 'dossier', 'montant_impaye', 'nb_mois_retard', 'statut', 'date_echeance']
    list_filter   = ['statut']
    search_fields = ['client__nom', 'client__prenom']
    ordering      = ['-date_echeance']
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