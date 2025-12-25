#!/bin/bash

##############################################
# Script de déploiement pour Fraud Detection API
# Usage: ./scripts/deploy.sh <version>
# Example: ./scripts/deploy.sh v1
##############################################

set -e  # Exit on error

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier les arguments
if [ $# -eq 0 ]; then
    log_error "Usage: $0 <version>"
    echo "Example: $0 v1"
    exit 1
fi

VERSION=$1
MODEL_PATH="models/fraud_model_${VERSION}.pkl"

log_info "=========================================="
log_info "Déploiement de la version ${VERSION}"
log_info "=========================================="

# Vérifier que le modèle existe
if [ ! -f "$MODEL_PATH" ]; then
    log_error "Le modèle ${MODEL_PATH} n'existe pas!"
    log_info "Modèles disponibles:"
    ls -l models/*.pkl 2>/dev/null || echo "Aucun modèle trouvé"
    exit 1
fi

log_success "Modèle trouvé: ${MODEL_PATH}"

# Sauvegarder l'ancienne version (pour rollback)
if docker ps | grep -q fraud-api; then
    CURRENT_VERSION=$(docker exec fraud-api printenv MODEL_VERSION 2>/dev/null || echo "unknown")
    log_info "Version actuelle: ${CURRENT_VERSION}"
    echo "${CURRENT_VERSION}" > .last_version
    log_info "Version sauvegardée pour rollback"
fi

# Arrêter le conteneur existant
log_info "Arrêt du conteneur existant..."
docker-compose stop api 2>/dev/null || true
docker-compose rm -f api 2>/dev/null || true

# Définir les variables d'environnement
export MODEL_VERSION=$VERSION
export MODEL_PATH=$MODEL_PATH

# Reconstruire l'image si nécessaire
log_info "Construction de l'image Docker..."
docker-compose build api

# Démarrer le nouveau conteneur
log_info "Démarrage du conteneur avec la version ${VERSION}..."
docker-compose up -d api

# Attendre que l'API soit prête
log_info "Attente du démarrage de l'API..."
sleep 5

MAX_RETRIES=30
RETRY_COUNT=0
API_URL="http://localhost:8000"

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s "${API_URL}/health" > /dev/null 2>&1; then
        log_success "API démarrée avec succès!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_info "Tentative ${RETRY_COUNT}/${MAX_RETRIES}..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "L'API n'a pas démarré dans le temps imparti"
    log_error "Logs du conteneur:"
    docker logs fraud-api
    exit 1
fi

# Vérifier la version déployée
log_info "Vérification de la version déployée..."
DEPLOYED_VERSION=$(curl -s "${API_URL}/" | jq -r '.version')

if [ "$DEPLOYED_VERSION" = "$VERSION" ]; then
    log_success "Version déployée: ${DEPLOYED_VERSION}"
else
    log_error "Version déployée (${DEPLOYED_VERSION}) ne correspond pas à la version attendue (${VERSION})"
    exit 1
fi

# Test de santé
log_info "Test de santé de l'API..."
HEALTH_RESPONSE=$(curl -s "${API_URL}/health")
echo "$HEALTH_RESPONSE" | jq .

# Test de prédiction
log_info "Test de prédiction..."
TEST_DATA='{"features": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0]}'

PREDICTION_RESPONSE=$(curl -s -X POST "${API_URL}/predict" \
    -H "Content-Type: application/json" \
    -d "$TEST_DATA")

echo "$PREDICTION_RESPONSE" | jq .

if echo "$PREDICTION_RESPONSE" | jq -e '.model_version' > /dev/null; then
    log_success "Test de prédiction réussi!"
else
    log_error "Test de prédiction échoué!"
    exit 1
fi

# Afficher les informations finales
log_info "=========================================="
log_success "DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
log_info "=========================================="
log_info "Version déployée: ${VERSION}"
log_info "URL de l'API: ${API_URL}"
log_info "Documentation: ${API_URL}/docs"
log_info "Métriques: ${API_URL}/metrics"
log_info "=========================================="
log_info "Logs en temps réel: docker logs -f fraud-api"
log_info "Rollback: ./scripts/rollback.sh"
log_info "=========================================="