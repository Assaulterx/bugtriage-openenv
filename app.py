"""FastAPI server exposing the BugTriage environment via HTTP API.

Implements the HTTP entrypoint for containerized deployment.
Endpoints mirror OpenEnv semantics: POST /reset, POST /step, GET /state.
"""

import json
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from envs.bug_triage import BugTriageEnv
from envs.models import ActionModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.env = BugTriageEnv()
    yield

app = FastAPI(title="BugTriage OpenEnv", version="1.0.0", lifespan=lifespan)


class ResetRequest(BaseModel):
    task_id: Optional[str] = "bug_triage_easy"


class StepRequest(BaseModel):
    action_type: str
    value: str


@app.post("/reset")
async def reset(req: Optional[ResetRequest] = None):
    env: BugTriageEnv = app.state.env
    task_id = req.task_id if req else "bug_triage_easy"
    try:
        obs = env.reset(task_id)
        return {"observation": obs.model_dump(), "task_id": task_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step")
async def step(req: StepRequest):
    env: BugTriageEnv = app.state.env
    try:
        action = ActionModel(action_type=req.action_type, value=req.value)
        obs, reward = env.step(action)
        return {
            "observation": obs.model_dump(),
            "reward": reward.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
async def state():
    env: BugTriageEnv = app.state.env
    return {"state": env.state().model_dump()}


@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok", "service": "bug_triage_benchmark"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
