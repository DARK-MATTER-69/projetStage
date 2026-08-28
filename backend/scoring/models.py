from django.db import models
from dossiers.models import Dossier


class ScoreCredit(models.Model):
    """
    Représente le résultat du scoring IA d'un dossier de crédit.
    Calculé automatiquement à la soumission du dossier par le commercial.
    """

    class NiveauRisque(models.TextChoices):
        FAIBLE  = 'FAIBLE',  'Risque faible'
        MOYEN   = 'MOYEN',   'Risque moyen'
        ELEVE   = 'ELEVE',   'Risque élevé'
        CRITIQUE = 'CRITIQUE', 'Risque critique'

    class Decision(models.TextChoices):
        FAVORABLE    = 'FAVORABLE',    'Favorable'
        CONDITIONNEL = 'CONDITIONNEL', 'Favorable sous conditions'
        DEFAVORABLE  = 'DEFAVORABLE',  'Défavorable'
        INELIGIBLE   = 'INELIGIBLE',   'Inéligible (bloqué avant analyse)'

    dossier     = models.OneToOneField(
        Dossier,
        on_delete=models.CASCADE,
        related_name='score',
        verbose_name='Dossier'
    )

    # Résultat global
    score           = models.PositiveIntegerField(
        verbose_name='Score (/100)',
        help_text='Score de solvabilité calculé par le modèle IA'
    )
    niveau_risque   = models.CharField(
        max_length=10,
        choices=NiveauRisque.choices,
        verbose_name='Niveau de risque'
    )
    decision_ia     = models.CharField(
        max_length=15,
        choices=Decision.choices,
        verbose_name='Décision IA'
    )

    # Détail des critères utilisés pour le scoring
    taux_endettement        = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Taux d\'endettement (%)'
    )
    ratio_mensualite_salaire = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Ratio mensualité / salaire (%)'
    )
    delai_securite          = models.IntegerField(
        verbose_name='Délai de sécurité (jours)',
        help_text='Écart entre le jour de salaire et le jour de prélèvement'
    )
    score_quotite            = models.PositiveIntegerField(
        verbose_name='Score quotité (/25)', 
        default=0
    )
    score_historique_sce     = models.PositiveIntegerField(
        verbose_name='Score historique SCE (/20)', 
        default=0
    )
    score_stabilite          = models.PositiveIntegerField(
        verbose_name='Score stabilité revenu (/15)', 
        default=0
    )
    score_montant_vs_salaire = models.PositiveIntegerField(
        verbose_name='Score montant vs salaire (/15)', 
        default=0
    )
    score_dossier            = models.PositiveIntegerField(
        verbose_name='Score complétude dossier (/10)', 
        default=0
    )
    score_fidelite           = models.PositiveIntegerField(
        verbose_name='Score fidélité relation (/10)', 
        default=0
    )
    score_marge_securite     = models.PositiveIntegerField(
        verbose_name='Score marge de sécurité (/5)', 
        default=0
    )
    eligible                 = models.BooleanField(
        default=True, 
        verbose_name='Dossier éligible (a passé le gardien)'
    )
    motif_ineligibilite      = models.TextField(
        blank=True, 
        verbose_name='Motif d\'inéligibilité'
    )
    
    score_regles       = models.PositiveIntegerField(
        default=0, 
        verbose_name='Score règles métier seul (/100)'
    )
    score_ml           = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, blank=True, verbose_name='Score ML brut (probabilité remboursement %)'
    )
    version_modele_ml  = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='Version du modèle ML utilisé'
    )
    facteurs_ml        = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name='Facteurs déterminants du modèle ML'
    )

   # Recommandation et conditions du moteur de scoring
    recommandation       = models.TextField(
        blank=True,
        verbose_name='Recommandation',
        help_text='Analyse générée par le moteur de scoring SCE'
    )
    conditions           = models.TextField(
        blank=True,
        verbose_name='Conditions proposées',
        help_text='Conditions suggérées si décision conditionnelle'
    )

    # Meta
    calcule_le  = models.DateTimeField(auto_now_add=True)
    mis_a_jour  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Score de crédit'
        verbose_name_plural = 'Scores de crédit'

    def __str__(self):
        return f"Score {self.score}/100 — {self.get_decision_ia_display()} — Dossier {self.dossier.pk}"

    @property
    def est_favorable(self):
        """Vérifie si la décision IA est favorable."""
        return self.decision_ia == self.Decision.FAVORABLE

    @property
    def couleur_risque(self):
        """
        Retourne un code couleur selon le niveau de risque.
        Utilisé pour l'affichage dans l'interface.
        """
        couleurs = {
            self.NiveauRisque.FAIBLE:   'green',
            self.NiveauRisque.MOYEN:    'orange',
            self.NiveauRisque.ELEVE:    'red',
            self.NiveauRisque.CRITIQUE: 'darkred',
        }
        return couleurs.get(self.niveau_risque, 'gray')
    

class TraceDecisionIA(models.Model):
    """
    Photographie immuable du score au moment précis d'une décision humaine.
    Objectifs :
    - Traçabilité : prouver sur quelle base une décision a été rendue,
      même si le barème ou le modèle ML évoluent ensuite.
    - Apprentissage : capturer les désaccords entre la décision IA et la
      décision humaine, pour analyse ultérieure (le modèle avait-il raison ?).
    """

    dossier = models.ForeignKey(
        'dossiers.Dossier',
        on_delete=models.CASCADE,
        related_name='traces_decision_ia',
        verbose_name='Dossier',
    )
    validateur = models.ForeignKey(
        'accounts.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Validateur',
    )
    etape = models.CharField(max_length=30, verbose_name='Étape du circuit')

    # Snapshot du score au moment de la décision
    score_fige          = models.PositiveIntegerField(verbose_name='Score figé (/100)')
    niveau_risque_fige  = models.CharField(max_length=10, verbose_name='Niveau de risque figé')
    decision_ia_figee   = models.CharField(max_length=15, verbose_name='Décision IA figée')
    score_regles_fige   = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Score règles métier (avant fusion ML)'
    )
    score_ml_fige       = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Score ML brut (probabilité de remboursement, %)'
    )
    version_modele_ml   = models.CharField(
        max_length=50, blank=True, verbose_name='Version du modèle ML utilisé'
    )

    # Décision humaine réelle
    decision_humaine = models.CharField(max_length=10, verbose_name='Décision humaine (APPROUVE/REJETE)')
    desaccord        = models.BooleanField(
        default=False,
        verbose_name='Désaccord IA / humain',
        help_text="True si la décision humaine contredit la recommandation IA",
    )

    date_decision = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Trace de décision IA'
        verbose_name_plural = 'Traces de décisions IA'
        ordering = ['-date_decision']

    def __str__(self):
        marqueur = ' [DÉSACCORD]' if self.desaccord else ''
        return f'Trace dossier {self.dossier_id} — {self.date_decision:%d/%m/%Y}{marqueur}'
