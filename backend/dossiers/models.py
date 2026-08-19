from django.db import models
from accounts.models import Utilisateur
from decimal import Decimal
from django.conf import settings


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
    date_versement_salaire = models.PositiveIntegerField(
    null=True,
    blank=True,
    verbose_name='Jour de versement du salaire',
    help_text='Jour habituel de réception du salaire (ex: 15 pour le 15 du mois)'
    )
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
    matricule = models.CharField(
    max_length=20,
    blank=True,
    verbose_name='Matricule'
    )
    mode_paiement = models.CharField(
        max_length=10,
        default='PSMA',
        verbose_name='Mode de paiement',
        help_text='PSMA = Prélèvement Sur Masse Salariale Automatique'
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
    Représente un dossier de demande de crédit SCE.
    Suit le circuit complet de validation depuis la création
    jusqu'à la décision finale.
    """

    class TypeCredit(models.TextChoices):
        EQUIPEMENT   = 'EQUIPEMENT',   'Crédit équipement'
        SCOLAIRE     = 'SCOLAIRE',     'Crédit scolaire'
        BAIL         = 'BAIL',         'Crédit-bail'
        CONSOMMATION = 'CONSOMMATION', 'Crédit consommation'
        AUTRE        = 'AUTRE',        'Autre'

    class Statut(models.TextChoices):
        BROUILLON        = 'BROUILLON',        'Brouillon'
        DOCUMENTS_INCOMPLETS = 'DOCUMENTS_INCOMPLETS', 'Documents incomplets'
        PRET_A_SOUMETTRE = 'PRET_A_SOUMETTRE', 'Prêt à soumettre'
        SOUMIS           = 'SOUMIS',           'Soumis au chef d\'agence'
        VALIDE_CHEF_1    = 'VALIDE_CHEF_1',    'Validé chef d\'agence (1ère signature)'
        EN_ANALYSE_1     = 'EN_ANALYSE_1',     'En cours d\'analyse (Analyste 1)'
        EN_ANALYSE_2     = 'EN_ANALYSE_2',     'En cours d\'analyse (Analyste 2)'
        ANALYSE_TERMINEE = 'ANALYSE_TERMINEE', 'Analyses terminées'
        VALIDE_CHEF_2    = 'VALIDE_CHEF_2',    'Validé chef d\'agence (2ème signature)'
        EN_DECISION      = 'EN_DECISION',      'En attente de décision direction'
        EN_COMITE        = 'EN_COMITE',        'En attente du comité'
        APPROUVE         = 'APPROUVE',         'Approuvé'
        REJETE           = 'REJETE',           'Rejeté'

    SEUIL_COMITE = 5_000_000

    # ── Relations ──────────────────────────────────────────
    client     = models.ForeignKey(
        Client, on_delete=models.PROTECT,
        related_name='dossiers', verbose_name='Client'
    )
    commercial = models.ForeignKey(
        Utilisateur, on_delete=models.PROTECT,
        related_name='dossiers_crees', verbose_name='Commercial'
    )

    # ── Fiche 2 — Appréciation commerciale ─────────────────
    type_credit        = models.CharField(
        max_length=20, choices=TypeCredit.choices,
        verbose_name='Type de crédit'
    )
    montant_sollicite  = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name='Montant sollicité (FCFA)'
    )
    duree_mois         = models.PositiveIntegerField(verbose_name='Durée (mois)')
    objet_financement  = models.TextField(verbose_name='Objet du financement')
    appreciation       = models.TextField(
        blank=True, verbose_name='Appréciation du commercial'
    )
    date_debut_prelevement = models.DateField(
        null=True, blank=True,
        verbose_name='Date de début de prélèvement'
    )
    jour_prelevement   = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Jour de prélèvement mensuel'
    )

    # ── Données SCE (Fiche 2 réelle) ───────────────────────
    echeance_mens_banque   = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Echéance mensuelle banque (FCFA)'
    )
    encours_sce            = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='Encours SCE (FCFA)'
    )
    assureur               = models.CharField(
        max_length=100, blank=True, verbose_name='Assureur'
    )
    montant_assurance_ttc  = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Montant assurance TTC (FCFA)'
    )
    avi                    = models.BooleanField(
        default=False, verbose_name='AVI'
    )
    delegation_salaire     = models.BooleanField(
        default=False, verbose_name='Délégation de salaire'
    )
    mode_paiement          = models.CharField(
        max_length=10, default='PSMA',
        verbose_name='Mode de paiement'
    )


    # ── Circuit de validation ───────────────────────────────
    statut           = models.CharField(
        max_length=25, choices=Statut.choices,
        default=Statut.BROUILLON, verbose_name='Statut'
    )
    necessite_comite = models.BooleanField(
        default=False, verbose_name='Nécessite le comité'
    )
    fiche2_verrouillee = models.BooleanField(
        default=False,
        verbose_name='Fiche 2 verrouillée',
        help_text='True dès que le dossier est soumis'
    )

    # ── Horodatage ──────────────────────────────────────────
    cree_le   = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)
    soumis_le  = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Dossier'
        verbose_name_plural = 'Dossiers'
        ordering            = ['-cree_le']

    def __str__(self):
        return f"Dossier {self.pk} — {self.client} — {self.get_statut_display()}"

    def save(self, *args, **kwargs):
        """Détermine automatiquement si le comité est requis."""
        self.necessite_comite = self.montant_sollicite > self.SEUIL_COMITE
        super().save(*args, **kwargs)

    @property
    def mensualite_estimee(self):
        if self.duree_mois:
            return self.montant_sollicite / self.duree_mois
        return Decimal('0')

    @property
    def taux_endettement(self):
        """Taux d'endettement basé sur données déclarées."""
        salaire = self.client.salaire_net
        if salaire and salaire > 0:
            charges_totales = self.client.charges_mensuelles + self.mensualite_estimee
            return round((charges_totales / salaire) * 100, 2)
        return Decimal('0')

    @property
    def traite_max_autorisee(self):
        """Traite max = Salaire x 33% - Crédits en cours."""
        quotite         = Decimal('0.33')
        capacite_brute  = self.client.salaire_net * quotite
        traite_max      = capacite_brute - self.client.credits_en_cours
        return max(traite_max, Decimal('0'))

    @property
    def est_traite_acceptable(self):
        return self.mensualite_estimee <= self.traite_max_autorisee

    @property
    def total_engagements_mensuel(self):
        """
        Total engagements mensuels réels :
        Echéance banque + nouvelle mensualité SCE.
        """
        return self.echeance_mens_banque + self.mensualite_estimee

    @property
    def quotite_relative(self):
        """
        Quotité = Total engagements / Salaire x 100.
        Seuil COBAC max : 33%.
        """
        salaire = self.client.salaire_net
        if salaire and salaire > 0:
            return round(
                (self.total_engagements_mensuel / salaire) * 100, 2
            )
        return Decimal('0')

    @property
    def echeance_mens_sce(self):
        """Echéance mensuelle SCE = mensualité + assurance."""
        return self.mensualite_estimee + self.montant_assurance_ttc

    def est_verouille_pour(self, utilisateur):
        """
        Vérifie si le dossier est verrouillé pour modification
        par un acteur donné.
        """
        if not self.fiche2_verrouillee:
            return False
        # Seul le commercial propriétaire peut modifier avant soumission
        return not (
            utilisateur.est_commercial and
            utilisateur == self.commercial and
            self.statut == self.Statut.BROUILLON
        )
        
class DocumentDossier(models.Model):
    """
    Représente un document physique numérisé et joint au dossier.
    Le commercial scanne et uploade les pièces remises par le client
    lors de l'entretien.
    """

    class TypeDocument(models.TextChoices):
        CNI               = 'CNI',               'Photocopie CNI'
        RIB               = 'RIB',               'Relevé d\'identité bancaire (RIB)'
        HISTORIQUE_BANQUE = 'HISTORIQUE_BANQUE',  'Historique de compte (3 derniers mois)'
        NIU               = 'NIU',               'Attestation d\'immatriculation (NIU)'
        AUTRE             = 'AUTRE',              'Autre document'

    dossier       = models.ForeignKey(
        Dossier,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Dossier'
    )
    type_document = models.CharField(
        max_length=20,
        choices=TypeDocument.choices,
        verbose_name='Type de document'
    )
    fichier       = models.FileField(
        upload_to='dossiers/documents/%Y/%m/',
        verbose_name='Fichier'
    )
    nom_fichier   = models.CharField(
        max_length=255,
        verbose_name='Nom du fichier'
    )
    uploade_par   = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        verbose_name='Uploadé par'
    )
    uploade_le    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Document'
        verbose_name_plural = 'Documents'
        ordering            = ['type_document']

    def __str__(self):
        return f"{self.get_type_document_display()} — Dossier {self.dossier.pk}"

class ValidationDossier(models.Model):
    """
    Enregistre chaque validation/avis dans le circuit SCE.
    Chaque acteur ajoute ses remarques sans modifier celles des précédents.
    """

    class Decision(models.TextChoices):
        APPROUVE   = 'APPROUVE',   'Approuvé'
        REJETE     = 'REJETE',     'Rejeté'
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'

    class Etape(models.TextChoices):
        VISA_CHEF_AGENCE    = 'VISA_CHEF_AGENCE',    '1ère signature Chef d\'agence'
        AVIS_ANALYSTE1 = 'AVIS_ANALYSTE1', 'Avis Analyste 1'
        AVIS_ANALYSTE2 = 'AVIS_ANALYSTE2', 'Avis Analyste 2'
        VISA_CHEF_ANALYSTE    = 'VISA_CHEF_ANALYSTE',    '2ème signature Chef d\'analyste'
        DECISION_DIR   = 'DECISION_DIR',   'Décision Direction'
        DECISION_COMITE = 'DECISION_COMITE', 'Décision Comité'

    dossier     = models.ForeignKey(
        Dossier, on_delete=models.CASCADE,
        related_name='validations', verbose_name='Dossier'
    )
    validateur  = models.ForeignKey(
        Utilisateur, on_delete=models.PROTECT,
        verbose_name='Validateur'
    )
    etape = models.CharField(
        max_length=20,
        choices=Etape.choices,
        default=Etape.VISA_CHEF_AGENCE,
        verbose_name='Étape du circuit'
    )
    decision    = models.CharField(
        max_length=15, choices=Decision.choices,
        default=Decision.EN_ATTENTE
    )
    commentaire = models.TextField(blank=True, verbose_name='Commentaire / Avis')
    date        = models.DateTimeField(auto_now_add=True)
    assigne_a = models.ForeignKey(
    Utilisateur,
    null=True, blank=True,
    on_delete=models.SET_NULL,
    related_name='dossiers_assignes',
    verbose_name='Assigné à',
    help_text='Analyste à qui ce dossier est assigné pour cette étape'
)

    class Meta:
        verbose_name        = 'Validation'
        verbose_name_plural = 'Validations'
        ordering            = ['date']

    def __str__(self):
        return f"{self.get_etape_display()} — {self.get_decision_display()} — {self.date:%d/%m/%Y}"
    

class HistoriqueSalaire(models.Model):
    """
    Historique des salaires d'un client SCE.
    Permet de détecter l'évolution des revenus et de recalculer
    le score si le salaire augmente.
    """
    client     = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='historique_salaires',
        verbose_name='Client'
    )
    salaire    = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Salaire net (FCFA)'
    )
    date_effet = models.DateField(
        verbose_name='Date d\'effet'
    )
    note       = models.CharField(
        max_length=200, blank=True,
        verbose_name='Note',
        help_text='Ex: Promotion, revalorisation, changement de poste'
    )
    enregistre_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        verbose_name='Enregistré par'
    )
    cree_le    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Historique salaire'
        verbose_name_plural = 'Historiques salaires'
        ordering            = ['-date_effet']

    def __str__(self):
        return f"{self.client} — {self.salaire:,.0f} FCFA — {self.date_effet}"


class ImpayeSCE(models.Model):
    """
    Enregistre les impayés d'un client à la SCE.
    Donnée critique pour le scoring — un client avec impayés
    sera systématiquement pénalisé.
    """

    class Statut(models.TextChoices):
        EN_COURS   = 'EN_COURS',   'En cours'
        REGULARISE = 'REGULARISE', 'Régularisé'
        CONTENTIEUX = 'CONTENTIEUX', 'En contentieux'

    client          = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='impayes',
        verbose_name='Client'
    )
    dossier         = models.ForeignKey(
        'Dossier',
        on_delete=models.CASCADE,
        related_name='impayes',
        verbose_name='Dossier concerné'
    )
    montant_impaye  = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Montant impayé (FCFA)'
    )
    date_echeance   = models.DateField(
        verbose_name='Date d\'échéance manquée'
    )
    date_regularisation = models.DateField(
        null=True, blank=True,
        verbose_name='Date de régularisation'
    )
    statut          = models.CharField(
        max_length=15,
        choices=Statut.choices,
        default=Statut.EN_COURS,
        verbose_name='Statut'
    )
    nb_mois_retard  = models.PositiveIntegerField(
        default=0,
        verbose_name='Nombre de mois de retard'
    )
    cree_le         = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Impayé SCE'
        verbose_name_plural = 'Impayés SCE'
        ordering            = ['-date_echeance']

    def __str__(self):
        return f"{self.client} — {self.montant_impaye:,.0f} FCFA — {self.get_statut_display()}"

class Notification(models.Model):
    """Notification simple envoyée à un utilisateur (ex: résultat d'un dossier)."""

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications'
    )
    dossier   = models.ForeignKey(Dossier, on_delete=models.CASCADE, null=True)
    message   = models.CharField(max_length=255)
    lue       = models.BooleanField(default=False)
    cree_le   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-cree_le']

    def __str__(self):
        return f'{self.destinataire} — {self.message}'