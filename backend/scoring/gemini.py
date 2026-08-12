"""
Module d'extraction intelligente des relevés bancaires PDF via Gemini.
Gemini est utilisé UNIQUEMENT pour cette tâche de vision documentaire.
Le scoring et les recommandations restent 100% locaux.
"""

import json
import base64
from google import genai
from google.genai import types
from django.conf import settings
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class ResultatReleve:
    """Résultat de l'extraction Gemini d'un relevé bancaire."""
    total_credits:           Decimal = Decimal('0')
    total_debits:            Decimal = Decimal('0')
    solde_final:             Optional[Decimal] = None
    solde_moyen:             Optional[Decimal] = None
    remboursements_credits:  Decimal = Decimal('0')
    decouvert_detecte:       bool    = False
    nb_operations:           int     = 0
    banque_detectee:         str     = ""
    succes:                  bool    = True
    message:                 str     = ""

    @property
    def moyenne_credits_mensuelle(self):
        return round(self.total_credits / 3, 2)

    @property
    def moyenne_debits_mensuelle(self):
        return round(self.total_debits / 3, 2)


class ExtracteurReleveGemini:
    """
    Extrait les données financières d'un relevé bancaire PDF
    en utilisant les capacités de vision multimodale de Gemini.

    Compatible avec tous les formats de relevés bancaires camerounais :
    BICEC, AfriLand, SGBC, SCB, Campost, La Regional Bank, CCA.
    Fonctionne aussi sur les PDFs scannés.
    """

    PROMPT_EXTRACTION = """
Tu es un expert en analyse de relevés bancaires camerounais.
Analyse ce relevé bancaire et extrait les données financières suivantes.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après.

{
  "banque": "Nom de la banque détectée",
  "total_credits": 0.00,
  "total_debits": 0.00,
  "solde_final": 0.00,
  "solde_moyen": 0.00,
  "remboursements_credits": 0.00,
  "decouvert_detecte": false,
  "nb_operations": 0,
  "message": "Résumé en 1 phrase"
}

Règles d'extraction :
- total_credits : somme de TOUTES les opérations créditrices sur les 3 mois
- total_debits : somme de TOUTES les opérations débitrices sur les 3 mois
- solde_final : dernier solde visible sur le relevé
- solde_moyen : moyenne des soldes relevés (si disponible, sinon null)
- remboursements_credits : somme des lignes contenant les mots
  "echéance", "remboursement", "amortissement", "prêt", "crédit", "leasing"
- decouvert_detecte : true si un solde négatif ou le mot "découvert" apparaît
- nb_operations : nombre total de lignes d'opérations
- Tous les montants en FCFA sans le symbole, juste le nombre décimal
- Si une valeur est introuvable, mettre null (pas 0)
"""

    def __init__(self):
        """Configure le client Gemini."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model  = 'gemini-2.0-flash'

    def extraire(self, chemin_pdf: str) -> ResultatReleve:
        """
        Extrait les données d'un relevé bancaire PDF via Gemini Vision.

        :param chemin_pdf: str chemin vers le fichier PDF
        :return:           ResultatReleve avec toutes les données extraites
        """
        resultat = ResultatReleve()

        try:
            # Lire et encoder le PDF en base64
            with open(chemin_pdf, 'rb') as f:
                contenu_pdf = f.read()

            # Envoyer à Gemini avec le PDF en pièce jointe
            response = self.client.models.generate_content(
                model    = self.model,
                contents = [
                    types.Part.from_bytes(
                        data      = contenu_pdf,
                        mime_type = 'application/pdf',
                    ),
                    self.PROMPT_EXTRACTION,
                ]
            )

            # Parser la réponse JSON
            texte = response.text.strip()

            # Nettoyer les balises markdown si présentes
            if texte.startswith('```'):
                texte = texte.split('```')[1]
                if texte.startswith('json'):
                    texte = texte[4:]
            texte = texte.strip()

            donnees = json.loads(texte)

            # Construire le résultat
            def to_decimal(val):
                if val is None:
                    return None
                return Decimal(str(val))

            resultat.banque_detectee        = donnees.get('banque', '')
            resultat.total_credits          = to_decimal(donnees.get('total_credits')) or Decimal('0')
            resultat.total_debits           = to_decimal(donnees.get('total_debits')) or Decimal('0')
            resultat.solde_final            = to_decimal(donnees.get('solde_final'))
            resultat.solde_moyen            = to_decimal(donnees.get('solde_moyen'))
            resultat.remboursements_credits = to_decimal(donnees.get('remboursements_credits')) or Decimal('0')
            resultat.decouvert_detecte      = bool(donnees.get('decouvert_detecte', False))
            resultat.nb_operations          = int(donnees.get('nb_operations', 0))
            resultat.message                = donnees.get('message', '')

            resultat.succes = True

        except FileNotFoundError:
            resultat.succes  = False
            resultat.message = "Fichier PDF introuvable."

        except json.JSONDecodeError as e:
            resultat.succes  = False
            resultat.message = f"Réponse Gemini non parseable : {str(e)}"

        except Exception as e:
            # Fallback : si Gemini échoue, on retourne un résultat vide
            resultat.succes  = False
            resultat.message = f"Extraction indisponible : {str(e)}"

        return resultat