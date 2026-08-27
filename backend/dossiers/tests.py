from django.test import TestCase

# Create your tests here.
"""
Suite de tests automatisés — plateforme de gestion de crédit SCE.

Couvre :
  - Les propriétés calculées du modèle Dossier
  - Le circuit complet de validation (5 rôles)
  - Le recalcul automatique du score (salaire, impayé)
  - La recherche de client par CNI ("Nouveau prêt")
  - Les restrictions de permission par rôle
  - La création automatique de notifications

Lancer avec : python manage.py test dossiers
"""

from decimal import Decimal
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import Utilisateur
from dossiers.models import (
    Client, Dossier, DocumentDossier, HistoriqueSalaire,
    ImpayeSCE, Notification,
)
from scoring.services import calculer_et_sauvegarder_score


class BaseCircuitTestCase(TestCase):
    """Classe de base : crée un utilisateur par rôle et un client type."""

    def setUp(self):
        self.commercial = Utilisateur.objects.create_user(
            username='commercial_test', password='Test@1234',
            role=Utilisateur.Role.COMMERCIAL,
        )
        self.chef_commercial = Utilisateur.objects.create_user(
            username='chef_com_test', password='Test@1234',
            role=Utilisateur.Role.CHEF_AGENCE_COMMERCIALE,
        )
        self.analyste1 = Utilisateur.objects.create_user(
            username='analyste1_test', password='Test@1234',
            role=Utilisateur.Role.ANALYSTE,
        )
        self.analyste2 = Utilisateur.objects.create_user(
            username='analyste2_test', password='Test@1234',
            role=Utilisateur.Role.ANALYSTE,
        )
        self.chef_analyse = Utilisateur.objects.create_user(
            username='chef_analyse_test', password='Test@1234',
            role=Utilisateur.Role.CHEF_AGENCE_ANALYSE,
        )
        self.direction = Utilisateur.objects.create_user(
            username='direction_test', password='Test@1234',
            role=Utilisateur.Role.DIRECTION,
        )
        self.comite = Utilisateur.objects.create_user(
            username='comite_test', password='Test@1234',
            role=Utilisateur.Role.COMITE,
        )

        self.client_sce = Client.objects.create(
            civilite='M', nom='Ateba', prenom='Jean',
            date_naissance=date(1985, 5, 12), lieu_naissance='Yaoundé',
            numero_cni='CNI00000001', telephone='690000000',
            adresse='Bastos, Yaoundé', type_employeur='FONCTIONNAIRE',
            nom_employeur='MINESUP', poste_occupe='Cadre',
            anciennete=10, salaire_net=Decimal('300000'),
            charges_mensuelles=Decimal('20000'), credits_en_cours=Decimal('0'),
            cree_par=self.commercial,
        )

        self.api = APIClient()

    def _creer_dossier(self, montant='500000'):
        return Dossier.objects.create(
            client=self.client_sce, commercial=self.commercial,
            type_credit='EQUIPEMENT', montant_sollicite=Decimal(montant),
            duree_mois=12, objet_financement='Achat matériel',
            jour_prelevement=25,
        )

    def _uploader_documents_requis(self, dossier):
        for type_doc in ['CNI', 'RIB', 'HISTORIQUE_BANQUE', 'NIU']:
            DocumentDossier.objects.create(
                dossier=dossier, type_document=type_doc,
                fichier='dossiers/documents/test.pdf',
                nom_fichier='test.pdf', uploade_par=self.commercial,
            )


class TestProprietesDossier(BaseCircuitTestCase):
    """Vérifie les calculs financiers du modèle Dossier."""

    def test_mensualite_estimee(self):
        dossier = self._creer_dossier(montant='1200000')
        dossier.duree_mois = 12
        self.assertEqual(dossier.mensualite_estimee, Decimal('100000'))

    def test_traite_max_autorisee(self):
        dossier = self._creer_dossier()
        # 300000 * 0.33 - 0 = 99000
        self.assertEqual(dossier.traite_max_autorisee, Decimal('99000.00'))

    def test_quotite_relative(self):
        dossier = self._creer_dossier(montant='600000')
        dossier.duree_mois = 12  # mensualité = 50000
        dossier.echeance_mens_banque = Decimal('10000')
        # (50000 + 10000) / 300000 * 100 = 20.0
        self.assertEqual(dossier.quotite_relative, Decimal('20.00'))

    def test_necessite_comite_calcule_a_la_sauvegarde(self):
        dossier = self._creer_dossier(montant='6000000')
        self.assertTrue(dossier.necessite_comite)

        dossier2 = self._creer_dossier(montant='1000000')
        self.assertFalse(dossier2.necessite_comite)


class TestSoumissionDossier(BaseCircuitTestCase):
    """Vérifie le flux de soumission et la gestion des documents manquants."""

    def test_soumission_bloquee_si_documents_manquants(self):
        dossier = self._creer_dossier()
        self.api.force_authenticate(user=self.commercial)

        response = self.api.post(f'/api/dossiers/{dossier.id}/soumettre/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.DOCUMENTS_INCOMPLETS)

    def test_soumission_reussie_avec_documents_complets(self):
        dossier = self._creer_dossier()
        self._uploader_documents_requis(dossier)
        self.api.force_authenticate(user=self.commercial)

        response = self.api.post(f'/api/dossiers/{dossier.id}/soumettre/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('score', response.data)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.SOUMIS)
        self.assertTrue(hasattr(dossier, 'score'))

    def test_resoumission_apres_completion_documents(self):
        dossier = self._creer_dossier()
        self.api.force_authenticate(user=self.commercial)
        self.api.post(f'/api/dossiers/{dossier.id}/soumettre/')  # → DOCUMENTS_INCOMPLETS

        self._uploader_documents_requis(dossier)
        response = self.api.post(f'/api/dossiers/{dossier.id}/soumettre/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestCircuitValidationComplet(BaseCircuitTestCase):
    """
    Vérifie le circuit complet, rôle par rôle :
    Commercial → Chef commercial → Analyste1 → Analyste2
    → Chef analyse → (Comité) → Direction → APPROUVE
    """

    def _soumettre(self, dossier):
        self.api.force_authenticate(user=self.commercial)
        self._uploader_documents_requis(dossier)
        self.api.post(f'/api/dossiers/{dossier.id}/soumettre/')
        dossier.refresh_from_db()

    def test_chef_commercial_valide_et_assigne_analyste(self):
        dossier = self._creer_dossier()
        self._soumettre(dossier)

        self.api.force_authenticate(user=self.chef_commercial)
        response = self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'APPROUVE', 'commentaire': 'RAS', 'assigne_a': self.analyste1.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.EN_ANALYSE_1)

    def test_chef_commercial_sans_assignation_est_rejete(self):
        dossier = self._creer_dossier()
        self._soumettre(dossier)

        self.api.force_authenticate(user=self.chef_commercial)
        response = self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'APPROUVE', 'commentaire': 'RAS'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_circuit_complet_jusqu_a_approbation_sans_comite(self):
        dossier = self._creer_dossier(montant='800000')  # sous le seuil comité
        self._soumettre(dossier)

        # Chef d'agence commerciale → assigne analyste 1
        self.api.force_authenticate(user=self.chef_commercial)
        self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'APPROUVE', 'assigne_a': self.analyste1.id},
        )

        # Analyste 1 → assigne analyste 2
        self.api.force_authenticate(user=self.analyste1)
        r = self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'APPROUVE', 'assigne_a': self.analyste2.id},
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.EN_ANALYSE_2)

        # Analyste 2 → rend son avis
        self.api.force_authenticate(user=self.analyste2)
        r = self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'APPROUVE'},
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.ANALYSE_TERMINEE)

        # Chef d'agence analyse → 2ème signature
        self.api.force_authenticate(user=self.chef_analyse)
        r = self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'APPROUVE'},
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.EN_DECISION)

        # Direction → décision finale
        self.api.force_authenticate(user=self.direction)
        r = self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'APPROUVE'},
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.APPROUVE)

    def test_circuit_avec_comite_pour_montant_eleve(self):
        dossier = self._creer_dossier(montant='6000000')  # au-dessus du seuil
        self._soumettre(dossier)
        self.assertTrue(dossier.necessite_comite)

        self.api.force_authenticate(user=self.chef_commercial)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/',
                       {'decision': 'APPROUVE', 'assigne_a': self.analyste1.id})

        self.api.force_authenticate(user=self.analyste1)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/',
                       {'decision': 'APPROUVE', 'assigne_a': self.analyste2.id})

        self.api.force_authenticate(user=self.analyste2)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/', {'decision': 'APPROUVE'})

        self.api.force_authenticate(user=self.chef_analyse)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/', {'decision': 'APPROUVE'})

        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.EN_COMITE)

        # Comité → transmet à la direction (ne doit PAS approuver directement)
        self.api.force_authenticate(user=self.comite)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/', {'decision': 'APPROUVE'})
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.EN_DECISION)

        # Direction → décision finale réelle
        self.api.force_authenticate(user=self.direction)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/', {'decision': 'APPROUVE'})
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.APPROUVE)

    def test_rejet_a_n_importe_quelle_etape_est_final(self):
        dossier = self._creer_dossier()
        self._soumettre(dossier)

        self.api.force_authenticate(user=self.chef_commercial)
        response = self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'REJETE', 'commentaire': 'Dossier incomplet'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.REJETE)

    def test_notification_creee_a_l_approbation(self):
        dossier = self._creer_dossier(montant='800000')
        self._soumettre(dossier)

        self.api.force_authenticate(user=self.chef_commercial)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/',
                       {'decision': 'APPROUVE', 'assigne_a': self.analyste1.id})
        self.api.force_authenticate(user=self.analyste1)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/',
                       {'decision': 'APPROUVE', 'assigne_a': self.analyste2.id})
        self.api.force_authenticate(user=self.analyste2)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/', {'decision': 'APPROUVE'})
        self.api.force_authenticate(user=self.chef_analyse)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/', {'decision': 'APPROUVE'})
        self.api.force_authenticate(user=self.direction)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/', {'decision': 'APPROUVE'})

        self.assertTrue(
            Notification.objects.filter(
                destinataire=self.commercial, dossier=dossier, lue=False
            ).exists()
        )


class TestRecalculScore(BaseCircuitTestCase):
    """Vérifie le recalcul automatique du score sur événement client."""

    def test_nouveau_salaire_recalcule_le_score(self):
        dossier = self._creer_dossier()
        self._uploader_documents_requis(dossier)
        self.api.force_authenticate(user=self.commercial)
        self.api.post(f'/api/dossiers/{dossier.id}/soumettre/')

        response = self.api.post(
            f'/api/dossiers/clients/{self.client_sce.id}/salaires/',
            {'salaire': '450000', 'date_effet': '2026-08-01', 'note': 'Promotion'},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['scores_recalcules'], 1)
        self.client_sce.refresh_from_db()
        self.assertEqual(self.client_sce.salaire_net, Decimal('450000'))

    def test_seul_commercial_peut_ajouter_salaire(self):
        response_libre = self.api.post(
            f'/api/dossiers/clients/{self.client_sce.id}/salaires/',
            {'salaire': '450000', 'date_effet': '2026-08-01'},
        )
        self.assertIn(response_libre.status_code,
                       [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        self.api.force_authenticate(user=self.analyste1)
        response = self.api.post(
            f'/api/dossiers/clients/{self.client_sce.id}/salaires/',
            {'salaire': '450000', 'date_effet': '2026-08-01'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regularisation_impaye_recalcule_le_score(self):
        dossier = self._creer_dossier()
        self._uploader_documents_requis(dossier)
        self.api.force_authenticate(user=self.commercial)
        self.api.post(f'/api/dossiers/{dossier.id}/soumettre/')

        impaye = ImpayeSCE.objects.create(
            client=self.client_sce, dossier=dossier,
            montant_impaye=Decimal('50000'), date_echeance=date(2026, 1, 15),
            nb_mois_retard=2,
        )

        response = self.api.post(f'/api/dossiers/impayes/{impaye.id}/regulariser/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        impaye.refresh_from_db()
        self.assertEqual(impaye.statut, ImpayeSCE.Statut.REGULARISE)


class TestNouveauPret(BaseCircuitTestCase):
    """Vérifie la recherche de client existant pour un nouveau prêt."""

    def test_recherche_par_cni_exact(self):
        self.api.force_authenticate(user=self.commercial)
        response = self.api.get('/api/dossiers/clients/recherche/', {'cni': 'CNI00000001'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['numero_cni'], 'CNI00000001')

    def test_recherche_par_cni_introuvable(self):
        self.api.force_authenticate(user=self.commercial)
        response = self.api.get('/api/dossiers/clients/recherche/', {'cni': 'INEXISTANT'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nouveau_pret_ne_duplique_pas_le_client(self):
        nb_clients_avant = Client.objects.count()

        dossier1 = self._creer_dossier(montant='500000')
        dossier2 = Dossier.objects.create(
            client=self.client_sce, commercial=self.commercial,
            type_credit='CONSOMMATION', montant_sollicite=Decimal('300000'),
            duree_mois=6, objet_financement='Nouveau prêt',
        )

        self.assertEqual(Client.objects.count(), nb_clients_avant)
        self.assertEqual(
            Client.objects.get(numero_cni='CNI00000001').dossiers.count(), 2
        )

class TestScoringMoteur(BaseCircuitTestCase):
    """Vérifie que le moteur de scoring produit un résultat cohérent."""

    def test_calcul_score_cree_un_scorecredit(self):
        dossier = self._creer_dossier(montant='800000')
        score = calculer_et_sauvegarder_score(dossier)

        self.assertIsNotNone(score)
        self.assertGreaterEqual(score.score, 0)
        self.assertLessEqual(score.score, 100)
        self.assertIn(score.niveau_risque, ['FAIBLE', 'MOYEN', 'ELEVE', 'CRITIQUE'])
        self.assertIn(score.decision_ia, ['FAVORABLE', 'CONDITIONNEL', 'DEFAVORABLE'])

    def test_client_avec_impaye_est_penalise(self):
        dossier_propre = self._creer_dossier(montant='800000')
        score_propre = calculer_et_sauvegarder_score(dossier_propre)

        ImpayeSCE.objects.create(
            client=self.client_sce, dossier=dossier_propre,
            montant_impaye=Decimal('50000'), date_echeance=date(2026, 1, 15),
            nb_mois_retard=3, statut=ImpayeSCE.Statut.EN_COURS,
        )
        score_avec_impaye = calculer_et_sauvegarder_score(dossier_propre)

        self.assertLess(score_avec_impaye.score, score_propre.score)
        
class TestCorrectifsAudit(BaseCircuitTestCase):
    """
    Tests couvrant spécifiquement les failles corrigées lors de l'audit :
    décision invalide, auto-assignation, modification par un tiers,
    dossier verrouillé.
    """

    def _soumettre(self, dossier):
        self.api.force_authenticate(user=self.commercial)
        self._uploader_documents_requis(dossier)
        self.api.post(f'/api/dossiers/{dossier.id}/soumettre/')
        dossier.refresh_from_db()

    # --- B1 : la décision doit être APPROUVE ou REJETE, rien d'autre ---
    def test_decision_invalide_est_rejetee(self):
        dossier = self._creer_dossier()
        self._soumettre(dossier)

        self.api.force_authenticate(user=self.chef_commercial)
        response = self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'PEUT_ETRE', 'assigne_a': self.analyste1.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.SOUMIS)  # inchangé

    # --- B2 : un analyste ne peut pas s'auto-assigner comme 2ème signataire ---
    def test_analyste_ne_peut_pas_s_auto_assigner(self):
        dossier = self._creer_dossier()
        self._soumettre(dossier)

        self.api.force_authenticate(user=self.chef_commercial)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/',
                       {'decision': 'APPROUVE', 'assigne_a': self.analyste1.id})

        self.api.force_authenticate(user=self.analyste1)
        response = self.api.post(
            f'/api/dossiers/{dossier.id}/valider/',
            {'decision': 'APPROUVE', 'assigne_a': self.analyste1.id},  # lui-même
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        dossier.refresh_from_db()
        self.assertEqual(dossier.statut, Dossier.Statut.EN_ANALYSE_1)  # inchangé

    # --- S1 : un commercial ne peut pas modifier le dossier d'un collègue ---
    def test_commercial_ne_peut_pas_modifier_dossier_d_un_autre(self):
        autre_commercial = Utilisateur.objects.create_user(
            username='autre_commercial', password='Test@1234',
            role=Utilisateur.Role.COMMERCIAL,
        )
        dossier = self._creer_dossier()

        self.api.force_authenticate(user=autre_commercial)
        response = self.api.patch(
            f'/api/dossiers/{dossier.id}/',
            {'montant_sollicite': '9999999'},
        )
        self.assertIn(response.status_code,
                       [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        dossier.refresh_from_db()
        self.assertNotEqual(dossier.montant_sollicite, Decimal('9999999'))

    # --- S1 (bis) : un dossier verrouillé n'est plus modifiable par le commercial ---
    def test_dossier_verrouille_non_modifiable_par_commercial(self):
        dossier = self._creer_dossier()
        dossier.fiche2_verrouillee = True
        dossier.save()

        self.api.force_authenticate(user=self.commercial)
        response = self.api.patch(
            f'/api/dossiers/{dossier.id}/',
            {'montant_sollicite': '9999999'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- S2 : un commercial ne peut pas modifier le client d'un autre commercial ---
    def test_commercial_ne_peut_pas_modifier_client_d_un_autre(self):
        autre_commercial = Utilisateur.objects.create_user(
            username='autre_commercial_2', password='Test@1234',
            role=Utilisateur.Role.COMMERCIAL,
        )

        self.api.force_authenticate(user=autre_commercial)
        response = self.api.patch(
            f'/api/dossiers/clients/{self.client_sce.id}/',
            {'salaire_net': '9999999'},
        )
        self.assertIn(response.status_code,
                       [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.client_sce.refresh_from_db()
        self.assertNotEqual(self.client_sce.salaire_net, Decimal('9999999'))

    # --- Bug NameError : historique_salaires en GET ne doit pas planter ---
    def test_consultation_historique_salaires_ne_plante_pas(self):
        self.api.force_authenticate(user=self.commercial)
        response = self.api.get(
            f'/api/dossiers/clients/{self.client_sce.id}/salaires/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    # --- Notification à l'acteur suivant (pas seulement au dénouement final) ---
    def test_analyste_assigne_recoit_une_notification(self):
        dossier = self._creer_dossier()
        self._soumettre(dossier)

        self.api.force_authenticate(user=self.chef_commercial)
        self.api.post(f'/api/dossiers/{dossier.id}/valider/',
                       {'decision': 'APPROUVE', 'assigne_a': self.analyste1.id})

        self.assertTrue(
            Notification.objects.filter(
                destinataire=self.analyste1, dossier=dossier
            ).exists()
        )
        