"""HTTP helpers for DevAssist: public routes + optional Bearer auth on /mcp.

Keeps MCP tool registration in ``server.py``. This module only wraps the
Streamable HTTP Starlette app the official MCP SDK builds.
"""

from __future__ import annotations

import logging
import secrets
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from config import Settings

logger = logging.getLogger("devassist")

SERVICE_INFO = {
    "name": "DevAssist",
    "service": "devassist-mcp",
    "version": "0.2.0",
    "transport": "streamable-http",
    "mcp_endpoint": "/mcp",
    "tools": ["list_projects", "search_code", "git_summary"],
}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Require ``Authorization: Bearer <API_KEY>`` for MCP paths when configured.

    Public routes (``/``, ``/health``) stay open so load balancers and humans
    can probe the service without a token.
    """

    def __init__(self, app, api_key: str) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        path = request.url.path
        # MCP endpoint is /mcp and may include trailing slash or subpaths.
        if path == "/mcp" or path.startswith("/mcp/"):
            auth = request.headers.get("authorization", "")
            scheme, _, token = auth.partition(" ")
            # Constant-time compare when lengths match; never log the token.
            token_ok = False
            if scheme.lower() == "bearer" and token:
                try:
                    token_ok = secrets.compare_digest(token, self._api_key)
                except (TypeError, ValueError):
                    token_ok = False
            if not token_ok:
                logger.warning("Unauthorized MCP request from %s", request.client)
                return JSONResponse(
                    {"error": "unauthorized", "detail": "Valid Bearer token required"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return await call_next(request)


def register_public_routes(mcp) -> None:
    """Attach GET / and GET /health via MCPServer.custom_route (no MCP auth)."""

    @mcp.custom_route("/", methods=["GET"])
    async def root(_request: Request) -> Response:
        """Service information for humans and deploy dashboards."""
        return JSONResponse(
            {
                **SERVICE_INFO,
                "status": "ok",
                "docs": "See README.md — Remote MCP Server",
            }
        )

    @mcp.custom_route("/health", methods=["GET"])
    async def health(_request: Request) -> Response:
        """Liveness probe for Railway / load balancers."""
        return JSONResponse({"status": "healthy", "service": "devassist"})


def build_transport_security(settings: Settings):
    """Configure DNS rebinding protection per official MCP deploy guidance.

    - If ``MCP_ALLOWED_HOSTS`` is set: enable protection and allowlist those Hosts
      (correct for a known Railway public domain).
    - If unset on a public bind: disable protection. Official docs treat this as
      acceptable behind a reverse proxy that already controls the Host header
      (Railway's HTTPS edge). Prefer setting ``MCP_ALLOWED_HOSTS`` once the
      domain is known.
    """
    from mcp.server.transport_security import TransportSecuritySettings

    if settings.allowed_hosts:
        # Include both bare host and host:* so :443 / odd ports still match.
        hosts: list[str] = []
        for host in settings.allowed_hosts:
            hosts.append(host)
            if ":" not in host:
                hosts.append(f"{host}:*")
        logger.info("DNS rebinding protection ON; allowed_hosts=%s", hosts)
        return TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
        )

    logger.warning(
        "MCP_ALLOWED_HOSTS unset — DNS rebinding protection OFF "
        "(ok behind Railway's reverse proxy; set MCP_ALLOWED_HOSTS to your "
        "public domain when you have it)"
    )
    return TransportSecuritySettings(enable_dns_rebinding_protection=False)


def build_http_app(mcp, settings: Settings):
    """Build the Streamable HTTP Starlette app with optional API key middleware.

    Uses the official SDK path ``/mcp`` (Streamable HTTP, not legacy SSE).
    ``stateless_http=True`` keeps Railway / multi-instance deploys simple.
    """
    register_public_routes(mcp)

    app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        transport_security=build_transport_security(settings),
        host=settings.host,
    )

    if settings.auth_enabled:
        assert settings.api_key is not None
        app.add_middleware(BearerAuthMiddleware, api_key=settings.api_key)
        logger.info("API key auth enabled for /mcp")
    else:
        logger.warning(
            "API_KEY not set — /mcp is open (ok for local loopback, not for public URLs)"
        )

    return app
