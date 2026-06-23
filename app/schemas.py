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
    winner: ModelAnswer
    answers: list[ModelAnswer]
    judge: str
