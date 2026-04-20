import asyncio
import time
from typing import Any, Callable, Coroutine

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.heal_agent import HealAgent
from app.agents.infra_agent import InfraAgent
from app.agents.pipeline_agent import PipelineAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

EventCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class AgentOrchestrator:
    def __init__(self) -> None:
        self._agents: dict[str, type[BaseAgent]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._agents["infra"] = InfraAgent
        self._agents["pipeline"] = PipelineAgent
        self._agents["heal"] = HealAgent

    def register_agent(self, agent_type: str, agent_class: type[BaseAgent]) -> None:
        self._agents[agent_type] = agent_class

    def get_agent(self, agent_type: str) -> BaseAgent:
        agent_class = self._agents.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(self._agents.keys())}")
        return agent_class()

    async def run_single(
        self,
        agent_type: str,
        input_data: dict[str, Any],
        callback: EventCallback | None = None,
    ) -> AgentResult:
        agent = self.get_agent(agent_type)

        if callback:
            await callback({
                "type": "started",
                "agent_type": agent_type,
                "timestamp": time.time(),
            })

        if callback:
            await callback({
                "type": "thinking",
                "agent_type": agent_type,
                "message": f"Validating input for {agent_type} agent...",
                "timestamp": time.time(),
            })

        result = await agent.run(input_data)

        if callback:
            await callback({
                "type": "result",
                "agent_type": agent_type,
                "success": result.success,
                "execution_time_ms": result.execution_time_ms,
                "timestamp": time.time(),
            })

            await callback({
                "type": "completed",
                "agent_type": agent_type,
                "success": result.success,
                "timestamp": time.time(),
            })

        return result

    async def run_multi(
        self,
        agents_config: list[dict[str, Any]],
        mode: str = "sequential",
        callback: EventCallback | None = None,
    ) -> list[AgentResult]:
        if mode == "parallel":
            return await self._run_parallel(agents_config, callback)
        return await self._run_sequential(agents_config, callback)

    async def _run_sequential(
        self,
        agents_config: list[dict[str, Any]],
        callback: EventCallback | None = None,
    ) -> list[AgentResult]:
        results: list[AgentResult] = []
        previous_output: dict[str, Any] = {}

        for i, config in enumerate(agents_config):
            agent_type = config["agent_type"]
            input_data = config.get("input_data", {})

            if previous_output:
                input_data["previous_agent_output"] = previous_output

            if callback:
                await callback({
                    "type": "action",
                    "agent_type": agent_type,
                    "message": f"Running agent {i + 1}/{len(agents_config)}: {agent_type}",
                    "timestamp": time.time(),
                })

            result = await self.run_single(agent_type, input_data, callback)
            results.append(result)

            if result.success:
                previous_output = result.output
            else:
                logger.warning(
                    "sequential_agent_failed",
                    agent_type=agent_type,
                    step=i + 1,
                    error=result.error,
                )
                break

        return results

    async def _run_parallel(
        self,
        agents_config: list[dict[str, Any]],
        callback: EventCallback | None = None,
    ) -> list[AgentResult]:
        tasks = []
        for config in agents_config:
            agent_type = config["agent_type"]
            input_data = config.get("input_data", {})
            tasks.append(self.run_single(agent_type, input_data, callback))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results: list[AgentResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    AgentResult(
                        success=False,
                        output={"error": str(result)},
                        execution_time_ms=0,
                        agent_type=agents_config[i]["agent_type"],
                        error=str(result),
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def auto_diagnose(
        self,
        input_data: dict[str, Any],
        callback: EventCallback | None = None,
    ) -> dict[str, Any]:
        if callback:
            await callback({
                "type": "started",
                "agent_type": "orchestrator",
                "message": "Starting auto-diagnosis workflow: Heal -> Pipeline -> Infra",
                "timestamp": time.time(),
            })

        all_results: dict[str, Any] = {"steps": []}

        if callback:
            await callback({
                "type": "thinking",
                "agent_type": "orchestrator",
                "message": "Step 1: Running Heal Agent to diagnose errors...",
                "timestamp": time.time(),
            })

        heal_result = await self.run_single("heal", input_data, callback)
        all_results["steps"].append({
            "agent": "heal",
            "success": heal_result.success,
            "output": heal_result.output,
            "execution_time_ms": heal_result.execution_time_ms,
        })

        if heal_result.success and input_data.get("yaml_content"):
            if callback:
                await callback({
                    "type": "thinking",
                    "agent_type": "orchestrator",
                    "message": "Step 2: Running Pipeline Agent to analyze CI/CD...",
                    "timestamp": time.time(),
                })

            pipeline_input = {
                "action": "analyze",
                "yaml_content": input_data["yaml_content"],
                "platform": input_data.get("platform", "github_actions"),
            }
            pipeline_result = await self.run_single("pipeline", pipeline_input, callback)
            all_results["steps"].append({
                "agent": "pipeline",
                "success": pipeline_result.success,
                "output": pipeline_result.output,
                "execution_time_ms": pipeline_result.execution_time_ms,
            })

        if heal_result.success:
            diagnosis = heal_result.output.get("diagnosis", [])
            if any(d.get("category") in ("resource", "scheduling") for d in diagnosis):
                if callback:
                    await callback({
                        "type": "thinking",
                        "agent_type": "orchestrator",
                        "message": "Step 3: Running Infra Agent to suggest infrastructure fixes...",
                        "timestamp": time.time(),
                    })

                infra_input = {
                    "config_type": "kubernetes",
                    "app_description": f"Fix infrastructure for: {heal_result.output.get('summary', 'diagnosed issues')}",
                    "options": {"source": "auto-diagnose"},
                }
                infra_result = await self.run_single("infra", infra_input, callback)
                all_results["steps"].append({
                    "agent": "infra",
                    "success": infra_result.success,
                    "output": infra_result.output,
                    "execution_time_ms": infra_result.execution_time_ms,
                })

        total_time = sum(s["execution_time_ms"] for s in all_results["steps"])
        all_results["success"] = bool(all_results["steps"]) and all(
            step["success"] for step in all_results["steps"]
        )
        all_results["total_execution_time_ms"] = total_time
        all_results["agents_run"] = len(all_results["steps"])
        all_results["summary"] = self._build_diagnosis_summary(all_results["steps"])

        if callback:
            await callback({
                "type": "completed",
                "agent_type": "orchestrator",
                "message": f"Auto-diagnosis complete. Ran {len(all_results['steps'])} agents in {total_time}ms.",
                "timestamp": time.time(),
            })

        return all_results

    def _build_diagnosis_summary(self, steps: list[dict[str, Any]]) -> str:
        parts = []
        for step in steps:
            agent = step["agent"]
            if step["success"]:
                summary = step["output"].get("summary", "Completed successfully")
                parts.append(f"[{agent.upper()}] {summary}")
            else:
                error = step["output"].get("error", "Unknown error")
                parts.append(f"[{agent.upper()}] Failed: {error}")
        return " | ".join(parts)


orchestrator = AgentOrchestrator()
