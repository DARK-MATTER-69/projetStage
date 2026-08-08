from .moteur import MoteurScoring
from .gemini import ServiceGemini
from .models import ScoreCredit


def calculer_et_sauvegarder_score(dossier):
    """
    Orchestre le calcul du score, la prédiction ML
    et la génération de l'analyse Gemini.
    Crée ou met à jour le ScoreCredit associé au dossier.

    :param dossier: Instance de dossiers.models.Dossier
    :return: Instance de scoring.models.ScoreCredit
    """
    # Calcul du score par règles métier
    moteur    = MoteurScoring(dossier)
    resultats = moteur.calculer()

    # Tentative de prédiction ML si le modèle existe
    try:
        from .ml.prediction import PredicteurScoring
        predicteur       = PredicteurScoring()
        prediction_ml    = predicteur.predire(
            type('obj', (object,), resultats)(),
            dossier
        )
        # Score final = moyenne pondérée règles (50%) + ML (50%)
        score_ml = prediction_ml['proba_remboursement'] / 2
        score_regles = resultats['score'] / 2
        resultats['score'] = round(score_regles + score_ml)

    except FileNotFoundError:
        # Modèle pas encore entraîné, on utilise uniquement les règles
        pass

    # Génération de l'analyse Gemini
    gemini     = ServiceGemini()
    analyse    = gemini.generer_analyse(dossier, resultats)
    conditions = gemini.generer_conditions(dossier, resultats)

    # Sauvegarde en base
    score, _ = ScoreCredit.objects.update_or_create(
        dossier=dossier,
        defaults={
            **resultats,
            'recommandation_ia':    analyse,
            'conditions_proposees': conditions,
        }
    )

    return score