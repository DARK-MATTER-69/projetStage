from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    """Sérialise les informations publiques d'un utilisateur."""

    class Meta:
        model   = Utilisateur
        fields  = [
            'id', 'username', 'first_name', 'last_name',
            'email', 'role', 'agence', 'telephone'
        ]
        read_only_fields = ['id']


class CreationUtilisateurSerializer(serializers.ModelSerializer):
    """
    Sérialise la création d'un nouvel utilisateur.
    Réservé à l'administrateur.
    """

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta:
        model  = Utilisateur
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'agence', 'telephone', 'password'
        ]

    def create(self, validated_data):
        """Crée un utilisateur avec mot de passe hashé."""
        password = validated_data.pop('password')
        user     = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ModificationMotDePasseSerializer(serializers.Serializer):
    """Sérialise le changement de mot de passe."""

    ancien_mot_de_passe  = serializers.CharField(write_only=True)
    nouveau_mot_de_passe = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    def validate_ancien_mot_de_passe(self, value):
        """Vérifie que l'ancien mot de passe est correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe incorrect.")
        return value

    def save(self):
        """Applique le nouveau mot de passe."""
        user = self.context['request'].user
        user.set_password(self.validated_data['nouveau_mot_de_passe'])
        user.save()
        return user