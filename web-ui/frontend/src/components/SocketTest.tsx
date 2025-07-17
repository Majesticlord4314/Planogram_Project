import React, { useEffect, useState } from 'react';
import socketService, { JobStatus, JobLogs } from '../services/socket';

interface LogEntry {
  message: string;
  level: 'info' | 'warning' | 'error' | 'success';
  timestamp: string;
}

const SocketTest: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [jobId, setJobId] = useState('');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [connectionDetails, setConnectionDetails] = useState<any>(null);

  useEffect(() => {
    // Connect to WebSocket server on component mount
    connectToServer();

    // Set up event listeners
    setupEventListeners();

    // Clean up on component unmount
    return () => {
      socketService.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const connectToServer = async () => {
    try {
      addLog('Connecting to WebSocket server...', 'info');
      await socketService.connect();
      setConnected(true);
      addLog('Connected to WebSocket server', 'success');
      
      // Get connection details for debugging
      const details = socketService.debug();
      setConnectionDetails(details);
      addLog(`Connection details: ${JSON.stringify(details)}`, 'info');
    } catch (error) {
      setConnected(false);
      addLog(`Connection error: ${error instanceof Error ? error.message : String(error)}`, 'error');
    }
  };

  const setupEventListeners = () => {
    // Job status updates
    socketService.onJobStatusUpdate((data: JobStatus) => {
      addLog(`Job status update: ${data.job_id} - ${data.status} (${data.progress}%)`, 'info');
    });

    // Job logs stream
    socketService.onJobLogsStream((data: JobLogs) => {
      addLog(`Received ${data.logs.length} log entries for job ${data.job_id}`, 'info');
      
      // Add individual log entries
      data.logs.forEach(log => {
        addLog(`[Job ${data.job_id}] ${log.message}`, log.level as any);
      });
    });

    // Job cancellation response
    socketService.onJobCancellationResponse((data) => {
      addLog(`Job cancellation response: ${data.job_id} - ${data.success ? 'Success' : 'Failed'}`, 
        data.success ? 'success' : 'error');
    });

    // Legacy events
    socketService.onProgress((data) => {
      addLog(`Progress update: ${data.job_id} - ${data.progress}% (${data.status})`, 'info');
    });

    socketService.onComplete((data) => {
      addLog(`Job completed: ${data.job_id}`, 'success');
    });

    socketService.onError((data) => {
      addLog(`Job error: ${data.job_id} - ${data.error.message}`, 'error');
    });
  };

  const addLog = (message: string, level: 'info' | 'warning' | 'error' | 'success') => {
    setLogs(prevLogs => [
      ...prevLogs,
      {
        message,
        level,
        timestamp: new Date().toLocaleTimeString()
      }
    ]);
  };

  const handleJoinJob = () => {
    if (!jobId) {
      addLog('Please enter a job ID', 'error');
      return;
    }
    
    socketService.joinJob(jobId);
    addLog(`Joined job room: ${jobId}`, 'info');
  };

  const handleLeaveJob = () => {
    if (!jobId) {
      addLog('Please enter a job ID', 'error');
      return;
    }
    
    socketService.leaveJob(jobId);
    addLog(`Left job room: ${jobId}`, 'info');
  };

  const handleGetStatus = () => {
    if (!jobId) {
      addLog('Please enter a job ID', 'error');
      return;
    }
    
    socketService.requestJobStatus(jobId);
    addLog(`Requested status for job: ${jobId}`, 'info');
  };

  const handleGetLogs = () => {
    if (!jobId) {
      addLog('Please enter a job ID', 'error');
      return;
    }
    
    socketService.requestJobLogs(jobId);
    addLog(`Requested logs for job: ${jobId}`, 'info');
  };

  const handleCancelJob = () => {
    if (!jobId) {
      addLog('Please enter a job ID', 'error');
      return;
    }
    
    socketService.requestJobCancellation(jobId);
    addLog(`Requested cancellation for job: ${jobId}`, 'warning');
  };

  const handleReconnect = () => {
    socketService.disconnect();
    setConnected(false);
    connectToServer();
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>WebSocket Connection Test</h1>
      
      <div style={{ 
        padding: '10px', 
        margin: '10px 0', 
        backgroundColor: connected ? '#d4edda' : '#f8d7da',
        color: connected ? '#155724' : '#721c24',
        borderRadius: '5px'
      }}>
        {connected ? 'Connected' : 'Disconnected'}
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={handleReconnect}
          style={{ padding: '8px 16px', marginRight: '10px' }}
        >
          Reconnect
        </button>
        <button 
          onClick={() => { socketService.disconnect(); setConnected(false); }}
          style={{ padding: '8px 16px' }}
        >
          Disconnect
        </button>
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Job Operations</h3>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="jobId">Job ID: </label>
          <input 
            type="text" 
            id="jobId" 
            value={jobId} 
            onChange={(e) => setJobId(e.target.value)}
            style={{ padding: '8px', width: '300px', marginRight: '10px' }}
            placeholder="Enter job ID"
          />
        </div>
        <div>
          <button onClick={handleJoinJob} style={{ padding: '8px 16px', margin: '5px' }}>Join Job</button>
          <button onClick={handleLeaveJob} style={{ padding: '8px 16px', margin: '5px' }}>Leave Job</button>
          <button onClick={handleGetStatus} style={{ padding: '8px 16px', margin: '5px' }}>Get Status</button>
          <button onClick={handleGetLogs} style={{ padding: '8px 16px', margin: '5px' }}>Get Logs</button>
          <button onClick={handleCancelJob} style={{ padding: '8px 16px', margin: '5px' }}>Cancel Job</button>
        </div>
      </div>
      
      {connectionDetails && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Connection Details</h3>
          <pre style={{ 
            backgroundColor: '#f8f9fa', 
            padding: '10px', 
            borderRadius: '5px',
            overflow: 'auto'
          }}>
            {JSON.stringify(connectionDetails, null, 2)}
          </pre>
        </div>
      )}
      
      <h3>Event Log</h3>
      <div style={{ 
        height: '300px', 
        overflow: 'auto', 
        border: '1px solid #ccc', 
        padding: '10px',
        backgroundColor: '#f8f9fa'
      }}>
        {logs.map((log, index) => (
          <div 
            key={index} 
            style={{ 
              margin: '5px 0', 
              padding: '5px', 
              borderBottom: '1px solid #eee',
              color: log.level === 'error' ? '#721c24' : 
                    log.level === 'warning' ? '#856404' :
                    log.level === 'success' ? '#155724' : '#0c5460'
            }}
          >
            <span style={{ fontWeight: 'bold' }}>{log.timestamp}</span> - {log.message}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SocketTest;