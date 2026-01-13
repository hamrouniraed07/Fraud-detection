# 📊 Guide Rapide - Monitoring & Dashboards

## 🚀 Démarrage Rapide (30 secondes)

```bash
# 1. Lancer tous les services
docker-compose up -d

# 2. Vérifier l'état
docker-compose ps

# 3. Générer des métriques
python scripts/test_api.py

# 4. Ouvrir les interfaces
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# API: http://localhost:8000/docs
```

---

## 📍 Accès Rapide aux Services

### 🔵 Grafana (Dashboards Visuels)
```
URL: http://localhost:3000
Login: admin / admin
Dashboard: "Fraud Detection API - Monitoring"
Features:
  ✓ Real-time metrics
  ✓ 7 panneaux pré-configurés
  ✓ Alertes automatiques
  ✓ Export de données
```

### 🟢 Prometheus (Base de Données Métriques)
```
URL: http://localhost:9090
Features:
  ✓ Requêtes PromQL
  ✓ Historique complet
  ✓ Scraping: API tous les 10s
  ✓ Retention: 15 jours
```

### 🟠 MLflow (Tracking Expériences)
```
URL: http://localhost:5000
Features:
  ✓ Entraînements trackés
  ✓ Comparaison de modèles
  ✓ Artifacts versionnés
  ✓ Métriques et paramètres
```

### 🔵 FastAPI (API & Docs)
```
URL: http://localhost:8000/docs
Features:
  ✓ Documentation interactive
  ✓ Test les endpoints
  ✓ Logs des requêtes
  ✓ Health check: /health
```

---

## 📊 Panneaux Grafana Expliqués

### 1️⃣ Total Predictions by Type (Pie Chart)
**Affiche**: Distribution fraude vs légitime
**Utilité**: Voir le ratio de fraudes détectées
**Seuil OK**: > 50% si fraude dans données

### 2️⃣ Total Predictions (Stat Card)
**Affiche**: Nombre cumulé de prédictions
**Utilité**: Volume total traité
**Seuil OK**: Croissance continue

### 3️⃣ Prediction Rate (Time Series)
**Affiche**: Requêtes par 5 minutes
**Utilité**: Identifier les pics d'utilisation
**Seuil ALERTE**: = 0 (arrêt du service)

### 4️⃣ Prediction Latency (Time Series)
**Affiche**: P50, P95, P99 de latence
**Utilité**: Performance de l'API
**Seuil ALERTE**: P95 > 100ms

### 5️⃣ Fraud Detection Rate (Stat Card)
**Affiche**: % de fraudes détectées
**Utilité**: Efficacité du modèle
**Seuil ALERTE**: < 50%

### 6️⃣ Error Rate (Bar Chart)
**Affiche**: Taux d'erreurs par type
**Utilité**: Stabilité du système
**Seuil ALERTE**: > 5%

### 7️⃣ Total Errors (Stat Card)
**Affiche**: Erreurs par minute
**Utilité**: Anomalies système
**Seuil ALERTE**: > 0

---

## 🔍 Requêtes Prometheus Utiles

### Copier-Coller dans http://localhost:9090

```promql
# 📈 Taux de prédictions/min
rate(predictions_total[1m])

# ⏱️ Latence moyenne
rate(prediction_latency_seconds_sum[5m]) / 
rate(prediction_latency_seconds_count[5m])

# 📊 Latence P99
histogram_quantile(0.99, rate(prediction_latency_seconds_bucket[5m]))

# ❌ Taux d'erreurs (%)
(rate(prediction_errors_total[5m]) / 
 rate(predictions_total[5m]) * 100)

# 🚨 Fraudes/heure
increase(predictions_total{prediction="fraud"}[1h])

# 🟢 API en ligne?
up{job="api"}

# 📊 Prédictions par modèle
sum by (model_version) (predictions_total)
```

---

## ⚙️ Configuration Grafana (Première Fois)

### Étape 1: Ajouter Prometheus

```
1. Connexion: admin / admin
2. Cliquer sur ⚙️ (Settings) en bas à gauche
3. Data Sources → Add data source
4. Choisir Prometheus
5. URL: http://prometheus:9090
6. Cliquer "Save & Test"
✓ Data source should be working
```

### Étape 2: Importer le Dashboard

```
1. Menu Dashboards (quatre carrés)
2. Import
3. Coller le contenu de: monitoring/dashboards/fraud-detection-dashboard.json
   OU Upload JSON file
4. Sélectionner Prometheus comme datasource
5. Click Import
✓ Dashboard visible avec données
```

### Étape 3: Configurer Alertes (Optionnel)

```
1. Aller sur un panneau
2. Edit → Alert
3. Set condition: Quand value > X
4. Set notification channel
5. Save
```

---

## 🐛 Troubleshooting

### ❌ Grafana vide (pas de données)

**Cause probable**: Prometheus n'est pas configuré

**Solution**:
```bash
# 1. Vérifier Prometheus
curl http://localhost:9090

# 2. Vérifier le scraping
curl http://localhost:9090/api/v1/targets | jq '.data'

# 3. Vérifier l'API
curl http://localhost:8000/metrics | grep predictions_total

# 4. Attendre 10s (premier scrape)
sleep 10

# 5. Rafraîchir Grafana (F5)
```

### ❌ "Prometheus is not responding"

**Cause**: Datasource mal configurée

**Solution**:
```bash
# Test depuis Grafana
docker exec grafana curl http://prometheus:9090

# Reconfigurer datasource:
# http://prometheus:9090 (pas localhost!)
```

### ❌ Pas de métriques de l'API

**Cause**: API pas en train de servir

**Solution**:
```bash
# Vérifier l'API
curl http://localhost:8000/health

# Générer des métriques
python scripts/test_api.py

# Vérifier les métriques
curl http://localhost:8000/metrics
```

### ❌ "Connection refused"

**Cause**: Services pas lancés

**Solution**:
```bash
# Relancer docker-compose
docker-compose down
docker-compose up -d --build

# Attendre le démarrage (~30s)
sleep 30

# Vérifier
docker-compose ps
```

---

## 📊 Cas d'Usage

### 📱 Vérifier la Performance en Production

```
1. Ouvrir Grafana → Prediction Latency
2. Regarder P95 et P99
3. Si > 100ms → Performance dégradée
4. Augmenter les ressources serveur
```

### 🔴 Monitorer les Fraudes

```
1. Ouvrir Grafana → Fraud Detection Rate
2. Regarder le pourcentage
3. Si < 50% → Modèle doit être ré-entraîné
4. Lancer training_pipeline.py
```

### ⚠️ Détecter les Anomalies

```
1. Ouvrir Grafana → Error Rate
2. Si spike → Vérifier les logs
3. docker-compose logs -f api
4. Corriger et redéployer
```

### 📈 Analyser la Croissance

```
1. Ouvrir Prometheus
2. Requête: rate(predictions_total[1h])
3. Voir les tendances
4. Planifier la capacité
```

---

## 🚀 Commandes Utiles

```bash
# Logs en temps réel
docker-compose logs -f api

# Logs d'un service spécifique
docker-compose logs -f prometheus

# Redémarrer tout
docker-compose restart

# Arrêter proprement
docker-compose down

# Vue d'ensemble
docker-compose ps

# Nettoyer les données
docker-compose down -v  # ⚠️ Supprime les données!
```

---

## 📚 Fichiers Importants

```
monitoring/
├── prometheus.yml          # Configuration Prometheus
├── dashboards/
│   └── fraud-detection-dashboard.json  # Dashboard Grafana
└── alert-rules.yml         # Règles d'alerte (optionnel)

docker-compose.yml          # Services (Prometheus + Grafana)
```

---

## 💡 Tips & Tricks

### 💾 Sauvegarder un Dashboard
```
Grafana → Dashboard → Share → Export → Save JSON
```

### 📤 Exporter les Métriques
```bash
# Requête avec date range
curl -G 'http://localhost:9090/api/v1/query_range' \
  --data-urlencode 'query=predictions_total' \
  --data-urlencode 'start=2026-01-12T00:00:00Z' \
  --data-urlencode 'end=2026-01-13T00:00:00Z' \
  --data-urlencode 'step=60s'
```

### 🔔 Notifications
```
Grafana → Alerting → Notification channels
→ Slack / Email / Webhook / etc
```

---

## 🎯 Checklist Monitoring

- [ ] Docker-compose lancé (`docker-compose up -d`)
- [ ] Tous les services verts (`docker-compose ps`)
- [ ] API répond (`curl localhost:8000/health`)
- [ ] Prometheus scrape (`curl localhost:9090/api/v1/targets`)
- [ ] Grafana accessible (http://localhost:3000)
- [ ] Prometheus configuré en datasource
- [ ] Dashboard importé
- [ ] Prédictions générées (`python scripts/test_api.py`)
- [ ] Données visibles dans Grafana
- [ ] Alertes testées (optionnel)

---

## 📞 Support

**Problème persistent?**
1. Vérifier les logs: `docker-compose logs`
2. Vérifier les ports: `netstat -an | grep 8000`
3. Redémarrer clean: `docker-compose down && docker-compose up -d --build`
4. Réinstaller images: `docker-compose pull && docker-compose up -d`

---

*Dernière mise à jour: 13 Janvier 2026*
