from .moteur import MoteurScoring
from .gemini import ServiceGemini
from .models import ScoreCredit


def calculer_et_sauvegarder_score(dossier):
    """
    Met en oeuvre le calcul du score et la génération de l'analyse Gemini.
    Crée ou met à jour le ScoreCredit associé au dossier.

    :param dossier: Instance de dossiers.models.Dossier
    :return: Instance de scoring.models.ScoreCredit
    """
    # Calcul du score
    moteur    = MoteurScoring(dossier)
    resultats = moteur.calculer()

    # Génération de l'analyse Gemini
    gemini      = ServiceGemini()
    analyse     = gemini.generer_analyse(dossier, resultats)
    conditions  = gemini.generer_conditions(dossier, resultats)

    # Création ou mise à jour du score en base
    score, _ = ScoreCredit.objects.update_or_create(
        dossier=dossier,
        defaults={
            **resultats,
            'recommandation_ia':    analyse,
            'conditions_proposees': conditions,
        }
    )

    return score