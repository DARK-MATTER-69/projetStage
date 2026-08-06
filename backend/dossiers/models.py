from django.db import models
from accounts.models import Utilisateur


class Client(models.Model):
    """
    Représente un prospect/client de la SCE.
    Correspond aux informations saisies dans la Fiche 1 par le commercial.
    """

    class TypeEmployeur(models.TextChoices):
        FONCTIONNAIRE = 'FONCTIONNAIRE', 'Fonctionnaire'
        PRIVE         = 'PRIVE',         'Secteur privé'
        ONG           = 'ONG',           'ONG / Association'
        COMMERCANT    = 'COMMERCANT',    'Commerçant'
        RETRAITE      = 'RETRAITE',      'Retraité'
        AUTRE         = 'AUTRE',         'Autre'

    class Civilite(models.TextChoices):
        M   = 'M',   'Monsieur'
        MME = 'MME', 'Madame'

    # Identité
    civilite        = models.CharField(max_length=3, choices=Civilite.choices)
    nom             = models.CharField(max_length=100, verbose_name='Nom')
    prenom          = models.CharField(max_length=100, verbose_name='Prénom')
    date_naissance  = models.DateField(verbose_name='Date de naissance')
    lieu_naissance  = models.CharField(max_length=100, verbose_name='Lieu de naissance')
    nationalite     = models.CharField(max_length=100, default='Camerounaise')
    numero_cni      = models.CharField(max_length=50, unique=True, verbose_name='Numéro CNI')
    telephone       = models.CharField(max_length=20, verbose_name='Téléphone')
    email           = models.EmailField(blank=True, verbose_name='Email')
    adresse         = models.TextField(verbose_name='Adresse')

    # Situation professionnelle
    type_employeur  = models.CharField(
        max_length=20,
        choices=TypeEmployeur.choices,
        verbose_name="Type d'employeur"
    )
    nom_employeur   = models.CharField(max_length=150, verbose_name="Nom de l'employeur")
    poste_occupe    = models.CharField(max_length=100, verbose_name='Poste occupé')
    anciennete      = models.PositiveIntegerField(verbose_name="Ancienneté (années)")
    salaire_net     = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Salaire net mensuel (FCFA)'
    )

    # Situation financière
    charges_mensuelles = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Charges mensuelles (FCFA)'
    )
    credits_en_cours = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Crédits en cours (FCFA)'
    )

    # Meta
    cree_par    = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='clients_crees',
        verbose_name='Créé par'
    )
    cree_le     = models.DateTimeField(auto_now_add=True)
    modifie_le  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.civilite} {self.nom} {self.prenom}"


class Dossier(models.Model):
    """
    Représente un dossier de demande de crédit.
    Contient la Fiche 1 (client) et la Fiche 2 (appréciation commerciale)
    et suit l'état du circuit de validation interne de la SCE.
    """

    class TypeCredit(models.TextChoices):
        EQUIPEMENT   = 'EQUIPEMENT',   'Crédit équipement'
        SCOLAIRE     = 'SCOLAIRE',     'Crédit scolaire'
        BAIL         = 'BAIL',         'Crédit-bail'
        CONSOMMATION = 'CONSOMMATION', 'Crédit consommation'
        AUTRE        = 'AUTRE',        'Autre'

    class Statut(models.TextChoices):
        BROUILLON          = 'BROUILLON',          'Brouillon'
        SOUMIS             = 'SOUMIS',             'Soumis au chef d\'agence'
        VALIDE_CHEF        = 'VALIDE_CHEF',        'Validé par le chef d\'agence'
        EN_ANALYSE         = 'EN_ANALYSE',         'En cours d\'analyse'
        ANALYSE_TERMINEE   = 'ANALYSE_TERMINEE',   'Analyse terminée'
        VALIDE_DIRECTION   = 'VALIDE_DIRECTION',   'Validé par la direction'
        EN_COMITE          = 'EN_COMITE',          'En attente du comité'
        APPROUVE           = 'APPROUVE',           'Approuvé'
        REJETE             = 'REJETE',             'Rejeté'

    SEUIL_COMITE = 5_000_000  # FCFA

    # Relations
    client      = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='dossiers',
        verbose_name='Client'
    )
    commercial  = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='dossiers_crees',
        verbose_name='Commercial'
    )

    # Fiche 2 — Appréciation commerciale
    type_credit         = models.CharField(
        max_length=20,
        choices=TypeCredit.choices,
        verbose_name='Type de crédit'
    )
    montant_sollicite   = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='Montant sollicité (FCFA)'
    )
    duree_mois          = models.PositiveIntegerField(verbose_name='Durée (mois)')
    objet_financement   = models.TextField(verbose_name='Objet du financement')
    appreciation        = models.TextField(
        verbose_name='Appréciation du commercial',
        help_text='Observations et avis du commercial sur le dossier'
    )

    # Circuit de validation
    statut              = models.CharField(
        max_length=25,
        choices=Statut.choices,
        default=Statut.BROUILLON,
        verbose_name='Statut'
    )
    necessite_comite    = models.BooleanField(
        default=False,
        verbose_name='Nécessite le comité'
    )

    # Horodatage
    cree_le             = models.DateTimeField(auto_now_add=True)
    modifie_le          = models.DateTimeField(auto_now=True)
    soumis_le           = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Dossier'
        verbose_name_plural = 'Dossiers'
        ordering = ['-cree_le']

    def __str__(self):
        return f"Dossier {self.pk} — {self.client} — {self.get_statut_display()}"

    def save(self, *args, **kwargs):
        """
        Détermine automatiquement si le dossier nécessite
        le passage en comité selon le seuil de 5 000 000 FCFA.
        """
        self.necessite_comite = self.montant_sollicite > self.SEUIL_COMITE
        super().save(*args, **kwargs)

    @property
    def mensualite_estimee(self):
        """Calcule la mensualité estimée sans intérêts."""
        if self.duree_mois:
            return self.montant_sollicite / self.duree_mois
        return 0

    @property
    def taux_endettement(self):
        """
        Calcule le taux d'endettement du client.
        La COBAC exige un maximum de 33%.
        """
        salaire = self.client.salaire_net
        if salaire:
            charges_totales = self.client.charges_mensuelles + self.mensualite_estimee
            return round((charges_totales / salaire) * 100, 2)
        return 0


class ValidationDossier(models.Model):
    """
    Enregistre chaque étape de validation du circuit interne SCE.
    Remplace les déplacements physiques et les signatures papier.
    """

    class Decision(models.TextChoices):
        APPROUVE = 'APPROUVE', 'Approuvé'
        REJETE   = 'REJETE',   'Rejeté'
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'

    dossier     = models.ForeignKey(
        Dossier,
        on_delete=models.CASCADE,
        related_name='validations',
        verbose_name='Dossier'
    )
    validateur  = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        verbose_name='Validateur'
    )
    decision    = models.CharField(
        max_length=15,
        choices=Decision.choices,
        default=Decision.EN_ATTENTE
    )
    commentaire = models.TextField(blank=True, verbose_name='Commentaire')
    date        = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Validation'
        verbose_name_plural = 'Validations'
        ordering = ['date']

    def __str__(self):
        return f"{self.validateur} — {self.get_decision_display()} — {self.date:%d/%m/%Y}"
    
    
    
    class DocumentDossier(models.Model):
        """
        Représente un document physique numérisé et joint au dossier.
        Le commercial scanne et uploade les pièces remises par le client
        lors de l'entretien.
        """

        class TypeDocument(models.TextChoices):
            CNI              = 'CNI',              'Photocopie CNI'
            RIB              = 'RIB',              'Relevé d\'identité bancaire (RIB)'
            HISTORIQUE_BANQUE = 'HISTORIQUE_BANQUE', 'Historique de compte (3 derniers mois)'
            NIU              = 'NIU',              'Attestation d\'immatriculation (NIU)'
            AUTRE            = 'AUTRE',            'Autre document'

        dossier         = models.ForeignKey(
            Dossier,
            on_delete=models.CASCADE,
            related_name='documents',
            verbose_name='Dossier'
        )
        type_document   = models.CharField(
            max_length=20,
            choices=TypeDocument.choices,
            verbose_name='Type de document'
        )
        fichier         = models.FileField(
            upload_to='dossiers/documents/%Y/%m/',
            verbose_name='Fichier'
        )
        nom_fichier     = models.CharField(
            max_length=255,
            verbose_name='Nom du fichier'
        )
        uploade_par     = models.ForeignKey(
            Utilisateur,
            on_delete=models.PROTECT,
            verbose_name='Uploadé par'
        )
        uploade_le      = models.DateTimeField(auto_now_add=True)

        class Meta:
            verbose_name = 'Document'
            verbose_name_plural = 'Documents'
            ordering = ['type_document']

        def __str__(self):
            return f"{self.get_type_document_display()} — Dossier {self.dossier.pk}"