# Security baseline and threat model

## Protected assets
Provider/MCP credentials, tenant data, tool privileges, workflow state, evidence, reports and audit records.

## Threats
Malicious user input, prompt injection in retrieved content, malicious MCP servers, over-permissioned agents, credential leakage, duplicate Activity execution, cross-tenant access, model hallucination and tool argument manipulation.

## Baseline controls
- Read-only by default; fail closed for unknown tools/actions.
- Explicit MCP server and tool allowlists.
- Authentication and tenant-scoped authorization.
- Least-privilege credentials and secret manager integration.
- Schema validation before tool invocation.
- Network egress restrictions for tool workers.
- Human approval for sensitive operations.
- Idempotency keys for side-effecting operations.
- Append-only audit events and trace correlation.
- No secrets in prompts, logs, traces or model context.
- External content is untrusted data, never policy.

## Milestone 0 non-goals
No production infrastructure access, arbitrary shell execution, unrestricted filesystem access, autonomous credential changes or destructive operations.
