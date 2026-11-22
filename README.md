# Aegis Agent Runtime

A model-independent autonomous AI agent runtime built with Python, LangGraph, Temporal, LiteLLM, PostgreSQL and the Model Context Protocol (MCP).

Aegis provides the foundational architecture for building secure, durable and extensible AI agents with controlled tool execution and persistent memory.

**Current progress:** Milestones 0–5 implemented. Multi-agent coordination and production hardening are planned.

## Architecture

Aegis separates agent reasoning, orchestration, model access, tool integration, authorization and persistent memory into independent components.

| Component | Responsibility |
|---|---|
| LiteLLM | Model and embedding provider integration |
| Provider abstraction | Model-independent request and response contracts |
| LangGraph | Agent state transitions, planning and bounded reasoning |
| Temporal | Durable task execution, retries, timeouts and workflow recovery |
| MCP | External tool and context interoperability |
| Policy engine | Independent authorization of tool actions |
| PostgreSQL | Application data and persistent memory storage |
| pgvector | Vector storage and semantic similarity retrieval |
| Redis | Ephemeral data and caching |

## Architecture rules

- Temporal owns durable task lifecycles, retries, timeouts, cancellation and approval waits.
- LangGraph owns agent state transitions and bounded reasoning loops.
- External I/O must not execute inside deterministic Temporal Workflow code. Use Activities.
- MCP is an interoperability protocol, not an authorization boundary.
- Deterministic policy code authorizes actions independently of model output.
- PostgreSQL is the application source of truth; LangGraph checkpoints and persistent memory are separate systems.
- Persistent memories are scoped by tenant and principal.
- Memory retrieval must enforce ownership boundaries and expiration rules.
- Side-effecting operations require idempotency controls.
- Secrets and credentials must never be hard-coded or committed.

## Implemented milestones

### Milestone 0 — Repository foundation

- Project structure and configuration.
- Domain contracts and validation.
- Security policy baseline.
- Development and testing configuration.

### Milestone 1 — Model-independent intelligence engine

- Provider abstraction.
- LiteLLM provider adapter.
- Provider registry and factory.
- Model routing.
- Bounded retry handling.
- Runtime orchestration.

### Milestone 2 — LangGraph agent runtime

- Typed agent state.
- Planning and execution nodes.
- Conditional routing.
- Bounded reasoning loops.
- AI-powered planning through the model runtime.
- Deterministic planning fallback.

### Milestone 3 — Temporal durable orchestration

- Temporal workflow implementation.
- Agent task activities.
- Worker configuration.
- Temporal client integration.
- Workflow execution with retry and timeout policies.
- Structured task results.

### Milestone 4 — MCP tool gateway

- MCP client using stdio transport.
- External MCP server connection management.
- Dynamic tool discovery.
- Tool and policy registries.
- Trusted authorization policies.
- Independent tool authorization.
- MCP tool execution and result normalization.
- MCP gateway server implementation.
- Unit and real-process integration tests.

**Security principle:** Discovering an MCP tool does not automatically authorize its execution. A trusted local policy must authorize the requested action.

### Milestone 5 — Persistent memory and semantic retrieval

- PostgreSQL-backed persistent memory storage.
- SQLAlchemy asynchronous database foundation.
- Alembic database migrations.
- pgvector extension and vector storage.
- Tenant and principal ownership scopes.
- Validated memory schemas and memory categories.
- Memory repository for creating, retrieving, listing and deleting records.
- Expiration-aware memory management and cleanup.
- Provider-independent embedding abstraction.
- LiteLLM embedding provider adapter.
- Vector similarity search using cosine distance.
- Memory type filtering and configurable result limits.
- Semantic retrieval with tenant and principal isolation.
- Memory service coordinating embedding generation, persistence and retrieval.
- Unit and PostgreSQL integration tests.

**Memory architecture principle:** Persistent memory stores information intended to be reused across tasks. LangGraph checkpointing stores execution state required to resume workflows. These responsibilities remain separate.

## Planned milestones

6. Multi-agent coordination.

7. Production hardening, observability and evaluation.

## Technology stack

- Python 3.12+
- Pydantic
- SQLAlchemy
- Alembic
- LiteLLM
- LangGraph
- Temporal
- Model Context Protocol (MCP)
- FastAPI
- PostgreSQL
- pgvector
- Redis
- pytest
- Ruff
- Docker and Docker Compose

## Requirements

- Python 3.12+
- `uv`
- Docker Desktop or Docker Engine
- Docker Compose
- Temporal CLI

## Setup

Clone the repository:

```bash
git clone https://github.com/Jimitoza013/aegis-agent-runtime.git
cd aegis-agent-runtime
```

Install dependencies:

```bash
uv sync --all-groups
```

Create the local environment file:

```bash
cp .env.example .env
```

Configure any required provider credentials in `.env`. Never commit this file.

Start PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

Apply database migrations:

```bash
uv run alembic upgrade head
```

Start a local Temporal development server when running Temporal workflows:

```bash
temporal server start-dev
```

Run the test suite:

```bash
uv run pytest
```

Run lint checks:

```bash
uv run ruff check .
```

Verify formatting:

```bash
uv run ruff format --check .
```

## Database migrations

Aegis uses Alembic for database schema management.

Apply all migrations:

```bash
uv run alembic upgrade head
```

Check the current migration revision:

```bash
uv run alembic current
```

Generate a migration after changing database models:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
```

Review generated migrations before applying them.

## Testing

The project uses pytest for unit and integration testing.

Run all tests:

```bash
uv run pytest -v
```

Run MCP integration tests:

```bash
uv run pytest tests/integration/test_mcp_integration.py -v
```

Run MCP unit tests:

```bash
uv run pytest tests/unit -k mcp -v
```

Run memory schema tests:

```bash
uv run pytest tests/unit/test_memory_schemas.py -v
```

Run memory embedding tests:

```bash
uv run pytest tests/unit/test_memory_embeddings.py -v
```

Run LiteLLM embedding adapter tests:

```bash
uv run pytest tests/unit/test_litellm_embeddings.py -v
```

Run memory service tests:

```bash
uv run pytest tests/unit/test_memory_service.py -v
```

Run memory repository integration tests:

```bash
uv run pytest tests/integration/test_memory_repository.py -v
```

Run semantic retrieval integration tests:

```bash
uv run pytest tests/integration/test_memory_retrieval.py -v
```

Database integration tests require the PostgreSQL service to be running and the schema migrations to be applied.

Embedding adapter tests use mocked provider responses and do not require paid model API calls.

**Latest verification:** 199 tests passed. Ruff lint and formatting checks passed.

## Project structure

```text
aegis-agent-runtime/
├── docs/
├── migrations/
│   └── versions/
├── src/
│   └── aegis/
│       ├── agent/
│       ├── core/
│       ├── database/
│       │   └── models/
│       ├── domain/
│       ├── mcp/
│       ├── memory/
│       ├── orchestration/
│       ├── providers/
│       └── security/
├── tests/
│   ├── integration/
│   └── unit/
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Security

- Default to read-only access.
- Deny actions without an explicit trusted policy.
- Never treat model output or MCP metadata as authorization.
- Validate tool requests before execution.
- Enforce tenant and principal ownership when accessing persistent memories.
- Avoid exposing internal exception details to external callers.
- Keep credentials in environment variables.
- Do not connect unfinished components to production infrastructure.

## Development principles

- Keep components independently understandable.
- Prefer clean, maintainable and beginner-friendly code.
- Avoid unnecessary abstraction and over-engineering.
- Preserve existing working functionality.
- Include tests for new functionality.
- Document architectural decisions and meaningful changes.
- Use meaningful Git commits.

## License

License information will be added when the project license is selected.
