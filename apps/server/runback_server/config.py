"""Runtime configuration for the Runback backend."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RUNBACK_", env_file=".env", extra="ignore")

    db_path: Path = Field(default=Path(".runback/runback.db"))
    runtime_root: Path = Field(default=Path(".runback"))
    server_host: str = Field(default="127.0.0.1")
    server_port: int = Field(default=8000)
    runner_socket_path: Path = Field(default=Path("/tmp/runback-runner.sock"))


def get_settings() -> Settings:
    return Settings()
