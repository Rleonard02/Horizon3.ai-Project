from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Dict
import os

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for service statuses
service_statuses: Dict[str, Dict] = {}

# List of connected WebSocket clients
clients: List[WebSocket] = []

# Output directories for different modules
sonarqube_output_dir = "/sonarqube_shared/output"
binary_analysis_output_dir = "/bin_shared/output"

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

@app.get("/output_files/{module}")
def list_output_files(module: str):
    # Determine the correct directory based on the module
    if module == "sonarqube":
        output_dir = sonarqube_output_dir
    elif module == "binary_analysis":
        output_dir = binary_analysis_output_dir
    else:
        raise HTTPException(status_code=400, detail="Invalid module name")

    try:
        # List files in the selected directory
        files = os.listdir(output_dir)
        # Filter files by allowed extensions
        files = [f for f in files if os.path.splitext(f)[1] in ALLOWED_EXTENSIONS]
        return {"module": module, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing files: {str(e)}")

@app.get("/output_files/{module}/{filename}")
def get_output_file(module: str, filename: str):
    # Determine the correct directory based on the module
    if module == "sonarqube":
        output_dir = sonarqube_output_dir
    elif module == "binary_analysis":
        output_dir = binary_analysis_output_dir
    else:
        raise HTTPException(status_code=400, detail="Invalid module name")

    safe_filename = os.path.basename(filename)
    _, ext = os.path.splitext(safe_filename)

    # Check file extension for security
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=403, detail="File type not allowed")

    file_path = os.path.join(output_dir, safe_filename)

    # Return the file if it exists
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=safe_filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")
