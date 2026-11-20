from aegis.domain.models import PolicyDecision, RiskLevel, ToolRequest

POLICY_VERSION = "baseline-0.1"
ALLOWED_LOW_RISK_ACTIONS = frozenset({"read", "list", "search", "inspect"})


def authorize_tool(request: ToolRequest) -> PolicyDecision:
    """Fail-closed baseline. This is not yet a complete RBAC engine."""
    if request.risk_level is not RiskLevel.LOW:
        return PolicyDecision(
            allowed=False,
            requires_approval=True,
            reason="Only low-risk actions are enabled in the foundation milestone.",
            policy_version=POLICY_VERSION,
        )

    if request.action.lower() not in ALLOWED_LOW_RISK_ACTIONS:
        return PolicyDecision(
            allowed=False,
            requires_approval=False,
            reason="Action is not in the read-only allowlist.",
            policy_version=POLICY_VERSION,
        )

    return PolicyDecision(
        allowed=True,
        requires_approval=False,
        reason="Low-risk read-only action is permitted by the baseline policy.",
        policy_version=POLICY_VERSION,
    )
