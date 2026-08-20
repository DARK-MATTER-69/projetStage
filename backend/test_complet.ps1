# Script de test global — plateforme de gestion de crédit SCE (Windows)
#
# Vérifie le bon fonctionnement de bout en bout du système :
# migrations, génération de données, entraînement du modèle ML,
# suite de tests automatisés (circuit complet de validation),
# et vérification de configuration Django.
#
# Usage : depuis le dossier backend\, dans PowerShell :
#   .\test_complet.ps1
#
# Si l'exécution de scripts est bloquée, lance d'abord une fois :
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$etapes    = @()
$resultats = @()

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
    $succes = ($LASTEXITCODE -eq 0)

    $script:etapes    += $Nom
    $script:resultats += $(if ($succes) { "OK" } else { "ECHEC" })

    Write-Host ""
    if ($succes) {
        Write-Host "[OK] $Nom - reussi" -ForegroundColor Green
    } else {
        Write-Host "[ECHEC] $Nom - echoue (voir la sortie ci-dessus)" -ForegroundColor Red
    }
    Write-Host "----------------------------------------------------" -ForegroundColor DarkGray
}

Write-Host "======================================================"
Write-Host "  TEST GLOBAL - Plateforme de gestion de credit SCE"
Write-Host "======================================================"

# 1. Vérifie qu'aucune migration n'est manquante (modèles <-> base cohérents)
Executer-Etape -Nom "1. Verification des migrations en attente" `
               -Commande "python manage.py makemigrations --check --dry-run"

# 2. Applique toutes les migrations
Executer-Etape -Nom "2. Application des migrations" `
               -Commande "python manage.py migrate --no-input"

# 3. Vérification système Django (config, sécurité de base)
Executer-Etape -Nom "3. Verification de la configuration Django" `
               -Commande "python manage.py check"

# 4. Nettoyage des données de test précédentes (repart d'une base propre)
Executer-Etape -Nom "4. Nettoyage des donnees fictives existantes" `
               -Commande "python manage.py supprimer_donnees"

# 5. Génération d'un jeu de données réaliste (150 clients)
Executer-Etape -Nom "5. Generation des donnees de test (150 clients)" `
               -Commande "python manage.py generer_donnees --nombre 150"

# 6. Entraînement du modèle ML sur les données fraîchement générées
Executer-Etape -Nom "6. Entrainement du modele de scoring ML" `
               -Commande "python manage.py entrainer_modele"

# 7. Suite de tests automatisés — circuit complet, tous rôles, recalculs
Executer-Etape -Nom "7. Suite de tests automatises (dossiers)" `
               -Commande "python manage.py test dossiers -v 2"

# --- Résumé final ---
Write-Host ""
Write-Host "======================================================"
Write-Host "  RESUME"
Write-Host "======================================================"

$nbOk    = 0
$nbEchec = 0

for ($i = 0; $i -lt $etapes.Count; $i++) {
    if ($resultats[$i] -eq "OK") {
        Write-Host "  [OK]     $($etapes[$i])" -ForegroundColor Green
        $nbOk++
    } else {
        Write-Host "  [ECHEC]  $($etapes[$i])" -ForegroundColor Red
        $nbEchec++
    }
}

Write-Host ""
Write-Host "  Total : $nbOk reussi(s) / $nbEchec echoue(s) sur $($etapes.Count) etapes"
Write-Host "======================================================"

if ($nbEchec -gt 0) {
    Write-Host "Certaines etapes ont echoue - corrige-les avant de considerer le systeme stable." -ForegroundColor Red
    exit 1
} else {
    Write-Host "Toutes les etapes sont passees - le systeme fonctionne de bout en bout." -ForegroundColor Green
    exit 0
}
