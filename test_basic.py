def test_basic():
    assert True  # Test minimal pour vérifier que le workflow fonctionne

def test_environment(monkeypatch):
    import os
    # Simuler les variables d'environnement pour le test
    monkeypatch.setenv('API_KEY', 'test-key')
    monkeypatch.setenv('DB_URL', 'test-url')
    monkeypatch.setenv('EMAIL', 'test@email.com')
    monkeypatch.setenv('PASS', 'test-pass')
    monkeypatch.setenv('FIREBASE_KEY', 'test-firebase-key')
    
    assert os.getenv('API_KEY') == 'test-key'
    assert os.getenv('DB_URL') == 'test-url'
    assert os.getenv('EMAIL') == 'test@email.com'
    assert os.getenv('PASS') == 'test-pass'
    assert os.getenv('FIREBASE_KEY') == 'test-firebase-key'
