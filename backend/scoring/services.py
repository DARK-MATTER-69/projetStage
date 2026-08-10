from .moteur import MoteurScoring
from .models import ScoreCredit


def calculer_et_sauvegarder_score(dossier):
    """
    Met en oeuvre le calcul du score règles métier + prédiction ML.
    Aucun appel externe requis.

    :param dossier: Instance de dossiers.models.Dossier
    :return:        Instance de scoring.models.ScoreCredit
    """
    # Calcul score règles métier
    moteur    = MoteurScoring(dossier)
    resultats = moteur.calculer()

    score_final = resultats['score']

    # Prédiction ML si le modèle est entraîné
    try:
        from .ml.prediction import PredicteurScoring
        predicteur    = PredicteurScoring()
        prediction_ml = predicteur.predire(dossier)  # on passe le dossier directement

        # Score final = 50% règles métier + 50% ML
        score_final = round(
            (resultats['score'] * 0.5) +
            (prediction_ml['proba_remboursement'] * 0.5)
        )

    except FileNotFoundError:
        # Modèle pas encore entraîné → score règles métier uniquement
        pass

    # Recalcul niveau risque et décision selon score final
    if score_final >= 80:
        niveau_risque = 'FAIBLE'
    elif score_final >= 60:
        niveau_risque = 'MOYEN'
    elif score_final >= 40:
        niveau_risque = 'ELEVE'
    else:
        niveau_risque = 'CRITIQUE'

    if score_final >= 70:
        decision = 'FAVORABLE'
    elif score_final >= 50:
        decision = 'CONDITIONNEL'
    else:
        decision = 'DEFAVORABLE'

    score, _ = ScoreCredit.objects.update_or_create(
        dossier=dossier,
        defaults={
            'score':                        score_final,
            'niveau_risque':                niveau_risque,
            'decision_ia':                  decision,
            'taux_endettement':             resultats['taux_endettement'],
            'ratio_mensualite_salaire':     resultats['ratio_mensualite_salaire'],
            'delai_securite':               resultats['delai_securite'],
            'score_stabilite_emploi':       resultats['score_stabilite_emploi'],
            'score_capacite_remboursement': resultats['score_capacite_remboursement'],
            'score_profil_client':          resultats['score_profil_client'],
            'score_dossier':                resultats['score_dossier'],
            'recommandation':   resultats['recommandation'],
            'conditions':       resultats['conditions'],
        }
    )

    return score