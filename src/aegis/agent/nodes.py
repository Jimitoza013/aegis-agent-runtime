import json
from typing import Any

from pydantic import ValidationError

from aegis.agent.schemas import AgentPlan
from aegis.agent.state import AgentState
from aegis.core.config import Settings
from aegis.providers.base import (
    MessageRole,
    ModelMessage,
    ModelRequest,
    ProviderError,
)
from aegis.providers.router import TaskComplexity
from aegis.providers.runtime import ModelRuntime


def validate_input(state: AgentState) -> dict[str, Any]:
    """Validate the incoming user task."""

    user_input = state.get("user_input", "")

    if not user_input.strip():
        return {
            "task_status": "failed",
            "error": "User input cannot be empty.",
            "final_response": None,
        }

    return {
        "task_status": "planning",
        "error": None,
        "final_response": None,
    }


def create_initial_plan(state: AgentState) -> dict[str, Any]:
    """Create a deterministic initial plan for the task."""

    user_input = state["user_input"].strip()

    return {
        "plan": [
            f"Understand the task: {user_input}",
            "Determine the required actions.",
            "Review the results.",
            "Prepare the final response.",
        ],
        "current_step": 0,
        "iteration_count": 0,
        "task_status": "running",
        "error": None,
    }


def create_ai_planning_node(
    model_runtime: ModelRuntime,
    settings: Settings,
):
    """Create an asynchronous LangGraph node backed by ModelRuntime."""

    async def ai_planning_node(state: AgentState) -> dict[str, Any]:
        user_input = state.get("user_input", "").strip()

        if not user_input:
            return {
                "task_status": "failed",
                "error": "User input cannot be empty.",
                "final_response": None,
            }

        request = ModelRequest(
            messages=[
                ModelMessage(
                    role=MessageRole.SYSTEM,
                    content=(
                        "You are the planning component of Aegis Agent Runtime. "
                        "Create a concise, safe, ordered execution plan for "
                        "the user's task. Return only valid JSON with one "
                        "property named 'steps', containing an array of "
                        "non-empty strings. Do not execute actions. "
                        "Do not claim that actions have already been performed."
                    ),
                ),
                ModelMessage(
                    role=MessageRole.USER,
                    content=f"Create an execution plan for this task:\n{user_input}",
                ),
            ],
            model=settings.moderate_task_model,
            temperature=settings.model_temperature,
            max_tokens=settings.model_max_tokens,
            timeout_seconds=settings.model_timeout_seconds,
            response_format={"type": "json_object"},
        )

        try:
            response = await model_runtime.generate(
                request,
                complexity=TaskComplexity.MODERATE,
            )

            validated_plan = AgentPlan.model_validate_json(response.content)

        except (ProviderError, LookupError):
            return {
                "task_status": "failed",
                "error": "The AI planning service could not complete the request.",
                "final_response": None,
            }

        except (ValidationError, ValueError, json.JSONDecodeError):
            return {
                "task_status": "failed",
                "error": "The AI returned an invalid execution plan.",
                "final_response": None,
            }

        return {
            "plan": validated_plan.steps,
            "current_step": 0,
            "iteration_count": 0,
            "task_status": "running",
            "error": None,
            "final_response": None,
        }

    return ai_planning_node


def execute_next_step(state: AgentState) -> dict[str, Any]:
    """Advance execution by one bounded planning step."""

    current_step = state.get("current_step", 0)
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 5)
    plan = state.get("plan", [])

    if iteration_count >= max_iterations:
        return {
            "task_status": "failed",
            "error": "Maximum iteration limit reached.",
        }

    if current_step >= len(plan):
        return {
            "task_status": "completed",
            "final_response": "The task plan has been completed.",
        }

    return {
        "current_step": current_step + 1,
        "iteration_count": iteration_count + 1,
        "task_status": ("completed" if current_step + 1 >= len(plan) else "running"),
        "error": None,
    }


def finalize_task(state: AgentState) -> dict[str, Any]:
    """Prepare the final task response."""

    if state.get("task_status") == "failed":
        return {"final_response": (state.get("error") or "The task could not be completed.")}

    return {
        "task_status": "completed",
        "final_response": (f"Task completed successfully: {state['user_input']}"),
    }
