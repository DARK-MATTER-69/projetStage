from decimal import Decimal
from datetime import date


class MoteurScoring:
    """
    Moteur de scoring crédit 100% local SCE.

    Fonctionne en deux temps :
    1. LE GARDIEN : des critères d'exclusion binaires, appliqués AVANT
       tout calcul. Un dossier qui échoue ici n'est pas "mal noté",
       il est bloqué net — exactement comme dans une vraie politique
       de crédit bancaire.
    2. LE NOTATEUR : si le dossier passe le gardien, un barème sur 100
       points répartis en 7 critères pondérés selon leur pertinence
       réelle pour le risque de défaut (quotité et historique en tête).
    """

    SEUIL_COBAC        = Decimal('33.00')
    AGE_MAJORITE       = 18
    AGE_LIMITE_FIN_PRET = 65

    SCORE_FAVORABLE    = 70
    SCORE_CONDITIONNEL = 50

    DOCUMENTS_OBLIGATOIRES_COUNT = 4  # CNI, RIB, historique bancaire, NIU

    def __init__(self, dossier):
        self.dossier = dossier
        self.client  = dossier.client

    # ==================================================================
    # ÉTAPE 1 — LE GARDIEN (critères d'exclusion binaires)
    # ==================================================================

    def verifier_eligibilite(self):
        """
        Vérifie les critères d'exclusion AVANT tout calcul de score.

        :return: tuple (eligible: bool, motif: str ou None)
        """
        from dossiers.models import DocumentDossier

        client  = self.client
        dossier = self.dossier

        # --- 1. Impayé actif non régularisé ---
        if client.impayes.filter(statut__in=['EN_COURS', 'CONTENTIEUX']).exists():
            return False, (
                "Impayé actif non régularisé à la SCE. "
                "Dossier non éligible tant que la situation n'est pas régularisée."
            )

        # --- 2. Quotité au-delà du plafond réglementaire COBAC ---
        if Decimal(str(dossier.quotite_relative)) > self.SEUIL_COBAC:
            return False, (
                f"Quotité de {dossier.quotite_relative}% supérieure au seuil "
                f"réglementaire COBAC ({self.SEUIL_COBAC}%). Dossier non éligible en l'état."
            )

        # --- 3. Âge (mineur, ou plus de 65 ans à la fin du prêt) ---
        aujourd_hui = date.today()
        age_actuel  = (aujourd_hui - client.date_naissance).days // 365

        if age_actuel < self.AGE_MAJORITE:
            return False, "Client mineur. Dossier non éligible."

        mois_restants   = dossier.duree_mois or 0
        age_fin_pret    = age_actuel + (mois_restants / 12)
        if age_fin_pret > self.AGE_LIMITE_FIN_PRET:
            return False, (
                f"Le client aura {age_fin_pret:.0f} ans à l'échéance du prêt "
                f"(limite SCE : {self.AGE_LIMITE_FIN_PRET} ans). Dossier non éligible en l'état."
            )

        # --- 4. Pièces obligatoires manquantes ---
        # (Déjà bloqué à la soumission côté vue, ce contrôle est un filet
        #  de sécurité supplémentaire si le scoring est relancé plus tard.)
        docs_presents = set(
            dossier.documents.values_list('type_document', flat=True)
        )
        docs_requis = {
            DocumentDossier.TypeDocument.CNI,
            DocumentDossier.TypeDocument.RIB,
            DocumentDossier.TypeDocument.HISTORIQUE_BANQUE,
            DocumentDossier.TypeDocument.NIU,
        }
        if not docs_requis.issubset(docs_presents):
            manquants = docs_requis - docs_presents
            return False, (
                f"Pièces obligatoires manquantes : {', '.join(sorted(manquants))}. "
                f"Dossier non soumissible en l'état."
            )

        return True, None

    # ==================================================================
    # ÉTAPE 2 — LE NOTATEUR (barème à 7 critères / 100 points)
    # ==================================================================

    # --- Critère 1 — Quotité relative (25 pts) -----------------------
    def _score_quotite(self):
        """
        Plus la quotité est basse (loin du seuil COBAC), plus la
        capacité de remboursement réelle est confortable.
        """
        quotite = float(self.dossier.quotite_relative)
        if quotite <= 15:
            return 25
        elif quotite <= 20:
            return 20
        elif quotite <= 25:
            return 14
        elif quotite <= 30:
            return 8
        elif quotite <= 33:
            return 3
        return 0  # ne devrait pas arriver (bloqué par le gardien), filet de sécurité

    # --- Critère 2 — Historique SCE gradué (20 pts) -------------------
    def _score_historique_sce(self):
        """
        Évalue le comportement passé du client, avec une gradation
        selon la gravité des incidents plutôt qu'un simple oui/non :
          - Aucun dossier antérieur (nouveau client)      : 10/20 (neutre)
          - Dossiers antérieurs bien remboursés            : +8 par dossier (plafonné)
          - Retard court (<15 jours), déjà régularisé      : -4 par incident
          - Retard grave (>30 jours), même régularisé       : -10 par incident
        """
        client = self.client

        dossiers_approuves = client.dossiers.exclude(pk=self.dossier.pk).filter(statut='APPROUVE')
        nb_dossiers = dossiers_approuves.count()

        if nb_dossiers == 0:
            score = 10  # Nouveau client : note neutre, jamais pénalisé pour ça
        else:
            score = min(10 + nb_dossiers * 8, 20)

        # Gradation des incidents passés à partir des dates déjà enregistrées
        for impaye in client.impayes.exclude(pk=None):
            if impaye.statut == 'REGULARISE' and impaye.date_regularisation:
                duree_jours = (impaye.date_regularisation - impaye.date_echeance).days
            elif impaye.statut in ['EN_COURS', 'CONTENTIEUX']:
                duree_jours = (date.today() - impaye.date_echeance).days
            else:
                continue

            if duree_jours > 30:
                score -= 10
            elif duree_jours >= 15:
                score -= 6
            else:
                score -= 4

        return max(0, min(score, 20))

    # --- Critère 3 — Stabilité du revenu (15 pts) ---------------------
    def _score_stabilite(self):
        points_employeur = {
            'FONCTIONNAIRE': 8, 'RETRAITE': 7, 'PRIVE': 6,
            'ONG': 5, 'COMMERCANT': 3, 'AUTRE': 2,
        }
        score = points_employeur.get(self.client.type_employeur, 2)

        anciennete = self.client.anciennete
        if anciennete >= 10:
            score += 7
        elif anciennete >= 5:
            score += 5
        elif anciennete >= 2:
            score += 3
        else:
            score += 1

        return min(score, 15)

    # --- Critère 4 — Montant demandé vs salaire (15 pts) --------------
    def _score_montant_vs_salaire(self):
        """Un montant raisonnable au regard du salaire rassure davantage
        qu'un montant élevé, même si la mensualité reste techniquement finançable."""
        salaire = float(self.client.salaire_net or 0)
        montant = float(self.dossier.montant_sollicite or 0)
        if salaire <= 0:
            return 0

        ratio_mois_salaire = montant / salaire

        if ratio_mois_salaire <= 3:
            return 15
        elif ratio_mois_salaire <= 6:
            return 11
        elif ratio_mois_salaire <= 10:
            return 6
        return 2

    # --- Critère 5 — Complétude du dossier (10 pts) --------------------
    def _score_dossier(self):
        from dossiers.models import DocumentDossier

        score = 0
        docs_obligatoires = [
            DocumentDossier.TypeDocument.CNI,
            DocumentDossier.TypeDocument.RIB,
            DocumentDossier.TypeDocument.HISTORIQUE_BANQUE,
            DocumentDossier.TypeDocument.NIU,
        ]
        types_uploades = set(self.dossier.documents.values_list('type_document', flat=True))

        for doc in docs_obligatoires:
            if doc in types_uploades:
                score += 1.5

        if self.dossier.appreciation and len(self.dossier.appreciation) >= 50:
            score += 4

        return round(min(score, 10))

    # --- Critère 6 — Fidélité de la relation SCE (10 pts) --------------
    def _score_fidelite(self):
        """
        Calculée à partir de l'ancienneté réelle du client à la SCE
        (date de son tout premier dossier), sans nécessiter de champ
        supplémentaire sur le client.
        """
        premier_dossier = (
            self.client.dossiers.exclude(pk=self.dossier.pk)
            .order_by('cree_le').first()
        )
        if not premier_dossier:
            return 3  # Nouveau client : note neutre basse mais pas nulle

        anciennete_jours = (date.today() - premier_dossier.cree_le.date()).days
        anciennete_annees = anciennete_jours / 365

        if anciennete_annees >= 3:
            return 10
        elif anciennete_annees >= 1:
            return 7
        return 4

    # --- Critère 7 — Marge de sécurité (5 pts) --------------------------
    def _score_marge_securite(self):
        jour_salaire     = self.client.date_versement_salaire or 0
        jour_prelevement = self.dossier.jour_prelevement or 0

        if not (jour_salaire and jour_prelevement):
            return 2  # valeur neutre si donnée absente

        delai = jour_prelevement - jour_salaire
        if delai >= 5:
            return 5
        elif delai >= 1:
            return 3
        return 0

    # ==================================================================
    # Recalcul après modification (salaire, régularisation...)
    # ==================================================================

    @classmethod
    def recalculer_pour_client(cls, client):
        from scoring.services import calculer_et_sauvegarder_score

        dossiers_actifs = client.dossiers.filter(
            statut__in=[
                'BROUILLON', 'PRET_A_SOUMETTRE', 'SOUMIS',
                'EN_ANALYSE_1', 'EN_ANALYSE_2',
            ]
        )
        return [calculer_et_sauvegarder_score(d) for d in dossiers_actifs]

    # ==================================================================
    # Recommandation et conditions (texte motivé)
    # ==================================================================

    def _generer_recommandation(self, score_total, motif_ineligibilite=None):
        client, dossier = self.client, self.dossier

        if motif_ineligibilite:
            return (
                f"DOSSIER NON ÉLIGIBLE.\n\n"
                f"Motif : {motif_ineligibilite}\n\n"
                f"Ce dossier n'a pas été soumis au barème de notation : "
                f"il est bloqué par un critère d'exclusion préalable."
            )

        aujourd_hui = date.today()
        age = (aujourd_hui - client.date_naissance).days // 365

        qualifs_employeur = {
            'FONCTIONNAIRE': "c'est l'État qui paie son salaire. Employeur fiable.",
            'PRIVE':         f"employeur du secteur privé ({client.nom_employeur}).",
            'ONG':           f"employeur ONG/Association ({client.nom_employeur}).",
            'RETRAITE':      "retraité avec revenus fixes et stables.",
            'COMMERCANT':    "commerçant avec revenus variables.",
            'AUTRE':         "employeur à vérifier.",
        }

        lignes = [
            f"CLIENT {client.get_civilite_display().upper()} {client.nom.upper()} "
            f"{client.prenom.upper()}, ÂGÉ(E) DE {age} ANS, EST "
            f"{client.get_type_employeur_display().upper()}. "
            f"{qualifs_employeur.get(client.type_employeur, '').upper()} "
            f"IL/ELLE SOLLICITE CE FINANCEMENT POUR {dossier.objet_financement.upper()}.",
            "",
            f"SALAIRE : {float(client.salaire_net):,.0f} FRS. "
            f"QUOTITÉ RELATIVE : {float(dossier.quotite_relative):.2f}%. "
            f"TRAITE : {float(dossier.mensualite_estimee):,.0f} FRS. "
            f"DURÉE : {dossier.duree_mois} MOIS.",
            "",
        ]

        if score_total >= self.SCORE_FAVORABLE:
            lignes.append("VU LA CAPACITÉ DE REMBOURSEMENT ET LA QUOTITÉ CONFORME,")
            lignes.append("VU L'HISTORIQUE DU CLIENT,")
            lignes.append("NOUS DONNONS UN AVIS FAVORABLE.")
        elif score_total >= self.SCORE_CONDITIONNEL:
            lignes.append("VU UNE CAPACITÉ DE REMBOURSEMENT PARTIELLE,")
            lignes.append("NOUS DONNONS UN AVIS FAVORABLE SOUS CONDITIONS.")
        else:
            lignes.append("VU L'INSUFFISANCE DE LA CAPACITÉ DE REMBOURSEMENT GLOBALE,")
            lignes.append("NOUS DONNONS UN AVIS DÉFAVORABLE.")

        return "\n".join(lignes)

    def _generer_conditions(self, score_total):
        if score_total < self.SCORE_CONDITIONNEL or score_total >= self.SCORE_FAVORABLE:
            return ""

        conditions = []
        mensualite = float(self.dossier.mensualite_estimee)
        traite_max = float(self.dossier.traite_max_autorisee)

        if traite_max > 0 and mensualite > traite_max * 0.90:
            montant_max = traite_max * self.dossier.duree_mois
            conditions.append(f"Réduire le montant à {montant_max:,.0f} FCFA maximum.")

        if self.client.anciennete < 5:
            conditions.append("Fournir une caution solidaire.")

        return "\n".join(f"- {c}" for c in conditions)

    # ==================================================================
    # Calcul final
    # ==================================================================

    def calculer(self):
        """
        Calcule le score global. Applique d'abord le gardien ;
        si le dossier est bloqué, retourne directement un résultat
        INELIGIBLE sans passer par le barème.
        """
        eligible, motif = self.verifier_eligibilite()

        if not eligible:
            return {
                'score':                        0,
                'niveau_risque':                'CRITIQUE',
                'decision_ia':                  'INELIGIBLE',
                'eligible':                     False,
                'motif_ineligibilite':          motif,
                'taux_endettement':             self.dossier.taux_endettement,
                'ratio_mensualite_salaire':     0,
                'delai_securite':               0,
                'score_quotite':                0,
                'score_historique_sce':         0,
                'score_stabilite':              0,
                'score_montant_vs_salaire':     0,
                'score_dossier':                0,
                'score_fidelite':               0,
                'score_marge_securite':         0,
                'recommandation':               self._generer_recommandation(0, motif),
                'conditions':                   '',
            }

        s_quotite    = self._score_quotite()
        s_historique = self._score_historique_sce()
        s_stabilite  = self._score_stabilite()
        s_montant    = self._score_montant_vs_salaire()
        s_dossier    = self._score_dossier()
        s_fidelite   = self._score_fidelite()
        s_marge      = self._score_marge_securite()

        score_total = (
            s_quotite + s_historique + s_stabilite +
            s_montant + s_dossier + s_fidelite + s_marge
        )

        if score_total >= 80:
            niveau_risque = 'FAIBLE'
        elif score_total >= 60:
            niveau_risque = 'MOYEN'
        elif score_total >= 40:
            niveau_risque = 'ELEVE'
        else:
            niveau_risque = 'CRITIQUE'

        if score_total >= self.SCORE_FAVORABLE:
            decision = 'FAVORABLE'
        elif score_total >= self.SCORE_CONDITIONNEL:
            decision = 'CONDITIONNEL'
        else:
            decision = 'DEFAVORABLE'

        jour_salaire     = self.client.date_versement_salaire or 0
        jour_prelevement = self.dossier.jour_prelevement or 0

        return {
            'score':                        score_total,
            'niveau_risque':                niveau_risque,
            'decision_ia':                  decision,
            'eligible':                     True,
            'motif_ineligibilite':          None,
            'taux_endettement':             self.dossier.taux_endettement,
            'ratio_mensualite_salaire':     round(
                (self.dossier.mensualite_estimee / self.client.salaire_net) * 100, 2
            ) if self.client.salaire_net else 0,
            'delai_securite':               jour_prelevement - jour_salaire,
            'score_quotite':                s_quotite,
            'score_historique_sce':         s_historique,
            'score_stabilite':              s_stabilite,
            'score_montant_vs_salaire':     s_montant,
            'score_dossier':                s_dossier,
            'score_fidelite':               s_fidelite,
            'score_marge_securite':         s_marge,
            'recommandation':               self._generer_recommandation(score_total),
            'conditions':                   self._generer_conditions(score_total),
        }