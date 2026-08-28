from django.contrib import admin
from .models import ScoreCredit, TraceDecisionIA


@admin.register(ScoreCredit)
class ScoreCreditAdmin(admin.ModelAdmin):
    list_display = [
        'dossier', 'score', 'niveau_risque',
        'decision_ia', 'eligible', 'taux_endettement', 'calcule_le'
    ]
    list_filter  = ['niveau_risque', 'decision_ia', 'eligible']
    ordering     = ['-calcule_le']
    readonly_fields = [
        'score', 'niveau_risque', 'decision_ia', 'eligible', 'motif_ineligibilite',
        'taux_endettement', 'ratio_mensualite_salaire', 'delai_securite',
        'score_quotite', 'score_historique_sce', 'score_stabilite',
        'score_montant_vs_salaire', 'score_dossier', 'score_fidelite',
        'score_marge_securite', 'recommandation', 'conditions', 'calcule_le',
    ]


@admin.register(TraceDecisionIA)
class TraceDecisionIAAdmin(admin.ModelAdmin):
    list_display = [
        'dossier', 'etape', 'score_fige', 'decision_ia_figee',
        'decision_humaine', 'desaccord', 'date_decision',
    ]
    list_filter  = ['desaccord', 'decision_ia_figee', 'decision_humaine']
    ordering     = ['-date_decision']
    readonly_fields = [
        'dossier', 'validateur', 'etape', 'score_fige', 'niveau_risque_fige',
        'decision_ia_figee', 'score_regles_fige', 'score_ml_fige',
        'version_modele_ml', 'decision_humaine', 'desaccord', 'date_decision',
    ]