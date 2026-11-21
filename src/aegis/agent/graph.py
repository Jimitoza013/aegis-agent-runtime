from langgraph.graph import END, START, StateGraph

from aegis.agent.nodes import (
    create_ai_planning_node,
    create_initial_plan,
    execute_next_step,
    finalize_task,
    validate_input,
)
from aegis.agent.routing import (
    route_after_execution,
    route_after_planning,
    route_after_validation,
)
from aegis.agent.state import AgentState
from aegis.core.config import Settings
from aegis.providers.runtime import ModelRuntime


def build_agent_graph(
    *,
    model_runtime: ModelRuntime | None = None,
    settings: Settings | None = None,
):
    """Build and compile the Aegis agent workflow.

    When ModelRuntime and Settings are provided, use AI-powered planning.
    Otherwise, use the deterministic baseline planner.
    """

    if (model_runtime is None) != (settings is None):
        raise ValueError(
            "ModelRuntime and Settings must either both be provided or both be omitted."
        )

    if model_runtime is not None and settings is not None:
        planning_node = create_ai_planning_node(
            model_runtime,
            settings,
        )
    else:
        planning_node = create_initial_plan

    builder = StateGraph(AgentState)

    # Register workflow nodes.
    builder.add_node("validate_input", validate_input)
    builder.add_node("create_plan", planning_node)
    builder.add_node("execute_step", execute_next_step)
    builder.add_node("finalize", finalize_task)

    # Define workflow entry point.
    builder.add_edge(START, "validate_input")

    # Validation routing.
    builder.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "plan": "create_plan",
            "end": END,
        },
    )

    # Planning routing.
    builder.add_conditional_edges(
        "create_plan",
        route_after_planning,
        {
            "execute": "execute_step",
            "end": END,
        },
    )

    # Execution routing.
    builder.add_conditional_edges(
        "execute_step",
        route_after_execution,
        {
            "execute": "execute_step",
            "finalize": "finalize",
            "end": END,
        },
    )

    # Final workflow transition.
    builder.add_edge("finalize", END)

    return builder.compile()
