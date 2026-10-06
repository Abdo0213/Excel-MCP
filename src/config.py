"""Application configuration and settings schema using Pydantic."""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Pydantic schema for strongly typed environment configuration."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ollama / LLM configuration
    ollama_model: str = Field(default="gpt-oss:120b", alias="OLLAMA_MODEL")
    ollama_api_key: str = Field(default="dummy", alias="OLLAMA_API_KEY")
    ollama_base_url: str = Field(default="https://ollama.com/v1", alias="OLLAMA_BASE_URL")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")

    # Project directories
    project_root: Path = PROJECT_ROOT
    inputs_dir: Path = PROJECT_ROOT / "inputs"
    outputs_dir: Path = PROJECT_ROOT / "outputs"

    def ensure_directories(self) -> None:
        """Ensure input and output directories exist."""
        self.inputs_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)


# Global settings singleton instance
settings = Settings()
settings.ensure_directories()
