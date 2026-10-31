"""Wires the long-lived components together (one instance per application)."""
from dataclasses import dataclass
from typing import Optional

import httpx

from app.ai.ollama_gemma import OllamaGemmaProvider
from app.ai.provider import AIProvider
from app.core.config import Settings
from app.engine.event_bus import EventBus
from app.engine.orchestrator import Orchestrator
from app.engine.runner import ExperimentRunner
from app.engine.state_manager import StateManager
from app.engine.traffic import TrafficClient
from app.proxy.gateway import ProxyGateway
from app.proxy.rules import RuleRegistry


@dataclass
class Container:
    settings: Settings
    registry: RuleRegistry
    bus: EventBus
    http: httpx.AsyncClient
    gateway: ProxyGateway
    orchestrator: Orchestrator
    ai_provider: AIProvider


def build_container(settings: Settings, http: Optional[httpx.AsyncClient] = None,
                    ai_provider: Optional[AIProvider] = None) -> Container:
    http = http or httpx.AsyncClient(limits=httpx.Limits(max_connections=50))
    registry, bus = RuleRegistry(), EventBus()
    gateway = ProxyGateway(registry, http, settings.proxy_timeout_s)
    runner = ExperimentRunner(settings, registry, bus, TrafficClient(gateway), http)
    return Container(settings, registry, bus, http, gateway, Orchestrator(runner, registry, StateManager()),
                     ai_provider or OllamaGemmaProvider(settings))
