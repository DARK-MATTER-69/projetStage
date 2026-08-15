from rest_framework.permissions import BasePermission
from accounts.models import Utilisateur


class EstCommercial(BasePermission):
    """Autorise uniquement les commerciaux."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Utilisateur.Role.COMMERCIAL
        )


class EstChefAgence(BasePermission):
    """Autorise uniquement les chefs d'agence."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Utilisateur.Role.CHEF_AGENCE
        )


class EstAnalyste(BasePermission):
    """Autorise uniquement les analystes engagement."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Utilisateur.Role.ANALYSTE
        )


class EstDirection(BasePermission):
    """Autorise uniquement la direction."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Utilisateur.Role.DIRECTION
        )


class EstComite(BasePermission):
    """Autorise uniquement le comité."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Utilisateur.Role.COMITE
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