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
  logs: any[];
  timestamp?: string;
}

export interface JobLogs {
  job_id: string;
  logs: any[];
  total_logs: number;
  timestamp: string;
}

export interface JobCancellationResponse {
  job_id: string;
  success: boolean;
  timestamp: string;
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

      // Close any existing connection
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }

      console.log(`Connecting to WebSocket server at ${SOCKET_URL}...`);

      try {
        this.socket = io(SOCKET_URL, {
          transports: ['websocket', 'polling'],
          timeout: 10000,
          forceNew: true,
          reconnectionAttempts: this.maxReconnectAttempts,
          reconnectionDelay: this.reconnectDelay
        });

        this.socket.on('connect', () => {
          console.log('Connected to WebSocket server');
          console.log(`Socket ID: ${this.socket?.id}`);
          console.log(`Transport: ${this.socket?.io.engine.transport.name}`);
          this.reconnectAttempts = 0;
          resolve(this.socket!);
        });

        this.socket.on('connect_error', (error: Error) => {
          console.error('WebSocket connection error:', error.message);
          console.error('Connection URL:', SOCKET_URL);
          console.error('Transport:', this.socket?.io.engine.transport?.name);
          this.handleReconnect();
          reject(error);
        });

        this.socket.on('disconnect', (reason: string) => {
          console.log('Disconnected from WebSocket server:', reason);
          if (reason === 'io server disconnect') {
            // Server initiated disconnect, try to reconnect
            this.handleReconnect();
          }
        });

        this.socket.on('connected', (data: any) => {
          console.log('🎉 WebSocket handshake complete:', data);
        });

        // Set up error handling
        this.socket.on('error', (error: Error) => {
          console.error('WebSocket error:', error);
        });
      } catch (error) {
        console.error('Failed to initialize socket:', error);
        reject(error);
      }
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
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      console.log('WebSocket disconnected');
    }
  }

  // Job-specific room management
  joinJob(jobId: string) {
    if (this.socket?.connected) {
      this.socket.emit('join_job', { job_id: jobId });
      console.log(`Joined job room: ${jobId}`);
    } else {
      console.warn('Cannot join job room: Socket not connected');
    }
  }

  leaveJob(jobId: string) {
    if (this.socket?.connected) {
      this.socket.emit('leave_job', { job_id: jobId });
      console.log(`Left job room: ${jobId}`);
    } else {
      console.warn('Cannot leave job room: Socket not connected');
    }
  }

  // New methods for real-time progress tracking
  requestJobStatus(jobId: string) {
    if (this.socket?.connected) {
      this.socket.emit('get_job_status', { job_id: jobId });
      console.log(`Requested status for job: ${jobId}`);
    } else {
      console.warn('Cannot request job status: Socket not connected');
    }
  }

  requestJobLogs(jobId: string, limit: number = 50) {
    if (this.socket?.connected) {
      this.socket.emit('get_job_logs_stream', { job_id: jobId, limit });
      console.log(`Requested logs for job: ${jobId} (limit: ${limit})`);
    } else {
      console.warn('Cannot request job logs: Socket not connected');
    }
  }

  requestJobCancellation(jobId: string) {
    if (this.socket?.connected) {
      this.socket.emit('cancel_job_request', { job_id: jobId });
      console.log(`Requested cancellation for job: ${jobId}`);
    } else {
      console.warn('Cannot request job cancellation: Socket not connected');
    }
  }

  // Legacy methods (for backward compatibility)
  cancelJob(jobId: string) {
    if (this.socket?.connected) {
      this.socket.emit('cancel_job', { job_id: jobId });
      console.log(`Cancelled job: ${jobId} (legacy method)`);
    } else {
      console.warn('Cannot cancel job: Socket not connected');
    }
  }

  getJobLogs(jobId: string, limit: number = 20) {
    if (this.socket?.connected) {
      this.socket.emit('get_job_logs', { job_id: jobId, limit });
      console.log(`Requested logs for job: ${jobId} (legacy method)`);
    } else {
      console.warn('Cannot get job logs: Socket not connected');
    }
  }

  // Event listeners for real-time progress tracking
  onJobStatusUpdate(callback: (data: JobStatus) => void) {
    if (this.socket) {
      this.socket.on('job_status', callback);
    }
  }

  onJobLogsStream(callback: (data: JobLogs) => void) {
    if (this.socket) {
      this.socket.on('job_logs_stream', callback);
    }
  }

  onJobCancellationResponse(callback: (data: JobCancellationResponse) => void) {
    if (this.socket) {
      this.socket.on('job_cancellation_response', callback);
    }
  }

  // Legacy event listeners (for backward compatibility)
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

  offJobStatusUpdate(callback?: (data: JobStatus) => void) {
    if (this.socket) {
      this.socket.off('job_status', callback);
    }
  }

  offJobLogsStream(callback?: (data: JobLogs) => void) {
    if (this.socket) {
      this.socket.off('job_logs_stream', callback);
    }
  }

  offJobCancellationResponse(callback?: (data: JobCancellationResponse) => void) {
    if (this.socket) {
      this.socket.off('job_cancellation_response', callback);
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

  // Debug method to help troubleshoot connection issues
  debug() {
    if (!this.socket) {
      console.log('Socket not initialized');
      return {
        initialized: false,
        connected: false,
        url: SOCKET_URL
      };
    }
    
    return {
      initialized: true,
      connected: this.socket.connected,
      id: this.socket.id,
      url: SOCKET_URL,
      transport: this.socket.io.engine.transport.name,
      // Safely access upgrades if available
      upgrades: this.socket.io.engine.transport.name === 'polling' ? 
        (this.socket.io.engine as any).upgrades || [] : []
    };
  }
}

// Export singleton instance
export const socketService = new SocketService();
export default socketService;