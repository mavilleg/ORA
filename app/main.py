from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.cosmos_client import cosmos_client
from app.models import ArenaRun
from app.orchestrator import ArenaOrchestrator
from app.schemas import ArenaRunRequest, ArenaRunResponse, RunDetailResponse
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await cosmos_client.initialize()
    yield
    # Shutdown


app = FastAPI(title='ORA API', version='0.2.0', lifespan=lifespan)
orchestrator = ArenaOrchestrator()


@app.get('/health')
async def health() -> dict[str, str | list[str]]:
    return {
        'status': 'ok',
        'configured_models': settings.model_aliases,
        'judge_model': settings.arena_judge_model,
        'persistence': 'cosmos' if settings.cosmos_endpoint else 'none',
    }


@app.post('/arena/run', response_model=ArenaRunResponse)
async def run_arena(req: ArenaRunRequest) -> ArenaRunResponse:
    try:
        return await orchestrator.run(req)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get('/arena/runs/{run_id}', response_model=RunDetailResponse)
async def get_run(run_id: str) -> RunDetailResponse:
    run = await cosmos_client.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f'Run {run_id} not found')
    
    return RunDetailResponse(
        id=run.id,
        status=run.status,
        prompt=run.prompt,
        winner_alias=run.winner_alias,
        answers=run.answers,
        scores=run.scores,
        latencies=run.latencies,
        judge=run.judge,
        error=run.error,
    )
