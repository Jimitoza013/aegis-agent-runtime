from unittest.mock import AsyncMock

import pytest

from aegis.agent.nodes import create_ai_planning_node
from aegis.agent.state import AgentState
from aegis.core.config import Settings
from aegis.providers.base import ModelResponse, ProviderUnavailableError
from aegis.providers.router import TaskComplexity


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="test",
        moderate_task_model="test-model",
    )


@pytest.fixture
def model_runtime() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def initial_state() -> AgentState:
    return {
        "user_input": "Build a REST API",
        "plan": [],
        "current_step": 0,
        "task_status": "planning",
        "iteration_count": 0,
        "max_iterations": 5,
        "error": None,
        "final_response": None,
        "messages": [],
    }


@pytest.mark.asyncio
async def test_ai_planning_returns_validated_plan(
    settings: Settings,
    model_runtime: AsyncMock,
    initial_state: AgentState,
) -> None:
    model_runtime.generate.return_value = ModelResponse(
        content=(
            '{"steps": ['
            '"Understand API requirements", '
            '"Design API endpoints", '
            '"Implement and test the API"'
            "]}"
        ),
        provider="litellm",
        model="test-model",
    )

    node = create_ai_planning_node(model_runtime, settings)

    result = await node(initial_state)

    assert result["plan"] == [
        "Understand API requirements",
        "Design API endpoints",
        "Implement and test the API",
    ]
    assert result["current_step"] == 0
    assert result["iteration_count"] == 0
    assert result["task_status"] == "running"
    assert result["error"] is None

    model_runtime.generate.assert_awaited_once()

    request = model_runtime.generate.await_args.args[0]

    assert request.model == "test-model"
    assert request.response_format == {"type": "json_object"}
    assert model_runtime.generate.await_args.kwargs["complexity"] == (TaskComplexity.MODERATE)


@pytest.mark.asyncio
async def test_ai_planning_rejects_invalid_json(
    settings: Settings,
    model_runtime: AsyncMock,
    initial_state: AgentState,
) -> None:
    model_runtime.generate.return_value = ModelResponse(
        content="This is not valid JSON",
        provider="litellm",
        model="test-model",
    )

    node = create_ai_planning_node(model_runtime, settings)

    result = await node(initial_state)

    assert result["task_status"] == "failed"
    assert result["error"] == "The AI returned an invalid execution plan."
    assert result["final_response"] is None


@pytest.mark.asyncio
async def test_ai_planning_rejects_empty_plan(
    settings: Settings,
    model_runtime: AsyncMock,
    initial_state: AgentState,
) -> None:
    model_runtime.generate.return_value = ModelResponse(
        content='{"steps": []}',
        provider="litellm",
        model="test-model",
    )

    node = create_ai_planning_node(model_runtime, settings)

    result = await node(initial_state)

    assert result["task_status"] == "failed"
    assert result["error"] == "The AI returned an invalid execution plan."


@pytest.mark.asyncio
async def test_ai_planning_rejects_blank_plan_step(
    settings: Settings,
    model_runtime: AsyncMock,
    initial_state: AgentState,
) -> None:
    model_runtime.generate.return_value = ModelResponse(
        content='{"steps": ["Understand requirements", "   "]}',
        provider="litellm",
        model="test-model",
    )

    node = create_ai_planning_node(model_runtime, settings)

    result = await node(initial_state)

    assert result["task_status"] == "failed"
    assert result["error"] == "The AI returned an invalid execution plan."


@pytest.mark.asyncio
async def test_ai_planning_handles_provider_failure(
    settings: Settings,
    model_runtime: AsyncMock,
    initial_state: AgentState,
) -> None:
    model_runtime.generate.side_effect = ProviderUnavailableError(
        "Provider unavailable",
        provider="litellm",
        retryable=False,
    )

    node = create_ai_planning_node(model_runtime, settings)

    result = await node(initial_state)

    assert result["task_status"] == "failed"
    assert result["error"] == ("The AI planning service could not complete the request.")


@pytest.mark.asyncio
async def test_ai_planning_rejects_empty_user_input(
    settings: Settings,
    model_runtime: AsyncMock,
    initial_state: AgentState,
) -> None:
    initial_state["user_input"] = "   "

    node = create_ai_planning_node(model_runtime, settings)

    result = await node(initial_state)

    assert result["task_status"] == "failed"
    assert result["error"] == "User input cannot be empty."
    model_runtime.generate.assert_not_awaited()
