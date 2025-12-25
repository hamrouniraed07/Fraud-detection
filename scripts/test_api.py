"""Script pour tester l'API de détection de fraudes."""
import requests
import json
import time
from typing import List
import random


class FraudAPITester:
    """Classe pour tester l'API de détection de fraudes."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialise le testeur.
        
        Args:
            base_url: URL de base de l'API
        """
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health(self) -> bool:
        """Test du endpoint health."""
        print("🏥 Test du health check...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            data = response.json()
            
            print(f"   Status: {data.get('status')}")
            print(f"   Model version: {data.get('model_version')}")
            print(f"   Model loaded: {data.get('model_loaded')}")
            print("   ✅ Health check passed!\n")
            return True
            
        except Exception as e:
            print(f"   ❌ Health check failed: {e}\n")
            return False
    
    def test_root(self) -> bool:
        """Test du endpoint racine."""
        print("🏠 Test du endpoint racine...")
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            response.raise_for_status()
            data = response.json()
            
            print(f"   Message: {data.get('message')}")
            print(f"   Version: {data.get('version')}")
            print("   ✅ Root endpoint passed!\n")
            return True
            
        except Exception as e:
            print(f"   ❌ Root endpoint failed: {e}\n")
            return False
    
    def test_predict(self, features: List[float] = None) -> bool:
        """
        Test du endpoint de prédiction.
        
        Args:
            features: Liste de 29 features (optionnel)
        """
        print("🔮 Test de prédiction...")
        
        # Features par défaut
        if features is None:
            features = [0.0] * 29
            features[-1] = 100.0  # Amount
        
        payload = {"features": features}
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/predict",
                json=payload,
                timeout=10
            )
            latency = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            data = response.json()
            
            print(f"   Is fraud: {data.get('is_fraud')}")
            print(f"   Fraud probability: {data.get('fraud_probability'):.4f}")
            print(f"   Confidence: {data.get('confidence')}")
            print(f"   Model version: {data.get('model_version')}")
            print(f"   Latency: {latency:.2f}ms")
            print("   ✅ Prediction passed!\n")
            return True
            
        except Exception as e:
            print(f"   ❌ Prediction failed: {e}\n")
            return False
    
    def test_predict_batch(self, n_transactions: int = 5) -> bool:
        """
        Test du endpoint de prédiction en batch.
        
        Args:
            n_transactions: Nombre de transactions à tester
        """
        print(f"📦 Test de prédiction en batch ({n_transactions} transactions)...")
        
        transactions = []
        for i in range(n_transactions):
            features = [random.uniform(-3, 3) for _ in range(28)]
            features.append(random.uniform(0, 1000))  # Amount
            transactions.append({"features": features})
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/predict/batch",
                json=transactions,
                timeout=30
            )
            latency = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            data = response.json()
            
            predictions = data.get('predictions', [])
            fraud_count = sum(1 for p in predictions if p.get('is_fraud'))
            
            print(f"   Total predictions: {data.get('count')}")
            print(f"   Frauds detected: {fraud_count}")
            print(f"   Average latency: {latency/n_transactions:.2f}ms per transaction")
            print("   ✅ Batch prediction passed!\n")
            return True
            
        except Exception as e:
            print(f"   ❌ Batch prediction failed: {e}\n")
            return False
    
    def test_model_info(self) -> bool:
        """Test du endpoint model info."""
        print("ℹ️  Test des informations du modèle...")
        try:
            response = self.session.get(f"{self.base_url}/model/info", timeout=5)
            response.raise_for_status()
            data = response.json()
            
            print(f"   Model version: {data.get('model_version')}")
            print(f"   Model type: {data.get('model_type')}")
            print(f"   Number of features: {data.get('n_features')}")
            print("   ✅ Model info passed!\n")
            return True
            
        except Exception as e:
            print(f"   ❌ Model info failed: {e}\n")
            return False
    
    def test_metrics(self) -> bool:
        """Test du endpoint metrics."""
        print("📊 Test des métriques Prometheus...")
        try:
            response = self.session.get(f"{self.base_url}/metrics", timeout=5)
            response.raise_for_status()
            
            # Vérifier que c'est du texte
            content_type = response.headers.get('content-type', '')
            if 'text/plain' not in content_type:
                print(f"   ⚠️  Content-Type inattendu: {content_type}")
            
            # Vérifier qu'il y a des métriques
            metrics_text = response.text
            if 'predictions_total' in metrics_text:
                print("   ✅ Metrics endpoint passed!\n")
                return True
            else:
                print("   ⚠️  Métriques attendues non trouvées\n")
                return False
                
        except Exception as e:
            print(f"   ❌ Metrics failed: {e}\n")
            return False
    
    def run_load_test(self, n_requests: int = 100) -> dict:
        """
        Lance un test de charge simple.
        
        Args:
            n_requests: Nombre de requêtes à envoyer
            
        Returns:
            Statistiques du test
        """
        print(f"⚡ Test de charge ({n_requests} requêtes)...")
        
        latencies = []
        errors = 0
        
        start_time = time.time()
        
        for i in range(n_requests):
            try:
                features = [random.uniform(-3, 3) for _ in range(28)]
                features.append(random.uniform(0, 1000))
                
                req_start = time.time()
                response = self.session.post(
                    f"{self.base_url}/predict",
                    json={"features": features},
                    timeout=10
                )
                req_latency = (time.time() - req_start) * 1000
                
                if response.status_code == 200:
                    latencies.append(req_latency)
                else:
                    errors += 1
                    
            except Exception:
                errors += 1
        
        total_time = time.time() - start_time
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            throughput = n_requests / total_time
            
            stats = {
                'total_requests': n_requests,
                'successful': len(latencies),
                'errors': errors,
                'avg_latency_ms': avg_latency,
                'min_latency_ms': min_latency,
                'max_latency_ms': max_latency,
                'throughput_rps': throughput,
                'total_time_s': total_time
            }
            
            print(f"\n   📈 Résultats:")
            print(f"   Total requests: {stats['total_requests']}")
            print(f"   Successful: {stats['successful']}")
            print(f"   Errors: {stats['errors']}")
            print(f"   Avg latency: {stats['avg_latency_ms']:.2f}ms")
            print(f"   Min latency: {stats['min_latency_ms']:.2f}ms")
            print(f"   Max latency: {stats['max_latency_ms']:.2f}ms")
            print(f"   Throughput: {stats['throughput_rps']:.2f} req/s")
            print(f"   ✅ Load test complete!\n")
            
            return stats
        else:
            print("   ❌ Load test failed - no successful requests\n")
            return {}
    
    def run_all_tests(self) -> bool:
        """Lance tous les tests."""
        print("\n" + "="*60)
        print("🧪 TESTS DE L'API FRAUD DETECTION")
        print("="*60 + "\n")
        
        results = []
        
        results.append(("Health Check", self.test_health()))
        results.append(("Root Endpoint", self.test_root()))
        results.append(("Model Info", self.test_model_info()))
        results.append(("Prediction", self.test_predict()))
        results.append(("Batch Prediction", self.test_predict_batch()))
        results.append(("Metrics", self.test_metrics()))
        
        # Résumé
        print("="*60)
        print("📊 RÉSUMÉ DES TESTS")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<25} {status}")
        
        print("="*60)
        print(f"Résultat: {passed}/{total} tests passés ({passed/total*100:.0f}%)")
        print("="*60 + "\n")
        
        return passed == total


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test de l'API Fraud Detection")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="URL de l'API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--load-test",
        action="store_true",
        help="Lancer un test de charge"
    )
    parser.add_argument(
        "--n-requests",
        type=int,
        default=100,
        help="Nombre de requêtes pour le test de charge (default: 100)"
    )
    
    args = parser.parse_args()
    
    tester = FraudAPITester(base_url=args.url)
    
    # Tests standards
    all_passed = tester.run_all_tests()
    
    # Test de charge optionnel
    if args.load_test:
        tester.run_load_test(n_requests=args.n_requests)
    
    # Code de sortie
    exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()