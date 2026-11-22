from uuid import uuid4

from temporalio.client import Client

from aegis.coordination.schemas import AgentTaskAssignment
from aegis.core.config import Settings
from aegis.orchestration.contracts import (
    AgentTaskResult,
    MultiAgentTaskInput,
    MultiAgentTaskResult,
)
from aegis.orchestration.multi_agent_workflows import (
    AegisMultiAgentWorkflow,
)
from aegis.orchestration.workflows import AegisAgentWorkflow


async def connect_temporal(settings: Settings) -> Client:
    """Create a connection to the Temporal server."""

    return await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )


async def submit_agent_task(
    client: Client,
    user_input: str,
    settings: Settings,
) -> AgentTaskResult:
    """Submit a single-agent task and wait for its result."""

    if not user_input.strip():
        raise ValueError("User input cannot be empty.")

    return await client.execute_workflow(
        AegisAgentWorkflow.run,
        user_input,
        id=f"aegis-agent-{uuid4()}",
        task_queue=settings.temporal_task_queue,
    )


async def submit_multi_agent_task(
    client: Client,
    assignment: AgentTaskAssignment,
    settings: Settings,
) -> MultiAgentTaskResult:
    """Submit a validated multi-agent assignment to Temporal."""

    task_input = MultiAgentTaskInput(
        assignment_id=str(assignment.assignment_id),
        agent_id=assignment.agent_id,
        objective=assignment.objective,
        required_capability=assignment.required_capability,
        tenant_id=str(assignment.tenant_id),
        principal_id=str(assignment.principal_id),
    )

    return await client.execute_workflow(
        AegisMultiAgentWorkflow.run,
        task_input,
        id=f"aegis-multi-agent-{assignment.assignment_id}",
        task_queue=settings.temporal_task_queue,
    )
