from rest_framework.permissions import BasePermission
from accounts.models import Utilisateur


class EstCommercial(BasePermission):
    """Autorise uniquement les commerciaux."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Utilisateur.Role.COMMERCIAL
        )


class PeutValiderDossier(BasePermission):
    """
    Autorise les acteurs du circuit de validation :
    chef d'agence, analyste, direction et comité.
    """

    ROLES_AUTORISES = [
        Utilisateur.Role.CHEF_AGENCE_COMMERCIALE,
        Utilisateur.Role.CHEF_AGENCE_ANALYSE,
        Utilisateur.Role.ANALYSTE,
        Utilisateur.Role.DIRECTION,
        Utilisateur.Role.COMITE,
    ]

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.ROLES_AUTORISES
        )