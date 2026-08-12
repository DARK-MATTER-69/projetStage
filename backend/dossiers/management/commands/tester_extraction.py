from django.core.management.base import BaseCommand
from scoring.gemini import ExtracteurReleveGemini


class Command(BaseCommand):
    help = "Teste l'extraction Gemini d'un relevé bancaire PDF"

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf',
            type=str,
            required=True,
            help='Chemin vers le fichier PDF à tester'
        )

    def handle(self, *args, **options):
        chemin = options['pdf']
        self.stdout.write(f'Extraction Gemini de : {chemin}\n')

        extracteur = ExtracteurReleveGemini()
        resultat   = extracteur.extraire(chemin)

        if not resultat.succes:
            self.stdout.write(
                self.style.ERROR(f'Erreur : {resultat.message}')
            )
            return

        self.stdout.write(self.style.SUCCESS('Extraction réussie !\n'))
        self.stdout.write(f'Banque détectée        : {resultat.banque_detectee}')
        self.stdout.write(f'Opérations extraites   : {resultat.nb_operations}')
        self.stdout.write(f'Total crédits 3 mois   : {resultat.total_credits:>15,.0f} FCFA')
        self.stdout.write(f'Total débits 3 mois    : {resultat.total_debits:>15,.0f} FCFA')
        self.stdout.write(f'Moy. crédits/mois      : {resultat.moyenne_credits_mensuelle:>15,.0f} FCFA')
        self.stdout.write(f'Moy. débits/mois       : {resultat.moyenne_debits_mensuelle:>15,.0f} FCFA')
        self.stdout.write(f'Remb. crédits détectés : {resultat.remboursements_credits:>15,.0f} FCFA')
        self.stdout.write(f'Découvert détecté      : {"Oui" if resultat.decouvert_detecte else "Non"}')

        if resultat.solde_final:
            self.stdout.write(
                f'Solde final            : {resultat.solde_final:>15,.0f} FCFA'
            )
        if resultat.solde_moyen:
            self.stdout.write(
                f'Solde moyen            : {resultat.solde_moyen:>15,.0f} FCFA'
            )
        self.stdout.write(f'\nMessage : {resultat.message}')