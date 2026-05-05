from fastapi import WebSocket
from typing import Dict, List
import json


class ConnectionManager:
    def __init__(self):
        self.doctor_connections: Dict[int, List[WebSocket]] = {}
        self.general_connections: List[WebSocket] = []

    async def connect_doctor(self, websocket: WebSocket, doctor_id: int):
        await websocket.accept()
        self.doctor_connections.setdefault(doctor_id, []).append(websocket)

    async def connect_general(self, websocket: WebSocket):
        await websocket.accept()
        self.general_connections.append(websocket)

    def disconnect_doctor(self, websocket: WebSocket, doctor_id: int):
        if doctor_id in self.doctor_connections:
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
        if doctor_id in self.doctor_connections:
            for ws in self.doctor_connections[doctor_id]:
                await ws.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for ws in self.general_connections:
            await ws.send_text(json.dumps(message))


ws_manager = ConnectionManager()