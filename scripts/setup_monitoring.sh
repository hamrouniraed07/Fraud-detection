#!/bin/bash

echo "🚀 Configuration du monitoring pour Fraud Detection API"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier que les services sont actifs
echo -e "${YELLOW}1. Vérification des services...${NC}"
docker-compose ps | grep -E "mlflow|prometheus|grafana|api"
echo ""

# 2. Générer des métriques de test
echo -e "${YELLOW}2. Génération de métriques de test...${NC}"
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"features": [0.1, -1.2, 0.3, 1.8, -0.5, 2.1, -0.8, 0.4, -1.5, 0.9, 0.2, -0.3, 1.1, -0.7, 0.6, -1.9, 0.8, -0.2, 1.3, -0.4, 0.7, -1.1, 0.5, -0.6, 1.4, -0.9, 0.3, 1.7, -0.1, 100.0]}' \
    > /dev/null 2>&1
  echo -n "."
done
echo ""
echo -e "${GREEN}✅ 10 prédictions générées${NC}"
echo ""

# 3. Vérifier les métriques
echo -e "${YELLOW}3. Métriques disponibles:${NC}"
curl -s http://localhost:8000/metrics | grep "predictions_total"
echo ""

# 4. Afficher les URLs
echo ""
echo "======================================"
echo -e "${GREEN}✅ SERVICES ACTIFS${NC}"
echo "======================================"
echo ""
echo "📊 Prometheus (Métriques)"
echo "   URL: http://localhost:9090"
echo "   → Aller à Status > Targets pour voir l'API"
echo "   → Aller à Graph et taper: predictions_total"
echo ""
echo "📈 Grafana (Dashboards)"
echo "   URL: http://localhost:3000"
echo "   Login: admin / admin"
echo "   → Configuration > Data Sources > Add Prometheus"
echo "   → URL: http://prometheus:9090"
echo "   → Puis créer un dashboard"
echo ""
echo "🧪 MLflow (Tracking)"
echo "   URL: http://localhost:5000"
echo "   → Pour avoir des données, lancez un training:"
echo "   → python pipelines/training_pipeline_simple.py"
echo ""
echo "🔧 API (Swagger)"
echo "   URL: http://localhost:8000/docs"
echo "   → Testez l'API directement dans le navigateur"
echo ""
echo "======================================"
echo -e "${YELLOW}📝 ÉTAPES SUIVANTES:${NC}"
echo "======================================"
echo ""
echo "Pour Grafana:"
echo "1. Ouvrir http://localhost:3000"
echo "2. Login: admin / admin"
echo "3. Configuration (⚙️) > Data sources > Add data source"
echo "4. Choisir Prometheus"
echo "5. URL: http://prometheus:9090"
echo "6. Cliquer 'Save & Test'"
echo "7. Créer un nouveau dashboard avec ces queries:"
echo "   - rate(predictions_total[5m])"
echo "   - prediction_latency_seconds"
echo ""
echo "Pour MLflow (données de training):"
echo "cd pipelines && python training_pipeline_simple.py"
echo ""
