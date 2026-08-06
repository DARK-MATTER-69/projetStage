from rest_framework import serializers
from .models import ScoreCredit


class ScoreCreditSerializer(serializers.ModelSerializer):
    """Sérialise le score de crédit d'un dossier."""

    niveau_risque_display = serializers.CharField(
        source='get_niveau_risque_display',
        read_only=True
    )
    decision_ia_display = serializers.CharField(
        source='get_decision_ia_display',
        read_only=True
    )
    couleur_risque = serializers.CharField(read_only=True)

    class Meta:
        model  = ScoreCredit
        fields = [
            'id', 'score',
            'niveau_risque', 'niveau_risque_display',
            'decision_ia', 'decision_ia_display',
            'couleur_risque',
            'taux_endettement', 'ratio_mensualite_salaire',
            'delai_securite',
            'score_stabilite_emploi',
            'score_capacite_remboursement',
            'score_profil_client',
            'score_dossier',
            'recommandation_ia',
            'conditions_proposees',
            'calcule_le'
        ]
        read_only_fields = fields