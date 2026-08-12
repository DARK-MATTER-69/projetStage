from decimal import Decimal
from dossiers.models import DocumentDossier
from dossiers.extracteur_releve import ExtracteurReleve
import os

class MoteurScoring:
    """
    Moteur de calcul du score de crédit SCE.
    Basé sur les critères réels utilisés par la SCE :
    - Quotité disponible (seuil COBAC 33%)
    - Historique de compte bancaire
    - Dettes dans d'autres institutions
    - Capacité de remboursement réelle
    - Stabilité professionnelle

    Score final sur 100 réparti en 4 critères de 25 pts chacun.
    """

    SEUIL_COBAC             = Decimal('33.00')  # % max d'endettement
    SEUIL_ENDETTEMENT_BON   = Decimal('20.00')  # % considéré comme bon
    SCORE_FAVORABLE         = 70
    SCORE_CONDITIONNEL      = 50

    def __init__(self, dossier):
        """
        :param dossier: Instance de dossiers.models.Dossier
        """
        self.dossier = dossier
        self.client  = dossier.client


    # Critère 1 — Stabilité professionnelle (25 pts)

    def _score_stabilite(self):
        """
        Évalue la stabilité professionnelle du client.

        Points employeur :
            Fonctionnaire : 15 pts
            Retraité      : 13 pts
            Privé         : 12 pts
            ONG           : 10 pts
            Commerçant    :  7 pts
            Autre         :  5 pts

        Points ancienneté :
            >= 10 ans : 10 pts
            5–9 ans   :  7 pts
            2–4 ans   :  5 pts
            < 2 ans   :  2 pts
        """
        points_employeur = {
            'FONCTIONNAIRE': 15,
            'RETRAITE':      13,
            'PRIVE':         12,
            'ONG':           10,
            'COMMERCANT':     7,
            'AUTRE':          5,
        }
        score  = points_employeur.get(self.client.type_employeur, 5)
        annees = self.client.anciennete

        if annees >= 10:
            score += 10
        elif annees >= 5:
            score += 7
        elif annees >= 2:
            score += 5
        else:
            score += 2

        return min(score, 25)

    
    # Critère 2 — Quotité et capacité de remboursement (25 pts)

    def _score_capacite(self):
        """
        Évalue la capacité de remboursement selon les critères réels SCE.
        Basé sur la quotité relative (Total engagements / Salaire).
        Seuil COBAC maximum : 33%.
        """
        score    = 0
        quotite  = float(self.dossier.quotite_relative)
        traite   = self.dossier.mensualite_estimee
        traite_max = self.dossier.traite_max_autorisee

        # Points quotité (15 pts max)
        if quotite <= 20:
            score += 15
        elif quotite <= 25:
            score += 12
        elif quotite <= 33:
            score += 7
        else:
            score += 0  # Dépasse le seuil COBAC

        # Points mensualité vs traite max (10 pts max)
        if traite_max > 0:
            if traite <= traite_max * Decimal('0.80'):
                score += 10
            elif traite <= traite_max:
                score += 6
            else:
                score += 0

        return min(score, 25)
    
    
    # Critère 3 — Historique bancaire et dettes (25 pts)

    def _score_historique(self):
        """
        Évalue le profil financier basé sur l'historique bancaire
        et les dettes dans d'autres institutions.

        Points crédits en cours dans d'autres institutions (15 pts) :
            Aucun crédit en cours     : 15 pts
            <= 10% du salaire         : 10 pts
            <= 20% du salaire         : 5 pts
            > 20% du salaire          : 0 pt

        Points délai de sécurité (10 pts) :
            Prélèvement >= 5j après salaire : 10 pts
            Prélèvement 1–4j après salaire  :  6 pts
            Prélèvement avant salaire        :  0 pt
        """
        score  = 0
        salaire = self.client.salaire_net

        # Dettes autres institutions
        credits = self.client.credits_en_cours
        if credits == 0:
            score += 15
        elif salaire > 0 and credits <= salaire * Decimal('0.10'):
            score += 10
        elif salaire > 0 and credits <= salaire * Decimal('0.20'):
            score += 5
        else:
            score += 0

        # Délai de sécurité salaire / prélèvement
        jour_salaire     = self.client.date_versement_salaire or 0
        jour_prelevement = self.dossier.jour_prelevement or 0

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

        return min(score, 25)

 
    # Critère 4 — Complétude du dossier (25 pts)

    def _score_dossier(self):
        """
        Évalue la complétude du dossier transmis.

        Documents obligatoires (5 pts chacun = 20 pts max) :
            CNI, RIB, Historique bancaire 3 mois, NIU

        Appréciation commerciale renseignée (5 pts) :
            Texte d'au moins 50 caractères
        """
        from dossiers.models import DocumentDossier

        score = 0
        docs_obligatoires = [
            DocumentDossier.TypeDocument.CNI,
            DocumentDossier.TypeDocument.RIB,
            DocumentDossier.TypeDocument.HISTORIQUE_BANQUE,
            DocumentDossier.TypeDocument.NIU,
        ]

        types_uploades = set(
            self.dossier.documents.values_list('type_document', flat=True)
        )

        for doc in docs_obligatoires:
            if doc in types_uploades:
                score += 5

        if self.dossier.appreciation and len(self.dossier.appreciation) >= 50:
            score += 5

        return min(score, 25)

 
    # Génération de la recommandation locale (sans IA externe)

    def _generer_recommandation(self, score_total, resultats):
        """
        Génère une recommandation textuelle basée sur les résultats
        du scoring. Aucun appel externe requis.

        :param score_total: int score final /100
        :param resultats:   dict résultats du scoring
        :return:            str recommandation en français
        """
        taux        = resultats['taux_endettement']
        mensualite  = float(self.dossier.mensualite_estimee)
        traite_max  = float(self.dossier.traite_max_autorisee)
        credits     = float(self.client.credits_en_cours)
        salaire     = float(self.client.salaire_net)

        lignes = []

        # Synthèse
        lignes.append(
            f"Le client {self.client.civilite} {self.client.nom} "
            f"{self.client.prenom}, {self.client.get_type_employeur_display()} "
            f"avec {self.client.anciennete} ans d'ancienneté, sollicite un crédit "
            f"de {self.dossier.montant_sollicite:,.0f} FCFA "
            f"sur {self.dossier.duree_mois} mois."
        )

        lignes.append("")

        # Points forts
        points_forts = []
        if taux <= 20:
            points_forts.append(
                f"Taux d'endettement faible ({taux:.1f}%) — bien en dessous "
                f"du seuil COBAC de 33%."
            )
        if credits == 0:
            points_forts.append(
                "Aucun crédit en cours dans d'autres institutions financières."
            )
        if self.client.anciennete >= 5:
            points_forts.append(
                f"Bonne stabilité professionnelle "
                f"({self.client.anciennete} ans d'ancienneté)."
            )
        if mensualite <= traite_max * 0.80:
            points_forts.append(
                f"Mensualité de {mensualite:,.0f} FCFA confortable "
                f"par rapport à la traite maximale de {traite_max:,.0f} FCFA."
            )

        if points_forts:
            lignes.append("Points favorables :")
            for p in points_forts:
                lignes.append(f"  - {p}")
            lignes.append("")

        # Points de vigilance
        vigilances = []
        if taux > self.SEUIL_COBAC:
            vigilances.append(
                f"Taux d'endettement de {taux:.1f}% dépasse le seuil "
                f"légal COBAC de 33%. Dossier non recevable en l'état."
            )
        if mensualite > traite_max:
            vigilances.append(
                f"La mensualité demandée ({mensualite:,.0f} FCFA) dépasse "
                f"la traite maximale autorisée ({traite_max:,.0f} FCFA)."
            )
        if credits > salaire * 0.20:
            vigilances.append(
                f"Niveau de crédits en cours élevé "
                f"({credits:,.0f} FCFA) dans d'autres institutions."
            )
        if self.client.anciennete < 2:
            vigilances.append(
                "Ancienneté professionnelle inférieure à 2 ans — "
                "risque de stabilité d'emploi."
            )

        if vigilances:
            lignes.append("Points de vigilance :")
            for v in vigilances:
                lignes.append(f"  - {v}")
            lignes.append("")

        # Recommandation finale
        if score_total >= self.SCORE_FAVORABLE:
            lignes.append(
                f"RECOMMANDATION : Dossier favorable (score {score_total}/100). "
                f"Le profil du client présente une capacité de remboursement "
                f"satisfaisante. Accord recommandé."
            )
        elif score_total >= self.SCORE_CONDITIONNEL:
            lignes.append(
                f"RECOMMANDATION : Dossier conditionnel (score {score_total}/100). "
                f"Le dossier peut être accordé sous réserve de vérification "
                f"complémentaire de l'historique bancaire et des engagements "
                f"financiers en cours."
            )
        else:
            lignes.append(
                f"RECOMMANDATION : Dossier défavorable (score {score_total}/100). "
                f"Le profil financier du client ne satisfait pas aux critères "
                f"d'octroi de crédit de la SCE."
            )

        return "\n".join(lignes)

    def _generer_conditions(self, score_total, resultats):
        """
        Génère les conditions à imposer si la décision est CONDITIONNEL.

        :return: str conditions ou chaîne vide
        """
        if score_total < self.SCORE_CONDITIONNEL or \
           score_total >= self.SCORE_FAVORABLE:
            return ""

        conditions = []
        mensualite = float(self.dossier.mensualite_estimee)
        traite_max = float(self.dossier.traite_max_autorisee)

        if mensualite > traite_max * 0.90:
            montant_max = traite_max * self.dossier.duree_mois
            conditions.append(
                f"Réduire le montant sollicité à {montant_max:,.0f} FCFA maximum "
                f"pour respecter la traite maximale autorisée."
            )

        if self.client.anciennete < 5:
            conditions.append(
                "Fournir une caution solidaire d'un tiers solvable."
            )

        if self.client.credits_en_cours > 0:
            conditions.append(
                "Justifier du solde exact des crédits en cours "
                "dans les autres institutions financières."
            )

        conditions.append(
            "Fournir les 3 derniers relevés de compte bancaire "
            "pour vérification de la régularité des mouvements."
        )

        return "\n".join(f"- {c}" for c in conditions)

    
    # Calcul final
    def calculer(self):
        """
        Calcule le score global et retourne un dictionnaire
        contenant tous les résultats du scoring avec recommandation.

        :return: dict complet avec score, niveau_risque, decision,
                 recommandation et détail des critères
        """
        s_stabilite = self._score_stabilite()
        s_capacite  = self._score_capacite()
        s_historique = self._score_releve_bancaire()
        s_dossier   = self._score_dossier()

        score_total = s_stabilite + s_capacite + s_historique + s_dossier

        # Niveau de risque
        if score_total >= 80:
            niveau_risque = 'FAIBLE'
        elif score_total >= 60:
            niveau_risque = 'MOYEN'
        elif score_total >= 40:
            niveau_risque = 'ELEVE'
        else:
            niveau_risque = 'CRITIQUE'

        # Décision
        if score_total >= self.SCORE_FAVORABLE:
            decision = 'FAVORABLE'
        elif score_total >= self.SCORE_CONDITIONNEL:
            decision = 'CONDITIONNEL'
        else:
            decision = 'DEFAVORABLE'

        # Délai de sécurité
        jour_salaire     = self.client.date_versement_salaire or 0
        jour_prelevement = self.dossier.jour_prelevement or 0
        delai_securite   = jour_prelevement - jour_salaire

        resultats = {
            'score':                        score_total,
            'niveau_risque':                niveau_risque,
            'decision_ia':                  decision,
            'taux_endettement':             self.dossier.taux_endettement,
            'ratio_mensualite_salaire':     round(
                (self.dossier.mensualite_estimee / self.client.salaire_net) * 100, 2
            ) if self.client.salaire_net else 0,
            'delai_securite':               delai_securite,
            'score_stabilite_emploi':       s_stabilite,
            'score_capacite_remboursement': s_capacite,
            'score_profil_client':          s_historique,
            'score_dossier':                s_dossier,
        }

        # Recommandation générée localement
        resultats['recommandation'] = self._generer_recommandation(
            score_total, resultats
        )
        resultats['conditions']     = self._generer_conditions(
            score_total, resultats
        )

        return resultats
    
    def _score_releve_bancaire(self):
        """
        Évalue le profil financier à partir de l'extraction
        du relevé bancaire PDF via Gemini Vision.
        Fallback sur les données déclarées si extraction échoue.
        """
        from dossiers.models import DocumentDossier
        import os

        score   = 0
        salaire = float(self.client.salaire_net)

        doc_releve = self.dossier.documents.filter(
            type_document=DocumentDossier.TypeDocument.HISTORIQUE_BANQUE
        ).first()

        if doc_releve and doc_releve.fichier:
            chemin = doc_releve.fichier.path

            if os.path.exists(chemin):
                try:
                    from scoring.gemini import ExtracteurReleveGemini
                    extracteur = ExtracteurReleveGemini()
                    resultat   = extracteur.extraire(chemin)

                    if resultat.succes and resultat.nb_operations > 0:
                        moy_credits = float(resultat.moyenne_credits_mensuelle)

                        # Points régularité des crédits (10 pts)
                        if salaire > 0:
                            if moy_credits >= salaire:
                                score += 10
                            elif moy_credits >= salaire * 0.80:
                                score += 7
                            elif moy_credits >= salaire * 0.50:
                                score += 4
                            else:
                                score += 1

                        # Points gestion des débits (10 pts)
                        if not resultat.decouvert_detecte:
                            score += 10
                        elif resultat.solde_final and float(resultat.solde_final) > 0:
                            score += 7
                        else:
                            score += 2

                        # Points remboursements cachés (5 pts)
                        remb = float(resultat.remboursements_credits)
                        if remb == 0:
                            score += 5
                        elif salaire > 0 and remb < salaire * 0.10:
                            score += 3
                        else:
                            score += 0

                        return min(score, 25)

                except Exception:
                    pass

        # Fallback → données déclarées
        return self._score_historique_declare()

    def _score_historique_declare(self):
        """
        Calcule le score historique sur la base des données
        déclarées par le client quand le relevé n'est pas disponible.
        """
        score   = 0
        salaire = self.client.salaire_net
        credits = self.client.credits_en_cours

        if credits == 0:
            score += 15
        elif salaire > 0 and credits <= salaire * Decimal('0.10'):
            score += 10
        elif salaire > 0 and credits <= salaire * Decimal('0.20'):
            score += 5

        jour_salaire     = self.client.date_versement_salaire or 0
        jour_prelevement = self.dossier.jour_prelevement or 0

        if jour_salaire and jour_prelevement:
            delai = jour_prelevement - jour_salaire
            if delai >= 5:
                score += 10
            elif delai >= 1:
                score += 6
        else:
            score += 5

        return min(score, 25)
    def _generer_avis_motive(self):
        """
        Génère l'avis motivé dans le style SCE,
        basé sur les critères réels de la Fiche 2.
        """
        client  = self.client
        dossier = self.dossier

        return (
            f"{client.civilite} {client.nom} {client.prenom}, "
            f"âgé(e) de {self._calculer_age()} ans, est "
            f"{client.get_type_employeur_display().lower()} "
            f"au sein de {client.nom_employeur}. "
            f"C'est {self._qualifier_employeur()} "
            f"Il/Elle sollicite un financement de "
            f"{dossier.montant_sollicite:,.0f} FCFA "
            f"pour {dossier.objet_financement.lower()}.\n\n"
            f"Domiciliation du salaire : {client.nom_employeur}. "
            f"Salaire : {client.salaire_net:,.0f} FCFA. "
            f"Engagements bancaires : {dossier.echeance_mens_banque:,.0f} FCFA. "
            f"Quotité relative : {dossier.quotite_relative:.2f}%. "
            f"Traite : {dossier.mensualite_estimee:,.0f} FCFA. "
            f"Durée : {dossier.duree_mois} mois.\n\n"
            f"Conclusion : VU CAPACITÉ DE REMBOURSEMENT, "
            f"VU QUOTITÉ ({dossier.quotite_relative:.2f}%), "
            f"VU DOMICILIATION DU CLIENT, "
            f"{'NOUS DONNONS UN AVIS FAVORABLE.' if self._score_capacite() >= 15 else 'NOUS DONNONS UN AVIS DÉFAVORABLE.'}"
        )

    def _calculer_age(self):
        from datetime import date
        today = date.today()
        naissance = self.client.date_naissance
        return today.year - naissance.year - (
            (today.month, today.day) < (naissance.month, naissance.day)
        )

    def _qualifier_employeur(self):
        qualifs = {
            'FONCTIONNAIRE': "c'est l'État qui paie son salaire. Employeur fiable.",
            'PRIVE':         "employeur du secteur privé.",
            'ONG':           "employeur ONG/Association.",
            'RETRAITE':      "retraité avec revenus fixes.",
            'COMMERCANT':    "commerçant avec revenus variables.",
            'AUTRE':         "employeur à vérifier.",
        }
        return qualifs.get(self.client.type_employeur, "")