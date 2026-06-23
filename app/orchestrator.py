from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json

from app.cosmos_client import cosmos_client
from app.models import ArenaRun, RunStatus
from app.providers.foundry_client import chat_completion, load_model_config
from app.schemas import ArenaRunRequest, ArenaRunResponse, ModelAnswer
from app.settings import settings


class ArenaOrchestrator:
    async def run(self, req: ArenaRunRequest) -> ArenaRunResponse:
        candidates = req.candidates if req.candidates else settings.model_aliases
        if not candidates:
            raise ValueError('No candidate models configured. Set ARENA_MODELS or provide candidates.')

        # Create run record
        arena_run = ArenaRun(
            prompt=req.prompt,
            system_prompt=req.system_prompt,
            candidates=candidates,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            status=RunStatus.RUNNING,
        )
        await cosmos_client.save_run(arena_run)

        try:
            answers = await asyncio.gather(*[self._run_model(alias, req) for alias in candidates])

            judge_alias = settings.arena_judge_model.strip()
            if judge_alias:
                scored_answers = await self._judge_with_model(judge_alias, req.prompt, answers)
                judge = judge_alias
            else:
                scored_answers = self._heuristic_rank(answers)
                judge = 'heuristic'

            winner = max(scored_answers, key=lambda a: a.score)
            
            # Update run with results
            arena_run.status = RunStatus.COMPLETED
            arena_run.updated_at = datetime.now(timezone.utc)
            arena_run.winner_alias = winner.model_alias
            arena_run.judge = judge
            arena_run.answers = {a.model_alias: a.answer for a in scored_answers}
            arena_run.scores = {a.model_alias: a.score for a in scored_answers}
            arena_run.latencies = {a.model_alias: a.latency_ms for a in scored_answers}
            await cosmos_client.save_run(arena_run)

            return ArenaRunResponse(
                run_id=arena_run.id,
                winner=winner,
                answers=sorted(scored_answers, key=lambda a: a.score, reverse=True),
                judge=judge,
            )
        except Exception as exc:
            arena_run.status = RunStatus.FAILED
            arena_run.updated_at = datetime.now(timezone.utc)
            arena_run.error = str(exc)
            await cosmos_client.save_run(arena_run)
            raise

    async def _run_model(self, alias: str, req: ArenaRunRequest) -> ModelAnswer:
        cfg = load_model_config(alias)
        text, latency_ms = await chat_completion(
            cfg,
            system_prompt=req.system_prompt,
            user_prompt=req.prompt,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            timeout_seconds=settings.model_timeout_seconds,
        )
        return ModelAnswer(
            model_alias=alias,
            model_name=cfg.model,
            answer=text,
            latency_ms=latency_ms,
            score=0.0,
        )

    def _heuristic_rank(self, answers: list[ModelAnswer]) -> list[ModelAnswer]:
        for ans in answers:
            length_score = min(len(ans.answer) / 1000.0, 1.0)
            latency_bonus = max(0.0, 1.0 - (ans.latency_ms / 5000.0))
            ans.score = round((0.7 * length_score) + (0.3 * latency_bonus), 4)
        return answers

    async def _judge_with_model(
        self,
        judge_alias: str,
        original_prompt: str,
        answers: list[ModelAnswer],
    ) -> list[ModelAnswer]:
        cfg = load_model_config(judge_alias)
        candidate_block = '\n\n'.join([f'[{a.model_alias}]\n{a.answer}' for a in answers])
        judge_prompt = (
            'You are a strict evaluator. Rank responses for correctness, reasoning depth, and clarity. '
            'Return JSON only: {"scores": {"alias": number_between_0_and_1}}.\n\n'
            f'Task:\n{original_prompt}\n\n'
            f'Candidates:\n{candidate_block}'
        )

        raw, _ = await chat_completion(
            cfg,
            system_prompt='You are an expert evaluator.',
            user_prompt=judge_prompt,
            temperature=0.0,
            max_tokens=500,
            timeout_seconds=settings.model_timeout_seconds,
        )

        scores = self._parse_judge_scores(raw)

        for ans in answers:
            score = scores.get(ans.model_alias)
            ans.score = float(score) if isinstance(score, (int, float)) else 0.1

        return answers

    def _parse_judge_scores(self, raw: str) -> dict[str, float]:
        candidates = [raw]
        if '```' in raw:
            fenced = raw.split('```')
            candidates.extend(part.strip() for i, part in enumerate(fenced) if i % 2 == 1)

        for candidate in candidates:
            normalized = candidate.removeprefix('json').strip()
            try:
                payload = json.loads(normalized)
            except Exception:
                continue

            if isinstance(payload, dict) and isinstance(payload.get('scores'), dict):
                return payload['scores']
        return {}
