# Initial data model

Core entities: users, tasks, executions, agent_runs, agent_events, tool_definitions, tool_calls, approvals, evaluations, memory_records, model_calls and audit_logs.

LangGraph checkpoints use its PostgreSQL checkpointer integration. Temporal retains its own workflow event history. Do not duplicate either history wholesale in application tables.

## Required constraints

- Tenant-owned records carry tenant scope.
- Tool idempotency keys are unique within the correct scope.
- Event sequence numbers are unique per agent run.
- Approval decisions record reviewer identity and timestamp.
- Evaluations reference evidence, not only model-generated explanations.
- Embedding dimension matches the configured embedding model.
