"""Central, validated application configuration (environment driven)."""
import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parents[3]


def _read_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs without overriding real environment variables."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    app_name: str = "ChaosButton"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///./chaosbutton.db"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout: int = Field(90, ge=5)
    # Hard safety limits: the frontend can never exceed these.
    max_experiment_duration: int = Field(120, ge=1)
    max_affected_requests: int = Field(100, ge=1)
    max_injected_delay_ms: int = Field(5000, ge=1)
    max_concurrency: int = Field(5, ge=1)
    max_baseline_requests: int = Field(50, ge=1)
    recovery_probe_count: int = 15
    recovery_probe_interval_ms: int = 300
    proxy_timeout_s: float = 10.0
    default_target_host: str = "127.0.0.1"
    allowed_remote_hosts: list[str] = []
    upstream_url: str = "http://127.0.0.1:9100"
    cors_origins: list[str] = ["http://localhost:5173"]

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ.get
        return cls(
            app_name=env("APP_NAME", "ChaosButton"),
            app_env=env("APP_ENV", "development"),
            app_host=env("APP_HOST", "127.0.0.1"),
            app_port=int(env("APP_PORT", "8000")),
            database_url=env("DATABASE_URL", "sqlite:///./chaosbutton.db"),
            ollama_base_url=env("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=env("OLLAMA_MODEL", "gemma3:4b"),
            ollama_timeout=int(env("OLLAMA_TIMEOUT", "90")),
            max_experiment_duration=int(env("MAX_EXPERIMENT_DURATION", "120")),
            max_affected_requests=int(env("MAX_AFFECTED_REQUESTS", "100")),
            max_injected_delay_ms=int(env("MAX_INJECTED_DELAY_MS", "5000")),
            max_concurrency=int(env("MAX_CONCURRENCY", "5")),
            max_baseline_requests=int(env("MAX_BASELINE_REQUESTS", "50")),
            default_target_host=env("DEFAULT_TARGET_HOST", "127.0.0.1"),
            allowed_remote_hosts=_csv(env("ALLOWED_REMOTE_HOSTS", "")),
            upstream_url=env("UPSTREAM_URL", "http://127.0.0.1:9100"),
            cors_origins=_csv(env("CORS_ORIGINS", "http://localhost:5173")),
        )

    def public_dict(self) -> dict:
        """Non-secret configuration safe to expose through the API."""
        return {
            "app_name": self.app_name,
            "app_env": self.app_env,
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "limits": {
                "max_experiment_duration": self.max_experiment_duration,
                "max_affected_requests": self.max_affected_requests,
                "max_injected_delay_ms": self.max_injected_delay_ms,
                "max_concurrency": self.max_concurrency,
                "max_baseline_requests": self.max_baseline_requests,
            },
            "allowed_remote_hosts": self.allowed_remote_hosts,
            "upstream_url": self.upstream_url,
        }


@lru_cache
def get_settings() -> Settings:
    _read_dotenv(Path.cwd() / ".env")
    _read_dotenv(_ROOT / ".env")
    return Settings.from_env()
