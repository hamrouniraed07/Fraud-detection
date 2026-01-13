# 📊 Grafana Dashboard - Guide Complet

## Vue d'Ensemble

Le dashboard **"🎯 Fraud Detection API - Monitoring"** est un système de monitoring complet en temps réel pour l'API de détection de fraude. Il fournit une visibilité totale sur les performances, la fiabilité et l'efficacité du système.

### 🎨 Layout du Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│  🎯 Fraud Detection API - Monitoring Dashboard               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │ Total Pred      │  │ 📈 Prediction Rate (5min)        │  │
│  │ by Type (Pie)   │  │                                  │  │
│  │                 │  │  Time Series Graph               │  │
│  │                 │  │                                  │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │ 🔢 Total        │  │ ⏱️ Latency Percentiles (P50..P99) │  │
│  │ Predictions     │  │                                  │  │
│  │ [STAT CARD]     │  │ Time Series Multi-line           │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │ ❌ Error Rate   │  │ 🚨 Fraud Rate (%)               │  │
│  │ (per 5min)      │  │ [STAT CARD - BIG NUMBER]        │  │
│  │ Bar Chart       │  │                                  │  │
│  │                 │  │                                  │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 Description Détaillée des Panneaux

### 1. 📊 Total Predictions by Type (Donut Chart)

**Position**: Top-Left  
**Type**: Pie/Donut Chart  
**Dimensions**: 12x8 (1/2 de la largeur)

#### Qu'est-ce que c'est?
Affiche la distribution des prédictions en deux catégories:
- **Légitime (0)** - Transactions normales
- **Fraude (1)** - Transactions frauduleuses

#### Métrique Prometheus
```promql
predictions_total
  Labels: model_version, prediction
```

#### Lecture des Données
```
Si fraude: 5 | Légitime: 95
→ 5% de fraudes détectées
```

#### 🎯 Seuils Recommandés
- **Vert** (0-1%): Normal (données équilibrées)
- **Orange** (1-5%): Attention (plusieurs fraudes)
- **Rouge** (>5%): Vigilance (taux élevé)

#### Actions Possibles
```
Si fraude > 10%:
→ Modèle détecte beaucoup de fraudes
→ Vérifier les faux positifs
→ Peut-être ré-entraîner le modèle
```

---

### 2. 🔢 Total Predictions (Stat Card)

**Position**: Top-Right  
**Type**: Stat Card (Nombre Grand)  
**Dimensions**: 6x8 (1/4 de la largeur)

#### Qu'est-ce que c'est?
Affiche le **nombre total cumulé** de prédictions depuis le démarrage du service.

#### Métrique Prometheus
```promql
sum(predictions_total)
```

#### Exemple de Lecture
```
Affichage: 15,847
= 15,847 prédictions au total
```

#### 🎯 Utilité
- Voir le volume total traité
- Vérifier la croissance dans le temps
- Identifier les arrêts de service (nombre gelé)

#### Actions Possibles
```
Si nombre = constant (ne croît pas):
→ API ne traite plus de requêtes
→ Vérifier: docker-compose ps
→ Relancer si nécessaire
```

---

### 3. 📈 Prediction Rate per 5min (Time Series)

**Position**: Top-Right  
**Type**: Time Series (Line Graph)  
**Dimensions**: 12x8 (1/2 de la largeur)

#### Qu'est-ce que c'est?
Affiche le **taux de prédictions** calculé sur les 5 dernières minutes.
- **Axe X**: Temps (dernière 1 heure)
- **Axe Y**: Prédictions par seconde
- **Légende**: Fraude vs Légitime

#### Métrique Prometheus
```promql
rate(predictions_total[5m])
  # Avec label: prediction
```

#### Exemple de Lecture
```
Pic à 15h30:
Légitime: 5 req/s
Fraude: 0.5 req/s
= Total: 5.5 req/s (330 req/min)
```

#### 🎯 Seuils Recommandés
```
Vert:   > 0 (service actif)
Orange: 0 pendant 5-10min (peut être normal)
Rouge:  = 0 pendant > 10min (problème!)
```

#### Cas d'Usage
1. **Identifier les heures de pointe**
   - Pics élevés → Charge haute
   - Creux → Charge basse

2. **Détecter les arrêts**
   - Chute à 0 → Problème service
   - Remontée → Service rétabli

3. **Planifier la capacité**
   - Moyenne haute → Augmenter ressources
   - Pics erratiques → Balancer de charge

---

### 4. ⏱️ Prediction Latency Percentiles (Time Series Multi-line)

**Position**: Right Middle  
**Type**: Time Series (Line Graph)  
**Dimensions**: 12x8 (1/2 de la largeur)

#### Qu'est-ce que c'est?
Affiche **trois lignes de latence** (temps de réponse):
- **P50** = Médiane (50% des requêtes plus rapides)
- **P95** = 95e percentile (95% plus rapides)
- **P99** = 99e percentile (99% plus rapides)

#### Métrique Prometheus
```promql
histogram_quantile(0.50, rate(prediction_latency_seconds_bucket[5m]))
histogram_quantile(0.95, rate(prediction_latency_seconds_bucket[5m]))
histogram_quantile(0.99, rate(prediction_latency_seconds_bucket[5m]))
```

#### Exemple de Lecture
```
À 15h30:
P50: 5ms  (requête typique)
P95: 25ms (quelques requêtes lentes)
P99: 80ms (très rares requêtes très lentes)
```

#### 🎯 Seuils Recommandés (en ms)
```
           P50    P95    P99    Verdict
Excellent  <5     <20    <50    ✅
Bon        5-10   20-50  50-100 ✅
Acceptable 10-20  50-100 100-200⚠️
Mauvais    >20    >100   >200   ❌
```

#### Cas d'Usage
1. **Monitoring Performance**
   - Ligne monte → Dégradation
   - Ligne descend → Amélioration

2. **Détecter les Goulots**
   - P99 >> P95 → Quelques requêtes très lentes
   - Toutes les trois montent → Problème général

3. **SLA (Service Level Agreement)**
   - P95 < 100ms (objectif courant)
   - P99 < 500ms (acceptable)

---

### 5. 🚨 Fraud Detection Rate (Stat Card)

**Position**: Right Middle  
**Type**: Stat Card (Gros Nombre avec %)  
**Dimensions**: 6x8 (1/4 de la largeur)

#### Qu'est-ce que c'est?
Affiche le **pourcentage** de prédictions classées comme fraude sur les 5 dernières minutes.

#### Métrique Prometheus
```promql
(sum(rate(predictions_total{prediction="fraud"}[5m])) / 
 sum(rate(predictions_total[5m]))) * 100
```

#### Exemple de Lecture
```
Affichage: 2.3%
= 2.3% des prédictions détectent une fraude
= Sur 100 transactions, ~2-3 sont frauduleuses
```

#### 🎯 Seuils Recommandés
```
Valeur     Verdict           Action
0-1%       Normal (données   OK
           équilibrées)
1-5%       Plusieurs         Monitor
           fraudes
5-10%      Taux modéré       Vérifier
>10%       Taux élevé        Alert!
0%         Pas de fraude     Suspect?
           (5+ min)
```

#### Cas d'Usage
1. **Validation du Modèle**
   - 0% → Modèle ne détecte rien
   - 5-10% → Normal en production
   - >20% → Trop de faux positifs?

2. **Alertes**
   - Si < 1% ET données ont des fraudes → Mauvais modèle
   - Si spike à 20%+ → Possible attaque?
   - Si 0% pendant longtemps → Modèle défaillant

---

### 6. ❌ Error Rate (Bar Chart)

**Position**: Bottom-Left  
**Type**: Bar Chart (Stacked)  
**Dimensions**: 12x8 (1/2 de la largeur)

#### Qu'est-ce que c'est?
Affiche le **taux d'erreurs** par type d'erreur sur les 5 dernières minutes.

Types d'erreurs possibles:
- `validation_error` - Input invalide
- `model_error` - Erreur du modèle
- `server_error` - Erreur serveur 5xx
- Autres...

#### Métrique Prometheus
```promql
rate(prediction_errors_total[5m])
  # Groupé par: error_type
```

#### Exemple de Lecture
```
À 15h30:
validation_error: 2 err/s
model_error: 0.1 err/s
server_error: 0 err/s
Total: 2.1 err/s
```

#### 🎯 Seuils Recommandés
```
Rate       Verdict        Action
0          Parfait        ✅
<1%        Excellent      ✅
1-5%       Acceptable     ⚠️ Watch
>5%        Problème       🔴 Alert
>10%       Critique       🔴🔴 Action!

Interprétation:
- 2.1 err/s ÷ 5.5 req/s ≈ 38% d'erreurs!
```

#### Cas d'Usage
1. **Diagnostiquer les Problèmes**
   - validation_error élevé → Vérifier l'input
   - model_error élevé → Recharger le modèle
   - server_error élevé → Problème ressources

2. **Tendances**
   - Spike soudain → Attaque ou bug?
   - Croissance progressive → Dégradation progressive

---

### 7. ⚠️ Total Errors per 5min (Stat Card)

**Position**: Bottom-Right  
**Type**: Stat Card (Nombre)  
**Dimensions**: 6x8 (1/4 de la largeur)

#### Qu'est-ce que c'est?
Affiche le **nombre total d'erreurs** sur les 5 dernières minutes.

#### Métrique Prometheus
```promql
sum(rate(prediction_errors_total[5m]))
```

#### Exemple de Lecture
```
Affichage: 0.8
= 0.8 erreurs par seconde (moyenne sur 5 min)
= ~48 erreurs par minute
= ~240 erreurs sur 5 minutes
```

#### 🎯 Seuils Recommandés
```
Erreurs/sec   Verdict
0             Parfait ✅
<0.1          Excellent ✅
0.1-0.5       Acceptable ⚠️
0.5-1         Problème 🔴
>1            Critique 🔴🔴
```

#### Actions Possibles
```
Si > 0.5 err/s:
→ docker-compose logs -f api
→ Chercher les exceptions
→ Redémarrer si nécessaire: docker-compose restart api
```

---

## 🎯 Scénarios de Monitoring

### Scénario 1: Service Fonctionne Bien ✅

```
Signatures:
✅ Prediction Rate > 0 (croissance)
✅ Fraud Rate 2-5% (normal)
✅ Latency P95 < 50ms (bon)
✅ Error Rate ≈ 0 (excellent)
✅ Total Errors = 0 (parfait)

Actions:
→ Aucune! Continue monitoring
```

### Scénario 2: Service En Surcharge ⚠️

```
Signatures:
⚠️ Prediction Rate pic très élevé (1000+ req/s)
⚠️ Latency P95 > 100ms (dégradé)
⚠️ Latency P99 > 500ms (lent)
⚠️ Errors start appearing (network timeouts)

Actions:
→ Augmenter ressources CPU/RAM
→ Ajouter des replicas API (load balancer)
→ Optimizer la requête du modèle
```

### Scénario 3: Modèle Défaillant 🔴

```
Signatures:
🔴 Fraud Rate = 0% (pendant long moment)
🔴 OU Fraud Rate = 100% (suspect)
🔴 Model error counter élevé
🔴 Error Rate > 5%

Actions:
→ Arrêter: docker-compose stop api
→ Recharger modèle: Reloading model from models/
→ Ou redémarrer: docker-compose restart api
→ Ou ré-entraîner: python pipelines/training_pipeline.py
```

### Scénario 4: Ressources Épuisées 🔴

```
Signatures:
🔴 Prediction Rate dropping (< normal)
🔴 Latency P99 > 1000ms (très lent)
🔴 Server errors augmentent
🔴 Prometheus scrape timeout

Actions:
→ Vérifier: docker-compose logs -f api
→ Vérifier RAM: docker stats
→ Redémarrer: docker-compose restart
→ Augmenter: docker-compose.yml limits
```

---

## 📝 Configuration des Alertes

### Ajouter une Alerte (Exemple: Error Rate)

1. **Aller sur le panneau** "Error Rate"
2. **Cliquer Edit** (crayon en haut à droite)
3. **Aller à "Alert"**
4. **Configurer**:
   ```
   IF: average of query A
   WHEN: > 5  (5% = 0.05)
   FOR: 5m    (pendant 5 minutes)
   ```
5. **Notification channel**: Slack/Email/Webhook
6. **Save**

### Exemple d'Alerte Complète

```
Nom: High Error Rate
Condition: rate(prediction_errors_total[5m]) > 0.05
Duration: 5 minutes
Severity: Critical
Notification: Slack (#alerts)
Message: "🚨 Error rate {{ value }}% in production!"
```

---

## 🔄 Refresh & Intervalle de Temps

### Paramètres Importants

```
Refresh Rate: Auto (5s) - mettre à jour toutes les 5 secondes
Time Range: Last 1 hour - montrer les dernières 24h (par défaut)
Time Zone: Browser - utiliser le fuseau horaire local
```

### Changer l'Intervalle

```
En haut à droite du dashboard:
→ Cliquer "Last 1 hour"
→ Choisir:
   - Last 5 minutes (très détaillé)
   - Last 1 hour (standard)
   - Last 24 hours (vue d'ensemble)
   - Last 7 days (tendances)
```

---

## 💾 Sauvegarder & Exporter

### Sauvegarder le Dashboard

```
Menu → Save (Ctrl+S)
→ Ajouter description
→ Tags optionnels
→ Save
```

### Exporter en JSON

```
Menu → Share → Export → Download JSON
→ Fichier: fraud_detection_dashboard.json
→ Importer dans autre Grafana via Import
```

### Exporter les Données

```
Sur un panneau:
→ Cliquer les 3 points (...) en haut à gauche
→ Inspect → Data
→ Download as CSV/JSON
```

---

## 📱 Responsive & Mobile

Le dashboard s'adapte à différentes tailles d'écran:

```
Desktop (1920x1080): 2 colonnes
Tablet (800x600):    1 colonne
Mobile (400x800):    Vertical stack
```

---

## 🔗 Intégrations Rapides

### Accéder à Prometheus depuis Grafana

```
Cliquer sur un panneau → Inspect → Query
→ Voir la requête PromQL
→ Cliquer sur Prometheus icon
→ Ouvre http://localhost:9090 avec la requête
```

### Lier vers MLflow

```
En production, ajouter un lien:
Dashboard → Edit → Add link
Type: Dashboards
MLflow: http://localhost:5000
```

---

## 🎓 Bonnes Pratiques

1. **Surveiller les 3 métriques clés**:
   - Latency (P95 < 100ms)
   - Error Rate (< 5%)
   - Fraud Rate (2-10% normal)

2. **Configurer les alertes**:
   - Ne pas sous-estimer P99
   - Error Rate spike = investigation
   - Fraud Rate extremes = suspicious

3. **Logs + Metrics**:
   - Metrics = vue d'ensemble
   - Logs = détails spécifiques
   - Toujours vérifier les logs après une alerte

4. **Tendances vs Pics**:
   - Un spike = peut être normal
   - Tendance croissante = problème!

---

## 📞 Support & Aide

**Dashboard vide?**
```
1. Vérifier Prometheus datasource
2. Générer des métriques: python scripts/test_api.py
3. Attendre 10s (premier scrape)
4. Refresh: F5 ou Auto Refresh
```

**Requête PromQL invalide?**
```
1. Ouvrir Prometheus: http://localhost:9090
2. Copier la requête du panneau
3. Tester dans Prometheus
4. Chercher l'erreur
```

---

*Guide créé le 13 Janvier 2026*  
*Prometheus v2.x | Grafana v9.x+*
