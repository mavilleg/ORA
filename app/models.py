from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class ArenaRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: RunStatus = RunStatus.PENDING
    prompt: str
    system_prompt: str = 'You are a helpful reasoning assistant.'
    candidates: list[str]
    temperature: float = 0.2
    max_tokens: int = 800
    winner_alias: str | None = None
    answers: dict = Field(default_factory=dict)  # {alias: answer_text}
    scores: dict = Field(default_factory=dict)  # {alias: score}
    judge: str | None = None
    latencies: dict = Field(default_factory=dict)  # {alias: latency_ms}
    error: str | None = None

    class Config:
        use_enum_values = True
