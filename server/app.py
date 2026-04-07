"""Thin server entry point for OpenEnv multi-mode deployment.

Re-exports the FastAPI app from the project root so the [project.scripts]
entry point resolves correctly without duplicating any environment logic.
"""

import os
import sys

# Ensure the project root is on the path so envs/ and app can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: F401, E402


def main():
    """CLI entry point for bugtriage-server."""
    import uvicorn
    from app import app as application

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(application, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()


# Expose `app` at module level so openenv validate can discover it
__all__ = ["app", "main"]
