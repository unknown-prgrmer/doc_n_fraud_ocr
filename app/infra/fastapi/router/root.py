"""Root endpoint handler."""

from fastapi import Request
from fastapi.responses import RedirectResponse


async def root(req: Request) -> RedirectResponse:
    """Simple redirection to '/docs' taking root_path into account.

    Args:
        req: a request made to the root path.

    Returns:
        a redirection to the docs route.
    """
    root_path = req.scope.get("root_path", "").rstrip("/")
    return RedirectResponse(root_path + "/docs")
