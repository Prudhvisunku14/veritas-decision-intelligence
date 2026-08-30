from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    duckdb_path: str = "data/veritas_kpi.duckdb"

    # LLM provider: "template" | "anthropic" | "gemini"
    llm_provider: str = "template"

    # Anthropic (Claude)
    anthropic_api_key: str = ""
    anthropic_model: str = ""

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def root_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def db_path(self) -> Path:
        p = Path(self.duckdb_path)
        return p if p.is_absolute() else self.root_dir / p


settings = Settings()
