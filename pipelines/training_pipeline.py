"""Pipeline ZenML pour l'entraînement."""
from zenml import pipeline, step
from zenml.config import DockerSettings
from zenml.integrations.mlflow.experiment_trackers import MLFlowExperimentTracker
import pandas as pd
import numpy as np
from typing import Tuple, Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
import joblib
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


@step
def load_data_step() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Charge les données brutes.
    
    Returns:
        Tuple (X, y)
    """
    from src.data.load_data import load_raw_data, split_features_target
    
    print("📂 Chargement des données...")
    df = load_raw_data()
    X, y = split_features_target(df)
    
    return X, y


@step
def preprocess_data_step(
    X: pd.DataFrame, 
    y: pd.Series,
    test_size: float = 0.2
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Prétraite et divise les données.
    
    Args:
        X: Features
        y: Target
        test_size: Proportion du test set
        
    Returns:
        Tuple (X_train, X_test, y_train, y_test)
    """
    from src.data.preprocess import preprocess_data
    
    print("⚙️  Prétraitement des données...")
    X_train, X_test, y_train, y_test = preprocess_data(X, y, test_size=test_size)
    
    return X_train, X_test, y_train, y_test


@step(experiment_tracker="mlflow_tracker")
def train_model_step(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Dict
) -> RandomForestClassifier:
    """
    Entraîne le modèle.
    
    Args:
        X_train: Features d'entraînement
        y_train: Target d'entraînement
        params: Paramètres du modèle
        
    Returns:
        Modèle entraîné
    """
    import mlflow
    
    print("🏋️  Entraînement du modèle...")
    
    # Logger les paramètres
    mlflow.log_params(params)
    mlflow.log_param("train_samples", len(X_train))
    
    # Créer et entraîner le modèle
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    
    print("✅ Modèle entraîné!")
    return model


@step(experiment_tracker="mlflow_tracker")
def evaluate_model_step(
    model: RandomForestClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, float]:
    """
    Évalue le modèle.
    
    Args:
        model: Modèle entraîné
        X_test: Features de test
        y_test: Target de test
        
    Returns:
        Dictionnaire des métriques
    """
    import mlflow
    
    print("📊 Évaluation du modèle...")
    
    # Prédictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculer les métriques
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred)
    }
    
    # Logger les métriques
    for metric_name, value in metrics.items():
        mlflow.log_metric(metric_name, value)
    
    print(f"✅ F1-Score: {metrics['f1_score']:.4f}")
    
    return metrics


@step
def save_model_step(
    model: RandomForestClassifier,
    metrics: Dict[str, float],
    model_name: str = "fraud_model",
    threshold: float = 0.80
) -> str:
    """
    Sauvegarde le modèle si les métriques sont satisfaisantes.
    
    Args:
        model: Modèle entraîné
        metrics: Métriques d'évaluation
        model_name: Nom du modèle
        threshold: Seuil de F1-score pour sauvegarder
        
    Returns:
        Chemin du modèle sauvegardé
    """
    import mlflow
    from datetime import datetime
    
    f1 = metrics['f1_score']
    
    if f1 >= threshold:
        # Créer un nom avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f"models/{model_name}_{timestamp}.pkl"
        
        # Sauvegarder
        joblib.dump(model, model_path)
        print(f"💾 Modèle sauvegardé: {model_path}")
        
        # Logger dans MLflow
        mlflow.sklearn.log_model(model, "model")
        
        return model_path
    else:
        print(f"⚠️  F1-Score ({f1:.4f}) < seuil ({threshold}). Modèle non sauvegardé.")
        return "not_saved"


@pipeline
def fraud_detection_training_pipeline(
    test_size: float = 0.2,
    params: Dict = None
):
    """
    Pipeline complet d'entraînement.
    
    Args:
        test_size: Proportion du test set
        params: Paramètres du modèle
    """
    # Paramètres par défaut
    if params is None:
        params = {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42,
            'class_weight': 'balanced',
            'n_jobs': -1
        }
    
    # Étapes du pipeline
    X, y = load_data_step()
    X_train, X_test, y_train, y_test = preprocess_data_step(X, y, test_size)
    model = train_model_step(X_train, y_train, params)
    metrics = evaluate_model_step(model, X_test, y_test)
    model_path = save_model_step(model, metrics)
    
    return model_path


def run_pipeline_with_config(config_name: str = "baseline"):
    """
    Lance le pipeline avec une configuration spécifique.
    
    Args:
        config_name: Nom de la configuration dans model_params.yaml
    """
    import yaml
    
    # Charger les paramètres
    with open('configs/model_params.yaml', 'r') as f:
        all_params = yaml.safe_load(f)
    
    params = all_params[config_name]
    
    print("\n" + "="*60)
    print(f"ZENML PIPELINE: {config_name.upper()}")
    print("="*60)
    print(f"Paramètres: {params}")
    print("="*60 + "\n")
    
    # Lancer le pipeline
    pipeline_instance = fraud_detection_training_pipeline(params=params)
    pipeline_instance.run()


if __name__ == "__main__":
    """
    Pour exécuter ce pipeline, d'abord:
    1. Initialiser ZenML: zenml init
    2. Configurer MLflow: zenml integration install mlflow
    3. Enregistrer le tracker: zenml experiment-tracker register mlflow_tracker --flavor=mlflow
    4. Définir la stack: zenml stack register mlflow_stack -o default -a default -e mlflow_tracker
    5. Activer la stack: zenml stack set mlflow_stack
    """
    
    # Lancer plusieurs pipelines
    print("🚀 Lancement des pipelines ZenML...\n")
    
    # Pipeline baseline
    run_pipeline_with_config("baseline")
    
    # Pipeline variation 1
    # run_pipeline_with_config("variation_1")
    
    # Pipeline variation 2
    # run_pipeline_with_config("variation_2")