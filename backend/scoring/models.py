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
    score_stabilite_emploi  = models.PositiveIntegerField(
        verbose_name='Score stabilité emploi (/25)',
        help_text='Basé sur le type d\'employeur et l\'ancienneté'
    )
    score_capacite_remboursement = models.PositiveIntegerField(
        verbose_name='Score capacité de remboursement (/25)',
        help_text='Basé sur le taux d\'endettement et le ratio mensualité/salaire'
    )
    score_profil_client     = models.PositiveIntegerField(
        verbose_name='Score profil client (/25)',
        help_text='Basé sur l\'âge, l\'ancienneté et le délai de sécurité'
    )
    score_dossier           = models.PositiveIntegerField(
        verbose_name='Score dossier (/25)',
        help_text='Basé sur la complétude des documents et le type de crédit'
    )

    # Recommandation Gemini
    recommandation_ia   = models.TextField(
        blank=True,
        verbose_name='Recommandation IA',
        help_text='Analyse narrative générée par Gemini API'
    )
    conditions_proposees = models.TextField(
        blank=True,
        verbose_name='Conditions proposées',
        help_text='Conditions suggérées par l\'IA si décision conditionnelle'
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
