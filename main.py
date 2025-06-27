import json
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import socket
import logging
from typing import Dict

app = FastAPI(title="Document Collaboration API", version="1.0.0")

# Logging and IP detection
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
logging.info(f"Detected Local IP: {local_ip}")

# Document data - Microscope Functional Requirements Specification
json_data = {
    "purpose1":
    "Defines the detailed system-level functionality and behavior required for the Microscope based on the User Requirements Specification (URS).",
    "scope":
    "Applies to the compound microscope with integrated imaging and digital functionalities intended for laboratory use.",
    "functional_requirements_table": {
        "headers":
        ["FRS ID", "Function Description", "Linked URS ID", "GxP Impact"],
        "rows":
        [[
            "FRS-001",
            "The system shall allow switching between objective lenses to achieve magnifications from 40x to 1000x.",
            "URS-001", "Yes"
        ],
         [
             "FRS-002",
             "The LED light source shall provide adjustable brightness to ensure optimal illumination.",
             "URS-002", "Yes"
         ],
         [
             "FRS-003",
             "The microscope shall integrate with a digital camera module.",
             "URS-003", "Yes"
         ],
         [
             "FRS-003",
             "The microscope shall integrate with a digital camera module.",
             "URS-003", "Yes"
         ]]
    },
    "non_functional_requirements": {
        "response_time":
        "System should load captured images within 2 seconds.",
        "storage":
        "Captured data must be storable on local drive or shared network.",
        "usability":
        "Intuitive interface for non-technical lab personnel.",
        "maintainability":
        "Software and device should support routine maintenance with minimal downtime."
    },
    "interface_requirements": {
        "usb": "USB 3.0 port for camera communication",
        "hdmi": "HDMI output for image projection",
        "software_compatibility":
        "Compatible software for Windows 10 or higher"
    },
    "approval": {
        "qa_representative": {
            "name": "",
            "role": "Quality Assurance",
            "signature": "",
            "date": ""
        },
        "lab_manager": {
            "name": "",
            "role": "End User",
            "signature": "",
            "date": ""
        },
        "validation_lead": {
            "name": "",
            "role": "Project Owner",
            "signature": "",
            "date": ""
        }
    },
    "content":
    "Welcome to the Microscope Functional Requirements Specification collaborative editor!"
}

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# WebSocket client management
client_states: Dict[WebSocket, Dict] = {}


@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse('static/index.html')


@app.get("/document")
async def get_document():
    """
    Get the current document data including microscope specifications
    Returns the complete document with all functional requirements
    """
    logger.info("Document requested")
    return json_data


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_states[websocket] = {"cursor": None}
    logger.info(f"Connected clients: {list(client_states.keys())}")

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            # Update content and cursor bookmark object
            json_data = data["content"]
            client_states[websocket]["cursor"] = data.get("cursor")

            broadcast_data = {
                "type": "content_update",
                "content": json_data,
                "client_id": data.get("client_id"),
                "cursor": data.get("cursor")  # send bookmark object
            }

            for client in client_states:
                if client != websocket:
                    await client.send_text(json.dumps(broadcast_data))
    except WebSocketDisconnect:
        del client_states[websocket]


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "connected_clients": len(client_states),
        "server_ip": local_ip
    }


if __name__ == "__main__":
    # Run the application on port 5000, binding to all interfaces
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=5000,
                reload=True,
                log_level="info")
