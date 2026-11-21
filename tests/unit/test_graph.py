from unittest.mock import AsyncMock

import pytest

from aegis.agent.graph import build_agent_graph
from aegis.core.config import Settings
from aegis.providers.base import ModelResponse


def test_graph_builds_successfully() -> None:
    graph = build_agent_graph()

    assert graph is not None


def test_graph_completes_valid_task() -> None:
    graph = build_agent_graph()

    result = graph.invoke(
        {
            "user_input": "Research AI agents",
            "max_iterations": 5,
        }
    )

    assert result["task_status"] == "completed"
    assert result["final_response"] is not None
    assert len(result["plan"]) == 4


def test_graph_rejects_empty_input() -> None:
    graph = build_agent_graph()

    result = graph.invoke(
        {
            "user_input": "   ",
            "max_iterations": 5,
        }
    )

    assert result["task_status"] == "failed"
    assert result["error"] == "User input cannot be empty."


def test_graph_respects_iteration_limit() -> None:
    graph = build_agent_graph()

    result = graph.invoke(
        {
            "user_input": "Research AI agents",
            "max_iterations": 2,
        }
    )

    assert result["task_status"] == "failed"
    assert result["error"] == "Maximum iteration limit reached."


@pytest.mark.asyncio
async def test_ai_graph_completes_valid_task() -> None:
    model_runtime = AsyncMock()

    model_runtime.generate.return_value = ModelResponse(
        content=(
            '{"steps": ['
            '"Understand the requirements", '
            '"Research the technical approach", '
            '"Prepare the implementation plan"'
            "]}"
        ),
        provider="litellm",
        model="test-model",
    )

    settings = Settings(
        app_env="test",
        moderate_task_model="test-model",
    )

    graph = build_agent_graph(
        model_runtime=model_runtime,
        settings=settings,
    )

    result = await graph.ainvoke(
        {
            "user_input": "Research autonomous AI agents",
            "max_iterations": 5,
        }
    )

    assert result["task_status"] == "completed"
    assert result["plan"] == [
        "Understand the requirements",
        "Research the technical approach",
        "Prepare the implementation plan",
    ]
    assert result["final_response"] is not None

    model_runtime.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_ai_graph_rejects_invalid_model_output() -> None:
    model_runtime = AsyncMock()

    model_runtime.generate.return_value = ModelResponse(
        content="Invalid JSON response",
        provider="litellm",
        model="test-model",
    )

    settings = Settings(
        app_env="test",
        moderate_task_model="test-model",
    )

    graph = build_agent_graph(
        model_runtime=model_runtime,
        settings=settings,
    )

    result = await graph.ainvoke(
        {
            "user_input": "Research autonomous AI agents",
            "max_iterations": 5,
        }
    )

    assert result["task_status"] == "failed"
    assert result["error"] == "The AI returned an invalid execution plan."
    assert result["final_response"] is None


def test_graph_requires_runtime_and_settings_together() -> None:
    model_runtime = AsyncMock()

    with pytest.raises(ValueError, match="must either both be provided"):
        build_agent_graph(model_runtime=model_runtime)
