"""Module pour le modèle baseline."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    f1_score, precision_score, recall_score, accuracy_score,
    confusion_matrix, classification_report, roc_auc_score
)
import joblib
from typing import Dict, Tuple
import matplotlib.pyplot as plt
import seaborn as sns


class FraudDetectionModel:
    """Modèle de détection de fraudes."""
    
    def __init__(self, **params):
        """
        Initialise le modèle.
        
        Args:
            **params: Paramètres du RandomForestClassifier
        """
        self.model = RandomForestClassifier(**params)
        self.is_fitted = False
        
    def train(self, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Entraîne le modèle.
        
        Args:
            X_train: Features d'entraînement
            y_train: Target d'entraînement
        """
        print("Entraînement du modèle...")
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        print("Entraînement terminé!")
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Prédit les classes."""
        if not self.is_fitted:
            raise ValueError("Le modèle doit être entraîné avant de prédire")
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Prédit les probabilités."""
        if not self.is_fitted:
            raise ValueError("Le modèle doit être entraîné avant de prédire")
        return self.model.predict_proba(X)
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """
        Évalue le modèle sur le test set.
        
        Args:
            X_test: Features de test
            y_test: Target de test
            
        Returns:
            Dictionnaire des métriques
        """
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_proba)
        }
        
        return metrics
    
    def get_feature_importance(self, feature_names: list) -> pd.DataFrame:
        """Retourne l'importance des features."""
        if not self.is_fitted:
            raise ValueError("Le modèle doit être entraîné")
            
        importance = pd.DataFrame({
            'feature': feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance
    
    def plot_confusion_matrix(self, X_test: pd.DataFrame, 
                             y_test: pd.Series) -> plt.Figure:
        """Crée une matrice de confusion."""
        y_pred = self.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        ax.set_title('Confusion Matrix')
        
        return fig
    
    def save(self, path: str):
        """Sauvegarde le modèle."""
        joblib.dump(self.model, path)
        print(f"Modèle sauvegardé: {path}")
    
    @classmethod
    def load(cls, path: str):
        """Charge un modèle sauvegardé."""
        model_instance = cls()
        model_instance.model = joblib.load(path)
        model_instance.is_fitted = True
        print(f"Modèle chargé: {path}")
        return model_instance


def print_metrics(metrics: Dict[str, float]):
    """Affiche les métriques de façon formatée."""
    print("\n" + "="*50)
    print("MÉTRIQUES D'ÉVALUATION")
    print("="*50)
    for metric_name, value in metrics.items():
        print(f"{metric_name.upper():.<30} {value:.4f}")
    print("="*50 + "\n")


if __name__ == "__main__":
    # Test du module
    from src.data.load_data import load_raw_data, split_features_target
    from src.data.preprocess import preprocess_data
    
    # Charger les données
    df = load_raw_data()
    X, y = split_features_target(df)
    X_train, X_test, y_train, y_test = preprocess_data(X, y)
    
    # Créer et entraîner le modèle baseline
    params = {
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42,
        'class_weight': 'balanced',
        'n_jobs': -1
    }
    
    model = FraudDetectionModel(**params)
    model.train(X_train, y_train)
    
    # Évaluer
    metrics = model.evaluate(X_test, y_test)
    print_metrics(metrics)
    
    # Feature importance
    importance = model.get_feature_importance(X.columns.tolist())
    print("\nTop 10 features les plus importantes:")
    print(importance.head(10))