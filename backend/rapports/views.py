from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from dossiers.models import Dossier
from .utils import generer_rapport_pdf


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def telecharger_rapport(request, dossier_pk):
    """
    Génère et retourne le rapport PDF d'un dossier.

    GET /api/rapports/<dossier_pk>/
    """
    dossier = get_object_or_404(Dossier, pk=dossier_pk)

    pdf     = generer_rapport_pdf(dossier)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="rapport_dossier_{dossier_pk:06d}.pdf"'
    )
    return response