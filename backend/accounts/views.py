from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Utilisateur
from .serializers import (
    UtilisateurSerializer,
    CreationUtilisateurSerializer,
    ModificationMotDePasseSerializer
)


class PermissionAdminUniquement(IsAuthenticated):
    """Autorise uniquement les administrateurs."""

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role == Utilisateur.Role.ADMINISTRATEUR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profil(request):
    """
    Retourne le profil de l'utilisateur connecté.

    GET /api/auth/profil/
    """
    serializer = UtilisateurSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def modifier_profil(request):
    """
    Modifie le profil de l'utilisateur connecté.

    PUT /api/auth/profil/modifier/
    """
    serializer = UtilisateurSerializer(
        request.user,
        data=request.data,
        partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def modifier_mot_de_passe(request):
    """
    Modifie le mot de passe de l'utilisateur connecté.

    POST /api/auth/mot-de-passe/modifier/
    """
    serializer = ModificationMotDePasseSerializer(
        data=request.data,
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response({'detail': 'Mot de passe modifié avec succès.'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListeUtilisateursView(generics.ListCreateAPIView):
    """
    Liste et création des utilisateurs.
    Réservé à l'administrateur.

    GET  /api/auth/utilisateurs/
    POST /api/auth/utilisateurs/
    """

    queryset            = Utilisateur.objects.all().order_by('last_name')
    permission_classes  = [PermissionAdminUniquement]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreationUtilisateurSerializer
        return UtilisateurSerializer


class DetailUtilisateurView(generics.RetrieveUpdateDestroyAPIView):
    """
    Consultation, modification et suppression d'un utilisateur.
    Réservé à l'administrateur.

    GET    /api/auth/utilisateurs/<id>/
    PUT    /api/auth/utilisateurs/<id>/
    DELETE /api/auth/utilisateurs/<id>/
    """

    queryset            = Utilisateur.objects.all()
    serializer_class    = UtilisateurSerializer
    permission_classes  = [PermissionAdminUniquement]