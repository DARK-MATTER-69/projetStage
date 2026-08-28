"""
Entraînement du modèle ML de scoring crédit SCE.

Note méthodologique importante (à assumer dans le mémoire) :
la base actuelle étant synthétique, le label de remboursement est généré
par une heuristique probabiliste (generer_label), pas observé sur un
historique réel. Le pipeline (split temporel, métriques, versionnement,
explicabilité) est en revanche rigoureux et directement réutilisable
tel quel le jour où de vraies données de remboursement seront disponibles.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline

CHEMIN_MODELE  = os.path.join(os.path.dirname(__file__), 'modele_scoring.pkl')
CHEMIN_METADATA = os.path.join(os.path.dirname(__file__), 'modele_meta.json')

# Labels lisibles des features, pour l'explicabilité affichée à l'écran
LIBELLES_FEATURES = {
    'type_employeur':         "Type d'employeur",
    'anciennete':              "Ancienneté professionnelle",
    'salaire_net':             "Salaire net",
    'quotite':                 "Quotité relative",
    'mensualite_vs_traite':    "Mensualité vs traite maximale autorisée",
    'nb_dossiers_approuves':   "Nombre de dossiers déjà approuvés",
    'nb_dossiers_rejetes':     "Nombre de dossiers déjà rejetés",
    'nb_impayes_cours':        "Impayés actuellement en cours",
    'nb_impayes_regularises':  "Impayés régularisés dans le passé",
    'evolution_salaire':       "Évolution du salaire dans le temps",
    'necessite_comite':        "Dossier soumis au comité",
    'duree_mois':              "Durée du prêt",
}


def extraire_features_client(client, dossier):
    """
    Extrait les features d'un client SCE pour le ML.
    Basé sur l'historique interne uniquement.
    """
    types_employeur = {
        'FONCTIONNAIRE': 5, 'RETRAITE': 4, 'PRIVE': 3,
        'ONG': 2, 'COMMERCANT': 1, 'AUTRE': 0,
    }

    salaire    = float(client.salaire_net)
    mensualite = float(dossier.mensualite_estimee)
    traite_max = float(dossier.traite_max_autorisee)
    quotite    = float(dossier.quotite_relative)

    nb_dossiers_approuves = client.dossiers.exclude(pk=dossier.pk).filter(statut='APPROUVE').count()
    nb_dossiers_rejetes   = client.dossiers.exclude(pk=dossier.pk).filter(statut='REJETE').count()

    nb_impayes_cours       = client.impayes.filter(statut__in=['EN_COURS', 'CONTENTIEUX']).count()
    nb_impayes_regularises = client.impayes.filter(statut='REGULARISE').count()

    historique = client.historique_salaires.order_by('date_effet')
    evolution_salaire = 0
    if historique.count() >= 2:
        premier = float(historique.first().salaire)
        dernier = float(historique.last().salaire)
        if premier > 0:
            evolution_salaire = round(((dernier - premier) / premier) * 100, 2)

    return {
        'type_employeur':         types_employeur.get(client.type_employeur, 0),
        'anciennete':             client.anciennete,
        'salaire_net':            salaire,
        'quotite':                quotite,
        'mensualite_vs_traite':   (mensualite / traite_max) if traite_max > 0 else 2,
        'nb_dossiers_approuves':  nb_dossiers_approuves,
        'nb_dossiers_rejetes':    nb_dossiers_rejetes,
        'nb_impayes_cours':       nb_impayes_cours,
        'nb_impayes_regularises': nb_impayes_regularises,
        'evolution_salaire':      evolution_salaire,
        'necessite_comite':       int(dossier.necessite_comite),
        'duree_mois':             dossier.duree_mois,
    }


def generer_label(client, dossier):
    """
    Génère un label de remboursement heuristique (0/1), en l'absence
    d'historique réel de défaut sur la base actuelle (données synthétiques).
    """
    import random

    if client.impayes.filter(statut__in=['EN_COURS', 'CONTENTIEUX']).exists():
        return 0

    score = 50
    nb_approuves = client.dossiers.exclude(pk=dossier.pk).filter(statut='APPROUVE').count()
    score += nb_approuves * 10

    nb_regularises = client.impayes.filter(statut='REGULARISE').count()
    score -= nb_regularises * 5

    nb_rejetes = client.dossiers.exclude(pk=dossier.pk).filter(statut='REJETE').count()
    score -= nb_rejetes * 8

    if client.type_employeur == 'FONCTIONNAIRE':
        score += 15
    elif client.type_employeur == 'RETRAITE':
        score += 12

    quotite = float(dossier.quotite_relative)
    if quotite <= 20:
        score += 15
    elif quotite <= 33:
        score += 5
    else:
        score -= 20

    probabilite = min(max(score / 100, 0.05), 0.98)
    return 1 if random.random() < probabilite else 0


def charger_donnees():
    """
    Charge les données depuis la DB SCE, triées chronologiquement
    (nécessaire pour le split temporel de l'entraînement).

    :return: tuple (X: DataFrame, y: array, dates: liste de dates)
    """
    from dossiers.models import Dossier

    dossiers = (
        Dossier.objects.select_related('client')
        .exclude(statut='BROUILLON')
        .order_by('cree_le')  # tri chronologique, essentiel pour le split temporel
    )

    if dossiers.count() < 30:
        raise ValueError(
            f"Données insuffisantes : {dossiers.count()} dossiers. "
            f"Minimum requis : 30. Lance : python manage.py generer_donnees"
        )

    features, labels, dates = [], [], []

    for dossier in dossiers:
        try:
            f = extraire_features_client(dossier.client, dossier)
            l = generer_label(dossier.client, dossier)
            features.append(f)
            labels.append(l)
            dates.append(dossier.cree_le)
        except Exception:
            continue

    X = pd.DataFrame(features)
    y = np.array(labels)

    return X, y, dates


def entrainer_modele():
    """
    Entraîne le modèle Random Forest sur l'historique SCE, avec :
    - un split TEMPOREL (entraînement sur les dossiers les plus anciens,
      test sur les plus récents — pour simuler une vraie mise en situation
      réelle, contrairement à un split aléatoire) ;
    - un versionnement horodaté du modèle produit ;
    - l'extraction des facteurs les plus déterminants (explicabilité).

    :return: dict métriques
    """
    print('Chargement des données SCE (triées chronologiquement)...')
    X, y, dates = charger_donnees()
    print(f'  {len(X)} dossiers chargés, du {dates[0]:%d/%m/%Y} au {dates[-1]:%d/%m/%Y}.')
    print(f'  {y.sum()} bons payeurs / {len(y) - y.sum()} à risque')

    # --- Split TEMPOREL : les 80% les plus anciens pour l'entraînement,
    #     les 20% les plus récents pour le test ---
    coupure = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:coupure], X.iloc[coupure:]
    y_train, y_test = y[:coupure], y[coupure:]

    print(f'  Entraînement sur les dossiers jusqu\'au {dates[coupure - 1]:%d/%m/%Y}')
    print(f'  Test sur les dossiers à partir du {dates[coupure]:%d/%m/%Y}')

    pipeline = Pipeline([
        ('scaler',     StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=100, max_depth=8, min_samples_split=5,
            random_state=42, class_weight='balanced'
        ))
    ])

    print('Entraînement...')
    pipeline.fit(X_train, y_train)

    y_pred   = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    rapport  = classification_report(y_test, y_pred, target_names=['À risque', 'Bon payeur'], output_dict=True)

    print(f'\nPrécision (sur données jamais vues, les plus récentes) : {accuracy:.2%}')

    # --- Explicabilité : quelles features pèsent le plus, globalement ---
    classifieur = pipeline.named_steps['classifier']
    importances = classifieur.feature_importances_
    facteurs = sorted(
        zip(X.columns, importances), key=lambda t: t[1], reverse=True
    )
    facteurs_lisibles = [
        {'feature': nom, 'libelle': LIBELLES_FEATURES.get(nom, nom), 'importance': round(float(imp), 4)}
        for nom, imp in facteurs
    ]

    # --- Versionnement ---
    version = datetime.now().strftime('v%Y%m%d_%H%M')

    joblib.dump(pipeline, CHEMIN_MODELE)

    metadata = {
        'version':            version,
        'date_entrainement':  datetime.now().isoformat(),
        'nb_dossiers':        len(X),
        'nb_train':           len(X_train),
        'nb_test':            len(X_test),
        'accuracy':           round(accuracy * 100, 2),
        'periode_train':      f'{dates[0]:%d/%m/%Y} - {dates[coupure - 1]:%d/%m/%Y}',
        'periode_test':       f'{dates[coupure]:%d/%m/%Y} - {dates[-1]:%d/%m/%Y}',
        'facteurs_determinants': facteurs_lisibles,
        'rapport_classification': rapport,
    }
    with open(CHEMIN_METADATA, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f'\nModèle {version} sauvegardé : {CHEMIN_MODELE}')
    print(f'Métadonnées sauvegardées : {CHEMIN_METADATA}')

    return {
        'version':     version,
        'accuracy':    round(accuracy * 100, 2),
        'nb_dossiers': len(X),
        'nb_train':    len(X_train),
        'nb_test':     len(X_test),
    }