import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.models import ArenaRun, RunStatus
from app.schemas import ArenaRunResponse, ModelAnswer


def test_run_arena_success(monkeypatch) -> None:
    async def fake_run(_req):
        winner = ModelAnswer(
            model_alias='m1',
            model_name='model-1',
            answer='answer',
            latency_ms=10,
            score=0.9,
        )
        return ArenaRunResponse(
            run_id='run-1',
            winner=winner,
            answers=[winner],
            judge='heuristic',
        )

    monkeypatch.setattr('app.main.orchestrator.run', fake_run)

    client = TestClient(app)
    response = client.post('/arena/run', json={'prompt': 'hello'})

    assert response.status_code == 200
    assert response.json()['run_id'] == 'run-1'


def test_run_arena_error_mapping(monkeypatch) -> None:
    async def raise_value_error(_req):
        raise ValueError('bad input')

    async def raise_timeout(_req):
        raise httpx.TimeoutException('timeout')

    async def raise_http_status(_req):
        request = httpx.Request('POST', 'https://example.test')
        response = httpx.Response(429, request=request)
        raise httpx.HTTPStatusError('rate limited', request=request, response=response)

    async def raise_generic(_req):
        raise RuntimeError('boom')

    client = TestClient(app)

    monkeypatch.setattr('app.main.orchestrator.run', raise_value_error)
    assert client.post('/arena/run', json={'prompt': 'x'}).status_code == 400

    monkeypatch.setattr('app.main.orchestrator.run', raise_timeout)
    assert client.post('/arena/run', json={'prompt': 'x'}).status_code == 504

    monkeypatch.setattr('app.main.orchestrator.run', raise_http_status)
    assert client.post('/arena/run', json={'prompt': 'x'}).status_code == 502

    monkeypatch.setattr('app.main.orchestrator.run', raise_generic)
    assert client.post('/arena/run', json={'prompt': 'x'}).status_code == 500


def test_get_run_not_found(monkeypatch) -> None:
    async def fake_get_run(_run_id: str):
        return None

    monkeypatch.setattr('app.main.cosmos_client.get_run', fake_get_run)

    client = TestClient(app)
    response = client.get('/arena/runs/missing')

    assert response.status_code == 404


def test_get_run_success(monkeypatch) -> None:
    async def fake_get_run(_run_id: str):
        return ArenaRun(
            id='run-2',
            status=RunStatus.COMPLETED,
            prompt='prompt',
            candidates=['m1'],
            winner_alias='m1',
            answers={'m1': 'answer'},
            scores={'m1': 1.0},
            latencies={'m1': 12},
            judge='heuristic',
        )

    monkeypatch.setattr('app.main.cosmos_client.get_run', fake_get_run)

    client = TestClient(app)
    response = client.get('/arena/runs/run-2')

    assert response.status_code == 200
    payload = response.json()
    assert payload['id'] == 'run-2'
    assert payload['status'] == 'completed'
