from django.core.management.base import BaseCommand
from scoring.ml.entrainement import entrainer_modele


class Command(BaseCommand):
    """
    Commande Django pour entraîner le modèle ML de scoring crédit.

    Usage :
        python manage.py entrainer_modele
    """

    help = 'Entraîne le modèle ML de scoring crédit'

    def handle(self, *args, **options):
        self.stdout.write('Démarrage de l\'entraînement...\n')
        try:
            metriques = entrainer_modele()
            self.stdout.write(self.style.SUCCESS(
                f'\nEntraînement terminé :'
                f'\n  Précision     : {metriques["accuracy"]}%'
                f'\n  Dossiers      : {metriques["nb_dossiers"]}'
                f'\n  Entraînement  : {metriques["nb_train"]}'
                f'\n  Test          : {metriques["nb_test"]}'
                f'\n  Modèle        : {metriques["chemin_modele"]}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur : {e}'))