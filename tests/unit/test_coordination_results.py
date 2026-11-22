from uuid import uuid4

import pytest
from pydantic import ValidationError

from aegis.coordination.results import AgentExecutionResult
from aegis.domain.models import TaskStatus


def test_completed_result_requires_output() -> None:
    result = AgentExecutionResult(
        assignment_id=uuid4(),
        agent_id="research-agent",
        status=TaskStatus.COMPLETED,
        output="Research completed successfully.",
    )

    assert result.status == TaskStatus.COMPLETED
    assert result.output == "Research completed successfully."
    assert result.error is None


def test_failed_result_requires_error() -> None:
    result = AgentExecutionResult(
        assignment_id=uuid4(),
        agent_id="research-agent",
        status=TaskStatus.FAILED,
        error="Research provider unavailable.",
    )

    assert result.status == TaskStatus.FAILED
    assert result.error == "Research provider unavailable."
    assert result.output is None


def test_completed_result_rejects_missing_output() -> None:
    with pytest.raises(ValidationError, match="must include output"):
        AgentExecutionResult(
            assignment_id=uuid4(),
            agent_id="research-agent",
            status=TaskStatus.COMPLETED,
        )


def test_failed_result_rejects_missing_error() -> None:
    with pytest.raises(ValidationError, match="must include an error"):
        AgentExecutionResult(
            assignment_id=uuid4(),
            agent_id="research-agent",
            status=TaskStatus.FAILED,
        )


def test_completed_result_rejects_error() -> None:
    with pytest.raises(ValidationError, match="cannot contain an error"):
        AgentExecutionResult(
            assignment_id=uuid4(),
            agent_id="research-agent",
            status=TaskStatus.COMPLETED,
            output="Research completed.",
            error="Unexpected error.",
        )


def test_failed_result_rejects_output() -> None:
    with pytest.raises(ValidationError, match="cannot contain output"):
        AgentExecutionResult(
            assignment_id=uuid4(),
            agent_id="research-agent",
            status=TaskStatus.FAILED,
            output="Partial research.",
            error="Execution failed.",
        )


def test_result_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        AgentExecutionResult(
            assignment_id=uuid4(),
            agent_id="research-agent",
            status=TaskStatus.COMPLETED,
            output="Research completed.",
            permissions=["admin"],
        )


def test_result_is_immutable() -> None:
    result = AgentExecutionResult(
        assignment_id=uuid4(),
        agent_id="research-agent",
        status=TaskStatus.COMPLETED,
        output="Research completed.",
    )

    with pytest.raises(ValidationError):
        result.output = "Modified output."
