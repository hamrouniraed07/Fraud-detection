"""Tests pour l'API de détection de fraudes."""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent))

from src.serving.api import app


@pytest.fixture
def client():
    """Fixture pour le client de test."""
    return TestClient(app)


@pytest.fixture
def mock_model(tmp_path):
    """Crée un modèle factice pour les tests."""
    # Créer un modèle simple
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    
    # Entraîner sur des données factices
    X_dummy = np.random.rand(100, 29)
    y_dummy = np.random.randint(0, 2, 100)
    model.fit(X_dummy, y_dummy)
    
    # Sauvegarder le modèle
    model_path = tmp_path / "fraud_model_v1.pkl"
    joblib.dump(model, model_path)
    
    return str(model_path)


@pytest.fixture
def valid_transaction():
    """Fixture pour une transaction valide."""
    return {
        "features": [0.0] * 29
    }


def test_root_endpoint(client):
    """Test du endpoint racine."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


def test_health_endpoint(client):
    """Test du endpoint health."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "model_version" in data
    assert "timestamp" in data


def test_predict_valid_transaction(client, valid_transaction, monkeypatch, mock_model):
    """Test de prédiction avec une transaction valide."""
    # Mock le chargement du modèle
    import src.serving.api as api_module
    monkeypatch.setenv("MODEL_PATH", mock_model)
    
    # Charger le modèle
    api_module.load_model()
    
    response = client.post("/predict", json=valid_transaction)
    assert response.status_code == 200
    
    data = response.json()
    assert "is_fraud" in data
    assert "fraud_probability" in data
    assert "model_version" in data
    assert "timestamp" in data
    assert "confidence" in data
    
    # Vérifier les types
    assert isinstance(data["is_fraud"], bool)
    assert isinstance(data["fraud_probability"], float)
    assert 0 <= data["fraud_probability"] <= 1


def test_predict_invalid_features_count(client):
    """Test avec un mauvais nombre de features."""
    invalid_transaction = {
        "features": [0.0] * 20  # Seulement 20 au lieu de 29
    }
    
    response = client.post("/predict", json=invalid_transaction)
    assert response.status_code == 422  # Validation error


def test_predict_invalid_feature_type(client):
    """Test avec des features non numériques."""
    invalid_transaction = {
        "features": ["invalid"] * 29
    }
    
    response = client.post("/predict", json=invalid_transaction)
    assert response.status_code == 422


def test_predict_batch(client, valid_transaction, monkeypatch, mock_model):
    """Test de prédiction en batch."""
    monkeypatch.setenv("MODEL_PATH", mock_model)
    
    import src.serving.api as api_module
    api_module.load_model()
    
    transactions = [valid_transaction] * 5
    
    response = client.post("/predict/batch", json=transactions)
    assert response.status_code == 200
    
    data = response.json()
    assert "predictions" in data
    assert "count" in data
    assert data["count"] == 5
    assert len(data["predictions"]) == 5


def test_model_info(client, monkeypatch, mock_model):
    """Test du endpoint model info."""
    monkeypatch.setenv("MODEL_PATH", mock_model)
    
    import src.serving.api as api_module
    api_module.load_model()
    
    response = client.get("/model/info")
    assert response.status_code == 200
    
    data = response.json()
    assert "model_version" in data
    assert "model_type" in data
    assert "n_features" in data
    assert data["n_features"] == 29


def test_metrics_endpoint(client):
    """Test du endpoint metrics (Prometheus)."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_predict_without_model(client, valid_transaction):
    """Test de prédiction sans modèle chargé."""
    import src.serving.api as api_module
    api_module.MODEL = None
    
    response = client.post("/predict", json=valid_transaction)
    assert response.status_code == 503  # Service unavailable


def test_confidence_levels(client, monkeypatch, mock_model):
    """Test des niveaux de confiance."""
    monkeypatch.setenv("MODEL_PATH", mock_model)
    
    import src.serving.api as api_module
    api_module.load_model()
    
    response = client.post("/predict", json={"features": [0.0] * 29})
    data = response.json()
    
    assert data["confidence"] in ["low", "medium", "high"]


@pytest.mark.parametrize("feature_value", [0.0, 1.0, -1.0, 100.0])
def test_various_feature_values(client, monkeypatch, mock_model, feature_value):
    """Test avec différentes valeurs de features."""
    monkeypatch.setenv("MODEL_PATH", mock_model)
    
    import src.serving.api as api_module
    api_module.load_model()
    
    transaction = {"features": [feature_value] * 29}
    response = client.post("/predict", json=transaction)
    
    assert response.status_code == 200
    data = response.json()
    assert "is_fraud" in data