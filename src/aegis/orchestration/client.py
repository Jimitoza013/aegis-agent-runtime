from uuid import uuid4

from temporalio.client import Client

from aegis.core.config import Settings
from aegis.orchestration.contracts import AgentTaskResult
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
    """Submit an agent task and wait for its result."""

    if not user_input.strip():
        raise ValueError("User input cannot be empty.")

    return await client.execute_workflow(
        AegisAgentWorkflow.run,
        user_input,
        id=f"aegis-agent-{uuid4()}",
        task_queue=settings.temporal_task_queue,
    )
