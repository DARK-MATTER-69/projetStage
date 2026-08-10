"""
Module d'entraînement du modèle ML de scoring crédit.
Utilise les données historiques de la DB pour entraîner
un modèle Random Forest de classification.
"""

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline


# Chemin de sauvegarde du modèle
CHEMIN_MODELE = os.path.join(
    os.path.dirname(__file__),
    'modele_scoring.pkl'
)


def extraire_features(score, dossier):
    """
    Extrait les features d'un dossier pour l'entraînement du modèle.
    Doit être identique à extraire_features_dossier() dans prediction.py.

    :param score:   Instance de scoring.models.ScoreCredit
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

    taux_endettement = float(score.taux_endettement)
    ratio_mensualite = float(score.ratio_mensualite_salaire)
    delai_securite   = score.delai_securite

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


def generer_label(score):
    """
    Génère le label de remboursement basé sur le score des règles métier.
    Simule le comportement historique de remboursement.

    Labels :
        1 = a remboursé sans problème
        0 = a fait défaut ou remboursement difficile
    """
    import random

    s = score.score

    if s >= 80:
        probabilite = 0.95
    elif s >= 70:
        probabilite = 0.85
    elif s >= 60:
        probabilite = 0.70
    elif s >= 50:
        probabilite = 0.50
    elif s >= 40:
        probabilite = 0.30
    else:
        probabilite = 0.10

    return 1 if random.random() < probabilite else 0


def charger_donnees():
    """
    Charge les données depuis la base de données Django
    et les transforme en DataFrame pandas.

    :return: tuple (X, y) features et labels
    """
    from scoring.models import ScoreCredit
    from dossiers.models import Dossier

    scores = ScoreCredit.objects.select_related(
        'dossier__client'
    ).all()

    if scores.count() < 50:
        raise ValueError(
            f'Données insuffisantes : {scores.count()} dossiers. '
            f'Minimum requis : 50. '
            f'Lance : python manage.py generer_donnees'
        )

    features = []
    labels   = []

    for score in scores:
        try:
            f = extraire_features(score, score.dossier)
            l = generer_label(score)
            features.append(f)
            labels.append(l)
        except Exception:
            continue

    X = pd.DataFrame(features)
    y = np.array(labels)

    return X, y


def entrainer_modele():
    """
    Entraîne le modèle Random Forest sur les données historiques.
    Sauvegarde le modèle entraîné dans un fichier .pkl.

    :return: dict avec les métriques d'entraînement
    """
    print('Chargement des données depuis la DB...')
    X, y = charger_donnees()
    print(f'  {len(X)} dossiers chargés.')
    print(f'  Répartition : {y.sum()} remboursés / {len(y) - y.sum()} défauts')

    # Division train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # Pipeline : normalisation + Random Forest
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_split=5,
            random_state=42,
            class_weight='balanced'
        ))
    ])

    print('Entraînement du modèle...')
    pipeline.fit(X_train, y_train)

    # Évaluation
    y_pred   = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    rapport  = classification_report(y_test, y_pred, target_names=['Défaut', 'Remboursé'])

    print(f'\nPrécision globale : {accuracy:.2%}')
    print(f'\nRapport détaillé :\n{rapport}')

    # Sauvegarde du modèle
    joblib.dump(pipeline, CHEMIN_MODELE)
    print(f'\nModèle sauvegardé : {CHEMIN_MODELE}')

    return {
        'accuracy':        round(accuracy * 100, 2),
        'nb_dossiers':     len(X),
        'nb_train':        len(X_train),
        'nb_test':         len(X_test),
        'chemin_modele':   CHEMIN_MODELE,
    }