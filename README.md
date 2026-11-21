
# Aegis Agent Runtime

A model-independent autonomous AI agent runtime built with Python, LangGraph, Temporal, LiteLLM and the Model Context Protocol (MCP).

Aegis provides the foundational architecture for building secure, durable and extensible AI agents with controlled tool execution.

**Current progress:** Milestones 0–4 implemented. Persistent memory, multi-agent coordination and production hardening are planned.

## Architecture

Aegis separates agent reasoning, orchestration, model access, tool integration and authorization into independent components.

| Component | Responsibility |
|---|---|
| LiteLLM | Model provider integration |
| Provider abstraction | Model-independent request and response contracts |
| LangGraph | Agent state transitions, planning and bounded reasoning |
| Temporal | Durable task execution, retries, timeouts and workflow recovery |
| MCP | External tool and context interoperability |
| Policy engine | Independent authorization of tool actions |
| PostgreSQL | Application data persistence |
| Redis | Ephemeral data and caching |

## Architecture rules

- Temporal owns durable task lifecycles, retries, timeouts, cancellation and approval waits.
- LangGraph owns agent state transitions and bounded reasoning loops.
- External I/O must not execute inside deterministic Temporal Workflow code. Use Activities.
- MCP is an interoperability protocol, not an authorization boundary.
- Deterministic policy code authorizes actions independently of model output.
- PostgreSQL is the application source of truth; LangGraph checkpoints are stored separately.
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

## Planned milestones

5. Persistent memory and retrieval.
6. Multi-agent coordination.
7. Production hardening, observability and evaluation.

## Technology stack

- Python 3.12+
- Pydantic
- LiteLLM
- LangGraph
- Temporal
- Model Context Protocol (MCP)
- FastAPI
- PostgreSQL
- Redis
- pytest
- Ruff
- Docker and Docker Compose

## Requirements

- Python 3.12+
- `uv`
- Docker
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

Start PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

Start a local Temporal development server in another terminal:

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

Integration tests include a local MCP server process communicating over stdio. They do not require a paid model API.

## Project structure

```text
aegis-agent-runtime/
├── docs/
├── src/
│   └── aegis/
│       ├── agent/
│       ├── core/
│       ├── domain/
│       ├── mcp/
│       ├── orchestration/
│       ├── providers/
│       └── security/
├── tests/
│   ├── integration/
│   └── unit/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Security

- Default to read-only access.
- Deny actions without an explicit trusted policy.
- Never treat model output or MCP metadata as authorization.
- Validate tool requests before execution.
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

## License

License information will be added when the project license is selected.
