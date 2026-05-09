"""Long-lived runner daemon."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anyio
import ulid

from runback.config import RunnerSettings, get_settings, hooks_bin_dir, workspace_dir
from runback.http import BackendClient, BackendError
from runback.runner.boundary_watcher import BoundaryWatcher
from runback.runner.checkpoint import CheckpointSpec, create_checkpoint, restore_checkpoint
from runback.runner.hooks_setup import setup_hooks
from runback.runner.ipc import IpcRequest, IpcServer
from runback.runner.spawn import ClaudeSpawnSpec, spawn_claude
from runback.runner.worktree import create_worktree


@dataclass
class ActiveRun:
    run_id: str
    branch_id: str
    workspace_path: Path
    repo_path: Path
    proc: subprocess.Popen | None
    next_checkpoint_n: int = 1


@dataclass
class RunnerDaemon:
    socket_path: Path | None = None
    settings: RunnerSettings = field(default_factory=get_settings)
    _server: IpcServer | None = field(init=False, default=None)
    _active: dict[str, ActiveRun] = field(init=False, default_factory=dict)
    _watcher_tg: anyio.abc.TaskGroup | None = field(init=False, default=None)
    _stop_event: anyio.Event = field(init=False, default_factory=anyio.Event)

    def __post_init__(self) -> None:
        if self.socket_path is None:
            self.socket_path = self.settings.runner_socket

    async def serve_forever(self) -> None:
        assert self.socket_path is not None
        self._server = IpcServer(socket_path=self.socket_path, handler=self._dispatch)
        async with anyio.create_task_group() as tg:
            self._watcher_tg = tg
            tg.start_soon(self._server.serve_forever)
            await self._stop_event.wait()
            tg.cancel_scope.cancel()

    async def stop(self) -> None:
        for active in list(self._active.values()):
            self._terminate(active.proc)
        if self._server is not None:
            await self._server.stop()
        self._stop_event.set()

    async def _dispatch(self, req: IpcRequest) -> dict[str, Any]:
        if req.action == "start_run":
            return await self._start_run(req)
        if req.action == "replay":
            return await self._replay(req)
        if req.action == "stop":
            return {
                "ok": True,
                "request_id": req.request_id,
                "_after_response": self._finish_stop,
                "_stop_after_response": True,
            }
        return {
            "ok": False,
            "request_id": req.request_id,
            "error": f"unknown action: {req.action}",
            "code": "bad_request",
        }

    async def _start_run(self, req: IpcRequest) -> dict[str, Any]:
        prompt = req.body.get("prompt") or ""
        repo_path = Path(req.body.get("repo_path") or "").resolve()
        if not prompt or not repo_path.exists():
            return {
                "ok": False,
                "request_id": req.request_id,
                "error": "prompt and repo_path required",
                "code": "bad_request",
            }

        run_id = f"run_{ulid.new().str.lower()}"
        branch_id = f"branch_{ulid.new().str.lower()}"
        workspace = workspace_dir(run_id, self.settings)

        try:
            create_worktree(repo_root=repo_path, worktree_path=workspace, base_ref="HEAD")
            bin_dir = hooks_bin_dir(self.settings)
            forwarder = setup_hooks(workspace=workspace, runback_bin_dir=bin_dir)
            client = BackendClient(self.settings)
            client.create_run(
                run_id=run_id,
                prompt=prompt,
                repo_path=str(repo_path),
                workspace_path=str(workspace),
                base_branch_id=branch_id,
            )
            create_checkpoint(
                CheckpointSpec(run_id, branch_id, 0, "run start", repo_path, workspace, None),
                client=client,
            )
            proc = spawn_claude(
                ClaudeSpawnSpec(
                    run_id=run_id,
                    prompt=prompt,
                    workspace_path=workspace,
                    hook_forwarder_path=forwarder,
                    runback_bin_dir=bin_dir,
                    extra_env={"RUNBACK_BRANCH_ID": branch_id},
                )
            )
        except (BackendError, FileNotFoundError, Exception) as exc:
            return {
                "ok": False,
                "request_id": req.request_id,
                "error": str(exc),
                "code": "runtime",
            }

        active = ActiveRun(run_id, branch_id, workspace, repo_path, proc)
        self._active[run_id] = active
        watcher = BoundaryWatcher(
            run_id=run_id,
            client=client,
            create_checkpoint_fn=lambda *, run_id, label, node_id: create_checkpoint(
                CheckpointSpec(
                    run_id,
                    active.branch_id,
                    self._next_checkpoint_n(active),
                    label,
                    active.repo_path,
                    active.workspace_path,
                    node_id,
                ),
                client=client,
            ),
        )
        if self._watcher_tg is not None:
            self._watcher_tg.start_soon(self._watch_loop, watcher, active)
        return {"ok": True, "request_id": req.request_id, "run_id": run_id, "pid": proc.pid}

    async def _watch_loop(self, watcher: BoundaryWatcher, active: ActiveRun) -> None:
        while active.proc is not None and active.proc.poll() is None:
            try:
                await anyio.to_thread.run_sync(watcher.tick)
            except Exception:
                pass
            await anyio.sleep(0.5)

    def _next_checkpoint_n(self, active: ActiveRun) -> int:
        n = active.next_checkpoint_n
        active.next_checkpoint_n += 1
        return n

    async def _replay(self, req: IpcRequest) -> dict[str, Any]:
        body = req.body
        run_id = body.get("run_id")
        checkpoint_ref = body.get("git_ref")
        raw_workspace = body.get("workspace_path")

        active = self._active.get(str(run_id)) if run_id else None
        if not checkpoint_ref:
            checkpoint_ref = f"refs/runback/{run_id}/0"
        if raw_workspace:
            workspace = Path(str(raw_workspace))
        elif active is not None:
            workspace = active.workspace_path
        else:
            workspace = None
        if not run_id or not workspace:
            return {
                "ok": False,
                "request_id": req.request_id,
                "error": "run_id and workspace_path required",
                "code": "bad_request",
            }

        if active is not None:
            self._terminate(active.proc)
        try:
            restore_checkpoint(workspace_path=workspace, ref_name=str(checkpoint_ref))
            bin_dir = hooks_bin_dir(self.settings)
            forwarder = setup_hooks(workspace=workspace, runback_bin_dir=bin_dir)
            branch_id = str(body.get("new_branch_id") or f"branch_{ulid.new().str.lower()}")
            prompt = str(body.get("resume_prompt") or "")
            proc = spawn_claude(
                ClaudeSpawnSpec(
                    run_id=str(run_id),
                    prompt=prompt,
                    workspace_path=workspace,
                    hook_forwarder_path=forwarder,
                    runback_bin_dir=bin_dir,
                    extra_env={"RUNBACK_BRANCH_ID": branch_id},
                )
            )
        except (FileNotFoundError, Exception) as exc:
            return {
                "ok": False,
                "request_id": req.request_id,
                "error": str(exc),
                "code": "runtime",
            }
        if active is None:
            self._active[str(run_id)] = ActiveRun(
                str(run_id), branch_id, workspace, workspace, proc
            )
        else:
            active.branch_id = branch_id
            active.proc = proc
        return {"ok": True, "request_id": req.request_id, "pid": proc.pid}

    @staticmethod
    def _terminate(proc: subprocess.Popen | None) -> None:
        if proc is None or proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

    def _finish_stop(self) -> None:
        for active in list(self._active.values()):
            self._terminate(active.proc)
        self._stop_event.set()
