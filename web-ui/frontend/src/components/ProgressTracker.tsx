
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

import { socketService } from '../services/socket';
import { apiService, OptimizationJob } from '../services/api';

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

    const pollInterval = setInterval(async () => {
      try {
        const response = await apiService.getJobDetails(jobId);
        if (response.success && response.data) {
            const jobData = response.data as OptimizationJob;
            setProgress(jobData.progress || 0);
            setStatus(jobData.status);
            // Logs are not part of OptimizationJob, consider using socketService for live logs

            if (jobData.status === 'completed') {
                setIsComplete(true);
                setResult(jobData.summary || null);
                onComplete(jobData.summary || null);
                clearInterval(pollInterval);
            } else if (jobData.status === 'failed' || jobData.has_error) {
                setHasError(true);
                setLogs(prev => [...prev, `ERROR: Job failed`]);
                clearInterval(pollInterval);
            }
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    }, 2000);

    return () => {
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
              {result.utilization && (
                <Chip label={`${result.utilization.toFixed(1)}% utilization`} size="small" />
              )}
              {result.warnings_count && (
                <Chip label={`${result.warnings_count} warnings`} size="small" />
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
