#!/usr/bin/env python
"""
Script pour tester tous les endpoints de l'application
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, method="GET", data=None):
    """
    Teste un endpoint et affiche le résultat
    """
    print(f"\n{'='*50}")
    print(f"Test: {name}")
    print(f"URL: {url}")
    print(f"{'='*50}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=data, timeout=5)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: X-Process-Time = {response.headers.get('X-Process-Time', 'N/A')}s")
        
        if response.status_code < 400:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
        else:
            print(f"Error: {response.text[:200]}")
            
        return response.status_code < 400
        
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def main():
    print("Test des endpoints FastAPI")
    print(f"Base URL: {BASE_URL}")
    
    # Vérifier que le serveur est en cours d'exécution
    try:
        requests.get(BASE_URL, timeout=2)
    except:
        print("Le serveur n'est pas accessible. Lancez d'abord:")
        print("   uvicorn app.main:app --reload")
        return
    
    # Tester tous les endpoints
    tests = [
        ("Root", f"{BASE_URL}/"),
        ("Health", f"{BASE_URL}/health"),
        ("Config", f"{BASE_URL}/config"),
        ("Metrics", f"{BASE_URL}/metrics"),
        ("Weather API", f"{BASE_URL}/api/weather?lat=-1.2921&lon=36.8219&days=3"),
        ("Weather API avec IA", f"{BASE_URL}/api/weather?lat=-1.2921&lon=36.8219&ai=true"),
    ]
    
    results = []
    for name, url in tests:
        success = test_endpoint(name, url)
        results.append((name, success))
    
    # Résumé
    print(f"\n{'='*50}")
    print("RÉSUMÉ DES TESTS")
    print(f"{'='*50}")
    for name, success in results:
        status = "True" if success else "False"
        print(f"{status} {name}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\n{passed}/{total} tests réussis")

if __name__ == "__main__":
    main()