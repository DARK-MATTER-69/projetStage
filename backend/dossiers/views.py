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
    """
    Consultation et modification d'un client.

    GET /api/dossiers/clients/<id>/
    PUT /api/dossiers/clients/<id>/
    """

    queryset           = Client.objects.all()
    serializer_class   = ClientSerializer
    permission_classes = [IsAuthenticated]


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
    Enregistre la décision de validation d'un acteur du circuit.
    Met à jour le statut du dossier selon le rôle du validateur.

    POST /api/dossiers/<id>/valider/
    Body : { "decision": "APPROUVE" | "REJETE", "commentaire": "..." }
    """
    dossier    = get_object_or_404(Dossier, pk=pk)
    serializer = ValidationDossierSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    decision = serializer.validated_data['decision']

    # Enregistrement de la validation
    ValidationDossier.objects.create(
        dossier    = dossier,
        validateur = request.user,
        **serializer.validated_data
    )

    # Mise à jour du statut selon le rôle et la décision
    if decision == ValidationDossier.Decision.REJETE:
        dossier.statut = Dossier.Statut.REJETE

    elif request.user.est_chef_agence:
        if dossier.statut == Dossier.Statut.SOUMIS:
            dossier.statut = Dossier.Statut.VALIDE_CHEF
        elif dossier.statut == Dossier.Statut.ANALYSE_TERMINEE:
            dossier.statut = Dossier.Statut.VALIDE_DIRECTION

    elif request.user.est_analyste:
        dossier.statut = Dossier.Statut.ANALYSE_TERMINEE

    elif request.user.est_direction or request.user.role == 'COMITE':
        dossier.statut = Dossier.Statut.APPROUVE

    dossier.save()

    return Response({'detail': 'Décision enregistrée avec succès.'})


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