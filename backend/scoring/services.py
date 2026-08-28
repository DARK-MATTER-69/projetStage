from .moteur import MoteurScoring
from .models import ScoreCredit


def calculer_et_sauvegarder_score(dossier):
    """
    Calcule le score règles métier + prédiction ML, et les
    sauvegarde séparément (pas seulement fusionnés) pour que
    l'interface puisse afficher les deux côte à côte.
    """
    moteur    = MoteurScoring(dossier)
    resultats = moteur.calculer()

    score_regles = resultats['score']
    score_final  = score_regles

    score_ml            = None
    version_modele_ml   = ''
    facteurs_ml         = []

    # Un dossier inéligible (bloqué par le gardien) n'est pas envoyé au ML :
    # il n'y a rien à comparer, la décision est déjà tranchée.
    if resultats['eligible']:
        try:
            from .ml.prediction import PredicteurScoring
            predicteur    = PredicteurScoring()
            prediction_ml = predicteur.predire(dossier)

            score_ml           = prediction_ml['proba_remboursement']
            version_modele_ml  = prediction_ml['version_modele']
            facteurs_ml        = prediction_ml['facteurs_determinants']

            score_final = round((score_regles * 0.5) + (score_ml * 0.5))
        except FileNotFoundError:
            pass  # Modèle pas encore entraîné → score règles métier uniquement

    if not resultats['eligible']:
        niveau_risque = 'CRITIQUE'
        decision      = 'INELIGIBLE'
    else:
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
            'score':                    score_final,
            'score_regles':             score_regles,
            'score_ml':                 score_ml,
            'version_modele_ml':        version_modele_ml,
            'facteurs_ml':              facteurs_ml,
            'niveau_risque':            niveau_risque,
            'decision_ia':              decision,
            'eligible':                 resultats['eligible'],
            'motif_ineligibilite':      resultats['motif_ineligibilite'] or '',
            'taux_endettement':         resultats['taux_endettement'],
            'ratio_mensualite_salaire': resultats['ratio_mensualite_salaire'],
            'delai_securite':           resultats['delai_securite'],
            'score_quotite':            resultats['score_quotite'],
            'score_historique_sce':     resultats['score_historique_sce'],
            'score_stabilite':          resultats['score_stabilite'],
            'score_montant_vs_salaire': resultats['score_montant_vs_salaire'],
            'score_dossier':            resultats['score_dossier'],
            'score_fidelite':           resultats['score_fidelite'],
            'score_marge_securite':     resultats['score_marge_securite'],
            'recommandation':           resultats['recommandation'],
            'conditions':               resultats['conditions'],
        }
    )

    return score