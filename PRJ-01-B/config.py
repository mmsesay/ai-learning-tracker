"""Runtime configuration for DevAssist (env-driven, no secrets in code).

Used by the HTTP / Streamable HTTP entrypoint. Tool modules still read
WORKSPACE_ROOT directly so their behavior stays unchanged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    """Process settings for serving DevAssist."""

    host: str
    port: int
    api_key: str | None
    transport: str
    workspace_root: str

    @property
    def auth_enabled(self) -> bool:
        """True when API_KEY is set (Bearer required on /mcp)."""
        return bool(self.api_key)


def load_settings() -> Settings:
    """Load settings from the environment.

    PORT defaults to 3000 (Railway injects PORT in production).
    HOST defaults to 0.0.0.0 so containers / Railway accept external traffic.
    TRANSPORT is ``streamable-http`` (remote) or ``stdio`` (local Cursor).
    """
    port_raw = _env("PORT", "3000") or "3000"
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError(f"PORT must be an integer, got {port_raw!r}") from exc

    api_key = _env("API_KEY") or None
    transport = (_env("TRANSPORT", "streamable-http") or "streamable-http").lower()
    if transport in {"http", "streamable_http", "streamable-http"}:
        transport = "streamable-http"
    elif transport != "stdio":
        raise ValueError(
            f"TRANSPORT must be 'streamable-http' or 'stdio', got {transport!r}"
        )

    return Settings(
        host=_env("HOST", "0.0.0.0") or "0.0.0.0",
        port=port,
        api_key=api_key,
        transport=transport,
        workspace_root=_env("WORKSPACE_ROOT", ".") or ".",
    )
