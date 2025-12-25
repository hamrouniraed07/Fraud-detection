"""Module pour charger les données."""
import pandas as pd
import yaml
from pathlib import Path
from typing import Tuple


def load_config(config_path: str = "configs/config.yaml") -> dict:
    """Charge la configuration depuis le fichier YAML."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_raw_data(data_path: str = None) -> pd.DataFrame:
    """
    Charge les données brutes.
    
    Args:
        data_path: Chemin vers le fichier CSV
        
    Returns:
        DataFrame contenant les données
    """
    if data_path is None:
        config = load_config()
        data_path = config['data']['raw_path']
    
    print(f"Chargement des données depuis: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Données chargées: {df.shape[0]} lignes, {df.shape[1]} colonnes")
    
    return df


def split_features_target(df: pd.DataFrame, 
                          target_col: str = 'Class') -> Tuple[pd.DataFrame, pd.Series]:
    """
    Sépare les features de la target.
    
    Args:
        df: DataFrame complet
        target_col: Nom de la colonne cible
        
    Returns:
        Tuple (X, y)
    """
    X = df.drop(target_col, axis=1)
    y = df[target_col]
    
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    print(f"Target distribution:\n{y.value_counts()}")
    
    return X, y


def get_data_info(df: pd.DataFrame) -> dict:
    """
    Retourne des informations sur le dataset.
    
    Args:
        df: DataFrame à analyser
        
    Returns:
        Dictionnaire avec les statistiques
    """
    info = {
        'n_samples': len(df),
        'n_features': len(df.columns),
        'n_fraud': df['Class'].sum() if 'Class' in df.columns else None,
        'fraud_percentage': (df['Class'].sum() / len(df) * 100) if 'Class' in df.columns else None,
        'missing_values': df.isnull().sum().sum(),
        'duplicates': df.duplicated().sum()
    }
    
    return info


if __name__ == "__main__":
    # Test du module
    df = load_raw_data()
    info = get_data_info(df)
    print("\nInformations sur le dataset:")
    for key, value in info.items():
        print(f"{key}: {value}")
    
    X, y = split_features_target(df)
    print(f"\nNombre de fraudes: {y.sum()}")
    print(f"Pourcentage de fraudes: {y.sum() / len(y) * 100:.2f}%")