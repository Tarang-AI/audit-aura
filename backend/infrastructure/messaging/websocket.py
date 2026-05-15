"""
WebSocket Manager for Real-Time Alerts
Handles WebSocket connections and broadcasts compliance events
"""
import asyncio
import json
from typing import Set, Dict, Any
from fastapi import WebSocket
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_role: str = "guest"):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = {
            "role": user_role,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_ping": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"WebSocket connected: {user_role} (Total: {len(self.active_connections)})")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "message": "Connected to AuditAura real-time alerts",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            role = self.connection_metadata.get(websocket, {}).get("role", "unknown")
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            logger.info(f"WebSocket disconnected: {role} (Total: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any], exclude: Set[WebSocket] = None):
        """Broadcast a message to all connected clients"""
        exclude = exclude or set()
        disconnected = set()
        
        for connection in self.active_connections:
            if connection not in exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to connection: {e}")
                    disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_violation(self, violation: Dict[str, Any]):
        """Broadcast a new violation alert"""
        message = {
            "type": "violation",
            "severity": violation.get("severity", "medium"),
            "data": violation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted violation: {violation.get('control_id', 'unknown')}")
    
    async def broadcast_compliance_update(self, compliance_data: Dict[str, Any]):
        """Broadcast compliance score update"""
        message = {
            "type": "compliance_update",
            "data": compliance_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted compliance update")
    
    async def broadcast_pr_update(self, pr_data: Dict[str, Any]):
        """Broadcast PR status update"""
        message = {
            "type": "pr_update",
            "data": pr_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted PR update: {pr_data.get('number', 'unknown')}")
    
    async def broadcast_remediation(self, remediation_data: Dict[str, Any]):
        """Broadcast remediation action"""
        message = {
            "type": "remediation",
            "data": remediation_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted remediation action")
    
    async def send_heartbeat(self):
        """Send periodic heartbeat to all connections"""
        message = {
            "type": "heartbeat",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_connections": len(self.active_connections)
        }
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connections_by_role(self, role: str) -> int:
        """Get the number of connections for a specific role"""
        return sum(1 for meta in self.connection_metadata.values() if meta.get("role") == role)


# Global WebSocket manager instance
ws_manager = WebSocketManager()


async def start_heartbeat_task():
    """Background task to send periodic heartbeats"""
    while True:
        try:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            if ws_manager.get_connection_count() > 0:
                await ws_manager.send_heartbeat()
        except Exception as e:
            logger.error(f"Error in heartbeat task: {e}")