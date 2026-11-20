# ADR-0001: Separate durable workflows from agent reasoning

- Status: Accepted
- Date: 2026-11-18

## Context
The platform needs multi-step reasoning, durable execution, model portability and standardized tool integration. Combining all responsibilities in one framework makes recovery, testing and security boundaries harder to reason about.

## Decision
- Temporal owns durable task lifecycle.
- LangGraph owns agent state transitions and bounded reasoning.
- MCP is the external tool/context protocol.
- An application-owned policy engine authorizes actions.
- Provider adapters isolate model vendors.
- PostgreSQL stores application state and LangGraph checkpoints.

All external I/O occurs outside deterministic Temporal Workflow code, through Activities or explicitly durable integrations.

## Consequences
The architecture has more components and requires careful idempotency and versioning. In return, workflow durability, agent reasoning, provider portability and tool authorization can be tested independently.
