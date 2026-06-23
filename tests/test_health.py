from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get('/health')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert 'configured_models' in payload
    assert 'judge_model' in payload
    assert payload['persistence'] in {'none', 'cosmos'}
