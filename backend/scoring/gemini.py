import google.generativeai as genai
from django.conf import settings


class ServiceGemini:
    """
    Service d'intégration avec l'API Google Gemini.
    Génère une analyse narrative et des recommandations
    en français à partir des résultats du scoring IA.
    """

    def __init__(self):
        """Configure le client Gemini avec la clé API du settings."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _construire_prompt(self, dossier, resultats_scoring):
        """
        Construit le prompt envoyé à Gemini à partir des données
        du dossier et des résultats du scoring.

        :param dossier: Instance de dossiers.models.Dossier
        :param resultats_scoring: dict retourné par MoteurScoring.calculer()
        :return: str prompt structuré
        """
        client = dossier.client

        return f"""
Tu es un analyste de crédit senior dans un établissement financier camerounais.
Tu dois rédiger une analyse professionnelle et concise d'un dossier de demande de crédit.
Réponds uniquement en français. Sois direct et factuel.

--- INFORMATIONS DU DOSSIER ---
Type de crédit       : {dossier.get_type_credit_display()}
Montant sollicité    : {dossier.montant_sollicite:,.0f} FCFA
Durée                : {dossier.duree_mois} mois
Mensualité estimée   : {dossier.mensualite_estimee:,.0f} FCFA
Traite max autorisée : {dossier.traite_max_autorisee:,.0f} FCFA
Objet                : {dossier.objet_financement}
Nécessite comité     : {'Oui' if dossier.necessite_comite else 'Non'}

--- PROFIL DU CLIENT ---
Type d'employeur     : {client.get_type_employeur_display()}
Employeur            : {client.nom_employeur}
Ancienneté           : {client.anciennete} ans
Salaire net          : {client.salaire_net:,.0f} FCFA
Charges mensuelles   : {client.charges_mensuelles:,.0f} FCFA
Crédits en cours     : {client.credits_en_cours:,.0f} FCFA

--- RÉSULTATS DU SCORING ---
Score global         : {resultats_scoring['score']}/100
Niveau de risque     : {resultats_scoring['niveau_risque']}
Décision IA          : {resultats_scoring['decision_ia']}
Taux d'endettement   : {resultats_scoring['taux_endettement']}%
Délai de sécurité    : {resultats_scoring['delai_securite']} jours
Score stabilité      : {resultats_scoring['score_stabilite_emploi']}/25
Score remboursement  : {resultats_scoring['score_capacite_remboursement']}/25
Score profil         : {resultats_scoring['score_profil_client']}/25
Score dossier        : {resultats_scoring['score_dossier']}/25

--- INSTRUCTIONS ---
Rédige une analyse structurée en 3 parties :

1. SYNTHESE (2-3 phrases) : résume le profil du client et sa demande.

2. POINTS FORTS ET POINTS DE VIGILANCE : liste les éléments positifs
   et les risques identifiés dans ce dossier.

3. RECOMMANDATION : formule une recommandation claire à destination
   de l'analyste engagement. Si la décision est CONDITIONNEL, précise
   les conditions à imposer. Si DEFAVORABLE, explique les raisons principales.

Limite ta réponse à 250 mots maximum.
"""

    def generer_analyse(self, dossier, resultats_scoring):
        """
        Génère l'analyse narrative du dossier via Gemini.

        :param dossier: Instance de dossiers.models.Dossier
        :param resultats_scoring: dict retourné par MoteurScoring.calculer()
        :return: str analyse générée ou message d'erreur
        """
        try:
            prompt   = self._construire_prompt(dossier, resultats_scoring)
            response = self.model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            return (
                f"Analyse automatique indisponible. "
                f"Veuillez procéder à une analyse manuelle. "
                f"Erreur : {str(e)}"
            )

    def generer_conditions(self, dossier, resultats_scoring):
        """
        Génère des conditions spécifiques si la décision est CONDITIONNEL.
        N'est appelé que lorsque la décision IA est CONDITIONNEL.

        :param dossier: Instance de dossiers.models.Dossier
        :param resultats_scoring: dict retourné par MoteurScoring.calculer()
        :return: str conditions proposées
        """
        if resultats_scoring['decision_ia'] != 'CONDITIONNEL':
            return ''

        prompt = f"""
Tu es un analyste de crédit dans un établissement financier camerounais.
Le dossier suivant a reçu une décision CONDITIONNELLE (score {resultats_scoring['score']}/100).

Montant sollicité    : {dossier.montant_sollicite:,.0f} FCFA
Mensualité estimée   : {dossier.mensualite_estimee:,.0f} FCFA
Traite max autorisée : {dossier.traite_max_autorisee:,.0f} FCFA
Taux d'endettement   : {resultats_scoring['taux_endettement']}%
Type d'employeur     : {dossier.client.get_type_employeur_display()}

Propose 2 à 3 conditions concrètes et réalistes pour que ce dossier
puisse être approuvé. Par exemple : réduction du montant, augmentation
de la durée, apport personnel, caution solidaire, etc.
Sois bref et précis. Maximum 100 mots.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return ''