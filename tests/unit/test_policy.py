from uuid import uuid4

from aegis.domain.models import RiskLevel, ToolRequest
from aegis.security.policy import authorize_tool


def make_request(*, action: str, risk: RiskLevel) -> ToolRequest:
    return ToolRequest(
        tool_name="research.search",
        action=action,
        risk_level=risk,
        arguments={"query": "Temporal durable execution"},
        tenant_id=uuid4(),
        principal_id=uuid4(),
        idempotency_key="test-idempotency-key-0001",
    )


def test_low_risk_read_action_is_allowed() -> None:
    decision = authorize_tool(make_request(action="search", risk=RiskLevel.LOW))
    assert decision.allowed is True
    assert decision.requires_approval is False


def test_write_action_is_denied_even_if_marked_low_risk() -> None:
    decision = authorize_tool(make_request(action="delete", risk=RiskLevel.LOW))
    assert decision.allowed is False


def test_medium_risk_action_is_denied_by_default() -> None:
    decision = authorize_tool(make_request(action="restart", risk=RiskLevel.MEDIUM))
    assert decision.allowed is False
    assert decision.requires_approval is True


def test_critical_action_is_denied() -> None:
    decision = authorize_tool(make_request(action="delete", risk=RiskLevel.CRITICAL))
    assert decision.allowed is False
