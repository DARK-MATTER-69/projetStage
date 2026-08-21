# Script de test global — plateforme de gestion de crédit SCE (Windows)
#
# S'ARRÊTE IMMÉDIATEMENT dès qu'une étape échoue.
#
# Usage : depuis le dossier backend\, dans PowerShell :
#   .\test_complet.ps1
#
# Si l'exécution de scripts est bloquée :
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#   Unblock-File -Path .\test_complet.ps1

function Executer-Etape {
    param(
        [string]$Nom,
        [string]$Commande
    )

    Write-Host ""
    Write-Host "-> $Nom" -ForegroundColor Yellow
    Write-Host "   $Commande" -ForegroundColor DarkGray
    Write-Host ""

    Invoke-Expression $Commande

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "======================================================" -ForegroundColor Red
        Write-Host "[ECHEC] $Nom" -ForegroundColor Red
        Write-Host "Arret du script - corrige cette erreur avant de continuer." -ForegroundColor Red
        Write-Host "======================================================" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "[OK] $Nom - reussi" -ForegroundColor Green
    Write-Host "----------------------------------------------------" -ForegroundColor DarkGray
}

Write-Host "======================================================"
Write-Host "  TEST GLOBAL - Plateforme de gestion de credit SCE"
Write-Host "  (arret automatique a la premiere erreur)"
Write-Host "======================================================"

Executer-Etape -Nom "1. Verification des migrations en attente" `
               -Commande "python manage.py makemigrations --check --dry-run"

Executer-Etape -Nom "2. Application des migrations" `
               -Commande "python manage.py migrate --no-input"

Executer-Etape -Nom "3. Verification de la configuration Django" `
               -Commande "python manage.py check"

Executer-Etape -Nom "4. Nettoyage des donnees fictives existantes" `
               -Commande "python manage.py supprimer_donnees"

Executer-Etape -Nom "5. Generation des donnees de test (150 clients)" `
               -Commande "python manage.py generer_donnees --nombre 150"

Executer-Etape -Nom "6. Entrainement du modele de scoring ML" `
               -Commande "python manage.py entrainer_modele"

Executer-Etape -Nom "7. Suite de tests automatises (dossiers)" `
               -Commande "python manage.py test dossiers -v 2"

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  TOUTES LES ETAPES SONT PASSEES" -ForegroundColor Green
Write-Host "  Le systeme fonctionne de bout en bout." -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
exit 0
