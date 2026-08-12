"""
Extracteur automatique de relevés bancaires PDF.

Format détecté : Libellé | Date/Valeur | Débit | Crédit | Solde
"""

import re
import pdfplumber
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LigneReleve:
    """Représente une ligne extraite du relevé bancaire."""
    libelle: str
    debit:   Optional[Decimal] = None
    credit:  Optional[Decimal] = None
    solde:   Optional[Decimal] = None


@dataclass
class ResultatExtraction:
    """Résultat complet de l'extraction d'un relevé bancaire."""
    # Données financières clés
    total_credits:           Decimal = Decimal('0')
    total_debits:            Decimal = Decimal('0')
    solde_final:             Optional[Decimal] = None
    solde_initial:           Optional[Decimal] = None
    solde_moyen:             Optional[Decimal] = None
    remboursements_credits:  Decimal = Decimal('0')
    decouvert_detecte:       bool    = False
    nb_lignes_traitees:      int     = 0

    # Détail des lignes extraites
    lignes:                  list = field(default_factory=list)

    # Statut
    succes:                  bool = True
    message:                 str  = ""

    @property
    def solde_net(self):
        """Solde net = Total crédits - Total débits."""
        return self.total_credits - self.total_debits

    @property
    def moyenne_credits_mensuelle(self):
        """Moyenne des crédits sur 3 mois."""
        return round(self.total_credits / 3, 2)

    @property
    def moyenne_debits_mensuelle(self):
        """Moyenne des débits sur 3 mois."""
        return round(self.total_debits / 3, 2)


# Mots-clés indiquant un remboursement de crédit
MOTS_CLES_REMBOURSEMENT = [
    'echeance', 'échéance', 'remboursement', 'credit amort',
    'crédit amort', 'pret', 'prêt', 'mensualite', 'mensualité',
    'amortissement', 'dette', 'leasing', 'loc fin',
]

# Mots-clés indiquant un découvert
MOTS_CLES_DECOUVERT = [
    'decouvert', 'découvert', 'agios', 'commission depass',
    'dépassement', 'depassement', 'solde debiteur',
    'solde débiteur',
]

# Mots-clés à ignorer (lignes non financières)
MOTS_CLES_IGNORER = [
    'solde anterieur', 'solde antérieur', 'solde initial',
    'report', 'nouveau solde', 'total', 'sous-total',
    'date', 'libelle', 'libellé', 'debit', 'credit',
    'débit', 'crédit', 'solde', 'operation', 'opération',
]


def _nettoyer_montant(texte: str) -> Optional[Decimal]:
    """
    Convertit une chaîne de texte en Decimal.
    """
    if not texte:
        return None

    texte = texte.strip()

    # Supprimer les espaces insécables et normaux
    texte = texte.replace('\xa0', '').replace(' ', '')

    # Supprimer le signe moins (on le gère séparément)
    negatif = texte.startswith('-')
    texte   = texte.lstrip('-').lstrip('+')

    # Format français : 1.234.567,89 → 1234567.89
    if re.match(r'^\d{1,3}(\.\d{3})*,\d{2}$', texte):
        texte = texte.replace('.', '').replace(',', '.')

    # Format avec virgule comme séparateur décimal : 1234567,89
    elif ',' in texte and '.' not in texte:
        texte = texte.replace(',', '.')

    # Format avec point comme séparateur décimal : 1234567.89
    elif '.' in texte and ',' not in texte:
        pass  # Déjà correct

    # Supprimer tous les caractères non numériques sauf le point
    texte = re.sub(r'[^\d.]', '', texte)

    if not texte:
        return None

    try:
        valeur = Decimal(texte)
        return -valeur if negatif else valeur
    except InvalidOperation:
        return None


def _est_montant(texte: str) -> bool:
    """Vérifie si une chaîne ressemble à un montant financier."""
    texte = texte.strip().replace('\xa0', '').replace(' ', '')
    return bool(re.search(r'\d{2,}[.,]\d{2}', texte))


def _extraire_montants_ligne(cellules: list) -> tuple:
    """
    Extrait les montants débit, crédit et solde d'une liste de cellules.

    Stratégie :
    - On cherche les colonnes qui contiennent des montants
    - Les 2-3 dernières colonnes sont généralement débit/crédit/solde

    :param cellules: list de str représentant les cellules d'une ligne
    :return:         tuple (debit, credit, solde)
    """
    montants = []
    for c in cellules:
        if c and _est_montant(str(c)):
            val = _nettoyer_montant(str(c))
            if val is not None and val >= 0:
                montants.append(val)

    debit  = None
    credit = None
    solde  = None

    if len(montants) == 1:
        # Une seule valeur → soit débit soit crédit selon le contexte
        credit = montants[0]

    elif len(montants) == 2:
        # Deux valeurs → débit et crédit (ou crédit et solde)
        debit  = montants[0] if montants[0] > 0 else None
        credit = montants[1] if montants[1] > 0 else None

    elif len(montants) >= 3:
        # Trois valeurs ou plus → débit, crédit, solde
        debit  = montants[-3] if montants[-3] > 0 else None
        credit = montants[-2] if montants[-2] > 0 else None
        solde  = montants[-1]

    return debit, credit, solde


def _detecter_colonne_debit_credit(lignes_brutes: list) -> dict:
    """
    Analyse les en-têtes pour détecter quelle colonne est débit/crédit.

    :param lignes_brutes: list de list de str (tableau extrait)
    :return:              dict {'debit': index, 'credit': index, 'solde': index}
    """
    colonnes = {'debit': None, 'credit': None, 'solde': None}

    for ligne in lignes_brutes[:5]:  # Chercher dans les 5 premières lignes
        if not ligne:
            continue
        for i, cellule in enumerate(ligne):
            if not cellule:
                continue
            c = str(cellule).lower().strip()
            if c in ['débit', 'debit', 'débits', 'debits', 'montant débit']:
                colonnes['debit'] = i
            elif c in ['crédit', 'credit', 'crédits', 'credits', 'montant crédit']:
                colonnes['credit'] = i
            elif c in ['solde', 'balance']:
                colonnes['solde'] = i

    return colonnes


class ExtracteurReleve:
    """
    Extracteur de relevés bancaires PDF pour les banques camerounaises.
    Compatible avec : BICEC, AfriLand, SGBC, SCB, Campost,
                      La Regional Bank, CCA.
    """

    def extraire(self, chemin_pdf: str) -> ResultatExtraction:
        """
        Extrait les données financières d'un relevé bancaire PDF.

        :param chemin_pdf: str chemin vers le fichier PDF
        :return:           ResultatExtraction avec toutes les données
        """
        resultat = ResultatExtraction()

        try:
            with pdfplumber.open(chemin_pdf) as pdf:
                toutes_lignes = []

                for page in pdf.pages:
                    # Tentative 1 : extraction par tableaux
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            toutes_lignes.extend(table)
                    else:
                        # Tentative 2 : extraction par texte brut
                        texte = page.extract_text()
                        if texte:
                            for ligne in texte.split('\n'):
                                toutes_lignes.append([ligne])

                if not toutes_lignes:
                    resultat.succes  = False
                    resultat.message = "Aucun contenu extrait du PDF."
                    return resultat

                # Détection des colonnes
                colonnes = _detecter_colonne_debit_credit(toutes_lignes)

                # Traitement ligne par ligne
                soldes = []

                for ligne in toutes_lignes:
                    if not ligne or all(not c for c in ligne):
                        continue

                    # Reconstituer le libellé (première cellule non vide)
                    libelle = ""
                    for c in ligne:
                        if c and not _est_montant(str(c)):
                            libelle = str(c).strip()
                            break

                    libelle_lower = libelle.lower()

                    # Ignorer les lignes d'en-tête et de total
                    if any(mot in libelle_lower for mot in MOTS_CLES_IGNORER):
                        continue

                    # Extraire les montants
                    if colonnes['debit'] is not None:
                        # Colonnes détectées → extraction directe
                        debit_raw  = ligne[colonnes['debit']]  if colonnes['debit']  < len(ligne) else None
                        credit_raw = ligne[colonnes['credit']] if colonnes['credit'] and colonnes['credit'] < len(ligne) else None
                        solde_raw  = ligne[colonnes['solde']]  if colonnes['solde']  and colonnes['solde']  < len(ligne) else None

                        debit  = _nettoyer_montant(str(debit_raw))  if debit_raw  else None
                        credit = _nettoyer_montant(str(credit_raw)) if credit_raw else None
                        solde  = _nettoyer_montant(str(solde_raw))  if solde_raw  else None
                    else:
                        # Colonnes non détectées → heuristique
                        debit, credit, solde = _extraire_montants_ligne(ligne)

                    # Accumulation des totaux
                    if debit and debit > 0:
                        resultat.total_debits += debit

                        # Vérifier si c'est un remboursement de crédit
                        if any(m in libelle_lower for m in MOTS_CLES_REMBOURSEMENT):
                            resultat.remboursements_credits += debit

                    if credit and credit > 0:
                        resultat.total_credits += credit

                    if solde is not None:
                        soldes.append(solde)
                        # Détecter les découverts (solde négatif)
                        if solde < 0:
                            resultat.decouvert_detecte = True

                    # Détecter les découverts dans le libellé
                    if any(m in libelle_lower for m in MOTS_CLES_DECOUVERT):
                        resultat.decouvert_detecte = True

                    if libelle and (debit or credit):
                        resultat.lignes.append(LigneReleve(
                            libelle=libelle,
                            debit=debit,
                            credit=credit,
                            solde=solde,
                        ))
                        resultat.nb_lignes_traitees += 1

                # Calcul du solde moyen si disponible
                if soldes:
                    resultat.solde_initial = soldes[0]
                    resultat.solde_final   = soldes[-1]
                    resultat.solde_moyen   = Decimal(
                        str(sum(float(s) for s in soldes) / len(soldes))
                    ).quantize(Decimal('0.01'))

                resultat.message = (
                    f"{resultat.nb_lignes_traitees} opérations extraites. "
                    f"Total crédits : {resultat.total_credits:,.0f} FCFA. "
                    f"Total débits : {resultat.total_debits:,.0f} FCFA."
                )

        except Exception as e:
            resultat.succes  = False
            resultat.message = f"Erreur lors de l'extraction : {str(e)}"

        return resultat