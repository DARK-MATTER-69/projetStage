"""
Module de prédiction ML du scoring crédit SCE.
Prédit la probabilité de remboursement d'un nouveau dossier
à partir du modèle Random Forest entraîné.
"""

import os
import joblib
import pandas as pd

from .entrainement import CHEMIN_MODELE


def extraire_features_dossier(dossier):
    """
    Extrait les features numériques directement depuis un dossier Django.
    Même structure que lors de l'entraînement.

    :param dossier: Instance de dossiers.models.Dossier
    :return:        dict des features
    """
    client = dossier.client

    types_employeur = {
        'FONCTIONNAIRE': 5,
        'RETRAITE':      4,
        'PRIVE':         3,
        'ONG':           2,
        'COMMERCANT':    1,
        'AUTRE':         0,
    }

    salaire    = float(client.salaire_net)
    mensualite = float(dossier.mensualite_estimee)
    traite_max = float(dossier.traite_max_autorisee)

    taux_endettement = float(dossier.taux_endettement)
    ratio_mensualite = (mensualite / salaire * 100) if salaire > 0 else 0

    jour_salaire     = client.date_versement_salaire or 0
    jour_prelevement = dossier.jour_prelevement or 0
    delai_securite   = jour_prelevement - jour_salaire

    return {
        'taux_endettement':          taux_endettement,
        'ratio_mensualite_salaire':  ratio_mensualite,
        'delai_securite':            delai_securite,
        'anciennete':                client.anciennete,
        'type_employeur_encode':     types_employeur.get(client.type_employeur, 0),
        'salaire_net':               salaire,
        'montant_sollicite':         float(dossier.montant_sollicite),
        'duree_mois':                dossier.duree_mois,
        'necessite_comite':          int(dossier.necessite_comite),
        'credits_en_cours':          float(client.credits_en_cours),
        'mensualite_vs_traite':      (mensualite / traite_max) if traite_max > 0 else 2,
    }


class PredicteurScoring:
    """
    Prédit la probabilité de remboursement d'un dossier
    à partir du modèle ML entraîné.
    """

    def __init__(self):
        """Charge le modèle depuis le fichier .pkl."""
        if not os.path.exists(CHEMIN_MODELE):
            raise FileNotFoundError(
                'Modèle ML introuvable. '
                'Lance : python manage.py entrainer_modele'
            )
        self.pipeline = joblib.load(CHEMIN_MODELE)

    def predire(self, dossier):
        """
        Prédit la probabilité de remboursement d'un dossier.

        :param dossier: Instance de dossiers.models.Dossier
        :return:        dict avec probabilité et décision ML
        """
        features = extraire_features_dossier(dossier)
        X        = pd.DataFrame([features])
        proba    = self.pipeline.predict_proba(X)[0]

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