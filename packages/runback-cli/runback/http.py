"""Typed httpx client for the Runback backend."""
from __future__ import annotations

from typing import Any

import httpx

from runback.config import RunnerSettings, get_settings


class BackendError(RuntimeError):
    """Backend request failed."""


class BackendClient:
    def __init__(self, settings: RunnerSettings | None = None, client: httpx.Client | None = None):
        self._settings = settings or get_settings()
        self._client = client or httpx.Client(base_url=self._settings.backend_url, timeout=10.0)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BackendClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def health(self) -> bool:
        try:
            response = self._client.get("/openapi.json", timeout=2.0)
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    def create_run(
        self,
        *,
        run_id: str,
        prompt: str,
        repo_path: str,
        workspace_path: str,
        base_branch_id: str,
    ) -> dict[str, Any]:
        response = self._client.post(
            "/api/runs",
            json={
                "id": run_id,
                "run_kind": "ad_hoc",
                "status": "running",
                "original_prompt": prompt,
                "repo_path": repo_path,
                "workspace_path": workspace_path,
                "root_branch_id": base_branch_id,
                "current_branch_id": base_branch_id,
            },
        )
        if response.status_code not in (200, 201):
            raise BackendError(f"POST /api/runs -> {response.status_code} {response.text}")
        return response.json()

    def post_checkpoint(self, *, run_id: str, checkpoint: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(f"/api/runs/{run_id}/checkpoints", json=checkpoint)
        if response.status_code not in (200, 201):
            raise BackendError(
                f"POST /api/runs/{run_id}/checkpoints -> "
                f"{response.status_code} {response.text}"
            )
        return response.json()

    def get_run_dag(self, run_id: str) -> dict[str, Any]:
        response = self._client.get(f"/api/runs/{run_id}/dag")
        if response.status_code != 200:
            raise BackendError(
                f"GET /api/runs/{run_id}/dag -> {response.status_code} {response.text}"
            )
        return response.json()

    def heartbeat(self, *, runner_id: str, version: str, current_run_id: str | None = None) -> None:
        response = self._client.post(
            "/api/runners/heartbeat",
            json={
                "runner_id": runner_id,
                "status": "online",
                "current_run_id": current_run_id,
                "version": version,
                "claude_code_available": True,
            },
        )
        if response.status_code not in (200, 202):
            raise BackendError(f"heartbeat -> {response.status_code} {response.text}")
