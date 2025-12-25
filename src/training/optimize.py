"""Module pour l'optimisation avec Optuna."""
import optuna
from optuna.integration import MLflowCallback
import mlflow
import mlflow.sklearn
import yaml
import sys
from pathlib import Path
from sklearn.model_selection import cross_val_score

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.load_data import load_raw_data, split_features_target
from src.data.preprocess import preprocess_data
from src.models.baseline import FraudDetectionModel, print_metrics


class OptunaOptimizer:
    """Classe pour l'optimisation avec Optuna."""
    
    def __init__(self, X_train, y_train, X_test, y_test, n_trials=10):
        """
        Initialise l'optimiseur.
        
        Args:
            X_train, y_train: Données d'entraînement
            X_test, y_test: Données de test
            n_trials: Nombre d'essais Optuna
        """
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.n_trials = n_trials
        self.best_model = None
        self.best_params = None
        
    def objective(self, trial):
        """
        Fonction objectif pour Optuna.
        
        Args:
            trial: Objet trial Optuna
            
        Returns:
            F1-score moyen en validation croisée
        """
        # Définir l'espace de recherche
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300, step=50),
            'max_depth': trial.suggest_int('max_depth', 5, 30, step=5),
            'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5),
            'class_weight': trial.suggest_categorical('class_weight', ['balanced', None]),
            'random_state': 42,
            'n_jobs': -1
        }
        
        # Créer le modèle
        model = FraudDetectionModel(**params)
        
        # Validation croisée avec F1-score
        scores = cross_val_score(
            model.model, 
            self.X_train, 
            self.y_train,
            cv=3,  # 3-fold pour gagner du temps
            scoring='f1',
            n_jobs=-1
        )
        
        mean_f1 = scores.mean()
        
        # Logger dans MLflow (via callback)
        trial.set_user_attr("mean_f1", mean_f1)
        trial.set_user_attr("std_f1", scores.std())
        
        return mean_f1
    
    def optimize(self):
        """Lance l'optimisation Optuna."""
        print("\n" + "="*60)
        print("OPTIMISATION AVEC OPTUNA")
        print(f"Nombre de trials: {self.n_trials}")
        print("="*60 + "\n")
        
        # Configuration MLflow
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment("fraud_detection_optuna")
        
        # Callback MLflow pour Optuna
        mlflow_callback = MLflowCallback(
            tracking_uri="http://localhost:5000",
            metric_name="f1_score",
            create_experiment=False,
            mlflow_kwargs={"experiment_id": mlflow.get_experiment_by_name("fraud_detection_optuna").experiment_id}
        )
        
        # Créer l'étude Optuna
        study = optuna.create_study(
            direction='maximize',
            study_name='fraud_detection_optimization'
        )
        
        # Lancer l'optimisation
        study.optimize(
            self.objective,
            n_trials=self.n_trials,
            callbacks=[mlflow_callback],
            show_progress_bar=True
        )
        
        # Résultats
        print("\n" + "="*60)
        print("RÉSULTATS DE L'OPTIMISATION")
        print("="*60)
        print(f"Nombre de trials complétés: {len(study.trials)}")
        print(f"\nMeilleur F1-Score: {study.best_value:.4f}")
        print(f"\nMeilleurs paramètres:")
        for param, value in study.best_params.items():
            print(f"  {param}: {value}")
        
        # Sauvegarder les meilleurs paramètres
        self.best_params = study.best_params
        
        # Entraîner le modèle final avec les meilleurs paramètres
        print("\n" + "="*60)
        print("ENTRAÎNEMENT DU MODÈLE FINAL")
        print("="*60)
        
        final_params = study.best_params.copy()
        final_params['random_state'] = 42
        final_params['n_jobs'] = -1
        
        self.best_model = FraudDetectionModel(**final_params)
        self.best_model.train(self.X_train, self.y_train)
        
        # Évaluer sur le test set
        metrics = self.best_model.evaluate(self.X_test, self.y_test)
        print_metrics(metrics)
        
        # Logger dans MLflow
        with mlflow.start_run(run_name="optuna_best_model"):
            mlflow.log_params(final_params)
            for metric_name, value in metrics.items():
                mlflow.log_metric(metric_name, value)
            
            # Logger le modèle
            mlflow.sklearn.log_model(
                self.best_model.model,
                "model",
                registered_model_name="fraud_detection_optuna_best"
            )
            
            # Confusion matrix
            fig = self.best_model.plot_confusion_matrix(self.X_test, self.y_test)
            mlflow.log_figure(fig, "confusion_matrix.png")
        
        # Visualisation de l'optimisation
        self._plot_optimization_history(study)
        self._plot_param_importance(study)
        
        return study
    
    def _plot_optimization_history(self, study):
        """Visualise l'historique d'optimisation."""
        import matplotlib.pyplot as plt
        
        fig = optuna.visualization.matplotlib.plot_optimization_history(study)
        plt.tight_layout()
        fig.savefig("optuna_history.png")
        
        # Logger dans MLflow
        with mlflow.start_run(run_name="optuna_visualizations", nested=True):
            mlflow.log_artifact("optuna_history.png")
        
        print("📊 Historique d'optimisation sauvegardé: optuna_history.png")
    
    def _plot_param_importance(self, study):
        """Visualise l'importance des paramètres."""
        import matplotlib.pyplot as plt
        
        try:
            fig = optuna.visualization.matplotlib.plot_param_importances(study)
            plt.tight_layout()
            fig.savefig("optuna_param_importance.png")
            
            # Logger dans MLflow
            with mlflow.start_run(run_name="optuna_visualizations", nested=True):
                mlflow.log_artifact("optuna_param_importance.png")
            
            print("📊 Importance des paramètres sauvegardée: optuna_param_importance.png")
        except Exception as e:
            print(f"⚠️  Impossible de créer le graphique d'importance: {e}")


def run_optimization(n_trials=10):
    """Lance l'optimisation complète."""
    # Charger les données
    print("Chargement des données...")
    df = load_raw_data()
    X, y = split_features_target(df)
    X_train, X_test, y_train, y_test = preprocess_data(X, y)
    
    # Créer l'optimiseur
    optimizer = OptunaOptimizer(X_train, y_train, X_test, y_test, n_trials=n_trials)
    
    # Lancer l'optimisation
    study = optimizer.optimize()
    
    print("\n✅ Optimisation terminée!")
    print(f"🔗 Voir les résultats dans MLflow: http://localhost:5000")
    
    return optimizer, study


if __name__ == "__main__":
    optimizer, study = run_optimization(n_trials=10)