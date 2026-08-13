from decimal import Decimal
from datetime import date


class MoteurScoring:
    """
    Moteur de scoring crédit 100% local SCE.
    Basé sur l'historique interne des clients SCE :
    - Comportement de remboursement passé
    - Impayés SCE
    - Évolution du salaire
    - Quotité disponible
    - Engagements totaux

    Score sur 100 réparti en 4 critères de 25 pts chacun :
    1. Stabilité professionnelle       /25
    2. Capacité de remboursement       /25
    3. Historique client SCE           /25
    4. Complétude du dossier           /25
    """

    SEUIL_COBAC        = Decimal('33.00')
    SCORE_FAVORABLE    = 70
    SCORE_CONDITIONNEL = 50

    def __init__(self, dossier):
        """
        :param dossier: Instance de dossiers.models.Dossier
        """
        self.dossier = dossier
        self.client  = dossier.client

    # ------------------------------------------------------------------
    # Critère 1 — Stabilité professionnelle (25 pts)
    # ------------------------------------------------------------------

    def _score_stabilite(self):
        """
        Évalue la stabilité professionnelle.
        Points employeur + ancienneté + évolution salariale.
        """
        points_employeur = {
            'FONCTIONNAIRE': 15,
            'RETRAITE':      13,
            'PRIVE':         12,
            'ONG':           10,
            'COMMERCANT':     7,
            'AUTRE':          5,
        }
        score = points_employeur.get(self.client.type_employeur, 5)

        # Ancienneté
        anciennete = self.client.anciennete
        if anciennete >= 10:
            score += 7
        elif anciennete >= 5:
            score += 5
        elif anciennete >= 2:
            score += 3
        else:
            score += 1

        # Évolution salariale (bonus si salaire a augmenté)
        historique = self.client.historique_salaires.order_by('date_effet')
        if historique.count() >= 2:
            premier = historique.first().salaire
            dernier = historique.last().salaire
            if dernier > premier:
                score += 3  # Bonus évolution positive

        return min(score, 25)

    # ------------------------------------------------------------------
    # Critère 2 — Capacité de remboursement (25 pts)
    # ------------------------------------------------------------------

    def _score_capacite(self):
        """
        Évalue la capacité de remboursement selon les critères SCE.
        Basé sur la quotité relative et la traite max autorisée.
        """
        score    = 0
        quotite  = float(self.dossier.quotite_relative)
        traite   = self.dossier.mensualite_estimee
        traite_max = self.dossier.traite_max_autorisee

        # Points quotité (15 pts max)
        if quotite <= 15:
            score += 15
        elif quotite <= 20:
            score += 12
        elif quotite <= 25:
            score += 9
        elif quotite <= 33:
            score += 5
        else:
            score += 0  # Hors seuil COBAC

        # Points mensualité vs traite max (10 pts max)
        if traite_max > 0:
            ratio = float(traite / traite_max)
            if ratio <= 0.70:
                score += 10
            elif ratio <= 0.85:
                score += 7
            elif ratio <= 1.00:
                score += 4
            else:
                score += 0

        return min(score, 25)

    # ------------------------------------------------------------------
    # Critère 3 — Historique client SCE (25 pts)
    # ------------------------------------------------------------------

    def _score_historique_sce(self):
        """
        Évalue le comportement du client basé sur son historique
        interne à la SCE.

        Points dossiers précédents (10 pts) :
            Aucun dossier précédent     :  5 pts (nouveau client)
            1-2 dossiers bien remboursés: 10 pts
            Dossiers avec retards       :  3 pts
            Impayés non régularisés     :  0 pt

        Points impayés (10 pts) :
            Aucun impayé SCE            : 10 pts
            Impayés régularisés         :  5 pts
            Impayés en cours            :  0 pt
            En contentieux              :  0 pt

        Points délai sécurité (5 pts) :
            Prélèvement >= 5j après salaire : 5 pts
            Prélèvement 1-4j après          : 3 pts
            Avant salaire                    : 0 pt
        """
        from dossiers.models import ImpayeSCE

        score  = 0
        client = self.client

        # ── Historique dossiers SCE ──────────────────────
        dossiers_passes = client.dossiers.exclude(
            pk=self.dossier.pk
        ).filter(statut='APPROUVE')

        nb_dossiers = dossiers_passes.count()

        if nb_dossiers == 0:
            score += 5  # Nouveau client SCE
        elif nb_dossiers >= 1:
            score += 10  # Client fidèle avec bons antécédents

        # ── Impayés SCE ──────────────────────────────────
        impayes_en_cours = client.impayes.filter(
            statut__in=['EN_COURS', 'CONTENTIEUX']
        ).count()

        impayes_regularises = client.impayes.filter(
            statut='REGULARISE'
        ).count()

        if impayes_en_cours > 0:
            score += 0  # Impayés actifs = rédhibitoire
        elif impayes_regularises > 0:
            score += 5  # Impayés régularisés = toléré
        else:
            score += 10  # Aucun impayé

        # ── Délai de sécurité ────────────────────────────
        jour_salaire     = client.date_versement_salaire or 0
        jour_prelevement = self.dossier.jour_prelevement or 0

        if jour_salaire and jour_prelevement:
            delai = jour_prelevement - jour_salaire
            if delai >= 5:
                score += 5
            elif delai >= 1:
                score += 3
            else:
                score += 0
        else:
            score += 3  # Valeur neutre

        return min(score, 25)

    # ------------------------------------------------------------------
    # Critère 4 — Complétude du dossier (25 pts)
    # ------------------------------------------------------------------

    def _score_dossier(self):
        """
        Évalue la complétude du dossier transmis.
        Documents obligatoires + appréciation commerciale.
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

    # ------------------------------------------------------------------
    # Recalcul après modification salaire
    # ------------------------------------------------------------------

    @classmethod
    def recalculer_pour_client(cls, client):
        """
        Recalcule le score de tous les dossiers actifs d'un client
        après une modification de son salaire.
        Utilisé quand le salaire d'un client augmente.

        :param client: Instance de dossiers.models.Client
        :return:       list de ScoreCredit mis à jour
        """
        from scoring.services import calculer_et_sauvegarder_score

        dossiers_actifs = client.dossiers.filter(
            statut__in=[
                'BROUILLON', 'PRET_A_SOUMETTRE',
                'SOUMIS', 'VALIDE_CHEF_1',
                'EN_ANALYSE_1', 'EN_ANALYSE_2',
            ]
        )

        scores = []
        for dossier in dossiers_actifs:
            score = calculer_et_sauvegarder_score(dossier)
            scores.append(score)

        return scores

    # ------------------------------------------------------------------
    # Recommandation locale
    # ------------------------------------------------------------------

    def _generer_recommandation(self, score_total, resultats):
        """
        Génère l'avis motivé dans le style SCE.
        Format identique à la vraie Fiche 2 de la SCE.
        """
        from dossiers.models import ImpayeSCE

        client  = self.client
        dossier = self.dossier

        # Calcul âge
        aujourd_hui = date.today()
        age = (aujourd_hui - client.date_naissance).days // 365

        # Qualifier l'employeur
        qualifs_employeur = {
            'FONCTIONNAIRE': "c'est l'État qui paie son salaire. Employeur fiable.",
            'PRIVE':         f"employeur du secteur privé ({client.nom_employeur}).",
            'ONG':           f"employeur ONG/Association ({client.nom_employeur}).",
            'RETRAITE':      "retraité avec revenus fixes et stables.",
            'COMMERCANT':    "commerçant avec revenus variables.",
            'AUTRE':         "employeur à vérifier.",
        }

        lignes = []

        # En-tête style SCE
        lignes.append(
            f"CLIENT QUI ENTRE EN RELATION. "
            f"{client.get_civilite_display().upper()} "
            f"{client.nom.upper()} {client.prenom.upper()}, "
            f"ÂGÉ(E) DE {age} ANS, EST "
            f"{client.get_type_employeur_display().upper()}. "
            f"{qualifs_employeur.get(client.type_employeur, '').upper()} "
            f"IL/ELLE SOLLICITE CE FINANCEMENT POUR "
            f"{dossier.objet_financement.upper()}."
        )

        lignes.append("")

        # Employeur
        lignes.append(
            f"EMPLOYEUR : {client.nom_employeur.upper()}."
        )

        lignes.append("")

        # Domiciliation + données financières
        impayes = client.impayes.filter(statut='EN_COURS').count()
        eng_bq  = float(dossier.echeance_mens_banque)

        lignes.append(
            f"DOMICILIATION DU SALAIRE : {dossier.releve_banque or 'À PRÉCISER'}. "
            f"SALAIRE : {float(client.salaire_net):,.0f} FRS. "
            f"ENG BQ : {eng_bq:,.0f} FRS. "
            f"QUOTITE RELATIVE : {float(dossier.quotite_relative):.2f}%. "
            f"TRAITE : {float(dossier.mensualite_estimee):,.0f} FRS. "
            f"DUREE : {dossier.duree_mois} MOIS."
        )

        if impayes > 0:
            lignes.append(
                f"ATTENTION : {impayes} IMPAYÉ(S) EN COURS À LA SCE."
            )

        lignes.append("")

        # Conclusion style SCE
        if score_total >= self.SCORE_FAVORABLE:
            lignes.append("VU CAPACITÉ DE REMBOURSEMENT,")
            lignes.append(f"VU QUOTITÉ ({float(dossier.quotite_relative):.2f}%),")
            lignes.append("VU DOMICILIATION DU CLIENT,")
            if impayes == 0:
                lignes.append("VU ABSENCE D'IMPAYÉS À LA SCE,")
            lignes.append("NOUS DONNONS UN AVIS FAVORABLE.")

        elif score_total >= self.SCORE_CONDITIONNEL:
            lignes.append("VU CAPACITÉ DE REMBOURSEMENT PARTIELLE,")
            lignes.append(f"VU QUOTITÉ ({float(dossier.quotite_relative):.2f}%),")
            lignes.append("NOUS DONNONS UN AVIS FAVORABLE SOUS CONDITIONS.")

        else:
            lignes.append("VU INSUFFISANCE DE LA CAPACITÉ DE REMBOURSEMENT,")
            if impayes > 0:
                lignes.append("VU PRÉSENCE D'IMPAYÉS EN COURS À LA SCE,")
            if float(dossier.quotite_relative) > 33:
                lignes.append(
                    f"VU QUOTITÉ HORS SEUIL COBAC "
                    f"({float(dossier.quotite_relative):.2f}% > 33%),")
            lignes.append("NOUS DONNONS UN AVIS DÉFAVORABLE.")

        return "\n".join(lignes)

    def _generer_conditions(self, score_total, resultats):
        """Génère les conditions si décision conditionnelle."""
        if score_total < self.SCORE_CONDITIONNEL or \
           score_total >= self.SCORE_FAVORABLE:
            return ""

        conditions = []
        mensualite = float(self.dossier.mensualite_estimee)
        traite_max = float(self.dossier.traite_max_autorisee)

        if mensualite > traite_max * 0.90:
            montant_max = traite_max * self.dossier.duree_mois
            conditions.append(
                f"Réduire le montant à {montant_max:,.0f} FCFA maximum."
            )

        if self.client.anciennete < 5:
            conditions.append("Fournir une caution solidaire.")

        if self.client.impayes.filter(statut='REGULARISE').exists():
            conditions.append(
                "Justifier la régularisation complète des anciens impayés SCE."
            )

        return "\n".join(f"- {c}" for c in conditions)

    # ------------------------------------------------------------------
    # Calcul final
    # ------------------------------------------------------------------

    def calculer(self):
        """
        Calcule le score global et retourne le dictionnaire complet.
        """
        s_stabilite  = self._score_stabilite()
        s_capacite   = self._score_capacite()
        s_historique = self._score_historique_sce()
        s_dossier    = self._score_dossier()

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

        jour_salaire     = self.client.date_versement_salaire or 0
        jour_prelevement = self.dossier.jour_prelevement or 0

        resultats = {
            'score':                        score_total,
            'niveau_risque':                niveau_risque,
            'decision_ia':                  decision,
            'taux_endettement':             self.dossier.taux_endettement,
            'ratio_mensualite_salaire':     round(
                (self.dossier.mensualite_estimee / self.client.salaire_net) * 100, 2
            ) if self.client.salaire_net else 0,
            'delai_securite':               jour_prelevement - jour_salaire,
            'score_stabilite_emploi':       s_stabilite,
            'score_capacite_remboursement': s_capacite,
            'score_profil_client':          s_historique,
            'score_dossier':                s_dossier,
        }

        resultats['recommandation'] = self._generer_recommandation(
            score_total, resultats
        )
        resultats['conditions']     = self._generer_conditions(
            score_total, resultats
        )

        return resultats 