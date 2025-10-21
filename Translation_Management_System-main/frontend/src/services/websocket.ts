import { io, Socket } from 'socket.io-client';
import { useStore } from '../store/useStore';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;

  connect(userId: string) {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io(WS_URL, {
      path: '/ws',
      query: { user_id: userId },
      transports: ['websocket'],
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      useStore.getState().setWebSocketConnected(true);
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      useStore.getState().setWebSocketConnected(false);
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.handleReconnect();
    });

    this.socket.on('message', (message) => {
      this.handleMessage(message);
    });

    // Handle specific message types
    this.socket.on('user_joined', (data) => {
      this.handleMessage({ type: 'user_joined', ...data });
    });

    this.socket.on('user_left', (data) => {
      this.handleMessage({ type: 'user_left', ...data });
    });

    this.socket.on('segment_updated', (data) => {
      this.handleMessage({ type: 'segment_updated', ...data });
    });

    this.socket.on('typing', (data) => {
      this.handleMessage({ type: 'typing', ...data });
    });

    this.socket.on('cursor_position', (data) => {
      this.handleMessage({ type: 'cursor_position', ...data });
    });

    this.socket.on('comment_added', (data) => {
      this.handleMessage({ type: 'comment_added', ...data });
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      useStore.getState().setWebSocketConnected(false);
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.socket?.connect();
      }, this.reconnectInterval * this.reconnectAttempts);
    }
  }

  private handleMessage(message: any) {
    useStore.getState().handleWebSocketMessage(message);
  }

  // Send messages
  joinProject(projectId: string) {
    this.socket?.emit('message', {
      type: 'join_project',
      project_id: projectId,
    });
  }

  leaveProject(projectId: string) {
    this.socket?.emit('message', {
      type: 'leave_project',
      project_id: projectId,
    });
  }

  updateSegment(projectId: string, segmentId: string, content: string) {
    this.socket?.emit('message', {
      type: 'segment_update',
      project_id: projectId,
      segment_id: segmentId,
      content,
    });
  }

  sendTyping(projectId: string, segmentId: string, isTyping: boolean) {
    this.socket?.emit('message', {
      type: 'typing',
      project_id: projectId,
      segment_id: segmentId,
      is_typing: isTyping,
    });
  }

  sendCursorPosition(projectId: string, segmentId: string, position: number) {
    this.socket?.emit('message', {
      type: 'cursor_position',
      project_id: projectId,
      segment_id: segmentId,
      position,
    });
  }

  sendComment(projectId: string, segmentId: string, comment: string) {
    this.socket?.emit('message', {
      type: 'comment',
      project_id: projectId,
      segment_id: segmentId,
      comment,
    });
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const wsService = new WebSocketService();
export default wsService;
