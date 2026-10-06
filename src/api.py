"""FastAPI backend serving the HTML/CSS/JS frontend and agent API."""
import json
import sys
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings  # noqa: E402
from src.agent.excel_agent import ExcelAgent  # noqa: E402

app = FastAPI(title="SheetPT")

MODELS = [
    "gpt-oss:120b",
    "gpt-oss:20b",
    "gemma4:31b",
]

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class RunRequest(BaseModel):
    prompt: str
    model: str = settings.ollama_model
    max_retries: int = settings.max_retries


def _list_dir(path: Path):
    if path.exists():
        return sorted(f.name for f in path.iterdir() if not f.name.startswith("."))
    return []


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/models")
def list_models():
    return {"models": MODELS, "default": settings.ollama_model}


@app.get("/api/files")
def list_files():
    settings.ensure_directories()
    return {
        "inputs": _list_dir(settings.inputs_dir),
        "outputs": _list_dir(settings.outputs_dir),
    }


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    settings.ensure_directories()
    dest = settings.inputs_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)
    return {"saved": f"inputs/{file.filename}", "size": len(content)}


@app.post("/api/run")
def run_task(req: RunRequest):
    agent = ExcelAgent(model=req.model, max_retries=req.max_retries)

    def event_stream():
        for event in agent.run_step_by_step(req.prompt):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
