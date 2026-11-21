from temporalio.client import Client
from temporalio.worker import Worker

from aegis.core.config import Settings
from aegis.orchestration.activities import AgentActivities
from aegis.orchestration.workflows import AegisAgentWorkflow


async def run_worker(settings: Settings) -> None:
    """Connect to Temporal and start the Aegis worker."""

    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )

    activities = AgentActivities(settings)

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[AegisAgentWorkflow],
        activities=[activities.run_agent_task],
    )

    await worker.run()
