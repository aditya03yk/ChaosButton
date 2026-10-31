"""AI provider interface and error types."""
from abc import ABC, abstractmethod

from app.ai.schemas import AIStatus, AnalysisResult, FixValidation
from app.core.errors import AppError


class AIError(AppError):
    status_code, code = 503, "ai_error"


class AIUnavailableError(AIError):
    code = "ai_unavailable"


class AIModelMissingError(AIError):
    code = "ai_model_missing"


class AIInvalidOutputError(AIError):
    status_code, code = 502, "ai_invalid_output"


class AIProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    async def status(self) -> AIStatus: ...

    @abstractmethod
    async def generate_analysis(self, evidence: dict) -> AnalysisResult: ...

    @abstractmethod
    async def generate_fix_validation(self, comparison: dict) -> FixValidation: ...
