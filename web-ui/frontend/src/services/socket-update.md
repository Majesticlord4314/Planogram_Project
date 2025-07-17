# Socket Service Update Instructions

To fix the WebSocket connection issues, please update the `socket.ts` file with the following changes:

1. Add the new event listeners for the real-time progress tracking system:

```typescript
// New event listeners for real-time progress tracking
onJobStatusUpdate(callback: (data: JobStatus) => void) {
  if (this.socket) {
    this.socket.on('job_status', callback);
  }
}

onJobLogsStream(callback: (data: { job_id: string; logs: any[]; total_logs: number; timestamp: string }) => void) {
  if (this.socket) {
    this.socket.on('job_logs_stream', callback);
  }
}

onJobCancellationResponse(callback: (data: { job_id: string; success: boolean; timestamp: string }) => void) {
  if (this.socket) {
    this.socket.on('job_cancellation_response', callback);
  }
}

// New methods to request job status, logs, and cancellation
requestJobStatus(jobId: string) {
  if (this.socket?.connected) {
    this.socket.emit('get_job_status', { job_id: jobId });
  }
}

requestJobLogs(jobId: string, limit: number = 50) {
  if (this.socket?.connected) {
    this.socket.emit('get_job_logs_stream', { job_id: jobId, limit });
  }
}

requestJobCancellation(jobId: string) {
  if (this.socket?.connected) {
    this.socket.emit('cancel_job_request', { job_id: jobId });
    console.log(`⚠️ Requested cancellation for job: ${jobId}`);
  }
}
```

2. Update the connection options to ensure compatibility:

```typescript
this.socket = io(SOCKET_URL, {
  transports: ['websocket', 'polling'],
  timeout: 10000,
  forceNew: true,
  reconnectionAttempts: this.maxReconnectAttempts,
  reconnectionDelay: this.reconnectDelay
});
```

3. Add a debug method to help troubleshoot connection issues:

```typescript
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
    upgrades: this.socket.io.engine.transport.upgrades
  };
}
```

4. Update the error handling to provide more detailed information:

```typescript
this.socket.on('connect_error', (error) => {
  console.error('❌ WebSocket connection error:', error.message);
  console.error('Connection URL:', SOCKET_URL);
  console.error('Transport:', this.socket?.io.engine.transport?.name);
  this.handleReconnect();
  reject(error);
});
```

These changes will ensure that the frontend can properly connect to the backend WebSocket server and handle the new event types we've implemented for real-time progress tracking.