"""Pipeline ZenML simplifié pour l'entraînement."""
from zenml import pipeline, step
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
    """Charge les données brutes."""
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
    """Prétraite et divise les données."""
    from src.data.preprocess import preprocess_data
    
    print("⚙️  Prétraitement des données...")
    X_train, X_test, y_train, y_test = preprocess_data(X, y, test_size=test_size)
    
    return X_train, X_test, y_train, y_test


@step
def train_model_step(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Dict
) -> RandomForestClassifier:
    """Entraîne le modèle."""
    print("🏋️  Entraînement du modèle...")
    
    # Créer et entraîner le modèle
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    
    print("✅ Modèle entraîné!")
    return model


@step
def evaluate_model_step(
    model: RandomForestClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, float]:
    """Évalue le modèle."""
    print("📊 Évaluation du modèle...")
    
    # Prédictions
    y_pred = model.predict(X_test)
    
    # Calculer les métriques
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred)
    }
    
    print(f"✅ F1-Score: {metrics['f1_score']:.4f}")
    
    return metrics


@step
def save_model_step(
    model: RandomForestClassifier,
    metrics: Dict[str, float],
    model_name: str = "fraud_model",
    threshold: float = 0.80
) -> str:
    """Sauvegarde le modèle si les métriques sont satisfaisantes."""
    from datetime import datetime
    
    f1 = metrics['f1_score']
    
    if f1 >= threshold:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f"models/{model_name}_{timestamp}.pkl"
        
        # Sauvegarder
        joblib.dump(model, model_path)
        print(f"💾 Modèle sauvegardé: {model_path}")
        
        return model_path
    else:
        print(f"⚠️  F1-Score ({f1:.4f}) < seuil ({threshold}). Modèle non sauvegardé.")
        return "not_saved"


@pipeline
def fraud_detection_training_pipeline(
    test_size: float = 0.2,
    params: Dict = None
):
    """Pipeline complet d'entraînement."""
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


def run_pipeline_simple():
    """Lance le pipeline simplifié."""
    import yaml
    
    # Charger les paramètres
    with open('configs/model_params.yaml', 'r') as f:
        all_params = yaml.safe_load(f)
    
    params = all_params['baseline']
    
    print("\n" + "="*60)
    print("ZENML PIPELINE SIMPLIFIÉ: BASELINE")
    print("="*60)
    print(f"Paramètres: {params}")
    print("="*60 + "\n")
    
    # Lancer le pipeline
    pipeline_instance = fraud_detection_training_pipeline(params=params)
    result = pipeline_instance()
    
    print("\n" + "="*60)
    print("✅ PIPELINE TERMINÉ!")
    print("="*60)
    
    return result


if __name__ == "__main__":
    run_pipeline_simple()