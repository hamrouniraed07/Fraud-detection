#!/bin/bash

##############################################
# Script de configuration DVC
# Usage: ./scripts/setup_dvc.sh
##############################################

set -e

echo "=========================================="
echo "Configuration de DVC"
echo "=========================================="

# Vérifier que DVC est installé
if ! command -v dvc &> /dev/null; then
    echo "❌ DVC n'est pas installé"
    echo "Installation: pip install dvc"
    exit 1
fi

echo "✅ DVC est installé"

# Initialiser DVC si ce n'est pas déjà fait
if [ ! -d ".dvc" ]; then
    echo "📦 Initialisation de DVC..."
    dvc init
    git add .dvc .dvcignore
    git commit -m "Initialize DVC"
    echo "✅ DVC initialisé"
else
    echo "✅ DVC déjà initialisé"
fi

# Configurer le remote storage
echo ""
echo "Configuration du remote storage"
echo "Choisissez votre option:"
echo "1) Local (pour tests)"
echo "2) S3"
echo "3) Google Drive"
echo "4) Azure"

read -p "Votre choix (1-4): " choice

case $choice in
    1)
        echo "Configuration d'un remote local..."
        REMOTE_PATH="/tmp/dvc-storage"
        mkdir -p $REMOTE_PATH
        dvc remote add -d myremote $REMOTE_PATH
        echo "✅ Remote local configuré: $REMOTE_PATH"
        ;;
    2)
        echo "Configuration d'un remote S3..."
        read -p "Nom du bucket S3: " bucket
        read -p "Région AWS: " region
        dvc remote add -d myremote s3://$bucket/dvc-storage
        dvc remote modify myremote region $region
        echo "✅ Remote S3 configuré: s3://$bucket/dvc-storage"
        echo "⚠️  N'oubliez pas de configurer vos credentials AWS"
        ;;
    3)
        echo "Configuration d'un remote Google Drive..."
        read -p "ID du dossier Google Drive: " drive_id
        dvc remote add -d myremote gdrive://$drive_id
        echo "✅ Remote Google Drive configuré"
        echo "⚠️  Vous devrez vous authentifier lors du premier push"
        ;;
    4)
        echo "Configuration d'un remote Azure..."
        read -p "Nom du container Azure: " container
        dvc remote add -d myremote azure://$container/dvc-storage
        echo "✅ Remote Azure configuré"
        echo "⚠️  N'oubliez pas de configurer vos credentials Azure"
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

git add .dvc/config
git commit -m "Configure DVC remote storage"

echo ""
echo "=========================================="
echo "Configuration de DVC terminée!"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo "1. Ajouter vos données: dvc add data/raw/creditcard.csv"
echo "2. Commit: git add data/raw/creditcard.csv.dvc .gitignore && git commit -m 'Add dataset'"
echo "3. Push vers le remote: dvc push"
echo "=========================================="