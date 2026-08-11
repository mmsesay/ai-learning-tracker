"""Focused tests for config + Bearer auth (no full MCP handshake required)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from starlette.testclient import TestClient

# Ensure package imports resolve when pytest is run from PRJ-01-B/
ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_load_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("TRANSPORT", raising=False)
    monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)
    monkeypatch.setenv("WORKSPACE_ROOT", ".")

    from config import load_settings

    s = load_settings()
    assert s.port == 3000
    assert s.host == "0.0.0.0"
    assert s.api_key is None
    assert s.transport == "streamable-http"
    assert s.auth_enabled is False
    assert s.allowed_hosts == []
    assert s.binds_publicly is True


def test_load_settings_auth_and_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setenv("API_KEY", "secret-token")
    monkeypatch.setenv("TRANSPORT", "http")
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "demo.onrender.com, other.example.com")

    from config import load_settings

    s = load_settings()
    assert s.port == 8080
    assert s.api_key == "secret-token"
    assert s.auth_enabled is True
    assert s.transport == "streamable-http"
    assert s.allowed_hosts == ["demo.onrender.com", "other.example.com"]


def test_health_and_root_public(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("WORKSPACE_ROOT", str(ROOT))

    from config import load_settings
    from http_app import build_http_app
    from mcp.server import MCPServer

    mcp = MCPServer("devassist-test-public")
    app = build_http_app(mcp, load_settings())
    # Lifespan starts the Streamable HTTP session manager task group.
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

        r = client.get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "DevAssist"
        assert body["mcp_endpoint"] == "/mcp"


def test_mcp_requires_bearer_when_api_key_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("WORKSPACE_ROOT", str(ROOT))

    from config import load_settings
    from http_app import build_http_app
    from mcp.server import MCPServer

    mcp = MCPServer("devassist-test-auth")
    app = build_http_app(mcp, load_settings())
    with TestClient(app) as client:
        denied = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        assert denied.status_code == 401

        bad = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"Authorization": "Bearer wrong"},
        )
        assert bad.status_code == 401

        ok = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"},
                },
            },
            headers={
                "Authorization": "Bearer test-key",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
        )
        assert ok.status_code != 401
