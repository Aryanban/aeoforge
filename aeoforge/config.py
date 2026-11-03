"""Configuration settings for AEOForge using Pydantic Settings."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Meta AI / Meta Model API Configuration
    meta_model_api_key: Optional[str] = None
    meta_model_name: str = "meta/llama-3.2-11b-vision-instruct"
    meta_model_api_base: str = "https://api.meta.ai/v1"

    # Local Llama Stack Endpoint
    llama_stack_endpoint: str = "http://localhost:5001"
    use_local_llama: bool = False

    # Server settings
    aeoforge_host: str = "0.0.0.0"
    aeoforge_port: int = 8000
    aeoforge_env: str = "development"
    debug: bool = False

    # Playwright & Browser Settings
    playwright_headless: bool = True
    playwright_timeout_ms: int = 30000
    playwright_fast_route_filter: bool = True

    # Cache & File Paths
    aeoforge_cache_dir: str = ".cache/aeoforge"
    aeoforge_db_path: str = "aeoforge.db"


# Singleton instance
settings = Settings()
