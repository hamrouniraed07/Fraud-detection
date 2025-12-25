"""Tests pour le modèle de détection de fraudes."""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path
import tempfile

sys.path.append(str(Path(__file__).parent.parent))

from src.models.baseline import FraudDetectionModel


@pytest.fixture
def dummy_data():
    """Crée des données factices pour les tests."""
    np.random.seed(42)
    
    n_samples = 1000
    n_features = 29
    
    X_train = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"V{i}" for i in range(1, n_features)] + ["Amount"]
    )
    y_train = pd.Series(np.random.randint(0, 2, n_samples))
    
    X_test = pd.DataFrame(
        np.random.randn(200, n_features),
        columns=[f"V{i}" for i in range(1, n_features)] + ["Amount"]
    )
    y_test = pd.Series(np.random.randint(0, 2, 200))
    
    return X_train, X_test, y_train, y_test


@pytest.fixture
def trained_model(dummy_data):
    """Crée un modèle entraîné."""
    X_train, X_test, y_train, y_test = dummy_data
    
    model = FraudDetectionModel(
        n_estimators=10,
        max_depth=5,
        random_state=42,
        n_jobs=1
    )
    model.train(X_train, y_train)
    
    return model


def test_model_initialization():
    """Test de l'initialisation du modèle."""
    model = FraudDetectionModel(n_estimators=100, max_depth=10)
    
    assert model.model is not None
    assert model.is_fitted is False
    assert model.model.n_estimators == 100
    assert model.model.max_depth == 10


def test_model_training(dummy_data):
    """Test de l'entraînement du modèle."""
    X_train, X_test, y_train, y_test = dummy_data
    
    model = FraudDetectionModel(n_estimators=10, random_state=42)
    assert model.is_fitted is False
    
    model.train(X_train, y_train)
    assert model.is_fitted is True


def test_predict_before_training(dummy_data):
    """Test de prédiction avant entraînement."""
    X_train, X_test, y_train, y_test = dummy_data
    
    model = FraudDetectionModel()
    
    with pytest.raises(ValueError, match="doit être entraîné"):
        model.predict(X_test)


def test_predict(trained_model, dummy_data):
    """Test de prédiction."""
    X_train, X_test, y_train, y_test = dummy_data
    
    predictions = trained_model.predict(X_test)
    
    assert len(predictions) == len(X_test)
    assert all(p in [0, 1] for p in predictions)


def test_predict_proba(trained_model, dummy_data):
    """Test de prédiction des probabilités."""
    X_train, X_test, y_train, y_test = dummy_data
    
    probabilities = trained_model.predict_proba(X_test)
    
    assert probabilities.shape == (len(X_test), 2)
    assert all(0 <= p <= 1 for row in probabilities for p in row)
    assert all(abs(row.sum() - 1.0) < 1e-5 for row in probabilities)


def test_evaluate(trained_model, dummy_data):
    """Test de l'évaluation du modèle."""
    X_train, X_test, y_train, y_test = dummy_data
    
    metrics = trained_model.evaluate(X_test, y_test)
    
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics
    
    # Vérifier que les métriques sont dans [0, 1]
    for metric_name, value in metrics.items():
        assert 0 <= value <= 1, f"{metric_name} = {value} n'est pas dans [0, 1]"


def test_feature_importance(trained_model, dummy_data):
    """Test de l'importance des features."""
    X_train, X_test, y_train, y_test = dummy_data
    
    importance = trained_model.get_feature_importance(X_train.columns.tolist())
    
    assert len(importance) == len(X_train.columns)
    assert "feature" in importance.columns
    assert "importance" in importance.columns
    assert all(importance["importance"] >= 0)
    assert abs(importance["importance"].sum() - 1.0) < 1e-5


def test_save_and_load_model(trained_model, dummy_data):
    """Test de sauvegarde et chargement du modèle."""
    X_train, X_test, y_train, y_test = dummy_data
    
    # Sauvegarder
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp:
        model_path = tmp.name
        trained_model.save(model_path)
    
    # Charger
    loaded_model = FraudDetectionModel.load(model_path)
    
    # Vérifier que les prédictions sont identiques
    original_pred = trained_model.predict(X_test)
    loaded_pred = loaded_model.predict(X_test)
    
    assert np.array_equal(original_pred, loaded_pred)
    
    # Nettoyer
    Path(model_path).unlink()


def test_model_with_class_weight(dummy_data):
    """Test du modèle avec class_weight='balanced'."""
    X_train, X_test, y_train, y_test = dummy_data
    
    model = FraudDetectionModel(
        n_estimators=10,
        class_weight='balanced',
        random_state=42
    )
    model.train(X_train, y_train)
    
    metrics = model.evaluate(X_test, y_test)
    assert all(0 <= v <= 1 for v in metrics.values())


def test_confusion_matrix_plot(trained_model, dummy_data):
    """Test de la création de la matrice de confusion."""
    X_train, X_test, y_train, y_test = dummy_data
    
    fig = trained_model.plot_confusion_matrix(X_test, y_test)
    
    assert fig is not None
    assert len(fig.axes) == 1


@pytest.mark.parametrize("n_estimators,max_depth", [
    (10, 5),
    (50, 10),
    (100, 15),
])
def test_different_hyperparameters(dummy_data, n_estimators, max_depth):
    """Test avec différents hyperparamètres."""
    X_train, X_test, y_train, y_test = dummy_data
    
    model = FraudDetectionModel(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42
    )
    model.train(X_train, y_train)
    
    metrics = model.evaluate(X_test, y_test)
    assert all(0 <= v <= 1 for v in metrics.values())