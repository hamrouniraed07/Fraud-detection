"""API FastAPI pour l'inférence de détection de fraudes."""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import joblib
import numpy as np
import os
from datetime import datetime
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Métriques Prometheus
prediction_counter = Counter(
    'predictions_total', 
    'Total number of predictions',
    ['model_version', 'prediction']
)
prediction_latency = Histogram(
    'prediction_latency_seconds',
    'Prediction latency in seconds'
)
error_counter = Counter(
    'prediction_errors_total',
    'Total number of prediction errors',
    ['error_type']
)

# Créer l'application FastAPI
app = FastAPI(
    title="Fraud Detection API",
    description="API de détection de fraudes bancaires avec ML",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales
MODEL = None
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
MODEL_PATH = os.getenv("MODEL_PATH", f"models/fraud_model_{MODEL_VERSION}.pkl")
FEATURE_NAMES = [f"V{i}" for i in range(1, 29)] + ["Amount"]


class Transaction(BaseModel):
    """Modèle de données pour une transaction."""
    features: List[float] = Field(
        ..., 
        description="Liste de 29 features (V1-V28 + Amount)",
        min_items=29,
        max_items=29
    )
    
    @validator('features')
    def validate_features(cls, v):
        if len(v) != 29:
            raise ValueError(f"Expected 29 features, got {len(v)}")
        if not all(isinstance(x, (int, float)) for x in v):
            raise ValueError("All features must be numeric")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "features": [0.0] * 29
            }
        }


class PredictionResponse(BaseModel):
    """Modèle de réponse pour une prédiction."""
    is_fraud: bool = Field(..., description="Transaction est-elle frauduleuse?")
    fraud_probability: float = Field(..., description="Probabilité de fraude (0-1)")
    model_version: str = Field(..., description="Version du modèle utilisé")
    timestamp: str = Field(..., description="Timestamp de la prédiction")
    confidence: str = Field(..., description="Niveau de confiance")


class HealthResponse(BaseModel):
    """Modèle de réponse pour le health check."""
    status: str
    model_version: str
    model_loaded: bool
    timestamp: str


def load_model():
    """Charge le modèle ML."""
    global MODEL
    try:
        logger.info(f"Chargement du modèle depuis: {MODEL_PATH}")
        MODEL = joblib.load(MODEL_PATH)
        logger.info(f"✅ Modèle {MODEL_VERSION} chargé avec succès!")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du modèle: {e}")
        return False


def get_confidence_level(probability: float) -> str:
    """Détermine le niveau de confiance."""
    if probability < 0.3:
        return "low"
    elif probability < 0.7:
        return "medium"
    else:
        return "high"


@app.on_event("startup")
async def startup_event():
    """Événement de démarrage - charge le modèle."""
    logger.info("🚀 Démarrage de l'API Fraud Detection")
    logger.info(f"📦 Version du modèle: {MODEL_VERSION}")
    success = load_model()
    if not success:
        logger.warning("⚠️  API démarrée sans modèle chargé")


@app.get("/", tags=["General"])
async def root():
    """Point d'entrée racine de l'API."""
    return {
        "message": "Fraud Detection API",
        "version": MODEL_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Vérifie l'état de santé de l'API."""
    return HealthResponse(
        status="healthy" if MODEL is not None else "unhealthy",
        model_version=MODEL_VERSION,
        model_loaded=MODEL is not None,
        timestamp=datetime.now().isoformat()
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
@prediction_latency.time()
async def predict(transaction: Transaction):
    """
    Prédit si une transaction est frauduleuse.
    
    Args:
        transaction: Données de la transaction
        
    Returns:
        Prédiction avec probabilité
    """
    if MODEL is None:
        error_counter.labels(error_type="model_not_loaded").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Please check server logs."
        )
    
    try:
        # Convertir les features en array numpy
        features_array = np.array(transaction.features).reshape(1, -1)
        
        # Prédiction
        prediction = MODEL.predict(features_array)[0]
        probabilities = MODEL.predict_proba(features_array)[0]
        fraud_probability = float(probabilities[1])
        
        # Incrémenter le compteur
        prediction_result = "fraud" if prediction == 1 else "legitimate"
        prediction_counter.labels(
            model_version=MODEL_VERSION,
            prediction=prediction_result
        ).inc()
        
        # Logger
        logger.info(
            f"Prediction: {prediction_result} | "
            f"Probability: {fraud_probability:.4f} | "
            f"Model: {MODEL_VERSION}"
        )
        
        return PredictionResponse(
            is_fraud=bool(prediction),
            fraud_probability=fraud_probability,
            model_version=MODEL_VERSION,
            timestamp=datetime.now().isoformat(),
            confidence=get_confidence_level(fraud_probability)
        )
        
    except Exception as e:
        error_counter.labels(error_type="prediction_error").inc()
        logger.error(f"Error during prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )


@app.post("/predict/batch", tags=["Prediction"])
async def predict_batch(transactions: List[Transaction]):
    """
    Prédit plusieurs transactions en batch.
    
    Args:
        transactions: Liste de transactions
        
    Returns:
        Liste de prédictions
    """
    if MODEL is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    try:
        results = []
        for transaction in transactions:
            features_array = np.array(transaction.features).reshape(1, -1)
            prediction = MODEL.predict(features_array)[0]
            probabilities = MODEL.predict_proba(features_array)[0]
            
            results.append({
                "is_fraud": bool(prediction),
                "fraud_probability": float(probabilities[1]),
                "model_version": MODEL_VERSION
            })
        
        return {"predictions": results, "count": len(results)}
        
    except Exception as e:
        error_counter.labels(error_type="batch_prediction_error").inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction error: {str(e)}"
        )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Expose les métriques Prometheus."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/model/info", tags=["Model"])
async def model_info():
    """Retourne les informations sur le modèle."""
    if MODEL is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    return {
        "model_version": MODEL_VERSION,
        "model_type": type(MODEL).__name__,
        "n_features": 29,
        "feature_names": FEATURE_NAMES,
        "model_params": MODEL.get_params() if hasattr(MODEL, 'get_params') else {}
    }


@app.post("/model/reload", tags=["Model"])
async def reload_model():
    """Recharge le modèle (utile pour les mises à jour)."""
    success = load_model()
    if success:
        return {
            "status": "success",
            "message": f"Model {MODEL_VERSION} reloaded successfully",
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload model"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )