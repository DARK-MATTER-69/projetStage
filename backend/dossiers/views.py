from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.db.models import OuterRef, Subquery


from .models import Client, Dossier, DocumentDossier, ValidationDossier, Notification
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
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [EstCommercial()]
        return [IsAuthenticated()]

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
    Détail et modification d'un client.

    GET /api/dossiers/clients/<id>/
    PUT /api/dossiers/clients/<id>/
    """

    queryset         = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.est_commercial:
            return Client.objects.filter(cree_par=user)
        return Client.objects.all()

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [EstCommercial()]
        return [IsAuthenticated()]

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
        Chaque acteur ne voit que les dossiers qui le concernent
        directement, à l'étape où il doit intervenir.
        """

        user = self.request.user

        if user.est_commercial:
            return Dossier.objects.filter(commercial=user)

        if user.est_chef_agence_commerciale:
            return Dossier.objects.filter(
                statut=Dossier.Statut.SOUMIS
            )

        if user.est_analyste:
            # Seuls les dossiers réellement assignés à CET analyste,
            # d'après le dernier enregistrement de validation
            dernier_assigne = ValidationDossier.objects.filter(
                dossier=OuterRef('pk')
            ).order_by('-date').values('assigne_a')[:1]

            return Dossier.objects.filter(
                statut__in=[
                    Dossier.Statut.EN_ANALYSE_1,
                    Dossier.Statut.EN_ANALYSE_2,
                ]
            ).annotate(
                dernier_assigne_id=Subquery(dernier_assigne)
            ).filter(dernier_assigne_id=user.id)

        if user.est_chef_agence_analyse:
            return Dossier.objects.filter(
                statut=Dossier.Statut.ANALYSE_TERMINEE
            )

        if user.est_direction:
            return Dossier.objects.filter(
                statut=Dossier.Statut.EN_DECISION
            )

        if user.role == 'COMITE':
            return Dossier.objects.filter(
                statut=Dossier.Statut.EN_COMITE
            )

        if user.role == 'ADMINISTRATEUR':
            return Dossier.objects.all()

        return Dossier.objects.none()

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
    
    def get_queryset(self):
        user = self.request.user
        if user.est_commercial:
            return Dossier.objects.filter(commercial=user)
        return Dossier.objects.all()

    def update(self, request, *args, **kwargs):
        dossier = self.get_object()
        if dossier.fiche2_verrouillee and request.user.est_commercial:
            return Response({'detail': 'Dossier verrouillé, modification impossible.'}, status=403)
        return super().update(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([EstCommercial])
def soumettre_dossier(request, pk):
    dossier = get_object_or_404(Dossier, pk=pk, commercial=request.user)

    if dossier.statut not in [Dossier.Statut.BROUILLON, Dossier.Statut.DOCUMENTS_INCOMPLETS]:
        return Response(
            {'detail': 'Ce dossier a déjà été soumis.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    documents_requis = {'CNI', 'RIB', 'HISTORIQUE_BANQUE', 'NIU'}
    documents_presents = set(
        dossier.documents.values_list('type_document', flat=True)
    )
    manquants = documents_requis - documents_presents
    if manquants:
        dossier.statut = Dossier.Statut.DOCUMENTS_INCOMPLETS
        dossier.save()
        return Response(
            {'detail': 'Documents manquants.', 'documents_manquants': list(manquants)},
            status=status.HTTP_400_BAD_REQUEST
        )

    calculer_et_sauvegarder_score(dossier)
    dossier.statut    = Dossier.Statut.SOUMIS
    dossier.soumis_le = timezone.now()
    dossier.save()

    return Response({
        'detail':        'Dossier soumis avec succès. Score IA calculé.',
        'score':         dossier.score.score,
        'niveau_risque': dossier.score.niveau_risque,
        'decision_ia':   dossier.score.decision_ia,
    })


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
    from accounts.models import Utilisateur

    dossier    = get_object_or_404(Dossier, pk=pk)
    user       = request.user
    decision   = request.data.get('decision')
    commentaire = request.data.get('commentaire', '')
    assigne_a_id = request.data.get('assigne_a')

    def _notifier_un(destinataire, message):
        """Crée une notification pour UN destinataire."""
        if not destinataire:
            return
        Notification.objects.create(
            destinataire=destinataire,
            dossier=dossier,
            message=message,
        )

    def _notifier_role(role, message):
        """Crée une notification pour TOUS les utilisateurs actifs d'un rôle donné."""
        destinataires = Utilisateur.objects.filter(role=role, is_active=True)
        for u in destinataires:
            _notifier_un(u, message)

    if not decision:
        return Response(
            {'detail': 'La décision est requise.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if decision not in [ValidationDossier.Decision.APPROUVE, ValidationDossier.Decision.REJETE]:
        return Response(
            {'detail': 'Décision invalide.'},
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

    if assigne_a and assigne_a.id == user.id:
        return Response(
            {'detail': 'Vous ne pouvez pas vous assigner vous-même.'},
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

    # Mise à jour du statut + notification de l'acteur suivant
    if decision == ValidationDossier.Decision.REJETE:
        dossier.statut = Dossier.Statut.REJETE

    elif user.est_chef_agence_commerciale:
        if dossier.statut == Dossier.Statut.SOUMIS:
            if not assigne_a:
                return Response(
                    {'detail': 'Vous devez assigner un analyste.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            dossier.statut = Dossier.Statut.EN_ANALYSE_1
            _notifier_un(
                assigne_a,
                f'Le dossier #{dossier.id} vous est assigné pour analyse (1er avis).'
            )

    elif user.est_analyste:
        if dossier.statut == Dossier.Statut.EN_ANALYSE_1:
            if not assigne_a:
                return Response(
                    {'detail': 'Vous devez assigner le 2ème analyste.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            dossier.statut = Dossier.Statut.EN_ANALYSE_2
            _notifier_un(
                assigne_a,
                f'Le dossier #{dossier.id} vous est assigné pour la 2ème analyse.'
            )

        elif dossier.statut == Dossier.Statut.EN_ANALYSE_2:
            dossier.statut = Dossier.Statut.ANALYSE_TERMINEE
            _notifier_role(
                Utilisateur.Role.CHEF_AGENCE_ANALYSE,
                f'Le dossier #{dossier.id} a terminé sa double analyse et attend votre visa.'
            )

    elif user.est_chef_agence_analyse:
        if dossier.statut == Dossier.Statut.ANALYSE_TERMINEE:
            if dossier.necessite_comite:
                dossier.statut = Dossier.Statut.EN_COMITE
                _notifier_role(
                    Utilisateur.Role.COMITE,
                    f'Le dossier #{dossier.id} attend la décision du comité.'
                )
            else:
                dossier.statut = Dossier.Statut.EN_DECISION
                _notifier_role(
                    Utilisateur.Role.DIRECTION,
                    f'Le dossier #{dossier.id} attend la décision finale de la direction.'
                )

    elif user.role == 'COMITE':
        if dossier.statut == Dossier.Statut.EN_COMITE:
            dossier.statut = Dossier.Statut.EN_DECISION
            _notifier_role(
                Utilisateur.Role.DIRECTION,
                f'Le dossier #{dossier.id} a reçu l\'avis du comité et attend la décision finale.'
            )

    elif user.est_direction:
        if dossier.statut == Dossier.Statut.EN_DECISION:
            dossier.statut = Dossier.Statut.APPROUVE

    dossier.save()

    if dossier.statut == Dossier.Statut.APPROUVE:
        _notifier_un(dossier.commercial, f'Votre dossier #{dossier.id} a été approuvé.')
    elif dossier.statut == Dossier.Statut.REJETE:
        _notifier_un(dossier.commercial, f'Votre dossier #{dossier.id} a été rejeté.')

    return Response({'detail': 'Décision enregistrée avec succès.'})

def _determiner_etape(user, dossier):
    """
    Détermine l'étape de validation selon le rôle
    et le statut actuel du dossier.

    :return: str étape ou None si non autorisé
    """
    if user.est_chef_agence_commerciale:
        if dossier.statut == Dossier.Statut.SOUMIS:
            return ValidationDossier.Etape.VISA_CHEF_AGENCE

    if user.est_analyste:
        if dossier.statut == Dossier.Statut.EN_ANALYSE_1:
            return ValidationDossier.Etape.AVIS_ANALYSTE1
        if dossier.statut == Dossier.Statut.EN_ANALYSE_2:
            return ValidationDossier.Etape.AVIS_ANALYSTE2

    if user.est_chef_agence_analyse:
        if dossier.statut == Dossier.Statut.ANALYSE_TERMINEE:
            return ValidationDossier.Etape.VISA_CHEF_ANALYSTE

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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def historique_salaires(request, client_pk):
    """
    Liste et ajout d'historique salaire d'un client.

    GET  /api/dossiers/clients/<id>/salaires/
    POST /api/dossiers/clients/<id>/salaires/
    """
    from .models import HistoriqueSalaire, Client

    if request.method == 'GET':
        historiques = HistoriqueSalaire.objects.filter(client=client).order_by('-date_effet')
        data = [
            {
                'id':              h.id,
                'salaire':         h.salaire,
                'date_effet':      h.date_effet,
                'note':            h.note,
                'enregistre_par':  h.enregistre_par.get_full_name() if h.enregistre_par else None,
            }
            for h in historiques
        ]
        return Response(data)
    
    client = get_object_or_404(Client, pk=client_pk)
    
    if request.method == 'POST' and not request.user.est_commercial:
        return Response(
            {'detail': 'Seul le commercial peut effectuer cette action.'},
            status=status.HTTP_403_FORBIDDEN
        )

    elif request.method == 'POST':
        salaire    = request.data.get('salaire')
        date_effet = request.data.get('date_effet')
        note       = request.data.get('note', '')

        if not salaire or not date_effet:
            return Response(
                {'detail': 'Salaire et date d\'effet requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from decimal import Decimal
        historique = HistoriqueSalaire.objects.create(
            client         = client,
            salaire        = Decimal(str(salaire)),
            date_effet     = date_effet,
            note           = note,
            enregistre_par = request.user,
        )

        # Mettre à jour le salaire actuel du client
        client.salaire_net = historique.salaire
        client.save()

        # Recalculer les scores des dossiers actifs
        from scoring.moteur import MoteurScoring
        scores_recalcules = MoteurScoring.recalculer_pour_client(client)

        return Response({
            'detail':           'Salaire mis à jour et scores recalculés.',
            'scores_recalcules': len(scores_recalcules),
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def impayes_client(request, client_pk):
    """
    Liste et ajout d'impayés d'un client SCE.

    GET  /api/dossiers/clients/<id>/impayes/
    POST /api/dossiers/clients/<id>/impayes/
    """
    from .models import ImpayeSCE, Client

    client = get_object_or_404(Client, pk=client_pk)

    if request.method == 'GET':
        impayes = ImpayeSCE.objects.filter(client=client)
        data = [
            {
                'id':                  i.id,
                'dossier_id':          i.dossier.id,
                'montant_impaye':      float(i.montant_impaye),
                'date_echeance':       i.date_echeance,
                'statut':              i.statut,
                'statut_display':      i.get_statut_display(),
                'nb_mois_retard':      i.nb_mois_retard,
                'date_regularisation': i.date_regularisation,
            }
            for i in impayes
        ]
        return Response(data)

    elif request.method == 'POST':
        dossier_id    = request.data.get('dossier_id')
        montant       = request.data.get('montant_impaye')
        date_echeance = request.data.get('date_echeance')
        nb_mois       = request.data.get('nb_mois_retard', 1)

        if not all([dossier_id, montant, date_echeance]):
            return Response(
                {'detail': 'Dossier, montant et date d\'échéance requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from dossiers.models import Dossier
        from decimal import Decimal

        dossier = get_object_or_404(Dossier, pk=dossier_id, client=client)

        ImpayeSCE.objects.create(
            client          = client,
            dossier         = dossier,
            montant_impaye  = Decimal(str(montant)),
            date_echeance   = date_echeance,
            nb_mois_retard  = int(nb_mois),
        )

        # Recalculer le score du dossier concerné
        from scoring.services import calculer_et_sauvegarder_score
        calculer_et_sauvegarder_score(dossier)

        return Response(
            {'detail': 'Impayé enregistré et score recalculé.'},
            status=status.HTTP_201_CREATED
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regulariser_impaye(request, impaye_pk):
    """
    Régularise un impayé SCE.

    POST /api/dossiers/impayes/<id>/regulariser/
    """
    from .models import ImpayeSCE
    from datetime import date

    impaye = get_object_or_404(ImpayeSCE, pk=impaye_pk)
    if not request.user.est_commercial:
        return Response(
            {'detail': 'Seul le commercial peut effectuer cette action.'},
            status=status.HTTP_403_FORBIDDEN
        )
    impaye.statut              = ImpayeSCE.Statut.REGULARISE
    impaye.date_regularisation = date.today()
    impaye.save()

    # Recalculer le score
    from scoring.services import calculer_et_sauvegarder_score
    calculer_et_sauvegarder_score(impaye.dossier)

    return Response({'detail': 'Impayé régularisé et score recalculé.'})


@api_view(['POST'])
@permission_classes([EstCommercial])
def recalculer_score(request, pk):
    """
    Recalcule le score d'un dossier manuellement.
    Utilisé après modification des infos client.

    POST /api/dossiers/<id>/recalculer/
    """
    dossier = get_object_or_404(Dossier, pk=pk)

    from scoring.services import calculer_et_sauvegarder_score
    score = calculer_et_sauvegarder_score(dossier)

    return Response({
        'detail': 'Score recalculé avec succès.',
        'score':  score.score,
        'decision': score.decision_ia,
    })
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rechercher_client(request):
    """
    Recherche des clients par numéro CNI — recherche partielle,
    insensible à la casse et aux espaces, tolère une saisie imprécise.
    Retourne jusqu'à 5 candidats plutôt qu'un résultat unique.

    GET /api/dossiers/clients/recherche/?cni=<numero>
    """
    from django.db.models import Value
    from django.db.models.functions import Replace

    cni_saisi = request.query_params.get('cni', '').strip().replace(' ', '')
    if not cni_saisi:
        return Response(
            {'detail': 'Le paramètre cni est requis.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    clients = Client.objects.annotate(
        cni_normalise=Replace('numero_cni', Value(' '), Value(''))
    ).filter(
        cni_normalise__icontains=cni_saisi
    )[:5]

    if not clients:
        return Response(
            {'detail': 'Aucun client trouvé avec ce numéro CNI.'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(ClientSerializer(clients, many=True).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_notifications(request):
    """GET /api/dossiers/notifications/ — notifications de l'utilisateur connecté."""
    notifs = Notification.objects.filter(destinataire=request.user, lue=False)
    data = [
        {'id': n.id, 'message': n.message, 'dossier_id': n.dossier_id, 'cree_le': n.cree_le}
        for n in notifs
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marquer_notification_lue(request, pk):
    """POST /api/dossiers/notifications/<id>/lue/"""
    notif = get_object_or_404(Notification, pk=pk, destinataire=request.user)
    notif.lue = True
    notif.save()
    return Response({'detail': 'Notification marquée comme lue.'})


@api_view(['DELETE'])
@permission_classes([EstCommercial])
def supprimer_dossier(request, pk):
    """
    Supprime un dossier encore en brouillon — réservé au commercial
    propriétaire, uniquement si le dossier n'a pas encore été soumis.

    DELETE /api/dossiers/<id>/
    """
    dossier = get_object_or_404(Dossier, pk=pk, commercial=request.user)

    if dossier.statut not in [Dossier.Statut.BROUILLON, Dossier.Statut.DOCUMENTS_INCOMPLETS]:
        return Response(
            {'detail': 'Seul un dossier en brouillon peut être supprimé.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    dossier.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)