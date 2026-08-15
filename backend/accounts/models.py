from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    """
    Modèle utilisateur personnalisé de la plateforme SCE.
    Étend AbstractUser pour ajouter le rôle métier de chaque acteur
    dans le circuit d'octroi de crédit.
    """

    class Role(models.TextChoices):
        COMMERCIAL     = 'COMMERCIAL',     'Commercial'
        CHEF_AGENCE_COMMERCIALE = 'CHEF_AGENCE_COMMERCIALE', "Chef d'agence commerciale"
        CHEF_AGENCE_ANALYSE     = 'CHEF_AGENCE_ANALYSE',     "Chef d'agence analyse"
        ANALYSTE       = 'ANALYSTE',       'Analyste Engagement'
        DIRECTION      = 'DIRECTION',      'Direction'
        COMITE         = 'COMITE',         'Comité'
        ADMINISTRATEUR = 'ADMINISTRATEUR', 'Administrateur'

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.COMMERCIAL,
        verbose_name='Rôle'
    )

    agence = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Agence'
    )

    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Téléphone'
    )

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.get_full_name()} — {self.get_role_display()}"

    @property
    def est_commercial(self):
        """Vérifie si l'utilisateur est un commercial."""
        return self.role == self.Role.COMMERCIAL

    @property
    def est_chef_agence_commerciale(self):
        return self.role == self.Role.CHEF_AGENCE_COMMERCIALE

    @property
    def est_chef_agence_analyse(self):
        return self.role == self.Role.CHEF_AGENCE_ANALYSE

    @property
    def est_chef_agence(self):
        """Vrai pour l'un ou l'autre chef d'agence — utile pour les vérifications génériques."""
        return self.est_chef_agence_commerciale or self.est_chef_agence_analyse

    @property
    def est_analyste(self):
        """Vérifie si l'utilisateur est analyste engagement."""
        return self.role == self.Role.ANALYSTE

    @property
    def est_direction(self):
        """Vérifie si l'utilisateur est de la direction."""
        return self.role == self.Role.DIRECTION