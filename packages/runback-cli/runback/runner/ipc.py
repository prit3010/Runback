"""Unix-socket JSON IPC server for the runner daemon."""
from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anyio
from anyio.abc import SocketStream


@dataclass
class IpcRequest:
    action: str
    request_id: str
    body: dict[str, Any]


HandlerFn = Callable[[IpcRequest], Awaitable[dict[str, Any]] | dict[str, Any]]


class IpcServer:
    def __init__(self, *, socket_path: Path, handler: HandlerFn) -> None:
        self.socket_path = socket_path
        self._handler = handler
        self._stop_event = anyio.Event()

    async def serve_forever(self) -> None:
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        listener = await anyio.create_unix_listener(str(self.socket_path))
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(listener.serve, self._handle_one, tg)
                await self._stop_event.wait()
                tg.cancel_scope.cancel()
        finally:
            try:
                await listener.aclose()
            except Exception:
                pass
            try:
                self.socket_path.unlink()
            except FileNotFoundError:
                pass

    async def stop(self) -> None:
        self._stop_event.set()
        await anyio.sleep(0)

    async def _handle_one(self, stream: SocketStream) -> None:
        try:
            data = b""
            while not data.endswith(b"\n"):
                chunk = await stream.receive(4096)
                if not chunk:
                    break
                data += chunk
            line = data.decode().strip()
            try:
                payload = json.loads(line) if line else {}
            except json.JSONDecodeError as exc:
                await self._send(
                    stream,
                    {
                        "ok": False,
                        "request_id": "",
                        "error": f"invalid JSON: {exc}",
                        "code": "bad_request",
                    },
                )
                return
            if not isinstance(payload, dict):
                await self._send(
                    stream,
                    {
                        "ok": False,
                        "request_id": "",
                        "error": "request must be object",
                        "code": "bad_request",
                    },
                )
                return
            action = str(payload.get("action") or "")
            request_id = str(payload.get("request_id") or payload.get("replay_id") or "")
            if not action:
                await self._send(
                    stream,
                    {
                        "ok": False,
                        "request_id": request_id,
                        "error": "missing 'action'",
                        "code": "bad_request",
                    },
                )
                return
            req = IpcRequest(action=action, request_id=request_id, body=payload)
            try:
                response = self._handler(req)
                if inspect.isawaitable(response):
                    response = await response
            except Exception as exc:
                response = {
                    "ok": False,
                    "request_id": request_id,
                    "error": f"handler exception: {exc}",
                    "code": "internal",
                }
            stop_after_response = bool(response.pop("_stop_after_response", False))
            after_response = response.pop("_after_response", None)
            await self._send(stream, response)
            if after_response is not None:
                result = after_response()
                if inspect.isawaitable(result):
                    await result
            if stop_after_response:
                await self.stop()
        finally:
            try:
                await stream.aclose()
            except Exception:
                pass

    @staticmethod
    async def _send(stream: SocketStream, response: dict[str, Any]) -> None:
        await stream.send((json.dumps(response) + "\n").encode())
