# Aegis Agent Runtime

Model-independent autonomous AI agent platform built with Python, LangGraph, Temporal and MCP.

**Status:** Milestone 0 foundation scaffold. This is not yet a functioning autonomous agent.

## Architecture rules
- Temporal owns durable task lifecycles, retries, timeouts, cancellation and approval waits.
- LangGraph owns agent state transitions and bounded reasoning loops.
- LLM, database, network and MCP operations execute outside deterministic Temporal Workflow code, through Activities.
- MCP is an interoperability protocol, not an authorization boundary.
- Deterministic policy code authorizes actions independently of model output.
- PostgreSQL is application source of truth; LangGraph checkpoints are stored separately.
- Side-effecting operations require idempotency.

## Requirements
Python 3.12+, `uv`, Docker, Docker Compose, Temporal CLI.

## Quick start
```bash
uv sync --all-groups
cp .env.example .env
docker compose up -d postgres redis
uv run pytest
uv run ruff check .
uv run mypy src
```
In another terminal, start Temporal:
```bash
temporal server start-dev
```

No provider key is needed for Milestone 0. API and worker processes are implemented in later milestones.

## Milestones
0. Repository foundation, domain contracts, configuration and policy baseline.
1. Provider abstraction and model adapters.
2. LangGraph agent runtime.
3. Temporal durable execution.
4. MCP tool gateway.
5. Persistent memory.
6. Multi-agent coordination.
7. Production hardening and evaluation.

Never commit `.env` or credentials. Do not connect this scaffold to production infrastructure.
