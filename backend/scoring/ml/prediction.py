"""
Prédiction ML de scoring crédit SCE.
"""

import os
import json
import joblib
import pandas as pd

from .entrainement import CHEMIN_MODELE, CHEMIN_METADATA, extraire_features_client

NB_FACTEURS_AFFICHES = 3


class PredicteurScoring:
    """
    Prédit la probabilité de remboursement d'un client SCE,
    avec la version du modèle utilisé et ses facteurs les plus
    déterminants (explicabilité).
    """

    def __init__(self):
        if not os.path.exists(CHEMIN_MODELE):
            raise FileNotFoundError(
                'Modèle ML introuvable. Lance : python manage.py entrainer_modele'
            )
        self.pipeline = joblib.load(CHEMIN_MODELE)
        self.metadata = self._charger_metadata()

    def _charger_metadata(self):
        if os.path.exists(CHEMIN_METADATA):
            with open(CHEMIN_METADATA, encoding='utf-8') as f:
                return json.load(f)
        return {'version': 'inconnue', 'nb_dossiers': 0, 'facteurs_determinants': []}

    def predire(self, dossier):
        """
        Prédit la probabilité de remboursement.

        :param dossier: Instance de dossiers.models.Dossier
        :return:        dict avec probabilité, décision, version, facteurs
        """
        features = extraire_features_client(dossier.client, dossier)
        X        = pd.DataFrame([features])
        proba    = self.pipeline.predict_proba(X)[0]

        proba_remboursement = round(float(proba[1]) * 100, 2)

        if proba_remboursement >= 70:
            decision = 'FAVORABLE'
        elif proba_remboursement >= 50:
            decision = 'CONDITIONNEL'
        else:
            decision = 'DEFAVORABLE'

        # Facteurs les plus déterminants pour ce type de profil (importance
        # globale du modèle — pas une explication individuelle du dossier,
        # ce qui nécessiterait une librairie dédiée comme SHAP).
        facteurs = [
            f['libelle'] for f in self.metadata.get('facteurs_determinants', [])[:NB_FACTEURS_AFFICHES]
        ]

        return {
            'proba_remboursement': proba_remboursement,
            'proba_defaut':        round(float(proba[0]) * 100, 2),
            'decision_ml':         decision,
            'version_modele':      self.metadata.get('version', 'inconnue'),
            'nb_dossiers_entrainement': self.metadata.get('nb_dossiers', 0),
            'facteurs_determinants': facteurs,
        }