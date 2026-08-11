"""HTTP helpers for DevAssist: public routes + optional Bearer auth on /mcp.

Keeps MCP tool registration in ``server.py``. This module only wraps the
Streamable HTTP Starlette app the official MCP SDK builds.
"""

from __future__ import annotations

import logging
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
            expected = f"Bearer {self._api_key}"
            if auth != expected:
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


def build_http_app(mcp, settings: Settings):
    """Build the Streamable HTTP Starlette app with optional API key middleware.

    Uses the official SDK path ``/mcp`` (Streamable HTTP, not legacy SSE).
    ``stateless_http=True`` keeps Railway / multi-instance deploys simple.
    DNS-rebinding protection is off for public Host headers (Railway domains);
    ``API_KEY`` is the access control when set.
    """
    from mcp.server.transport_security import TransportSecuritySettings

    register_public_routes(mcp)

    app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        # Public deploy: Host is the Railway domain, not 127.0.0.1.
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=False
        ),
        host=settings.host,
    )

    if settings.auth_enabled:
        assert settings.api_key is not None
        app.add_middleware(BearerAuthMiddleware, api_key=settings.api_key)
        logger.info("API key auth enabled for /mcp")
    else:
        logger.warning(
            "API_KEY not set — /mcp is open (ok for local dev, not for public URLs)"
        )

    return app
