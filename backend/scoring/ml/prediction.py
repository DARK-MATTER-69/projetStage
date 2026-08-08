"""
Module de prédiction du modèle ML de scoring crédit.
Charge le modèle entraîné et prédit la probabilité
de remboursement d'un nouveau dossier.
"""

import os
import joblib
import pandas as pd

from .entrainement import CHEMIN_MODELE, extraire_features


class PredicteurScoring:
    """
    Prédit la probabilité de remboursement d'un dossier
    à partir du modèle ML entraîné.
    """

    def __init__(self):
        """Charge le modèle ML depuis le fichier .pkl."""
        if not os.path.exists(CHEMIN_MODELE):
            raise FileNotFoundError(
                'Modèle ML introuvable. '
                'Lance : python manage.py entrainer_modele'
            )
        self.pipeline = joblib.load(CHEMIN_MODELE)

    def predire(self, score, dossier):
        """
        Prédit la probabilité de remboursement d'un dossier.

        :param score: Instance de scoring.models.ScoreCredit
        :param dossier: Instance de dossiers.models.Dossier
        :return: dict avec probabilité et décision ML
        """
        features  = extraire_features(score, dossier)
        X         = pd.DataFrame([features])
        proba     = self.pipeline.predict_proba(X)[0]

        # proba[1] = probabilité de remboursement
        proba_remboursement = round(float(proba[1]) * 100, 2)

        if proba_remboursement >= 70:
            decision_ml = 'FAVORABLE'
        elif proba_remboursement >= 50:
            decision_ml = 'CONDITIONNEL'
        else:
            decision_ml = 'DEFAVORABLE'

        return {
            'proba_remboursement': proba_remboursement,
            'proba_defaut':        round(float(proba[0]) * 100, 2),
            'decision_ml':         decision_ml,
        }