"""
Prédiction ML de scoring crédit SCE.
"""

import os
import joblib
import pandas as pd

from .entrainement import CHEMIN_MODELE, extraire_features_client


class PredicteurScoring:
    """
    Prédit la probabilité de remboursement d'un client SCE.
    """

    def __init__(self):
        if not os.path.exists(CHEMIN_MODELE):
            raise FileNotFoundError(
                'Modèle ML introuvable. '
                'Lance : python manage.py entrainer_modele'
            )
        self.pipeline = joblib.load(CHEMIN_MODELE)

    def predire(self, dossier):
        """
        Prédit la probabilité de remboursement.

        :param dossier: Instance de dossiers.models.Dossier
        :return:        dict avec probabilité et décision
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

        return {
            'proba_remboursement': proba_remboursement,
            'proba_defaut':        round(float(proba[0]) * 100, 2),
            'decision_ml':         decision,
        }