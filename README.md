# ORA - Open Reasoning Arena

Open Reasoning Arena is an Azure-ready application concept to orchestrate multiple LLMs through Azure AI Foundry-compatible APIs, benchmark their reasoning quality, and route requests to the best model strategy for each task.

## Vision

The platform acts as a reasoning arena:
- Runs the same prompt across multiple models in parallel
- Evaluates outputs with scoring policies and optional judge models
- Selects a winner (or top-N) based on quality, latency, and cost
- Produces transparent traces for governance and improvement loops

## Why this project

Teams rarely want a single model forever. ORA is designed to:
- Compare model behavior continuously
- Prevent lock-in by abstracting provider-specific details
- Make model routing decisions measurable and auditable
- Support enterprise deployment patterns on Azure

## Target Architecture (Azure)

- API layer: FastAPI (or equivalent) exposed via Azure Container Apps or Azure App Service
- Orchestration engine: fan-out/fan-in workflow for model calls, scoring, and winner selection
- Model connectivity: Azure AI Foundry endpoints (and other compatible endpoints)
- Storage: run logs, prompts, scores, feedback (Azure Cosmos DB or Azure Database for PostgreSQL)
- Observability: Azure Monitor + Application Insights
- Secrets and keys: Azure Key Vault
- Async workloads (optional): Azure Service Bus / Azure Functions for batch evaluation

## Core Modules (MVP)

- Connector SDK
  - Unified client interface for model endpoints
  - Auth abstraction (API key / Entra ID token)

- Arena Orchestrator
  - Parallel execution across candidate models
  - Timeout, retry, and fallback strategies

- Evaluation Engine
  - Rule-based scoring (format, coverage, factual checks)
  - LLM-as-a-judge mode
  - Composite score: quality, latency, cost, safety

- Routing Policy
  - Winner-takes-all
  - Cost-constrained best model
  - Task-type specific routing

- Experiment Registry
  - Versioned prompts, model configs, and score policies
  - Replay support for deterministic comparisons

## Example Arena Flow

1. Receive a user task
2. Select candidate models from policy
3. Execute prompts in parallel
4. Normalize responses and metadata
5. Score each candidate
6. Select winning response
7. Persist run trace and metrics
8. Return response + decision rationale

## Initial API Surface (suggested)

- POST /arena/run
- GET /arena/runs/{id}
- POST /arena/evaluate
- GET /models
- GET /health

## Non-Functional Requirements

- Secure-by-default key management
- Full traceability for every model decision
- Config-driven orchestration and scoring
- Horizontal scalability under burst traffic
- Cost guardrails and per-tenant quotas

## Suggested Roadmap

### Phase 1 - MVP
- Multi-model parallel orchestration
- Heuristic scoring + basic winner selection
- Run history persistence

### Phase 2 - Evaluation intelligence
- Judge-model scoring
- Benchmark datasets and regression tests
- Prompt and policy versioning

### Phase 3 - Enterprise operations
- RBAC and tenant isolation
- Budget policies and chargeback reports
- Human-in-the-loop review workflows

## Deployment Notes

This repository is intended to be deployable on Azure with minimal adaptation. Recommended first target:
- Azure Container Apps for API runtime
- Azure Key Vault for secrets
- Azure Monitor for telemetry

## Status

Repository initialized. Next step is to scaffold the codebase (API + orchestrator + connectors + IaC) directly in this repo.
