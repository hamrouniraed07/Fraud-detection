"""Module pour le prétraitement des données."""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from typing import Tuple
import joblib


def preprocess_data(X: pd.DataFrame, y: pd.Series, 
                   test_size: float = 0.2,
                   random_state: int = 42) -> Tuple:
    """
    Prétraite les données et les divise en train/test.
    
    Args:
        X: Features
        y: Target
        test_size: Proportion du test set
        random_state: Seed pour la reproductibilité
        
    Returns:
        Tuple (X_train, X_test, y_train, y_test)
    """
    # Split train/test avec stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=test_size, 
        random_state=random_state,
        stratify=y
    )
    
    print(f"Train set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    print(f"Train frauds: {y_train.sum()} ({y_train.sum()/len(y_train)*100:.2f}%)")
    print(f"Test frauds: {y_test.sum()} ({y_test.sum()/len(y_test)*100:.2f}%)")
    
    return X_train, X_test, y_train, y_test


def scale_features(X_train: pd.DataFrame, 
                  X_test: pd.DataFrame,
                  save_scaler: bool = False,
                  scaler_path: str = "models/scaler.pkl") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Standardise les features (optionnel pour ce dataset).
    
    Args:
        X_train: Features d'entraînement
        X_test: Features de test
        save_scaler: Sauvegarder le scaler
        scaler_path: Chemin de sauvegarde
        
    Returns:
        Tuple (X_train_scaled, X_test_scaled)
    """
    scaler = StandardScaler()
    
    # Fit sur train uniquement
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Conserver les noms de colonnes
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns)
    
    if save_scaler:
        joblib.dump(scaler, scaler_path)
        print(f"Scaler sauvegardé: {scaler_path}")
    
    return X_train_scaled, X_test_scaled


def handle_imbalance(X_train: pd.DataFrame, 
                    y_train: pd.Series,
                    method: str = 'none') -> Tuple[pd.DataFrame, pd.Series]:
    """
    Gère le déséquilibre des classes (optionnel).
    
    Args:
        X_train: Features d'entraînement
        y_train: Target d'entraînement
        method: 'none', 'oversample', 'undersample', 'smote'
        
    Returns:
        Tuple (X_resampled, y_resampled)
    """
    if method == 'none':
        return X_train, y_train
    
    elif method == 'oversample':
        from imblearn.over_sampling import RandomOverSampler
        ros = RandomOverSampler(random_state=42)
        X_resampled, y_resampled = ros.fit_resample(X_train, y_train)
        
    elif method == 'undersample':
        from imblearn.under_sampling import RandomUnderSampler
        rus = RandomUnderSampler(random_state=42)
        X_resampled, y_resampled = rus.fit_resample(X_train, y_train)
        
    elif method == 'smote':
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
    
    else:
        raise ValueError(f"Méthode inconnue: {method}")
    
    print(f"After resampling: {len(y_resampled)} samples")
    print(f"Class distribution:\n{pd.Series(y_resampled).value_counts()}")
    
    return X_resampled, y_resampled


if __name__ == "__main__":
    from load_data import load_raw_data, split_features_target
    
    # Test du module
    df = load_raw_data()
    X, y = split_features_target(df)
    X_train, X_test, y_train, y_test = preprocess_data(X, y)
    
    print("\nTest de scaling...")
    X_train_scaled, X_test_scaled = scale_features(X_train, X_test)
    print(f"Train scaled shape: {X_train_scaled.shape}")
    print(f"Test scaled shape: {X_test_scaled.shape}")