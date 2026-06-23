from fastapi import FastAPI, HTTPException

from app.orchestrator import ArenaOrchestrator
from app.schemas import ArenaRunRequest, ArenaRunResponse
from app.settings import settings

app = FastAPI(title='ORA API', version='0.1.0')
orchestrator = ArenaOrchestrator()


@app.get('/health')
async def health() -> dict[str, str | list[str]]:
    return {
        'status': 'ok',
        'configured_models': settings.model_aliases,
        'judge_model': settings.arena_judge_model,
    }


@app.post('/arena/run', response_model=ArenaRunResponse)
async def run_arena(req: ArenaRunRequest) -> ArenaRunResponse:
    try:
        return await orchestrator.run(req)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
