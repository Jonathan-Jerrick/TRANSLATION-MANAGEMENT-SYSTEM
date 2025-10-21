"""WebSocket manager for real-time collaboration."""
import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import User, Project, ActivityLog
import uuid


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration."""
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Store project rooms (user IDs in each project)
        self.project_rooms: Dict[str, Set[str]] = {}
        # Store user sessions
        self.user_sessions: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, project_id: str = None):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = {
            "websocket": websocket,
            "project_id": project_id,
            "last_activity": asyncio.get_event_loop().time()
        }
        
        if project_id:
            if project_id not in self.project_rooms:
                self.project_rooms[project_id] = set()
            self.project_rooms[project_id].add(user_id)
        
        # Notify others in the project
        if project_id:
            await self.broadcast_to_project(
                project_id, 
                {
                    "type": "user_joined",
                    "user_id": user_id,
                    "timestamp": asyncio.get_event_loop().time()
                },
                exclude_user=user_id
            )
    
    def disconnect(self, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        if user_id in self.user_sessions:
            project_id = self.user_sessions[user_id].get("project_id")
            if project_id and project_id in self.project_rooms:
                self.project_rooms[project_id].discard(user_id)
            del self.user_sessions[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception:
                # Connection might be closed
                self.disconnect(user_id)
    
    async def broadcast_to_project(self, project_id: str, message: dict, exclude_user: str = None):
        """Broadcast a message to all users in a project."""
        if project_id in self.project_rooms:
            for user_id in self.project_rooms[project_id]:
                if user_id != exclude_user and user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_text(json.dumps(message))
                    except Exception:
                        # Connection might be closed
                        self.disconnect(user_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected users."""
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                # Connection might be closed
                self.disconnect(user_id)
    
    def get_project_users(self, project_id: str) -> List[str]:
        """Get list of users currently in a project."""
        if project_id in self.project_rooms:
            return list(self.project_rooms[project_id])
        return []
    
    def get_user_count(self) -> int:
        """Get total number of connected users."""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


class WebSocketHandler:
    """Handles WebSocket message processing."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
    
    async def handle_message(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        message: dict,
        db: Session
    ):
        """Handle incoming WebSocket messages."""
        message_type = message.get("type")
        
        if message_type == "join_project":
            await self._handle_join_project(websocket, user_id, message, db)
        elif message_type == "leave_project":
            await self._handle_leave_project(websocket, user_id, message, db)
        elif message_type == "segment_update":
            await self._handle_segment_update(websocket, user_id, message, db)
        elif message_type == "typing":
            await self._handle_typing(websocket, user_id, message, db)
        elif message_type == "cursor_position":
            await self._handle_cursor_position(websocket, user_id, message, db)
        elif message_type == "comment":
            await self._handle_comment(websocket, user_id, message, db)
        else:
            # Echo back unknown message types
            await self.manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }, user_id)
    
    async def _handle_join_project(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        message: dict,
        db: Session
    ):
        """Handle user joining a project."""
        project_id = message.get("project_id")
        if not project_id:
            await self.manager.send_personal_message({
                "type": "error",
                "message": "Project ID required"
            }, user_id)
            return
        
        # Verify project exists and user has access
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            await self.manager.send_personal_message({
                "type": "error",
                "message": "Project not found"
            }, user_id)
            return
        
        # Update user session
        if user_id in self.manager.user_sessions:
            self.manager.user_sessions[user_id]["project_id"] = project_id
        
        # Add to project room
        if project_id not in self.manager.project_rooms:
            self.manager.project_rooms[project_id] = set()
        self.manager.project_rooms[project_id].add(user_id)
        
        # Notify others
        await self.manager.broadcast_to_project(project_id, {
            "type": "user_joined",
            "user_id": user_id,
            "project_id": project_id,
            "timestamp": asyncio.get_event_loop().time()
        }, exclude_user=user_id)
        
        # Send current project users to the joining user
        await self.manager.send_personal_message({
            "type": "project_users",
            "users": self.manager.get_project_users(project_id)
        }, user_id)
    
    async def _handle_leave_project(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        message: dict,
        db: Session
    ):
        """Handle user leaving a project."""
        project_id = message.get("project_id")
        if project_id and project_id in self.manager.project_rooms:
            self.manager.project_rooms[project_id].discard(user_id)
            
            # Notify others
            await self.manager.broadcast_to_project(project_id, {
                "type": "user_left",
                "user_id": user_id,
                "project_id": project_id,
                "timestamp": asyncio.get_event_loop().time()
            })
    
    async def _handle_segment_update(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        message: dict,
        db: Session
    ):
        """Handle segment updates."""
        project_id = message.get("project_id")
        segment_id = message.get("segment_id")
        content = message.get("content")
        
        if not all([project_id, segment_id, content]):
            await self.manager.send_personal_message({
                "type": "error",
                "message": "Missing required fields"
            }, user_id)
            return
        
        # Broadcast update to other users in the project
        await self.manager.broadcast_to_project(project_id, {
            "type": "segment_updated",
            "segment_id": segment_id,
            "content": content,
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time()
        }, exclude_user=user_id)
    
    async def _handle_typing(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        message: dict,
        db: Session
    ):
        """Handle typing indicators."""
        project_id = message.get("project_id")
        segment_id = message.get("segment_id")
        is_typing = message.get("is_typing", False)
        
        if project_id:
            await self.manager.broadcast_to_project(project_id, {
                "type": "typing",
                "user_id": user_id,
                "segment_id": segment_id,
                "is_typing": is_typing,
                "timestamp": asyncio.get_event_loop().time()
            }, exclude_user=user_id)
    
    async def _handle_cursor_position(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        message: dict,
        db: Session
    ):
        """Handle cursor position updates."""
        project_id = message.get("project_id")
        segment_id = message.get("segment_id")
        position = message.get("position")
        
        if project_id:
            await self.manager.broadcast_to_project(project_id, {
                "type": "cursor_position",
                "user_id": user_id,
                "segment_id": segment_id,
                "position": position,
                "timestamp": asyncio.get_event_loop().time()
            }, exclude_user=user_id)
    
    async def _handle_comment(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        message: dict,
        db: Session
    ):
        """Handle comments on segments."""
        project_id = message.get("project_id")
        segment_id = message.get("segment_id")
        comment = message.get("comment")
        
        if not all([project_id, segment_id, comment]):
            await self.manager.send_personal_message({
                "type": "error",
                "message": "Missing required fields for comment"
            }, user_id)
            return
        
        # Log the activity
        activity = ActivityLog(
            id=str(uuid.uuid4()),
            message=f"User {user_id} commented on segment {segment_id}",
            category="comment",
            user_id=user_id,
            project_id=project_id
        )
        db.add(activity)
        db.commit()
        
        # Broadcast comment to project users
        await self.manager.broadcast_to_project(project_id, {
            "type": "comment_added",
            "segment_id": segment_id,
            "comment": comment,
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time()
        })


# Global WebSocket handler
websocket_handler = WebSocketHandler(manager)
