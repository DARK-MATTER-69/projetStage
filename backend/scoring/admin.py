from django.contrib import admin
from .models import ScoreCredit


@admin.register(ScoreCredit)
class ScoreCreditAdmin(admin.ModelAdmin):
    list_display = [
        'dossier', 'score', 'niveau_risque',
        'decision_ia', 'taux_endettement', 'calcule_le'
    ]
    list_filter  = ['niveau_risque', 'decision_ia']
    ordering     = ['-calcule_le']
    readonly_fields = [
    'score', 'niveau_risque', 'decision_ia',
    'taux_endettement', 'ratio_mensualite_salaire',
    'delai_securite', 'score_stabilite_emploi',
    'score_capacite_remboursement', 'score_profil_client',
    'score_dossier', 'recommandation',
    'conditions', 'calcule_le'
]