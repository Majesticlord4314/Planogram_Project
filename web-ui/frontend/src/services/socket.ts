import { io, Socket } from 'socket.io-client';

const SOCKET_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export interface ProgressUpdate {
  job_id: string;
  progress: number;
  status: string;
  logs: string[];
  timestamp: string;
}

export interface JobComplete {
  job_id: string;
  result: any;
  timestamp: string;
}

export interface JobError {
  job_id: string;
  error: {
    message: string;
    code?: string;
  };
  timestamp: string;
}

export interface JobStatus {
  job_id: string;
  status: string;
  progress: number;
  logs: string[];
}

class SocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(): Promise<Socket> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve(this.socket);
        return;
      }

      this.socket = io(SOCKET_URL, {
        transports: ['websocket', 'polling'],
        timeout: 10000,
        forceNew: true
      });

      this.socket.on('connect', () => {
        console.log('✅ Connected to WebSocket server');
        this.reconnectAttempts = 0;
        resolve(this.socket!);
      });

      this.socket.on('connect_error', (error) => {
        console.error('❌ WebSocket connection error:', error);
        this.handleReconnect();
        reject(error);
      });

      this.socket.on('disconnect', (reason) => {
        console.log('🔌 Disconnected from WebSocket server:', reason);
        if (reason === 'io server disconnect') {
          // Server initiated disconnect, try to reconnect
          this.handleReconnect();
        }
      });

      this.socket.on('connected', (data) => {
        console.log('🎉 WebSocket handshake complete:', data);
      });

      // Set up error handling
      this.socket.on('error', (error) => {
        console.error('WebSocket error:', error);
      });
    });
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('❌ Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      console.log('🔌 WebSocket disconnected');
    }
  }

  // Job-specific room management
  joinJob(jobId: string) {
    if (this.socket?.connected) {
      this.socket.emit('join_job', { job_id: jobId });
      console.log(`📥 Joined job room: ${jobId}`);
    }
  }

  leaveJob(jobId: string) {
    if (this.socket?.connected) {
      this.socket.emit('leave_job', { job_id: jobId });
      console.log(`📤 Left job room: ${jobId}`);
    }
  }

  cancelJob(jobId: string) {
    if (this.socket?.connected) {
      this.socket.emit('cancel_job', { job_id: jobId });
      console.log(`❌ Cancelled job: ${jobId}`);
    }
  }

  getJobLogs(jobId: string, limit: number = 20) {
    if (this.socket?.connected) {
      this.socket.emit('get_job_logs', { job_id: jobId, limit });
    }
  }

  // Event listeners
  onProgress(callback: (data: ProgressUpdate) => void) {
    if (this.socket) {
      this.socket.on('optimization_progress', callback);
    }
  }

  onComplete(callback: (data: JobComplete) => void) {
    if (this.socket) {
      this.socket.on('optimization_complete', callback);
    }
  }

  onError(callback: (data: JobError) => void) {
    if (this.socket) {
      this.socket.on('optimization_error', callback);
    }
  }

  onJobStatus(callback: (data: JobStatus) => void) {
    if (this.socket) {
      this.socket.on('job_status', callback);
    }
  }

  onJobCancelled(callback: (data: { job_id: string; success: boolean }) => void) {
    if (this.socket) {
      this.socket.on('job_cancelled', callback);
    }
  }

  onJobLogs(callback: (data: { job_id: string; logs: string[]; total_logs: number }) => void) {
    if (this.socket) {
      this.socket.on('job_logs', callback);
    }
  }

  // Remove event listeners
  offProgress(callback?: (data: ProgressUpdate) => void) {
    if (this.socket) {
      this.socket.off('optimization_progress', callback);
    }
  }

  offComplete(callback?: (data: JobComplete) => void) {
    if (this.socket) {
      this.socket.off('optimization_complete', callback);
    }
  }

  offError(callback?: (data: JobError) => void) {
    if (this.socket) {
      this.socket.off('optimization_error', callback);
    }
  }

  offJobStatus(callback?: (data: JobStatus) => void) {
    if (this.socket) {
      this.socket.off('job_status', callback);
    }
  }

  offJobCancelled(callback?: (data: { job_id: string; success: boolean }) => void) {
    if (this.socket) {
      this.socket.off('job_cancelled', callback);
    }
  }

  offJobLogs(callback?: (data: { job_id: string; logs: string[]; total_logs: number }) => void) {
    if (this.socket) {
      this.socket.off('job_logs', callback);
    }
  }

  // Utility methods
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getConnectionState(): string {
    if (!this.socket) return 'disconnected';
    return this.socket.connected ? 'connected' : 'disconnected';
  }
}

// Export singleton instance
export const socketService = new SocketService();
export default socketService;