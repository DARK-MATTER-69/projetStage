import random
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from accounts.models import Utilisateur
from dossiers.models import Client, Dossier, HistoriqueSalaire, ImpayeSCE
from scoring.services import calculer_et_sauvegarder_score


class Command(BaseCommand):

    help = 'Génère des données fictives pour le scoring crédit'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nombre',
            type=int,
            default=100,
            help='Nombre de clients à générer (défaut : 100)'
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
        self.stdout.write(f'Génération de {nombre} clients en cours...')
        self._creer_equipe_test()
        self._generer(nombre, depuis)

    def _date_aleatoire(self, debut, fin):
        """Génère une date aléatoire entre deux dates."""
        delta = fin - debut
        return debut + timedelta(days=random.randint(0, delta.days))

    def _creer_equipe_test(self):
        """
        Crée un utilisateur de test par rôle du circuit,
        pour pouvoir tester le workflow de validation complet.
        """
        equipe = [
            ('commercial_test',    'Wansi',    'Brayann',  Utilisateur.Role.COMMERCIAL),
            ('chef_com_test',      'Kaleuck',  'Sonya',    Utilisateur.Role.CHEF_AGENCE_COMMERCIALE),
            ('chef_analyse_test',  'Kamdem',   'Rudy',     Utilisateur.Role.CHEF_AGENCE_ANALYSE),
            ('analyste1_test',     'Siani',    'Ludivick', Utilisateur.Role.ANALYSTE),
            ('analyste2_test',     'Tchamni',  'Darlene',  Utilisateur.Role.ANALYSTE),
            ('direction_test',     'Nintcheu', 'Delva',    Utilisateur.Role.DIRECTION),
            ('comite_test',        'Ange',     'Douce',    Utilisateur.Role.COMITE),
        ]

        for username, prenom, nom, role in equipe:
            utilisateur, cree = Utilisateur.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': prenom,
                    'last_name':  nom,
                    'role':       role,
                    'agence':     'Yaoundé Centre',
                }
            )
            if cree or not utilisateur.has_usable_password():
                utilisateur.set_password('Test@1234')
                utilisateur.save()

        self.stdout.write(self.style.SUCCESS(
            'Équipe de test prête (mot de passe : Test@1234 pour tous).'
        ))

    def _generer(self, nombre, depuis=0):
        """Génère les clients et leur historique de dossiers fictifs."""

        commercial = Utilisateur.objects.get(username='commercial_test')

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

        types_credit  = ['EQUIPEMENT', 'SCOLAIRE', 'CONSOMMATION']
        assureurs     = ['SAAR Assurances', 'Activa Assurances', 'Chanas Assurances', '']

        objets = [
            'Achat téléviseur et climatiseur',
            'Frais de scolarité universitaire',
            'Achat réfrigérateur et cuisinière',
            'Achat de terrain',
            'Achat matériaux de construction',
            'Achat ordinateur portable',
            'Frais médicaux et hospitalisation',
        ]

        villes    = ['Yaoundé', 'Douala', 'Bafoussam', 'Garoua', 'Bertoua', 'Ngaoundéré']
        quartiers = ['Bastos', 'Melen', 'Ngousso', 'Biyem-Assi', 'Akwa', 'Bonanjo']
        postes    = ['Agent', 'Cadre', 'Technicien', 'Directeur', 'Secrétaire', 'Comptable']

        # Statuts finaux possibles pour qu'un dossier compte pour l'entraînement ML
        # (BROUILLON est exclu par charger_donnees())
        statuts_en_cours = [
            Dossier.Statut.SOUMIS, Dossier.Statut.VALIDE_CHEF_COMMERCIAL,
            Dossier.Statut.EN_ANALYSE_1, Dossier.Statut.EN_ANALYSE_2,
            Dossier.Statut.ANALYSE_TERMINEE,Dossier.Statut.VALIDE_CHEF_ANALYSTE,
            Dossier.Statut.EN_DECISION, Dossier.Statut.EN_COMITE,
        ]

        compteur_clients  = 0
        compteur_dossiers = 0

        for i in range(debut, debut + nombre):
            type_emp, noms_employeurs = random.choice(employeurs)

            salaires = {
                'FONCTIONNAIRE': (80,  400),
                'RETRAITE':      (60,  200),
                'PRIVE':         (100, 500),
                'ONG':           (150, 600),
                'COMMERCANT':    (50,  300),
            }
            mini, maxi = salaires[type_emp]
            salaire_initial   = Decimal(random.randint(mini, maxi) * 1000)
            anciennete        = random.randint(0, 25)
            charges           = salaire_initial * Decimal(str(round(random.uniform(0.05, 0.25), 2)))
            credits_en_cours  = salaire_initial * Decimal(str(round(random.uniform(0.00, 0.20), 2)))
            jour_salaire      = random.choice([15, 25, 28, 30])

            # Profil de risque du client — influence impayés et rejets
            profil_risque = random.random()   # 0 = très fiable, 1 = risqué

            try:
                client = Client.objects.create(
                    civilite                = random.choice(['M', 'MME']),
                    nom                     = f'CLIENT{i:04d}',
                    prenom                  = f'Prenom{i:04d}',
                    date_naissance          = self._date_aleatoire(
                        date(1965, 1, 1), date(2000, 1, 1)
                    ),
                    lieu_naissance          = random.choice(villes),
                    nationalite             = 'Camerounaise',
                    numero_cni              = f'CNI{i:08d}',
                    telephone               = f'6{random.randint(10000000, 99999999)}',
                    adresse                 = f'Quartier {random.choice(quartiers)}',
                    type_employeur          = type_emp,
                    nom_employeur           = random.choice(noms_employeurs),
                    poste_occupe            = random.choice(postes),
                    anciennete              = anciennete,
                    salaire_net             = salaire_initial,
                    charges_mensuelles      = charges,
                    credits_en_cours        = credits_en_cours,
                    date_versement_salaire  = jour_salaire,
                    cree_par                = commercial,
                )
                compteur_clients += 1

                # ── Historique salarial (1 à 3 revalorisations) ──────
                salaire_courant = salaire_initial
                nb_revalorisations = random.randint(0, 2)
                date_effet = date.today() - timedelta(days=random.randint(400, 1000))

                HistoriqueSalaire.objects.create(
                    client         = client,
                    salaire        = salaire_courant,
                    date_effet     = date_effet,
                    note           = 'Salaire initial',
                    enregistre_par = commercial,
                )
                for _ in range(nb_revalorisations):
                    date_effet      = date_effet + timedelta(days=random.randint(120, 300))
                    salaire_courant = salaire_courant * Decimal(str(round(random.uniform(1.05, 1.30), 2)))
                    HistoriqueSalaire.objects.create(
                        client         = client,
                        salaire        = salaire_courant,
                        date_effet     = min(date_effet, date.today()),
                        note           = random.choice(['Promotion', 'Revalorisation', 'Changement de poste']),
                        enregistre_par = commercial,
                    )
                client.salaire_net = salaire_courant
                client.save()

                # ── 1 à 3 dossiers, pour construire un historique ────
                nb_dossiers = random.randint(1, 3)
                dossiers_client = []

                for n in range(nb_dossiers):
                    montant = Decimal(random.randint(1, 20) * 100000)
                    duree   = random.choice([6, 12, 18, 24, 36])
                    echeance_banque = Decimal(random.randint(0, 3) * 15000)
                    encours_sce     = Decimal(random.randint(0, 2) * 200000)

                    dossier = Dossier.objects.create(
                        client                 = client,
                        commercial             = commercial,
                        type_credit            = random.choice(types_credit),
                        montant_sollicite      = montant,
                        duree_mois             = duree,
                        objet_financement      = random.choice(objets),
                        appreciation           = (
                            f'Client sérieux avec {anciennete} ans d\'ancienneté. '
                            f'Dossier complet et conforme.'
                        ),
                        jour_prelevement       = max(1, min(28, jour_salaire + random.randint(-3, 10))),
                        echeance_mens_banque   = echeance_banque,
                        encours_sce            = encours_sce,
                        assureur               = random.choice(assureurs),
                        montant_assurance_ttc  = montant * Decimal('0.02') if random.random() > 0.3 else Decimal('0'),
                        avi                    = random.random() > 0.5,
                        delegation_salaire     = random.random() > 0.6,
                    )

                    # Dernier dossier du client = en cours ; les précédents = déjà tranchés
                    est_dernier = (n == nb_dossiers - 1)
                    if est_dernier:
                        dossier.statut = random.choice(statuts_en_cours)
                    else:
                        dossier.statut = (
                            Dossier.Statut.REJETE if random.random() < profil_risque * 0.4
                            else Dossier.Statut.APPROUVE
                        )
                    dossier.save()

                    calculer_et_sauvegarder_score(dossier)
                    dossiers_client.append(dossier)
                    compteur_dossiers += 1

                # ── Impayés SCE (corrélés au profil de risque) ───────
                if profil_risque > 0.7 and dossiers_client:
                    nb_impayes = random.randint(1, 2)
                    for _ in range(nb_impayes):
                        dossier_concerne = random.choice(dossiers_client)
                        regularise = random.random() > 0.5
                        ImpayeSCE.objects.create(
                            client              = client,
                            dossier             = dossier_concerne,
                            montant_impaye      = dossier_concerne.mensualite_estimee,
                            date_echeance       = date.today() - timedelta(days=random.randint(30, 300)),
                            nb_mois_retard      = random.randint(1, 6),
                            statut              = (
                                ImpayeSCE.Statut.REGULARISE if regularise
                                else ImpayeSCE.Statut.EN_COURS
                            ),
                            date_regularisation = date.today() if regularise else None,
                        )

                if compteur_clients % 50 == 0:
                    self.stdout.write(
                        f'  {compteur_clients}/{nombre} clients '
                        f'({compteur_dossiers} dossiers) générés...'
                    )

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Erreur client {i} : {e}'))
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f'\nTerminé : {compteur_clients} clients et '
                f'{compteur_dossiers} dossiers générés avec succès.'
            )
        )