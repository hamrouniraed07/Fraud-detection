"""Module pour l'entraînement avec MLflow tracking."""
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
import yaml
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.load_data import load_raw_data, split_features_target
from src.data.preprocess import preprocess_data
from src.models.baseline import FraudDetectionModel, print_metrics


def load_model_params(config_name: str = 'baseline') -> dict:
    """Charge les paramètres du modèle depuis le fichier YAML."""
    with open('configs/model_params.yaml', 'r') as f:
        all_params = yaml.safe_load(f)
    return all_params[config_name]


def train_with_mlflow(run_name: str, params: dict, X_train, X_test, y_train, y_test):
    """
    Entraîne un modèle avec tracking MLflow.
    
    Args:
        run_name: Nom du run MLflow
        params: Paramètres du modèle
        X_train, X_test, y_train, y_test: Données d'entraînement et de test
    """
    with mlflow.start_run(run_name=run_name) as run:
        print(f"\n{'='*60}")
        print(f"MLflow Run: {run_name}")
        print(f"Run ID: {run.info.run_id}")
        print(f"{'='*60}\n")
        
        # Log des paramètres
        mlflow.log_params(params)
        
        # Log des infos sur les données
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))
        mlflow.log_param("n_features", X_train.shape[1])
        mlflow.log_param("fraud_rate_train", y_train.sum() / len(y_train))
        
        # Créer et entraîner le modèle
        model = FraudDetectionModel(**params)
        model.train(X_train, y_train)
        
        # Évaluer le modèle
        metrics = model.evaluate(X_test, y_test)
        print_metrics(metrics)
        
        # Log des métriques
        for metric_name, value in metrics.items():
            mlflow.log_metric(metric_name, value)
        
        # Créer et logger la matrice de confusion
        fig = model.plot_confusion_matrix(X_test, y_test)
        mlflow.log_figure(fig, "confusion_matrix.png")
        
        # Feature importance
        importance = model.get_feature_importance(X_train.columns.tolist())
        importance.to_csv("feature_importance.csv", index=False)
        mlflow.log_artifact("feature_importance.csv")
        
        # Inférer la signature du modèle
        signature = infer_signature(X_train, model.predict(X_train))
        
        # Logger le modèle
        mlflow.sklearn.log_model(
            model.model,
            "model",
            signature=signature,
            registered_model_name=f"fraud_detection_{run_name}"
        )
        
        print(f"\n✅ Run terminé avec succès!")
        print(f"📊 F1-Score: {metrics['f1_score']:.4f}")
        print(f"🔗 MLflow UI: http://localhost:5000")
        
        return model, metrics


def run_experiments():
    """Lance plusieurs expériences avec différentes configurations."""
    # Configuration MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("fraud_detection")
    
    # Charger les données
    print("Chargement des données...")
    df = load_raw_data()
    X, y = split_features_target(df)
    X_train, X_test, y_train, y_test = preprocess_data(X, y)
    
    # Expérience 1: Baseline
    print("\n" + "="*60)
    print("EXPÉRIENCE 1: BASELINE")
    print("="*60)
    params_baseline = load_model_params('baseline')
    model_baseline, metrics_baseline = train_with_mlflow(
        "baseline",
        params_baseline,
        X_train, X_test, y_train, y_test
    )
    
    # Expérience 2: Variation 1
    print("\n" + "="*60)
    print("EXPÉRIENCE 2: VARIATION 1 (Moins d'arbres)")
    print("="*60)
    params_var1 = load_model_params('variation_1')
    model_var1, metrics_var1 = train_with_mlflow(
        "variation_1",
        params_var1,
        X_train, X_test, y_train, y_test
    )
    
    # Expérience 3: Variation 2
    print("\n" + "="*60)
    print("EXPÉRIENCE 3: VARIATION 2 (Plus d'arbres)")
    print("="*60)
    params_var2 = load_model_params('variation_2')
    model_var2, metrics_var2 = train_with_mlflow(
        "variation_2",
        params_var2,
        X_train, X_test, y_train, y_test
    )
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES EXPÉRIENCES")
    print("="*60)
    print(f"Baseline F1:    {metrics_baseline['f1_score']:.4f}")
    print(f"Variation 1 F1: {metrics_var1['f1_score']:.4f}")
    print(f"Variation 2 F1: {metrics_var2['f1_score']:.4f}")
    
    best_f1 = max(metrics_baseline['f1_score'], 
                  metrics_var1['f1_score'], 
                  metrics_var2['f1_score'])
    
    if best_f1 == metrics_baseline['f1_score']:
        print("\n🏆 Meilleur modèle: BASELINE")
    elif best_f1 == metrics_var1['f1_score']:
        print("\n🏆 Meilleur modèle: VARIATION 1")
    else:
        print("\n🏆 Meilleur modèle: VARIATION 2")


if __name__ == "__main__":
    run_experiments()