from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/aviva_claims",
        description="PostgreSQL database connection URL",
    )

    chroma_url: str = Field(
        default="http://localhost:8001",
        description="ChromaDB server URL",
    )

    llm_provider: str = Field(
        default="openai",
        description="LLM provider (openai, anthropic, azure)",
    )

    llm_api_key: str = Field(
        default="",
        description="API key for LLM provider",
    )

    llm_model: str = Field(
        default="nvidia/nemotron-3-nano-30b-a3b:free",
        description="LLM model name (default: nvidia/nemotron-3-nano-30b-a3b:free)",
    )

    embedding_model: str = Field(
        default="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        description="Embedding model name (default: nvidia/llama-nemotron-embed-vl-1b-v2:free)",
    )

    llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="Base URL for LLM API (defaults to OpenRouter)",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    app_host: str = Field(
        default="0.0.0.0",
        description="Application host",
    )

    app_port: int = Field(
        default=8000,
        description="Application port",
    )

    enable_raw_logging: bool = Field(
        default=False,
        description="Whether to enable raw content logging (DANGER - for debugging only)",
    )

    def model_post_init(self, __context) -> None:
        if self.enable_raw_logging:
            raise ValueError(
                "SECURITY VIOLATION: enable_raw_logging is True. "
                "This would log raw email content and violate privacy requirements. "
                "This configuration is not allowed in production."
            )


settings = Settings()
