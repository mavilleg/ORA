from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class RunStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class ArenaRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: RunStatus = RunStatus.PENDING
    prompt: str
    system_prompt: str = 'You are a helpful reasoning assistant.'
    candidates: list[str]
    temperature: float = 0.2
    max_tokens: int = 800
    winner_alias: str | None = None
    answers: dict[str, str] = Field(default_factory=dict)
    scores: dict[str, float] = Field(default_factory=dict)
    judge: str | None = None
    latencies: dict[str, int] = Field(default_factory=dict)
    error: str | None = None

    model_config = ConfigDict(use_enum_values=True)
