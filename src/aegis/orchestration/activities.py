from temporalio import activity

from aegis.agent.graph import build_agent_graph
from aegis.core.config import Settings
from aegis.orchestration.contracts import AgentTaskResult
from aegis.providers.runtime import ModelRuntime


class AgentActivities:
    """Temporal activities that execute the Aegis agent."""

    def __init__(self, settings: Settings) -> None:
        model_runtime = ModelRuntime.from_settings(
            settings,
            enable_retries=False,
        )

        self._agent_graph = build_agent_graph(
            model_runtime=model_runtime,
            settings=settings,
        )

    @activity.defn(name="run_agent_task")
    async def run_agent_task(
        self,
        user_input: str,
    ) -> AgentTaskResult:
        """Execute an agent task through the LangGraph runtime."""

        result = await self._agent_graph.ainvoke(
            {
                "user_input": user_input,
                "max_iterations": 8,
            }
        )

        return AgentTaskResult(
            task_status=result.get("task_status", "failed"),
            plan=result.get("plan", []),
            current_step=result.get("current_step", 0),
            final_response=result.get("final_response"),
            error=result.get("error"),
        )
