from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Sum

from .models import Client, Dossier, DocumentDossier, ValidationDossier
from .serializers import (
    ClientSerializer,
    DossierListSerializer,
    DossierDetailSerializer,
    DocumentDossierSerializer,
    ValidationDossierSerializer,
    ClientDetailSerializer,
)
from .permissions import EstCommercial, PeutValiderDossier
from scoring.services import calculer_et_sauvegarder_score


class ListeClientsView(generics.ListCreateAPIView):
    """
    Liste et création des clients.
    Seul le commercial peut créer un client.

    GET  /api/dossiers/clients/
    POST /api/dossiers/clients/
    """

    serializer_class   = ClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Un commercial ne voit que ses propres clients.
        Les autres rôles voient tous les clients.
        """
        user = self.request.user
        if user.est_commercial:
            return Client.objects.filter(cree_par=user)
        return Client.objects.all()

    def perform_create(self, serializer):
        """Associe automatiquement le commercial connecté au client."""
        serializer.save(cree_par=self.request.user)


class DetailClientView(generics.RetrieveUpdateAPIView):
    queryset           = Client.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ClientDetailSerializer
        return ClientSerializer

class ListeDossiersView(generics.ListCreateAPIView):
    """
    Liste et création des dossiers.

    GET  /api/dossiers/
    POST /api/dossiers/
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DossierDetailSerializer
        return DossierListSerializer

    def get_queryset(self):
        """
        Filtre les dossiers selon le rôle de l'utilisateur connecté.
        Chaque acteur ne voit que les dossiers qui le concernent.
        """
        user = self.request.user

        if user.est_commercial:
            return Dossier.objects.filter(commercial=user)

        if user.est_chef_agence:
            return Dossier.objects.filter(
                statut__in=[
                    Dossier.Statut.SOUMIS,
                    Dossier.Statut.VALIDE_CHEF,
                    Dossier.Statut.ANALYSE_TERMINEE,
                ]
            )

        if user.est_analyste:
            return Dossier.objects.filter(
                statut=Dossier.Statut.VALIDE_CHEF
            )

        if user.est_direction:
            return Dossier.objects.filter(
                statut=Dossier.Statut.ANALYSE_TERMINEE,
                necessite_comite=False
            )

        return Dossier.objects.all()

    def perform_create(self, serializer):
        """Associe automatiquement le commercial connecté au dossier."""
        serializer.save(commercial=self.request.user)


class DetailDossierView(generics.RetrieveUpdateAPIView):
    """
    Consultation et modification d'un dossier.

    GET /api/dossiers/<id>/
    PUT /api/dossiers/<id>/
    """

    queryset           = Dossier.objects.all()
    serializer_class   = DossierDetailSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([EstCommercial])
def soumettre_dossier(request, pk):
    """
    Soumet un dossier au chef d'agence et déclenche le scoring IA.
    Réservé au commercial propriétaire du dossier.

    POST /api/dossiers/<id>/soumettre/
    """
    dossier = get_object_or_404(Dossier, pk=pk, commercial=request.user)

    if dossier.statut != Dossier.Statut.BROUILLON:
        return Response(
            {'detail': 'Ce dossier a déjà été soumis.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Calcul du score IA avant soumission
    calculer_et_sauvegarder_score(dossier)

    # Mise à jour du statut
    dossier.statut    = Dossier.Statut.SOUMIS
    dossier.soumis_le = timezone.now()
    dossier.save()

    return Response({'detail': 'Dossier soumis avec succès. Score IA calculé.'})


@api_view(['POST'])
@permission_classes([PeutValiderDossier])
def valider_dossier(request, pk):
    """
    Enregistre la décision d'un acteur dans le circuit de validation.
    Met à jour le statut du dossier selon l'étape et le rôle.

    POST /api/dossiers/<id>/valider/
    Body : {
        "decision":    "APPROUVE" | "REJETE",
        "commentaire": "...",
        "assigne_a":   <id_analyste>  (requis pour chef d'agence)
    }
    """
    dossier    = get_object_or_404(Dossier, pk=pk)
    user       = request.user
    decision   = request.data.get('decision')
    commentaire = request.data.get('commentaire', '')
    assigne_a_id = request.data.get('assigne_a')

    if not decision:
        return Response(
            {'detail': 'La décision est requise.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Déterminer l'étape selon le rôle et le statut actuel
    etape = _determiner_etape(user, dossier)
    if not etape:
        return Response(
            {'detail': 'Action non autorisée à cette étape.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Récupérer l'analyste assigné si fourni
    assigne_a = None
    if assigne_a_id:
        from accounts.models import Utilisateur
        try:
            assigne_a = Utilisateur.objects.get(
                pk=assigne_a_id,
                role=Utilisateur.Role.ANALYSTE
            )
        except Utilisateur.DoesNotExist:
            return Response(
                {'detail': 'Analyste introuvable.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Enregistrement de la validation
    ValidationDossier.objects.create(
        dossier     = dossier,
        validateur  = user,
        etape       = etape,
        decision    = decision,
        commentaire = commentaire,
        assigne_a   = assigne_a,
    )

    # Mise à jour du statut
    if decision == ValidationDossier.Decision.REJETE:
        dossier.statut = Dossier.Statut.REJETE

    elif user.est_chef_agence:
        if dossier.statut == Dossier.Statut.SOUMIS:
            if not assigne_a:
                return Response(
                    {'detail': 'Vous devez assigner un analyste.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            dossier.statut = Dossier.Statut.EN_ANALYSE_1

        elif dossier.statut == Dossier.Statut.ANALYSE_TERMINEE:
            dossier.statut = Dossier.Statut.VALIDE_CHEF_2
            if dossier.necessite_comite:
                dossier.statut = Dossier.Statut.EN_COMITE
            else:
                dossier.statut = Dossier.Statut.EN_DECISION

    elif user.est_analyste:
        if dossier.statut == Dossier.Statut.EN_ANALYSE_1:
            if not assigne_a:
                return Response(
                    {'detail': 'Vous devez assigner le 2ème analyste.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            dossier.statut = Dossier.Statut.EN_ANALYSE_2

        elif dossier.statut == Dossier.Statut.EN_ANALYSE_2:
            dossier.statut = Dossier.Statut.ANALYSE_TERMINEE

    elif user.est_direction:
        dossier.statut = Dossier.Statut.APPROUVE

    elif user.role == 'COMITE':
        dossier.statut = Dossier.Statut.APPROUVE

    dossier.save()

    return Response({'detail': 'Décision enregistrée avec succès.'})


def _determiner_etape(user, dossier):
    """
    Détermine l'étape de validation selon le rôle
    et le statut actuel du dossier.

    :return: str étape ou None si non autorisé
    """
    if user.est_chef_agence:
        if dossier.statut == Dossier.Statut.SOUMIS:
            return ValidationDossier.Etape.VISA_CHEF_1
        if dossier.statut == Dossier.Statut.ANALYSE_TERMINEE:
            return ValidationDossier.Etape.VISA_CHEF_2

    if user.est_analyste:
        # Vérifier que ce dossier lui est bien assigné
        derniere_validation = dossier.validations.filter(
            assigne_a=user
        ).last()

        if dossier.statut == Dossier.Statut.EN_ANALYSE_1 and derniere_validation:
            return ValidationDossier.Etape.AVIS_ANALYSTE1
        if dossier.statut == Dossier.Statut.EN_ANALYSE_2 and derniere_validation:
            return ValidationDossier.Etape.AVIS_ANALYSTE2

    if user.est_direction and dossier.statut == Dossier.Statut.EN_DECISION:
        return ValidationDossier.Etape.DECISION_DIR

    if user.role == 'COMITE' and dossier.statut == Dossier.Statut.EN_COMITE:
        return ValidationDossier.Etape.DECISION_COMITE

    return None


@api_view(['POST'])
@permission_classes([EstCommercial])
def upload_document(request, pk):
    """
    Upload un document pour un dossier.
    Réservé au commercial propriétaire du dossier.

    POST /api/dossiers/<id>/documents/
    """
    dossier    = get_object_or_404(Dossier, pk=pk, commercial=request.user)
    serializer = DocumentDossierSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(
            dossier     = dossier,
            uploade_par = request.user,
            nom_fichier = request.FILES.get('fichier').name
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats_dashboard(request):
    """
    Retourne les statistiques pour le tableau de bord.

    GET /api/dashboard/stats/
    """

    user     = request.user
    queryset = Dossier.objects.all()

    # Filtre selon le rôle
    if user.est_commercial:
        queryset = queryset.filter(commercial=user)

    stats = {
        'dossiers_en_cours': queryset.exclude(
            statut__in=['APPROUVE', 'REJETE', 'BROUILLON']
        ).count(),
        'dossiers_approuves': queryset.filter(statut='APPROUVE').count(),
        'dossiers_rejetes':   queryset.filter(statut='REJETE').count(),
        'montant_total':      queryset.filter(
            statut='APPROUVE'
        ).aggregate(total=Sum('montant_sollicite'))['total'] or 0,
    }

    return Response(stats)

@api_view(['POST'])
@permission_classes([EstCommercial])
def analyser_releve(request, pk):
    """
    Analyse le relevé bancaire PDF uploadé via Gemini.
    Calcule le score ML préliminaire.
    Met à jour le statut du dossier selon conformité.

    POST /api/dossiers/<id>/analyser-releve/
    """
    from scoring.gemini import ExtracteurReleveGemini
    from scoring.moteur import MoteurScoring

    dossier = get_object_or_404(
        Dossier, pk=pk, commercial=request.user
    )

    # Vérifier que le relevé a bien été uploadé
    doc_releve = dossier.documents.filter(
        type_document='HISTORIQUE_BANQUE'
    ).first()

    if not doc_releve:
        return Response(
            {'detail': 'Veuillez d\'abord uploader l\'historique de compte.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Analyse Gemini du relevé
    dossier.statut = Dossier.Statut.ANALYSE_RELEVE
    dossier.save()

    extracteur = ExtracteurReleveGemini()
    resultat   = extracteur.extraire(doc_releve.fichier.path)

    if not resultat.succes:
        dossier.statut             = Dossier.Statut.NON_CONFORME
        dossier.releve_analyse_ok  = False
        dossier.releve_raisons_refus = resultat.message
        dossier.save()
        return Response({
            'conforme': False,
            'raisons':  [resultat.message],
        })

    # Stocker les résultats de l'extraction
    dossier.releve_total_credits  = resultat.total_credits
    dossier.releve_total_debits   = resultat.total_debits
    dossier.releve_remboursements = resultat.remboursements_credits
    dossier.releve_solde_moyen    = resultat.solde_moyen
    dossier.releve_decouvert      = resultat.decouvert_detecte
    dossier.releve_banque         = resultat.banque_detectee

    # Mise à jour de l'échéance mensuelle banque
    if resultat.remboursements_credits > 0:
        dossier.echeance_mens_banque = resultat.remboursements_credits

    # Vérification de conformité
    raisons = []
    salaire = float(dossier.client.salaire_net)

    if resultat.decouvert_detecte:
        raisons.append("Découvert détecté sur le relevé bancaire.")

    if salaire > 0:
        moy_credits = float(resultat.moyenne_credits_mensuelle)
        if moy_credits < salaire * 0.50:
            raisons.append(
                f"Crédits moyens mensuels ({moy_credits:,.0f} FCFA) "
                f"inférieurs à 50% du salaire déclaré ({salaire:,.0f} FCFA)."
            )

    quotite = float(dossier.quotite_relative)
    if quotite > 33:
        raisons.append(
            f"Quotité de {quotite:.2f}% dépasse le seuil COBAC de 33%."
        )

    if not dossier.est_traite_acceptable:
        raisons.append(
            f"Mensualité demandée supérieure à la traite max autorisée "
            f"({float(dossier.traite_max_autorisee):,.0f} FCFA)."
        )

    conforme = len(raisons) == 0

    dossier.releve_analyse_ok    = conforme
    dossier.releve_raisons_refus = '\n'.join(raisons) if raisons else ''
    dossier.statut = (
        Dossier.Statut.PRET_A_SOUMETTRE if conforme
        else Dossier.Statut.NON_CONFORME
    )
    dossier.save()

    return Response({
        'conforme':              conforme,
        'raisons':               raisons,
        'banque':                resultat.banque_detectee,
        'total_credits':         float(resultat.total_credits),
        'total_debits':          float(resultat.total_debits),
        'moy_credits_mensuelle': float(resultat.moyenne_credits_mensuelle),
        'remboursements':        float(resultat.remboursements_credits),
        'decouvert':             resultat.decouvert_detecte,
        'solde_moyen':           float(resultat.solde_moyen) if resultat.solde_moyen else None,
        'quotite':               float(dossier.quotite_relative),
        'traite_max':            float(dossier.traite_max_autorisee),
        'mensualite':            float(dossier.mensualite_estimee),
        'echeance_banque':       float(dossier.echeance_mens_banque),
    })