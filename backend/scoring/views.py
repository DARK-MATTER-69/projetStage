from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from dossiers.models import Dossier
from .models import ScoreCredit
from .serializers import ScoreCreditSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def score_dossier(request, dossier_pk):
    """
    Retourne le score IA d'un dossier.

    GET /api/scoring/<dossier_pk>/
    """
    dossier = get_object_or_404(Dossier, pk=dossier_pk)
    score   = get_object_or_404(ScoreCredit, dossier=dossier)
    return Response(ScoreCreditSerializer(score).data)