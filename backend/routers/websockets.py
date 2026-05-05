from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from services.websocket_manager import ws_manager
import logging

router = APIRouter(tags=["WebSockets"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/doctor/{doctor_id}")
async def doctor_websocket(websocket: WebSocket, doctor_id: int):
    """WebSocket endpoint for a specific doctor to receive appointment notifications."""
    await ws_manager.connect_doctor(websocket, doctor_id)
    try:
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected as Doctor {doctor_id}. Waiting for appointment notifications..."
        })
        while True:
            # Keep connection alive; server pushes messages
            data = await websocket.receive_text()
            # Echo ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_doctor(websocket, doctor_id)
        logger.info(f"Doctor {doctor_id} WebSocket disconnected")


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for the admin dashboard to receive all real-time updates."""
    await ws_manager.connect_general(websocket)
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to hospital dashboard. Receiving live updates..."
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_general(websocket)
        logger.info("Dashboard WebSocket disconnected")
