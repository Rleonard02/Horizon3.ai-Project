# api_service/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Dict
import asyncio
import os
from pathlib import Path

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust for your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for service statuses
service_statuses: Dict[str, Dict] = {}

# List of connected WebSocket clients
clients: List[WebSocket] = []

# Shared output directory (mounted in docker-compose.yml)
shared_output_dir = "/shared/output"

# Allowed file extensions for security
ALLOWED_EXTENSIONS = {'.txt', '.md'}

@app.post("/update_status")
async def update_status(data: Dict):
    service = data.get("service")
    if service:
        service_statuses[service] = data
        # Notify all connected clients
        await notify_clients()
    return {"message": "Status updated"}

@app.get("/status")
def get_status():
    return {"services": list(service_statuses.values())}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

async def notify_clients():
    data = {"services": list(service_statuses.values())}
    for client in clients:
        try:
            await client.send_json(data)
        except Exception:
            clients.remove(client)

@app.get("/output_files")
def list_output_files():
    try:
        files = os.listdir(shared_output_dir)
        # Filter files by allowed extensions
        files = [f for f in files if os.path.splitext(f)[1] in ALLOWED_EXTENSIONS]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/output_files/{filename}")
def get_output_file(filename: str):
    safe_filename = os.path.basename(filename)
    # Check if the file extension is allowed
    _, ext = os.path.splitext(safe_filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=403, detail="File type not allowed")
    file_path = os.path.join(shared_output_dir, safe_filename)
    if os.path.isfile(file_path):
        return FileResponse(
            path=file_path,
            filename=safe_filename,
            media_type='application/octet-stream',
            headers={'Content-Disposition': f'attachment; filename="{safe_filename}"'}
        )
    else:
        raise HTTPException(status_code=404, detail="File not found")
