import os
import logging
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel

from .agent import HubClient

app = FastAPI(title="Kiro Swarm API")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kiro-api")

def get_client() -> HubClient:
    host = os.environ.get("KIRO_SWARM_HOST", "127.0.0.1")
    port = int(os.environ.get("KIRO_SWARM_PORT", "8765"))
    client = HubClient(host, port)
    # If API is running with a key, use it for the client connection
    client.auth_token = os.environ.get("KIRO_SWARM_KEY")
    return client

class TaskRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    type: str = "chat"

class TaskResponse(BaseModel):
    task_id: int

async def verify_token(x_kiro_key: Optional[str] = Header(None)):
    server_key = os.environ.get("KIRO_SWARM_KEY")
    if server_key:
        if x_kiro_key != server_key:
            raise HTTPException(status_code=403, detail="Invalid KIRO_SWARM_KEY")
    return x_kiro_key

@app.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskRequest, token: str = Depends(verify_token)):
    client = get_client()
    try:
        resp = client.call("enqueue", {
            "prompt": task.prompt,
            "system_prompt": task.system_prompt,
            "type": task.type
        })
        return TaskResponse(task_id=resp["task_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 50, token: str = Depends(verify_token)):
    client = get_client()
    try:
        resp = client.call("list", {"status": status, "limit": limit})
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats(token: str = Depends(verify_token)):
    client = get_client()
    try:
        resp = client.call("stats")
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_api(host: str, port: int):
    import uvicorn
    uvicorn.run(app, host=host, port=port)
