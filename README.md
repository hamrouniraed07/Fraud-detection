# Credit Card Fraud Detection - MLOps Project

## 📋 Project Description

This project implements a complete credit card fraud detection system using modern MLOps techniques. The system includes:

- **Automated training pipeline** with ZenML
- **Real-time prediction API** with FastAPI
- **Experiment tracking** with MLflow
- **Hyperparameter optimization** with Optuna
- **Automated testing** and CI/CD
- **Docker deployment** for production

## 🏗️ Project Architecture

```
fraud-detection-mlops/
├── src/                          # Main source code
│   ├── data/                     # Data management
│   │   ├── load_data.py         # Data loading
│   │   └── preprocess.py        # Preprocessing
│   ├── models/                   # ML models
│   │   └── baseline.py          # RandomForest model
│   ├── training/                 # Training
│   │   ├── train_mlflow.py      # Training with MLflow
│   │   └── optimize.py          # Optuna optimization
│   └── serving/                  # Service
│       └── api.py               # FastAPI
├── pipelines/                    # ML pipelines
│   ├── training_pipeline.py     # Complete ZenML pipeline
│   └── training_pipeline_simple.py # Simplified pipeline
├── configs/                      # Configuration
│   ├── config.yaml              # Main configuration
│   └── model_params.yaml        # Model parameters
├── docker/                       # Docker configuration
│   ├── Dockerfile.train         # Training image
│   └── Dockerfile.serve         # Service image
├── tests/                        # Unit tests
│   ├── test_api.py              # API tests
│   └── test_model.py            # Model tests
├── scripts/                      # Utility scripts
│   ├── deploy.sh                # Deployment
│   ├── rollback.sh              # Rollback
│   ├── test_api.py              # API tests
│   └── setup_dvc.sh             # DVC setup
├── notebooks/                    # Jupyter notebooks
│   ├── 01_exploration.ipynb     # Data exploration
│   └── 02_baseline.ipynb        # Baseline model
└── data/                         # Data
    ├── raw/                      # Raw data
    └── processed/                # Processed data
```

## 🚀 Features

### 1. Training Pipeline
- **ZenML pipeline** with modular steps
- **MLflow experiment tracking**
- **Cross-validation** and metrics
- **Automatic model saving**

### 2. Prediction API
- **REST endpoints** with FastAPI
- **Real-time and batch prediction**
- **Health checks** and Prometheus metrics
- **Data validation** with Pydantic

### 3. Optimization
- **Optuna hyperparameter optimization**
- **Results visualization**
- **Model comparison**

### 4. Deployment
- **Docker containerization** for training and service
- **Automated deployment scripts**
- **Integration testing** with pytest
- **Rollback** in case of issues

## 📊 Data

The project uses the **Credit Card Fraud Detection** dataset from Kaggle:
- **284,807 European transactions**
- **31 features** (30 anonymized + Time + Amount)
- **492 frauds** (0.172% of total)
- **CSV format** with fraud labels (Class: 0=Normal, 1=Fraud)

## 🛠️ Installation and Setup

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- Git

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd fraud-detection-mlops
```

### 2. Install Dependencies
```bash
# Install basic dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install serving dependencies
pip install -r requirements-serve.txt
```

### 3. DVC Configuration
```bash
# Initial DVC setup
./scripts/setup_dvc.sh

# Download data (if configured)
dvc pull
```

### 4. MLflow Configuration
```bash
# Start MLflow server
mlflow server --host 0.0.0.0 --port 5000
```

## 🏃 Usage

### Model Training

#### Simplified Pipeline
```bash
cd pipelines/
python training_pipeline_simple.py
```

#### Complete Pipeline with ZenML
```bash
# ZenML setup (first time)
zenml experiment-tracker register mlflow_tracker --flavor=mlflow
zenml stack register mlflow_stack -o default -a default -e mlflow_tracker
zenml stack set mlflow_stack

# Launch pipeline
python training_pipeline.py
```

#### Hyperparameter Optimization
```bash
python -m src.training.optimize
```

### API Launch

#### Local Mode
```bash
uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 --reload
```

#### With Docker
```bash
# Build image
docker build -f docker/Dockerfile.serve -t fraud-detection-api .

# Launch container
docker run -p 8000:8000 fraud-detection-api
```

#### With Docker Compose
```bash
docker-compose up -d
```

### Testing

#### Unit Tests
```bash
# All tests
pytest tests/

# Specific tests
pytest tests/test_model.py
pytest tests/test_api.py
```

#### API Tests
```bash
# Automated tests
python scripts/test_api.py

# Manual tests
curl http://localhost:8000/health
```

## 📡 API Endpoints

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API homepage |
| `/health` | GET | Service health check |
| `/predict` | POST | Single transaction prediction |
| `/predict/batch` | POST | Batch predictions |
| `/model/info` | GET | Model information |
| `/metrics` | GET | Prometheus metrics |

### Request Example

#### Single Prediction
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "features": [0.1, -1.2, 0.3, 1.8, -0.5, 2.1, -0.8, 0.4, -1.5, 0.9, 0.2, -0.3, 1.1, -0.7, 0.6, -1.9, 0.8, -0.2, 1.3, -0.4, 0.7, -1.1, 0.5, -0.6, 1.4, -0.9, 0.3, 1.7, -0.1]
  }'
```

#### Response
```json
{
  "prediction": 0,
  "probability": 0.92,
  "confidence": "high"
}
```

## 🐳 Deployment

### Manual Deployment
```bash
# Deployment
./scripts/deploy.sh

# Rollback in case of issues
./scripts/rollback.sh
```

### Docker Deployment
```bash
# Build and deploy
docker-compose up -d --build

# Check status
docker-compose ps

# Logs
docker-compose logs -f
```

### Environment Variables
```bash
# Production configuration
export MODEL_PATH="/path/to/model"
export MLFLOW_TRACKING_URI="http://mlflow:5000"
export API_HOST="0.0.0.0"
export API_PORT="8000"
```

## 📈 Monitoring and Metrics

### Available Metrics
- **Predictions per minute**
- **Average response time**
- **Model accuracy**
- **Detected fraud rate**

### Access Metrics
```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# MLflow UI
# http://localhost:5000
```

## 🧪 Testing and Validation

### Test Structure
- **Unit tests** : Individual function validation
- **Integration tests** : Complete API validation
- **Performance tests** : Response time validation
- **Load tests** : Stress validation

### Run Tests
```bash
# Code coverage
pytest --cov=src tests/

# Performance tests
python scripts/test_api.py --load-test

# Continuous testing
pytest --cov=src --cov-report=html tests/
```

## 🔧 Configuration

### Main Configuration File
```yaml
# configs/config.yaml
project:
  name: fraud-detection
  version: "1.0.0"

data:
  raw_path: "data/raw/creditcard.csv"
  test_size: 0.2
  random_state: 42

model:
  type: "RandomForestClassifier"
  save_path: "models/"

mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "fraud_detection"

serving:
  host: "0.0.0.0"
  port: 8000
```

### Model Parameters
```yaml
# configs/model_params.yaml
baseline:
  n_estimators: 100
  max_depth: 10
  min_samples_split: 2
  min_samples_leaf: 1
  random_state: 42
  class_weight: "balanced"

optimized:
  n_estimators: 200
  max_depth: 15
  min_samples_split: 5
  min_samples_leaf: 2
  random_state: 42
  class_weight: "balanced"
```

## 🐛 Troubleshooting

### Common Issues

#### Import Error
```bash
# Install in development mode
pip install -e .
```

#### Port Already in Use
```bash
# Kill process using the port
lsof -ti:8000 | xargs kill -9
```

#### Memory Issues
```bash
# Reduce batch size
export BATCH_SIZE=32
```

#### DVC Issues
```bash
# Reset DVC
dvc cache clear
dvc pull
```

### Logs and Debugging
```bash
# API logs
tail -f logs/api.log

# MLflow logs
tail -f logs/mlflow.log

# Debug mode
export DEBUG=True
uvicorn src.serving.api:app --log-level debug
```

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/new-feature`)
3. **Commit** changes (`git commit -am 'Add new feature'`)
4. **Push** to branch (`git push origin feature/new-feature`)
5. **Create** a Pull Request

### Code Standards
- **PEP 8** for Python
- **Type hints** required
- **Detailed docstrings**
- **Unit tests** for each function

### Pre-commit Hooks
```bash
# Installation
pre-commit install

# Manual execution
pre-commit run --all-files
```

## 📚 Technical Documentation

### MLOps Architecture
- **Data ingestion** : Automated scripts with validation
- **Feature Engineering** : Modular and reproducible pipeline
- **Training** : ZenML pipelines with MLflow tracking
- **Deployment** : Containerized REST API with monitoring
- **Monitoring** : Real-time metrics and alerts

### Technologies Used
- **ZenML** : Training pipeline
- **FastAPI** : Prediction API
- **MLflow** : Experiment tracking
- **Optuna** : Hyperparameter optimization
- **Docker** : Containerization
- **pytest** : Automated testing
- **DVC** : Data versioning

## 📊 Model Performance

### Current Metrics
- **Precision** : 99.9%
- **Recall** : 85.2%
- **F1-Score** : 92.1%
- **AUC-ROC** : 97.8%

### Benchmarks
- **Prediction time** : <10ms
- **Training time** : <5 minutes
- **Throughput** : 1000+ predictions/second

## 🔒 Security

### Implemented Measures
- **Input validation** with Pydantic
- **Rate limiting** on API
- **Security logging** of access
- **Docker isolation** of services

### Best Practices
- Never expose MLflow keys
- Use HTTPS in production
- Validate all user inputs
- Secure logging without sensitive data

## 📝 License

This project is under MIT license. See the `LICENSE` file for details.

## 👥 Team

- **Main Developer** : Raed Mohamed Amine Hamrouni | Wiem Hemdi
- **Supervisor** : Mr. Salah GONTARA
- **Institution** : Polytech

---

## 🚀 Quick Start

```bash
# Quick installation
git clone <repo-url>
cd fraud-detection-mlops
pip install -r requirements.txt

# Training and startup
python pipelines/training_pipeline_simple.py
uvicorn src.serving.api:app --host 0.0.0.0 --port 8000

# Test
curl http://localhost:8000/health
```

**API will be accessible at** : http://localhost:8000
**Swagger UI** : http://localhost:8000/docs
**MLflow metrics** : http://localhost:5000

---

*This README was automatically generated for the fraud detection MLOps project - Version 1.0.0*
