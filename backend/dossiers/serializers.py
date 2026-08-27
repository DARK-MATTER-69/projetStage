from rest_framework import serializers
from .models import Client, Dossier, DocumentDossier, ValidationDossier
from accounts.serializers import UtilisateurSerializer
from scoring.serializers import ScoreCreditSerializer


class DocumentDossierSerializer(serializers.ModelSerializer):
    """Sérialise un document joint à un dossier."""

    type_document_display = serializers.CharField(
        source='get_type_document_display',
        read_only=True
    )

    class Meta:
        model  = DocumentDossier
        fields = [
            'id', 'type_document', 'type_document_display',
            'fichier', 'nom_fichier', 'uploade_le'
        ]
        read_only_fields = ['id', 'uploade_le', 'nom_fichier']


class ClientSerializer(serializers.ModelSerializer):
    type_employeur_display = serializers.CharField(
        source='get_type_employeur_display',
        read_only=True
    )
    civilite_display = serializers.CharField(
        source='get_civilite_display',
        read_only=True
    )

    class Meta:
        model  = Client
        fields = [
            'id', 'civilite', 'civilite_display',
            'nom', 'prenom', 'date_naissance', 'lieu_naissance',
            'nationalite', 'numero_cni', 'telephone', 'email', 'adresse',
            'type_employeur', 'type_employeur_display', 'nom_employeur',
            'poste_occupe', 'anciennete', 'salaire_net',
            'charges_mensuelles', 'credits_en_cours',
            'date_versement_salaire','encours_sce_actuel',
            'matricule', 'mode_paiement',
            'cree_le'
        ]
        read_only_fields = ['id', 'cree_le']
        
    def get_encours_sce_actuel(self, obj):
        return obj.encours_sce_actuel()


class DossierListSerializer(serializers.ModelSerializer):
    """
    Sérialise un dossier pour l'affichage en liste.
    Version allégée sans les détails du client.
    """

    client_nom      = serializers.CharField(source='client.__str__', read_only=True)
    statut_display  = serializers.CharField(source='get_statut_display', read_only=True)
    type_credit_display = serializers.CharField(
        source='get_type_credit_display',
        read_only=True
    )
    commercial_nom  = serializers.CharField(
        source='commercial.get_full_name',
        read_only=True
    )
    score            = serializers.IntegerField(source='score.score', read_only=True, default=None)
    niveau_risque    = serializers.CharField(source='score.niveau_risque', read_only=True, default=None)
    decision_ia      = serializers.CharField(source='score.decision_ia', read_only=True, default=None)

    class Meta:
        model  = Dossier
        fields = [
            'id', 'client_nom', 'commercial_nom',
            'type_credit', 'type_credit_display',
            'montant_sollicite', 'duree_mois',
            'statut', 'statut_display',
            'necessite_comite', 'cree_le',
            'score', 'niveau_risque', 'decision_ia',
        ]
        read_only_fields = ['id', 'necessite_comite', 'cree_le']

class DossierDetailSerializer(serializers.ModelSerializer):
    client              = ClientSerializer(read_only=True)
    client_id           = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        source='client',
        write_only=True
    )
    documents           = DocumentDossierSerializer(many=True, read_only=True)
    validations         = serializers.SerializerMethodField()
    statut_display      = serializers.CharField(
        source='get_statut_display',
        read_only=True
    )
    type_credit_display = serializers.CharField(
        source='get_type_credit_display',
        read_only=True
    )
    score = ScoreCreditSerializer(read_only=True)

    # Propriétés calculées
    mensualite_estimee      = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    taux_endettement        = serializers.DecimalField(
        max_digits=5,  decimal_places=2, read_only=True
    )
    traite_max_autorisee    = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    est_traite_acceptable   = serializers.BooleanField(read_only=True)
    total_engagements_mensuel = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    quotite_relative        = serializers.DecimalField(
        max_digits=5,  decimal_places=2, read_only=True
    )

    class Meta:
        model  = Dossier
        fields = [
            'id', 'client', 'client_id',
            'type_credit', 'type_credit_display',
            'montant_sollicite', 'duree_mois',
            'objet_financement', 'appreciation',
            'date_debut_prelevement', 'jour_prelevement',
            # Nouveaux champs
            'echeance_mens_banque', 'encours_sce',
            'assureur', 'montant_assurance_ttc',
            'avi', 'delegation_salaire',
            # Statut et circuit
            'statut', 'statut_display',
            'necessite_comite', 'score','documents', 'validations',
            # Calculés
            'mensualite_estimee', 'taux_endettement',
            'traite_max_autorisee', 'est_traite_acceptable',
            'total_engagements_mensuel', 'quotite_relative',
            'cree_le', 'soumis_le'
        ]
        read_only_fields = [
            'id', 'necessite_comite', 'statut',
            'cree_le', 'soumis_le'
        ]

    def get_validations(self, obj):
        return [
            {
                'validateur':  v.validateur.get_full_name(),
                'role':        v.validateur.get_role_display(),
                'etape':       v.get_etape_display(),
                'decision':    v.get_decision_display(),
                'commentaire': v.commentaire,
                'assigne_a':   v.assigne_a.get_full_name() if v.assigne_a else None,
                'date':        v.date,
            }  
            for v in obj.validations.all()
    ]


class ValidationDossierSerializer(serializers.ModelSerializer):
    """Sérialise une décision de validation sur un dossier."""

    assigne_a_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model  = ValidationDossier
        fields = ['id', 'decision', 'commentaire', 'assigne_a_id']
        
class ClientDetailSerializer(ClientSerializer):
    """
    Sérialise un client avec ses dossiers associés.
    Utilisé pour la page détail client.
    """
    dossiers = DossierListSerializer(many=True, read_only=True)

    class Meta(ClientSerializer.Meta):
        fields = ClientSerializer.Meta.fields + ['dossiers']
        
class HistoriqueValidationSerializer(serializers.ModelSerializer):
    """
    Représente une décision passée d'un validateur, avec le contexte
    du dossier concerné, pour l'écran "Traités récemment".
    """
    dossier_id       = serializers.IntegerField(source='dossier.id', read_only=True)
    client_nom       = serializers.SerializerMethodField()
    montant_sollicite = serializers.DecimalField(
        source='dossier.montant_sollicite', max_digits=12, decimal_places=0, read_only=True
    )
    statut_actuel_dossier = serializers.CharField(source='dossier.statut', read_only=True)
    statut_actuel_display  = serializers.CharField(source='dossier.get_statut_display', read_only=True)
    decision_display  = serializers.CharField(source='get_decision_display', read_only=True)

    class Meta:
        model  = ValidationDossier
        fields = [
            'id', 'dossier_id', 'client_nom', 'montant_sollicite',
            'decision', 'decision_display', 'commentaire', 'date',
            'statut_actuel_dossier', 'statut_actuel_display',
        ]

    def get_client_nom(self, obj):
        client = obj.dossier.client
        return f"{client.prenom} {client.nom}"