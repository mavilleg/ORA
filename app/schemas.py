from pydantic import BaseModel, Field


class ArenaRunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system_prompt: str = 'You are a helpful reasoning assistant.'
    candidates: list[str] | None = None
    temperature: float = 0.2
    max_tokens: int = 800


class ModelAnswer(BaseModel):
    model_alias: str
    model_name: str
    answer: str
    latency_ms: int
    score: float


class ArenaRunResponse(BaseModel):
    run_id: str
    winner: ModelAnswer
    answers: list[ModelAnswer]
    judge: str


class RunDetailResponse(BaseModel):
    id: str
    status: str
    prompt: str
    winner_alias: str | None = None
    answers: dict
    scores: dict
    latencies: dict
    judge: str | None = None
    error: str | None = None
