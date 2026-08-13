"""
Utilitaire de génération de rapports PDF pour les dossiers SCE.
Utilise ReportLab pour produire un document professionnel.
"""

import os
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)


COULEUR_PRINCIPALE = colors.HexColor('#6B0F1A')
COULEUR_SECONDAIRE = colors.HexColor('#C9A84C')
COULEUR_GRIS       = colors.HexColor('#F5F5F5')


def generer_rapport_pdf(dossier):
    """
    Génère un rapport PDF complet pour un dossier de crédit SCE.

    :param dossier: Instance de dossiers.models.Dossier
    :return: bytes contenu du fichier PDF
    """
    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles  = getSampleStyleSheet()
    contenu = []

    # Style titre
    style_titre = ParagraphStyle(
        'Titre',
        parent=styles['Title'],
        fontSize=16,
        textColor=COULEUR_PRINCIPALE,
        spaceAfter=6,
    )

    # Style sous-titre section
    style_section = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=COULEUR_PRINCIPALE,
        spaceBefore=12,
        spaceAfter=6,
    )

    # Style corps
    style_corps = ParagraphStyle(
        'Corps',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4,
    )

    # Style alerte
    style_alerte = ParagraphStyle(
        'Alerte',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.red,
        spaceAfter=4,
    )

    client = dossier.client
    score  = getattr(dossier, 'score', None)

    # ── En-tête ────────────────────────────────────────────
    contenu.append(Paragraph(
        'SOCIÉTÉ CAMEROUNAISE D\'ÉQUIPEMENTS (SCE)',
        style_titre
    ))
    contenu.append(Paragraph(
        'RAPPORT D\'ANALYSE DE CRÉDIT',
        ParagraphStyle(
            'SousTitre',
            parent=styles['Normal'],
            fontSize=13,
            textColor=COULEUR_SECONDAIRE,
            spaceAfter=4,
        )
    ))
    contenu.append(HRFlowable(
        width='100%',
        thickness=2,
        color=COULEUR_SECONDAIRE,
        spaceAfter=12,
    ))

    # Référence et date
    contenu.append(Table(
        [[
            f'Dossier N° : {dossier.pk:06d}',
            f'Date : {datetime.now().strftime("%d/%m/%Y %H:%M")}',
            f'Commercial : {dossier.commercial.get_full_name()}',
        ]],
        colWidths=[5.5*cm, 5.5*cm, 6*cm],
        style=TableStyle([
            ('FONTSIZE',        (0,0), (-1,-1), 8),
            ('TEXTCOLOR',       (0,0), (-1,-1), colors.grey),
            ('ALIGN',           (1,0), (1,0), 'CENTER'),
            ('ALIGN',           (2,0), (2,0), 'RIGHT'),
        ])
    ))
    contenu.append(Spacer(1, 0.5*cm))

    # ── Section 1 : Informations client ───────────────────
    contenu.append(Paragraph('1. INFORMATIONS DU CLIENT', style_section))
    contenu.append(HRFlowable(width='100%', thickness=0.5, color=COULEUR_GRIS))
    contenu.append(Spacer(1, 0.2*cm))

    donnees_client = [
        ['Nom complet',     f'{client.civilite} {client.nom} {client.prenom}',
         'CNI',             client.numero_cni],
        ['Date naissance',  client.date_naissance.strftime('%d/%m/%Y'),
         'Téléphone',       client.telephone],
        ['Employeur',       client.nom_employeur,
         'Type',            client.get_type_employeur_display()],
        ['Poste',           client.poste_occupe,
         'Ancienneté',      f'{client.anciennete} ans'],
        ['Salaire net',     f'{client.salaire_net:,.0f} FCFA',
         'Charges',         f'{client.charges_mensuelles:,.0f} FCFA'],
        ['Crédits en cours', f'{client.credits_en_cours:,.0f} FCFA',
         'Jour salaire',    f'{client.date_versement_salaire or "N/A"}'],
    ]

    table_client = Table(
        donnees_client,
        colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm],
        style=TableStyle([
            ('FONTSIZE',        (0,0), (-1,-1), 8),
            ('BACKGROUND',      (0,0), (0,-1), COULEUR_GRIS),
            ('BACKGROUND',      (2,0), (2,-1), COULEUR_GRIS),
            ('FONTNAME',        (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME',        (2,0), (2,-1), 'Helvetica-Bold'),
            ('GRID',            (0,0), (-1,-1), 0.3, colors.lightgrey),
            ('ROWBACKGROUNDS',  (0,0), (-1,-1), [colors.white, colors.HexColor('#FAFAFA')]),
            ('PADDING',         (0,0), (-1,-1), 5),
        ])
    )
    contenu.append(table_client)
    contenu.append(Spacer(1, 0.4*cm))

    # ── Section 2 : Détails du crédit ─────────────────────
    contenu.append(Paragraph('2. DÉTAILS DE LA DEMANDE', style_section))
    contenu.append(HRFlowable(width='100%', thickness=0.5, color=COULEUR_GRIS))
    contenu.append(Spacer(1, 0.2*cm))

    donnees_credit = [
        ['Type de crédit',      dossier.get_type_credit_display(),
         'Statut',              dossier.get_statut_display()],
        ['Montant sollicité',   f'{dossier.montant_sollicite:,.0f} FCFA',
         'Durée',               f'{dossier.duree_mois} mois'],
        ['Mensualité estimée',  f'{dossier.mensualite_estimee:,.0f} FCFA',
         'Traite max autorisée', f'{dossier.traite_max_autorisee:,.0f} FCFA'],
        ['Jour prélèvement',    f'{dossier.jour_prelevement or "N/A"}',
         'Nécessite comité',    'Oui' if dossier.necessite_comite else 'Non'],
    ]

    table_credit = Table(
        donnees_credit,
        colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm],
        style=TableStyle([
            ('FONTSIZE',        (0,0), (-1,-1), 8),
            ('BACKGROUND',      (0,0), (0,-1), COULEUR_GRIS),
            ('BACKGROUND',      (2,0), (2,-1), COULEUR_GRIS),
            ('FONTNAME',        (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME',        (2,0), (2,-1), 'Helvetica-Bold'),
            ('GRID',            (0,0), (-1,-1), 0.3, colors.lightgrey),
            ('ROWBACKGROUNDS',  (0,0), (-1,-1), [colors.white, colors.HexColor('#FAFAFA')]),
            ('PADDING',         (0,0), (-1,-1), 5),
        ])
    )
    contenu.append(table_credit)

    # Objet du financement
    contenu.append(Spacer(1, 0.3*cm))
    contenu.append(Paragraph(
        f'<b>Objet du financement :</b> {dossier.objet_financement}',
        style_corps
    ))
    contenu.append(Paragraph(
        f'<b>Appréciation commerciale :</b> {dossier.appreciation}',
        style_corps
    ))

    # ── Section 3 : Score IA ──────────────────────────────
    if score:
        contenu.append(Paragraph('3. RÉSULTATS DU SCORING IA', style_section))
        contenu.append(HRFlowable(width='100%', thickness=0.5, color=COULEUR_GRIS))
        contenu.append(Spacer(1, 0.2*cm))

        couleurs_risque = {
            'FAIBLE':   colors.green,
            'MOYEN':    colors.orange,
            'ELEVE':    colors.red,
            'CRITIQUE': colors.darkred,
        }
        couleur_score = couleurs_risque.get(score.niveau_risque, colors.grey)

        # Score global
        table_score = Table(
            [[
                Paragraph(f'<b>Score global</b>', ParagraphStyle('s', fontSize=10)),
                Paragraph(
                    f'<font color="{couleur_score.hexval()}">'
                    f'<b>{score.score}/100 — {score.get_niveau_risque_display()}</b></font>',
                    ParagraphStyle('s2', fontSize=12)
                ),
                Paragraph(f'<b>Décision IA</b>', ParagraphStyle('s3', fontSize=10)),
                Paragraph(f'<b>{score.get_decision_ia_display()}</b>',
                    ParagraphStyle('s4', fontSize=10, textColor=couleur_score)
                ),
            ]],
            colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm],
            style=TableStyle([
                ('BACKGROUND',  (0,0), (-1,-1), COULEUR_GRIS),
                ('PADDING',     (0,0), (-1,-1), 8),
                ('GRID',        (0,0), (-1,-1), 0.3, colors.lightgrey),
            ])
        )
        contenu.append(table_score)
        contenu.append(Spacer(1, 0.3*cm))

        # Détail des critères
        donnees_scoring = [
            ['Critère', 'Score', 'Détail'],
            ['Stabilité de l\'emploi',      f'{score.score_stabilite_emploi}/25',
             f'Employeur : {client.get_type_employeur_display()}, {client.anciennete} ans'],
            ['Capacité de remboursement',   f'{score.score_capacite_remboursement}/25',
             f'Taux endettement : {score.taux_endettement}%'],
            ['Profil client',               f'{score.score_profil_client}/25',
             f'Délai sécurité : {score.delai_securite} jours'],
            ['Complétude du dossier',       f'{score.score_dossier}/25',
             f'Ratio mensualité/salaire : {score.ratio_mensualite_salaire}%'],
        ]

        table_scoring = Table(
            donnees_scoring,
            colWidths=[5*cm, 2.5*cm, 9.5*cm],
            style=TableStyle([
                ('FONTSIZE',        (0,0), (-1,-1), 8),
                ('BACKGROUND',      (0,0), (-1,0), COULEUR_PRINCIPALE),
                ('TEXTCOLOR',       (0,0), (-1,0), colors.white),
                ('FONTNAME',        (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID',            (0,0), (-1,-1), 0.3, colors.lightgrey),
                ('ROWBACKGROUNDS',  (0,1), (-1,-1), [colors.white, COULEUR_GRIS]),
                ('ALIGN',           (1,0), (1,-1), 'CENTER'),
                ('PADDING',         (0,0), (-1,-1), 5),
            ])
        )
        contenu.append(table_scoring)
        contenu.append(Spacer(1, 0.3*cm))

        # Recommandation IA
        if score.recommandation:
            contenu.append(Paragraph('Analyse et recommandation IA :', style_corps))
            contenu.append(Paragraph(score.recommandation, style_corps))

        if score.conditions:
            contenu.append(Spacer(1, 0.2*cm))
            contenu.append(Paragraph(
                f'<b>Conditions proposées :</b> {score.conditions}',
                style_alerte
            ))

    # ── Section 4 : Circuit de validation ─────────────────
    validations = dossier.validations.all()
    if validations.exists():
        contenu.append(Paragraph('4. CIRCUIT DE VALIDATION', style_section))
        contenu.append(HRFlowable(width='100%', thickness=0.5, color=COULEUR_GRIS))
        contenu.append(Spacer(1, 0.2*cm))

        donnees_validations = [['Validateur', 'Rôle', 'Décision', 'Commentaire', 'Date']]
        for v in validations:
            donnees_validations.append([
                v.validateur.get_full_name(),
                v.validateur.get_role_display(),
                v.get_decision_display(),
                v.commentaire[:50] + '...' if len(v.commentaire) > 50 else v.commentaire,
                v.date.strftime('%d/%m/%Y %H:%M'),
            ])

        table_validations = Table(
            donnees_validations,
            colWidths=[3.5*cm, 3*cm, 2.5*cm, 5*cm, 3*cm],
            style=TableStyle([
                ('FONTSIZE',    (0,0), (-1,-1), 7),
                ('BACKGROUND',  (0,0), (-1,0), COULEUR_PRINCIPALE),
                ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
                ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID',        (0,0), (-1,-1), 0.3, colors.lightgrey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, COULEUR_GRIS]),
                ('PADDING',     (0,0), (-1,-1), 4),
            ])
        )
        contenu.append(table_validations)

    # ── Pied de page ──────────────────────────────────────
    contenu.append(Spacer(1, 0.8*cm))
    contenu.append(HRFlowable(
        width='100%', thickness=1,
        color=COULEUR_SECONDAIRE, spaceAfter=8
    ))
    contenu.append(Paragraph(
        f'Document généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")} '
        f'— Plateforme SCE — Confidentiel',
        ParagraphStyle('Pied', parent=styles['Normal'], fontSize=7, textColor=colors.grey)
    ))

    doc.build(contenu)
    return buffer.getvalue()