from decimal import Decimal


class MoteurScoring:
    """
    Moteur de calcul du score de crédit d'un dossier SCE.
    Le score final est sur 100, réparti en 4 critères de 25 points chacun :
        - Stabilité de l'emploi        : 25 pts
        - Capacité de remboursement    : 25 pts
        - Profil client                : 25 pts
        - Complétude du dossier        : 25 pts
    """

    SEUIL_ENDETTEMENT_MAX   = Decimal('33.00')  # % exigé par la COBAC
    SEUIL_ENDETTEMENT_BON   = Decimal('20.00')  # % considéré comme bon
    SCORE_FAVORABLE         = 70
    SCORE_CONDITIONNEL      = 50

    def __init__(self, dossier):
        """
        Initialise le moteur avec un dossier de crédit.

        :param dossier: Instance de dossiers.models.Dossier
        """
        self.dossier = dossier
        self.client  = dossier.client


    # Critère 1 — Stabilité de l'emploi (25 pts)

    def _score_stabilite_emploi(self):
        """
        Calcule le score de stabilité de l'emploi.
        Basé sur le type d'employeur et l'ancienneté du client.

        Points par type d'employeur :
            Fonctionnaire : 15 pts (emploi garanti)
            Privé CDI     : 12 pts
            ONG           : 10 pts
            Retraité      : 13 pts (revenus fixes)
            Commerçant    : 7 pts  (revenus variables)
            Autre         : 5 pts

        Points par ancienneté :
            >= 10 ans : 10 pts
            5 à 9 ans :  7 pts
            2 à 4 ans :  5 pts
            < 2 ans   :  2 pts
        """
        score = 0

        # Points employeur
        points_employeur = {
            'FONCTIONNAIRE': 15,
            'RETRAITE':      13,
            'PRIVE':         12,
            'ONG':           10,
            'COMMERCANT':     7,
            'AUTRE':          5,
        }
        score += points_employeur.get(self.client.type_employeur, 5)

        # Points ancienneté
        anciennete = self.client.anciennete
        if anciennete >= 10:
            score += 10
        elif anciennete >= 5:
            score += 7
        elif anciennete >= 2:
            score += 5
        else:
            score += 2

        return min(score, 25)


    # Critère 2 — Capacité de remboursement (25 pts)

    def _score_capacite_remboursement(self):
        """
        Calcule le score de capacité de remboursement.
        Basé sur le taux d'endettement et le ratio mensualité/salaire.
        Un taux d'endettement supérieur à 33% (seuil COBAC) = 0 point.
        """
        score = 0
        taux  = self.dossier.taux_endettement

        # Points taux d'endettement (15 pts max)
        if taux <= 15:
            score += 15
        elif taux <= self.SEUIL_ENDETTEMENT_BON:
            score += 12
        elif taux <= self.SEUIL_ENDETTEMENT_MAX:
            score += 7
        else:
            score += 0  # Dépasse le seuil COBAC

        # Points ratio mensualité / salaire (10 pts max)
        salaire = self.client.salaire_net
        if salaire and salaire > 0:
            ratio = (self.dossier.mensualite_estimee / salaire) * 100
            if ratio <= 15:
                score += 10
            elif ratio <= 25:
                score += 7
            elif ratio <= 33:
                score += 4
            else:
                score += 0
        
        # Points traite acceptable (bonus/malus)
        if self.dossier.est_traite_acceptable:
            score += 3
        else:
            score = max(score - 5, 0)  # Penalite si traite depasse le max autorise
        
        return min(score, 25)

    
    # Critère 3 — Profil client (25 pts)
    def _score_profil_client(self):
        """
        Calcule le score du profil client.
        Basé sur l'âge, l'ancienneté et le délai de sécurité
        entre le jour de salaire et le jour de prélèvement.
        """
        from datetime import date
        score = 0

        # Points âge (10 pts max)
        aujourd_hui = date.today()
        age = (
            aujourd_hui - self.client.date_naissance
        ).days // 365

        if 30 <= age <= 50:
            score += 10
        elif 25 <= age < 30 or 50 < age <= 55:
            score += 7
        elif 21 <= age < 25 or 55 < age <= 60:
            score += 4
        else:
            score += 1

        # Points délai de sécurité (10 pts max)
        jour_salaire      = self.client.date_versement_salaire
        jour_prelevement  = self.dossier.jour_prelevement

        if jour_salaire and jour_prelevement:
            delai = jour_prelevement - jour_salaire
            if delai >= 5:
                score += 10
            elif delai >= 1:
                score += 6
            else:
                score += 0
        else:
            score += 5  # Valeur neutre si non renseigné

        # Points charges (5 pts max)
        if self.client.credits_en_cours == 0:
            score += 5
        elif self.client.credits_en_cours <= self.client.salaire_net * Decimal('0.1'):
            score += 3
        else:
            score += 1

        return min(score, 25)

  
    # Critère 4 — Complétude du dossier (25 pts)
    def _score_dossier(self):
        """
        Calcule le score de complétude du dossier.
        Basé sur la présence des documents obligatoires et le type de crédit.
        """
        from dossiers.models import DocumentDossier
        score = 0

        # Documents obligatoires attendus
        documents_obligatoires = [
            DocumentDossier.TypeDocument.CNI,
            DocumentDossier.TypeDocument.RIB,
            DocumentDossier.TypeDocument.HISTORIQUE_BANQUE,
            DocumentDossier.TypeDocument.NIU,
        ]

        # Récupère les types de documents déjà uploadés
        types_uploades = set(
            self.dossier.documents.values_list('type_document', flat=True)
        )

        # 5 pts par document présent (4 docs = 20 pts max)
        for doc in documents_obligatoires:
            if doc in types_uploades:
                score += 5

        # Points appréciation commerciale renseignée (5 pts)
        if self.dossier.appreciation and len(self.dossier.appreciation) >= 50:
            score += 5

        return min(score, 25)

    
    # Calcul final
    def calculer(self):
        """
        Calcule le score global et retourne un dictionnaire
        contenant tous les résultats du scoring.

        :return: dict avec score, niveau_risque, decision et détail des critères
        """
        from dossiers.models import Dossier

        s_emploi        = self._score_stabilite_emploi()
        s_remboursement = self._score_capacite_remboursement()
        s_profil        = self._score_profil_client()
        s_dossier       = self._score_dossier()

        score_total = s_emploi + s_remboursement + s_profil + s_dossier

        # Niveau de risque
        if score_total >= 80:
            niveau_risque = 'FAIBLE'
        elif score_total >= 60:
            niveau_risque = 'MOYEN'
        elif score_total >= 40:
            niveau_risque = 'ELEVE'
        else:
            niveau_risque = 'CRITIQUE'

        # Décision IA
        if score_total >= self.SCORE_FAVORABLE:
            decision = 'FAVORABLE'
        elif score_total >= self.SCORE_CONDITIONNEL:
            decision = 'CONDITIONNEL'
        else:
            decision = 'DEFAVORABLE'

        # Délai de sécurité pour stockage
        jour_salaire     = self.client.date_versement_salaire or 0
        jour_prelevement = self.dossier.jour_prelevement or 0
        delai_securite   = jour_prelevement - jour_salaire

        return {
            'score':                        score_total,
            'niveau_risque':                niveau_risque,
            'decision_ia':                  decision,
            'taux_endettement':             self.dossier.taux_endettement,
            'ratio_mensualite_salaire':     round(
                (self.dossier.mensualite_estimee / self.client.salaire_net) * 100, 2
            ) if self.client.salaire_net else 0,
            'delai_securite':               delai_securite,
            'score_stabilite_emploi':       s_emploi,
            'score_capacite_remboursement': s_remboursement,
            'score_profil_client':          s_profil,
            'score_dossier':                s_dossier,
        }