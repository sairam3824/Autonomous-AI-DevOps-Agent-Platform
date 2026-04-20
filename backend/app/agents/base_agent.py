import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class AgentResult:
    success: bool
    output: dict[str, Any]
    execution_time_ms: int
    agent_type: str
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class BaseAgent(ABC):
    agent_type: str = "base"

    def __init__(self) -> None:
        self._ollama_url = settings.OLLAMA_URL
        self._model = settings.OLLAMA_MODEL
        self._code_model = settings.OLLAMA_CODE_MODEL

    @abstractmethod
    async def validate_input(self, input_data: dict[str, Any]) -> tuple[bool, str]:
        ...

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def _rule_based_fallback(self, input_data: dict[str, Any]) -> dict[str, Any]:
        ...

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        start = time.perf_counter()
        try:
            valid, msg = await self.validate_input(input_data)
            if not valid:
                return AgentResult(
                    success=False,
                    output={"error": msg},
                    execution_time_ms=int((time.perf_counter() - start) * 1000),
                    agent_type=self.agent_type,
                    error=msg,
                )

            output = await self.execute(input_data)
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.info("agent_run_complete", agent_type=self.agent_type, elapsed_ms=elapsed)
            return AgentResult(
                success=True,
                output=output,
                execution_time_ms=elapsed,
                agent_type=self.agent_type,
            )
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.error("agent_run_failed", agent_type=self.agent_type, error=str(e))
            return AgentResult(
                success=False,
                output={"error": str(e)},
                execution_time_ms=elapsed,
                agent_type=self.agent_type,
                error=str(e),
            )

    async def _call_ollama(self, prompt: str, model: str | None = None, system: str | None = None) -> str:
        target_model = model or self._model
        payload: dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{self._ollama_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")
        except Exception as e:
            logger.warning("ollama_call_failed", model=target_model, error=str(e))
            return ""

    async def _call_ollama_stream(
        self, prompt: str, model: str | None = None, system: str | None = None
    ) -> AsyncGenerator[str, None]:
        target_model = model or self._model
        payload: dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "stream": True,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST", f"{self._ollama_url}/api/generate", json=payload
                ) as resp:
                    resp.raise_for_status()
                    import json

                    async for line in resp.aiter_lines():
                        if line.strip():
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done", False):
                                break
        except Exception as e:
            logger.warning("ollama_stream_failed", model=target_model, error=str(e))
            yield f"[LLM unavailable: {e}]"

    async def _is_ollama_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._ollama_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
