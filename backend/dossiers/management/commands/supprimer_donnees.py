from django.core.management.base import BaseCommand
from django.db import transaction

from scoring.models import ScoreCredit
from dossiers.models import DocumentDossier, ValidationDossier, Dossier, Client
from accounts.models import Utilisateur


class Command(BaseCommand):
    """
    Supprime toutes les données fictives générées par generer_donnees.
    Conserve les vrais utilisateurs (superusers).

    Usage :
        python manage.py supprimer_donnees
    """

    help = 'Supprime toutes les données fictives de la base'

    def handle(self, *args, **options):
        self.stdout.write('Suppression des données fictives en cours...')

        with transaction.atomic():
            scores    = ScoreCredit.objects.all().count()
            validations = ValidationDossier.objects.all().count()
            documents = DocumentDossier.objects.all().count()
            dossiers  = Dossier.objects.all().count()
            clients   = Client.objects.all().count()

            ScoreCredit.objects.all().delete()
            ValidationDossier.objects.all().delete()
            DocumentDossier.objects.all().delete()
            Dossier.objects.all().delete()
            Client.objects.all().delete()

            # Supprime uniquement le commercial fictif, pas les superusers
            Utilisateur.objects.filter(
                username='commercial_test'
            ).delete()

        self.stdout.write(self.style.SUCCESS(
            f'\nSuppression terminée :'
            f'\n  {scores} scores supprimés'
            f'\n  {validations} validations supprimées'
            f'\n  {documents} documents supprimés'
            f'\n  {dossiers} dossiers supprimés'
            f'\n  {clients} clients supprimés'
        ))