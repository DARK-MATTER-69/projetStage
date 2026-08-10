from google import genai
from google.genai import types
from django.conf import settings
import time 


class ServiceGemini:
    """
    Service d'intégration avec l'API Google Gemini.
    Génère une analyse narrative et des recommandations
    en français à partir des résultats du scoring IA.
    """

    def __init__(self):
        """Configure le client Gemini avec la clé API du settings."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model  = 'gemini-2.0-flash'

    def _construire_prompt(self, dossier, resultats_scoring):
        """
        Construit un prompt concis pour économiser les tokens.
        """
        client = dossier.client

        return f"""Tu es analyste de crédit à la SCE Cameroun. Analyse ce dossier en 150 mots max.

    DOSSIER
    - Client : {client.get_type_employeur_display()}, {client.anciennete} ans ancienneté
    - Salaire : {client.salaire_net:,.0f} FCFA
    - Montant : {dossier.montant_sollicite:,.0f} FCFA / {dossier.duree_mois} mois
    - Mensualité : {dossier.mensualite_estimee:,.0f} FCFA
    - Traite max : {dossier.traite_max_autorisee:,.0f} FCFA
    - Taux endettement : {resultats_scoring['taux_endettement']}%

    SCORE IA : {resultats_scoring['score']}/100 — {resultats_scoring['niveau_risque']} — {resultats_scoring['decision_ia']}

    Rédige en français :
    1. SYNTHESE (1 phrase)
    2. POINTS CLES (2-3 points max)
    3. RECOMMANDATION (1 phrase claire)"""

    def generer_analyse(self, dossier, resultats_scoring):
        try:
            # Respecte la limite de 15 requêtes/minute
            time.sleep(4.5)
            prompt   = self._construire_prompt(dossier, resultats_scoring)
            response = self.client.models.generate_content(
                model    = self.model,
                contents = prompt
            )
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
            response = self.client.models.generate_content(
            model    = self.model,
            contents = prompt
            )
            return response.text.strip()
        except Exception:
            return ''