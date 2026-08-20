from django.core.management.base import BaseCommand
from django.db import transaction

from scoring.models import ScoreCredit
from dossiers.models import (
    DocumentDossier, ValidationDossier, Dossier, Client,
    HistoriqueSalaire, ImpayeSCE, Notification,
)
from accounts.models import Utilisateur


class Command(BaseCommand):
    """
    Supprime toutes les données fictives générées par generer_donnees.
    Conserve les vrais utilisateurs (superusers) et les comptes de
    test par rôle (recréés/réutilisés à chaque génération).
    """

    help = 'Supprime toutes les données fictives de la base'

    def handle(self, *args, **options):
        self.stdout.write('Suppression des données fictives en cours...')

        with transaction.atomic():
            scores      = ScoreCredit.objects.all().count()
            validations = ValidationDossier.objects.all().count()
            documents   = DocumentDossier.objects.all().count()
            historiques = HistoriqueSalaire.objects.all().count()
            impayes     = ImpayeSCE.objects.all().count()
            notifs      = Notification.objects.all().count()
            dossiers    = Dossier.objects.all().count()
            clients     = Client.objects.all().count()

            ScoreCredit.objects.all().delete()
            ValidationDossier.objects.all().delete()
            DocumentDossier.objects.all().delete()
            Notification.objects.all().delete()
            Dossier.objects.all().delete()
            Client.objects.all().delete()
            Utilisateur.objects.filter(
                username='commercial_test'
            ).delete()

        self.stdout.write(self.style.SUCCESS(
            f'\nSuppression terminée :'
            f'\n  {scores} scores supprimés'
            f'\n  {validations} validations supprimées'
            f'\n  {documents} documents supprimés'
            f'\n  {historiques} historiques de salaire supprimés'
            f'\n  {impayes} impayés supprimés'
            f'\n  {notifs} notifications supprimées'
            f'\n  {dossiers} dossiers supprimés'
            f'\n  {clients} clients supprimés'
        ))