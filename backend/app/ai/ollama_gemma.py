"""Gemma provider using the local Ollama HTTP API (no cloud key required)."""
import json
import logging
from typing import Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.ai.prompts import SYSTEM_PROMPT, build_analysis_prompt, build_validation_prompt
from app.ai.provider import (AIInvalidOutputError, AIModelMissingError, AIProvider, AIUnavailableError)
from app.ai.schemas import AIStatus, AnalysisResult, FixValidation
from app.core.config import Settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class OllamaGemmaProvider(AIProvider):
    def __init__(self, settings: Settings):
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._timeout = settings.ollama_timeout

    @property
    def model_name(self) -> str:
        return self._model

    async def status(self) -> AIStatus:
        pull = f"ollama pull {self._model}"
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self._base_url}/api/tags")
            response.raise_for_status()
        except (httpx.HTTPError, OSError):
            return AIStatus(provider="ollama", model=self._model, reachable=False, model_available=False,
                            message="Ollama is not reachable.", hint="Start it with `ollama serve`, then retry.")
        try:
            models = response.json().get("models", [])
        except (ValueError, AttributeError):
            return AIStatus(provider="ollama", model=self._model, reachable=True, model_available=False,
                            message="Ollama responded with an unreadable model list.",
                            hint="Check the Ollama service, then retry.")
        names = {str(m.get("name", "")) for m in models if isinstance(m, dict)}
        wanted = self._model.strip()
        available = wanted in names or f"{wanted}:latest" in names or wanted.split(":", 1)[0] in names
        return AIStatus(provider="ollama", model=self._model, reachable=True, model_available=available,
                        message="Gemma is ready." if available else f"Model '{self._model}' is not installed.",
                        hint=None if available else f"Run `{pull}` and retry.")

    async def generate_analysis(self, evidence: dict) -> AnalysisResult:
        prompt = build_analysis_prompt(evidence, evidence.get("code_context"))
        return await self._generate(prompt, AnalysisResult)

    async def generate_fix_validation(self, comparison: dict) -> FixValidation:
        return await self._generate(build_validation_prompt(comparison), FixValidation)

    async def _generate(self, prompt: str, schema: Type[T]) -> T:
        """Call Gemma with JSON-schema output; validate; retry once; then fail safely."""
        for attempt in (1, 2):
            raw = await self._chat(prompt, schema)
            try:
                return schema.model_validate_json(raw)
            except (ValidationError, json.JSONDecodeError, ValueError) as exc:
                logger.warning("Gemma output invalid (attempt %s): %s", attempt, type(exc).__name__)
                prompt += "\nYour previous reply was not valid for the schema. Reply with valid JSON only."
        raise AIInvalidOutputError("Gemma returned output that did not match the expected schema. "
                                   "Retry the analysis; a larger model tag may help.")

    async def _chat(self, prompt: str, schema: Type[BaseModel]) -> str:
        payload = {"model": self._model, "stream": False, "format": schema.model_json_schema(),
                   "options": {"temperature": 0.2},
                   "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt}]}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(f"{self._base_url}/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            raise AIUnavailableError("Gemma did not respond in time. Retry, or raise OLLAMA_TIMEOUT.") from exc
        except (httpx.HTTPError, OSError) as exc:
            raise AIUnavailableError("Ollama is not reachable. Start it with `ollama serve` and retry.") from exc
        if response.status_code == 404:
            raise AIModelMissingError(f"Model '{self._model}' is not installed. Run `ollama pull {self._model}`.")
        if response.status_code >= 400:
            raise AIUnavailableError(f"Ollama returned HTTP {response.status_code}.")
        try:
            content = response.json().get("message", {}).get("content", "")
        except (ValueError, AttributeError) as exc:
            raise AIUnavailableError("Ollama returned an unreadable response. Retry the analysis.") from exc
        if not isinstance(content, str) or not content.strip():
            raise AIUnavailableError("Ollama returned an empty response. Check that the selected model is ready.")
        return content
