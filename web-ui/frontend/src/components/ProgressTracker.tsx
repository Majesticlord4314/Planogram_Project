import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Paper
} from '@mui/material';
import {
  Close as CloseIcon,
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';

import { socketService, ProgressUpdate, JobComplete, JobError } from '../services/socket';
import { apiService } from '../services/api';

interface ProgressTrackerProps {
  open: boolean;
  jobId: string | null;
  jobType: string;
  onClose: () => void;
  onComplete: (result: any) => void;
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  open,
  jobId,
  jobType,
  onClose,
  onComplete
}) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Starting...');
  const [logs, setLogs] = useState<string[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (!open || !jobId) return;

    // Reset state
    setProgress(0);
    setStatus('Starting...');
    setLogs([]);
    setIsComplete(false);
    setHasError(false);
    setResult(null);

    // Initialize WebSocket connection
    const initializeConnection = async () => {
      try {
        await socketService.connect();
        console.log('WebSocket connected:', socketService.isConnected());
        console.log('Joining job room:', jobId);
        socketService.joinJob(jobId);
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        // Continue with polling fallback
      }
    };

    initializeConnection();

    // Set up event listeners for both new and legacy events
    const handleProgress = (data: ProgressUpdate) => {
      if (data.job_id === jobId) {
        console.log('Received progress update:', data);
        setProgress(data.progress);
        setStatus(data.status);
        if (data.logs && data.logs.length > 0) {
          setLogs(prev => {
            const newLogs = [...prev];
            data.logs.forEach(log => {
              if (!newLogs.includes(log)) {
                newLogs.push(log);
              }
            });
            return newLogs;
          });
        }
      }
    };

    const handleComplete = (data: JobComplete) => {
      if (data.job_id === jobId) {
        console.log('Job completed:', data);
        setProgress(100);
        setStatus('Completed');
        setIsComplete(true);
        setResult(data.result);
        onComplete(data.result);
      }
    };

    const handleJobStatus = (data: any) => {
      if (data.job_id === jobId) {
        console.log('Received job status:', data);
        setProgress(data.progress || 0);
        
        // Handle different status formats
        let statusText = data.status;
        if (statusText === 'completed') {
          statusText = 'Completed';
          setIsComplete(true);
          onComplete(data.result || { status: 'completed', progress: 100 });
        } else if (statusText === 'failed') {
          statusText = 'Failed';
          setHasError(true);
          if (data.error) {
            setLogs(prev => [...prev, `ERROR: ${data.error}`]);
          }
        }
        
        setStatus(statusText);
        
        if (data.logs && data.logs.length > 0) {
          console.log('Setting logs:', data.logs);
          // Handle both string logs and object logs
          const formattedLogs = data.logs.map((log: any) => {
            if (typeof log === 'string') {
              return log;
            } else if (log.message) {
              return `[${log.timestamp || new Date().toLocaleTimeString()}] ${log.message}`;
            }
            return JSON.stringify(log);
          });
          setLogs(formattedLogs);
        }
      }
    };

    const handleError = (data: JobError) => {
      if (data.job_id === jobId) {
        console.log('Job error:', data);
        setStatus(`Error: ${data.error.message}`);
        setHasError(true);
        setLogs(prev => [...prev, `ERROR: ${data.error.message}`]);
      }
    };

    // New event handlers for real-time progress tracking
    const handleJobStatusUpdate = (data: any) => {
      if (data.job_id === jobId) {
        console.log('Received job status update:', data);
        handleJobStatus(data);
      }
    };

    const handleJobLogsStream = (data: any) => {
      if (data.job_id === jobId) {
        console.log('Received job logs stream:', data);
        if (data.logs && data.logs.length > 0) {
          const formattedLogs = data.logs.map((log: any) => {
            if (typeof log === 'string') {
              return log;
            } else if (log.message) {
              return `[${log.timestamp || new Date().toLocaleTimeString()}] [${log.level || 'info'}] ${log.message}`;
            }
            return JSON.stringify(log);
          });
          setLogs(formattedLogs);
        }
      }
    };

    // Set up all event listeners
    socketService.onProgress(handleProgress);
    socketService.onComplete(handleComplete);
    socketService.onError(handleError);
    socketService.onJobStatus(handleJobStatus);
    socketService.onJobStatusUpdate(handleJobStatusUpdate);
    socketService.onJobLogsStream(handleJobLogsStream);

    // Only request initial status and logs if we have a valid job ID and the job exists
    if (socketService.isConnected() && jobId && jobId.length > 10) {
      // Add a small delay to ensure the job is created before requesting status
      setTimeout(() => {
        socketService.requestJobStatus(jobId);
        socketService.requestJobLogs(jobId, 50);
      }, 500);
    }

    // Enhanced polling fallback with exponential backoff
    let pollAttempts = 0;
    const maxPollAttempts = 150; // 5 minutes at 2-second intervals
    
    const pollInterval = setInterval(async () => {
      try {
        pollAttempts++;
        const response = await apiService.getJobDetails(jobId);
        
        if (response.success && response.data) {
          const jobData = response.data;
          console.log(`Polling job status (attempt ${pollAttempts}):`, jobData);
          
          setProgress(jobData.progress || 0);
          
          let statusText = jobData.status;
          if (statusText === 'completed') {
            statusText = 'Completed';
            setIsComplete(true);
            onComplete(jobData.result || { status: 'completed' });
            clearInterval(pollInterval);
          } else if (statusText === 'failed') {
            statusText = 'Failed';
            setHasError(true);
            if (jobData.error) {
              setLogs(prev => [...prev, `ERROR: ${jobData.error}`]);
            }
            clearInterval(pollInterval);
          }
          
          setStatus(statusText);
          
          if (jobData.logs && jobData.logs.length > 0) {
            setLogs(jobData.logs);
          }
          
          // Stop polling if job is complete or failed
          if (jobData.status === 'completed' || jobData.status === 'failed') {
            clearInterval(pollInterval);
          }
        }
        
        // Stop polling after max attempts to prevent infinite polling
        if (pollAttempts >= maxPollAttempts) {
          console.warn('Max polling attempts reached, stopping');
          setStatus('Timeout - Job may still be running');
          clearInterval(pollInterval);
        }
        
      } catch (error) {
        console.error('Error polling job status:', error);
        // Don't clear interval on error, keep trying
      }
    }, 2000);

    return () => {
      socketService.offProgress(handleProgress);
      socketService.offComplete(handleComplete);
      socketService.offError(handleError);
      socketService.offJobStatus(handleJobStatus);
      socketService.offJobStatusUpdate(handleJobStatusUpdate);
      socketService.offJobLogsStream(handleJobLogsStream);
      if (jobId) {
        socketService.leaveJob(jobId);
      }
      clearInterval(pollInterval);
    };
  }, [open, jobId, onComplete]);

  const handleCancel = async () => {
    if (jobId && !isComplete) {
      try {
        await apiService.cancelJob(jobId);
        setStatus('Cancelled');
        setLogs(prev => [...prev, 'Job cancelled by user']);
      } catch (error) {
        console.error('Failed to cancel job:', error);
      }
    }
  };

  const getStatusIcon = () => {
    if (hasError) return <ErrorIcon color="error" />;
    if (isComplete) return <CheckCircleIcon color="success" />;
    return null;
  };

  const getStatusColor = () => {
    if (hasError) return 'error';
    if (isComplete) return 'success';
    return 'primary';
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center">
            {getStatusIcon()}
            <Typography variant="h6" sx={{ ml: 1 }}>
              {jobType} Optimization
            </Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Progress
            </Typography>
            <Chip 
              label={`${progress}%`} 
              size="small" 
              color={getStatusColor()}
            />
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography variant="body2" sx={{ mt: 1 }}>
            {status}
          </Typography>
        </Box>

        {jobId && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Job ID: {jobId.substring(0, 8)}
            </Typography>
          </Box>
        )}

        {/* Results Summary */}
        {isComplete && result && (
          <Paper sx={{ p: 2, mb: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
            <Typography variant="h6" gutterBottom>
              Optimization Complete!
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap">
              {result.products_placed && (
                <Chip label={`${result.products_placed} products placed`} size="small" />
              )}
              {result.products_rejected && (
                <Chip label={`${result.products_rejected} products rejected`} size="small" />
              )}
              {result.metrics?.average_utilization && (
                <Chip label={`${result.metrics.average_utilization.toFixed(1)}% utilization`} size="small" />
              )}
            </Box>
          </Paper>
        )}

        {/* Live Logs */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Live Logs
          </Typography>
          <Paper 
            sx={{ 
              maxHeight: 300, 
              overflow: 'auto', 
              bgcolor: '#1e1e1e', 
              color: '#fff',
              fontFamily: 'monospace'
            }}
          >
            <List dense>
              {logs.length === 0 ? (
                <ListItem>
                  <ListItemText primary="Waiting for logs..." />
                </ListItem>
              ) : (
                logs.map((log, index) => (
                  <ListItem key={index}>
                    <ListItemText 
                      primary={log}
                      sx={{ 
                        '& .MuiListItemText-primary': { 
                          fontSize: '0.875rem',
                          fontFamily: 'monospace'
                        }
                      }}
                    />
                  </ListItem>
                ))
              )}
            </List>
          </Paper>
        </Box>
      </DialogContent>

      <DialogActions>
        {!isComplete && !hasError && (
          <Button 
            onClick={handleCancel} 
            color="error" 
            startIcon={<CancelIcon />}
          >
            Cancel
          </Button>
        )}
        <Button onClick={onClose} variant="contained">
          {isComplete || hasError ? 'Close' : 'Hide'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProgressTracker;