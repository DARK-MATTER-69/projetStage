import random
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from accounts.models import Utilisateur
from dossiers.models import Client, Dossier
from scoring.services import calculer_et_sauvegarder_score


class Command(BaseCommand):

    help = 'Génère des données fictives pour le scoring crédit'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nombre',
            type=int,
            default=100,
            help='Nombre de dossiers à générer (défaut : 600)'
        )
        parser.add_argument(
            '--depuis',
            type=int,
            default=0,
            help='Reprendre la génération depuis un index précis (défaut : 0)'
        )

    def handle(self, *args, **options):
        nombre = options['nombre']
        depuis = options['depuis']
        self.stdout.write(f'Génération de {nombre} dossiers en cours...')
        self._generer(nombre, depuis)

    def _date_aleatoire(self, debut, fin):
        """Génère une date aléatoire entre deux dates."""
        delta = fin - debut
        return debut + timedelta(days=random.randint(0, delta.days))

    def _generer(self, nombre, depuis=0):
        """Génère les clients et dossiers fictifs en évitant les doublons."""

        commercial, created = Utilisateur.objects.get_or_create(
            username='commercial_test',
            defaults={
                'first_name': 'Wansi',
                'last_name':  'Brayann',
                'role': Utilisateur.Role.COMMERCIAL,
                'agence': 'Yaoundé Centre',
            }
        )
        if created or not commercial.has_usable_password():
            commercial.set_password('Test@1234')
            commercial.save()

        # Calcule le prochain index disponible
        dernier_index = Client.objects.filter(
            numero_cni__startswith='CNI'
        ).count()
        debut = max(depuis, dernier_index)

        self.stdout.write(f'Reprise depuis l\'index {debut}...')

        employeurs = [
            ('FONCTIONNAIRE', ['Ministère des Finances', 'MINESUP', 'Armée Camerounaise', 'Police Nationale']),
            ('PRIVE', ['MTN Cameroun', 'Orange Cameroun', 'Société Générale', 'Total Energies']),
            ('ONG', ['Croix Rouge Cameroun', 'Plan International', 'UNICEF Cameroun']),
            ('COMMERCANT', ['Commerce général', 'Boutique textile', 'Alimentation générale']),
            ('RETRAITE', ['Retraité CNPS', 'Retraité Fonction Publique']),
        ]

        types_credit = ['EQUIPEMENT', 'SCOLAIRE', 'CONSOMMATION']

        objets = [
            'Achat téléviseur et climatiseur',
            'Frais de scolarité universitaire',
            'Achat réfrigérateur et cuisinière',
            'Achat moto pour usage personnel',
            'Achat matériaux de construction',
            'Achat ordinateur portable',
            'Frais médicaux et hospitalisation',
        ]

        villes = ['Yaoundé', 'Douala', 'Bafoussam', 'Garoua', 'Bertoua', 'Ngaoundéré']
        quartiers = ['Bastos', 'Melen', 'Ngousso', 'Biyem-Assi', 'Akwa', 'Bonanjo']
        postes = ['Agent', 'Cadre', 'Technicien', 'Directeur', 'Secrétaire', 'Comptable']

        compteur = 0

        for i in range(debut, debut + nombre):
            type_emp, noms_employeurs = random.choice(employeurs)

            # Salaire selon type d'employeur
            salaires = {
                'FONCTIONNAIRE': (80,  400),
                'RETRAITE': (60,  200),
                'PRIVE': (100, 500),
                'ONG': (150, 600),
                'COMMERCANT': (50,  300),
            }
            mini, maxi = salaires[type_emp]
            salaire = Decimal(random.randint(mini, maxi) * 1000)
            anciennete = random.randint(0, 25)
            charges = salaire * Decimal(str(round(random.uniform(0.05, 0.25), 2)))
            credits_en_cours = salaire * Decimal(str(round(random.uniform(0.00, 0.20), 2)))
            jour_salaire = random.choice([15, 25, 28, 30])
            jour_prelevement = max(1, min(28, jour_salaire + random.randint(-3, 10)))

            try:
                client = Client.objects.create(
                    civilite  = random.choice(['M', 'MME']),
                    nom= f'CLIENT{i:04d}',
                    prenom  = f'Prenom{i:04d}',
                    date_naissance= self._date_aleatoire(
                        date(1965, 1, 1), date(2000, 1, 1)
                    ),
                    lieu_naissance   = random.choice(villes),
                    nationalite   = 'Camerounaise',
                    numero_cni = f'CNI{i:08d}',
                    telephone= f'6{random.randint(10000000, 99999999)}',
                    adresse = f'Quartier {random.choice(quartiers)}',
                    type_employeur = type_emp,
                    nom_employeur = random.choice(noms_employeurs),
                    poste_occupe = random.choice(postes),
                    anciennete = anciennete,
                    salaire_net = salaire,
                    charges_mensuelles  = charges,
                    credits_en_cours  = credits_en_cours,
                    date_versement_salaire = jour_salaire,
                    cree_par = commercial,
                )

                montant = Decimal(random.randint(1, 20) * 100000)
                duree   = random.choice([6, 12, 18, 24, 36])

                dossier = Dossier.objects.create(
                    client  = client,
                    commercial = commercial,
                    type_credit  = random.choice(types_credit),
                    montant_sollicite = montant,
                    duree_mois  = duree,
                    objet_financement = random.choice(objets),
                    appreciation= (
                        f'Client sérieux avec {anciennete} ans d\'ancienneté. '
                        f'Dossier complet et conforme.'
                    ),
                    statut            = Dossier.Statut.SOUMIS,
                    jour_prelevement  = jour_prelevement,
                )

                calculer_et_sauvegarder_score(dossier)
                compteur += 1

                if compteur % 50 == 0:
                    self.stdout.write(f'  {compteur}/{nombre} dossiers generés...')

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Erreur dossier {i} : {e}'))
                continue

        self.stdout.write(
            self.style.SUCCESS(f'\nTerminé : {compteur} dossiers générés avec succès.')
         )
         