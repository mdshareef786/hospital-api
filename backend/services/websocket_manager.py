from fastapi import WebSocket
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # doctor_id -> list of websocket connections
        self.doctor_connections: Dict[int, List[WebSocket]] = {}
        # general connections (admin dashboard)
        self.general_connections: List[WebSocket] = []

    async def connect_doctor(self, websocket: WebSocket, doctor_id: int):
        await websocket.accept()
        if doctor_id not in self.doctor_connections:
            self.doctor_connections[doctor_id] = []
        self.doctor_connections[doctor_id].append(websocket)
        logger.info(f"Doctor {doctor_id} connected via WebSocket")

    async def connect_general(self, websocket: WebSocket):
        await websocket.accept()
        self.general_connections.append(websocket)
        logger.info("General WebSocket connection established")

    def disconnect_doctor(self, websocket: WebSocket, doctor_id: int):
        if doctor_id in self.doctor_connections:
            self.doctor_connections[doctor_id].discard(websocket) if hasattr(
                self.doctor_connections[doctor_id], 'discard'
            ) else None
            try:
                self.doctor_connections[doctor_id].remove(websocket)
            except ValueError:
                pass

    def disconnect_general(self, websocket: WebSocket):
        try:
            self.general_connections.remove(websocket)
        except ValueError:
            pass

    async def notify_doctor(self, doctor_id: int, message: dict):
        """Notify a specific doctor of a new appointment."""
        if doctor_id in self.doctor_connections:
            dead = []
            for ws in self.doctor_connections[doctor_id]:
                try:
                    await ws.send_text(json.dumps(message))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                try:
                    self.doctor_connections[doctor_id].remove(ws)
                except ValueError:
                    pass

    async def broadcast(self, message: dict):
        """Broadcast to all general connections (admin dashboard)."""
        dead = []
        for ws in self.general_connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_general(ws)


ws_manager = ConnectionManager()
