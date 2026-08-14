"""
Entraînement du modèle ML de scoring crédit SCE.
Basé uniquement sur l'historique interne des clients SCE.
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

CHEMIN_MODELE = os.path.join(os.path.dirname(__file__), 'modele_scoring.pkl')


def extraire_features_client(client, dossier):
    """
    Extrait les features d'un client SCE pour le ML.
    Basé sur l'historique interne uniquement.

    :param client:  Instance de dossiers.models.Client
    :param dossier: Instance de dossiers.models.Dossier
    :return:        dict des features
    """
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
    quotite    = float(dossier.quotite_relative)

    # Historique dossiers SCE
    nb_dossiers_approuves = client.dossiers.exclude(
        pk=dossier.pk
    ).filter(statut='APPROUVE').count()

    nb_dossiers_rejetes = client.dossiers.exclude(
        pk=dossier.pk
    ).filter(statut='REJETE').count()

    # Impayés SCE
    nb_impayes_cours = client.impayes.filter(
        statut__in=['EN_COURS', 'CONTENTIEUX']
    ).count()

    nb_impayes_regularises = client.impayes.filter(
        statut='REGULARISE'
    ).count()

    # Evolution salariale
    historique = client.historique_salaires.order_by('date_effet')
    evolution_salaire = 0
    if historique.count() >= 2:
        premier = float(historique.first().salaire)
        dernier = float(historique.last().salaire)
        if premier > 0:
            evolution_salaire = round(
                ((dernier - premier) / premier) * 100, 2
            )

    return {
        'type_employeur':        types_employeur.get(client.type_employeur, 0),
        'anciennete':            client.anciennete,
        'salaire_net':           salaire,
        'quotite':               quotite,
        'mensualite_vs_traite':  (mensualite / traite_max) if traite_max > 0 else 2,
        'nb_dossiers_approuves': nb_dossiers_approuves,
        'nb_dossiers_rejetes':   nb_dossiers_rejetes,
        'nb_impayes_cours':      nb_impayes_cours,
        'nb_impayes_regularises': nb_impayes_regularises,
        'evolution_salaire':     evolution_salaire,
        'necessite_comite':      int(dossier.necessite_comite),
        'duree_mois':            dossier.duree_mois,
    }


def generer_label(client, dossier):
    """
    Génère le label de remboursement basé sur
    l'historique réel du client SCE.

    1 = a remboursé / va rembourser
    0 = risque de défaut

    :return: int 0 ou 1
    """
    import random

    # Impayés actifs → risque élevé
    if client.impayes.filter(
        statut__in=['EN_COURS', 'CONTENTIEUX']
    ).exists():
        return 0

    # Calcul score de base
    score = 50

    # Bonus historique positif SCE
    nb_approuves = client.dossiers.exclude(
        pk=dossier.pk
    ).filter(statut='APPROUVE').count()
    score += nb_approuves * 10

    # Malus impayés régularisés
    nb_regularises = client.impayes.filter(
        statut='REGULARISE'
    ).count()
    score -= nb_regularises * 5

    # Malus dossiers rejetés
    nb_rejetes = client.dossiers.exclude(
        pk=dossier.pk
    ).filter(statut='REJETE').count()
    score -= nb_rejetes * 8

    # Bonus fonctionnaire
    if client.type_employeur == 'FONCTIONNAIRE':
        score += 15
    elif client.type_employeur == 'RETRAITE':
        score += 12

    # Quotité
    quotite = float(dossier.quotite_relative)
    if quotite <= 20:
        score += 15
    elif quotite <= 33:
        score += 5
    else:
        score -= 20

    # Probabilité de remboursement
    probabilite = min(max(score / 100, 0.05), 0.98)
    return 1 if random.random() < probabilite else 0


def charger_donnees():
    """
    Charge les données depuis la DB SCE.
    Utilise uniquement les dossiers soumis ou plus avancés.

    :return: tuple (X, y)
    """
    from dossiers.models import Dossier

    dossiers = Dossier.objects.select_related(
        'client'
    ).exclude(
        statut='BROUILLON'
    )

    if dossiers.count() < 30:
        raise ValueError(
            f"Données insuffisantes : {dossiers.count()} dossiers. "
            f"Minimum requis : 30. "
            f"Lance : python manage.py generer_donnees"
        )

    features = []
    labels   = []

    for dossier in dossiers:
        try:
            f = extraire_features_client(dossier.client, dossier)
            l = generer_label(dossier.client, dossier)
            features.append(f)
            labels.append(l)
        except Exception:
            continue

    X = pd.DataFrame(features)
    y = np.array(labels)

    return X, y


def entrainer_modele():
    """
    Entraîne le modèle Random Forest sur l'historique SCE.
    Sauvegarde le modèle dans modele_scoring.pkl.

    :return: dict métriques
    """
    print('Chargement des données SCE...')
    X, y = charger_donnees()
    print(f'  {len(X)} dossiers chargés.')
    print(f'  {y.sum()} bons payeurs / {len(y) - y.sum()} à risque')

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ('scaler',     StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_split=5,
            random_state=42,
            class_weight='balanced'
        ))
    ])

    print('Entraînement...')
    pipeline.fit(X_train, y_train)

    y_pred   = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    rapport  = classification_report(
        y_test, y_pred,
        target_names=['À risque', 'Bon payeur']
    )

    print(f'\nPrécision : {accuracy:.2%}')
    print(f'\n{rapport}')

    joblib.dump(pipeline, CHEMIN_MODELE)
    print(f'\nModèle sauvegardé : {CHEMIN_MODELE}')

    return {
        'accuracy':    round(accuracy * 100, 2),
        'nb_dossiers': len(X),
        'nb_train':    len(X_train),
        'nb_test':     len(X_test),
    }