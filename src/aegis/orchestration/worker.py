from temporalio.client import Client
from temporalio.worker import Worker

from aegis.coordination.service import AgentExecutionService
from aegis.core.config import Settings
from aegis.orchestration.activities import AgentActivities
from aegis.orchestration.multi_agent_activities import MultiAgentActivities
from aegis.orchestration.multi_agent_workflows import AegisMultiAgentWorkflow
from aegis.orchestration.workflows import AegisAgentWorkflow


async def run_worker(
    settings: Settings,
    *,
    multi_agent_service: AgentExecutionService | None = None,
) -> None:
    """Connect to Temporal and start the configured Aegis worker."""

    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )

    agent_activities = AgentActivities(settings)

    workflows = [AegisAgentWorkflow]
    registered_activities = [agent_activities.run_agent_task]

    if multi_agent_service is not None:
        multi_agent_activities = MultiAgentActivities(multi_agent_service)

        workflows.append(AegisMultiAgentWorkflow)
        registered_activities.append(multi_agent_activities.execute_multi_agent_task)

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=workflows,
        activities=registered_activities,
    )

    await worker.run()
