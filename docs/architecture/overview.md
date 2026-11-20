# Architecture overview

## Runtime boundaries

1. FastAPI accepts authenticated task requests.
2. Temporal owns durable task lifecycle, retries, timeouts, cancellation and approval waits.
3. LangGraph owns agent state, planning, routing and bounded reasoning loops.
4. Provider adapters normalize model calls behind an application-owned interface.
5. MCP gateway discovers and invokes allowlisted tools.
6. Policy engine authorizes every action independently of model output.
7. PostgreSQL stores application records and LangGraph checkpoints.
8. Redis is a cache/ephemeral coordination layer, not the source of truth.
9. OpenTelemetry correlates API, workflow, agent, model and tool activity.

## Durable execution

Temporal Workflow code must be deterministic. Network I/O, model calls, MCP calls, database access and other external side effects execute in Activities. Activity retries must be paired with idempotency for side-effecting operations.

## LangGraph and Temporal

Temporal is the outer durable business workflow. LangGraph is the agent state machine invoked through bounded execution steps. LangGraph checkpoints persist in PostgreSQL. Avoid wrapping an unbounded graph run in one opaque Activity. Each externally visible side effect needs an idempotency key and durable execution record.

## Model independence

The domain and graph depend on an internal ModelProvider protocol, not vendor SDKs. LiteLLM is an adapter candidate. Provider-specific capabilities must be represented explicitly rather than assumed identical.

## MCP boundary

MCP provides interoperability, not permission. Authenticate the principal, allowlist server/tool identities, validate arguments, enforce resource scope, apply risk policy and audit every invocation.
