import React, { useEffect, useState } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import {
  Container,
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Badge,
  Tooltip,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Refresh as RefreshIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon
} from '@mui/icons-material';

import Dashboard from './components/Dashboard';
import { socketService } from './services/socket';
import { apiService } from './services/api';

function App() {
  const navigate = useNavigate();
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const [activeJobs, setActiveJobs] = useState(0);
  const [notification, setNotification] = useState<{ message: string; severity: 'success' | 'error' | 'info' | 'warning' } | null>(null);

  useEffect(() => {
    // Initialize WebSocket connection
    initializeSocket();

    // Check system health on startup
    checkSystemHealth();

    return () => {
      socketService.disconnect();
    };
  }, []);

  const initializeSocket = async () => {
    try {
      setConnectionStatus('connecting');
      await socketService.connect();
      setConnectionStatus('connected');

      // Set up global event listeners
      socketService.onProgress((data) => {
        console.log('Progress update:', data);
      });

      socketService.onComplete((data) => {
        setNotification({
          message: `Optimization completed for job ${data.job_id.substring(0, 8)}`,
          severity: 'success'
        });
      });

      socketService.onError((data) => {
        setNotification({
          message: `Optimization failed: ${data.error.message}`,
          severity: 'error'
        });
      });

    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      setConnectionStatus('disconnected');
      setNotification({
        message: 'Failed to connect to server. Some features may not work.',
        severity: 'warning'
      });
    }
  };

  const checkSystemHealth = async () => {
    try {
      const response = await apiService.getHealth();
      if (response.success && response.data) {
        setActiveJobs(response.data.active_jobs || 0);
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setNotification({
        message: 'Unable to connect to backend server',
        severity: 'error'
      });
    }
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const handleCloseNotification = () => {
    setNotification(null);
  };

  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <WifiIcon color="success" />;
      case 'connecting':
        return <WifiIcon color="warning" />;
      default:
        return <WifiOffIcon color="error" />;
    }
  };

  const getConnectionTooltip = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected to server';
      case 'connecting':
        return 'Connecting to server...';
      default:
        return 'Disconnected from server';
    }
  };

  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: '#F2F2F7' }}>
      <AppBar position="static" elevation={0} sx={{ backgroundColor: '#007AFF' }}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/dashboard')}
            sx={{ mr: 2 }}
          >
            <DashboardIcon />
          </IconButton>

          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            🍎 Planogram Optimizer
          </Typography>

          {/* Active Jobs Badge */}
          {activeJobs > 0 && (
            <Badge badgeContent={activeJobs} color="secondary" sx={{ mr: 2 }}>
              <Typography variant="body2" color="inherit">
                Active Jobs
              </Typography>
            </Badge>
          )}

          {/* Connection Status */}
          <Tooltip title={getConnectionTooltip()}>
            <IconButton color="inherit" size="small" sx={{ mr: 1 }}>
              {getConnectionIcon()}
            </IconButton>
          </Tooltip>

          {/* Refresh Button */}
          <Tooltip title="Refresh Application">
            <IconButton color="inherit" onClick={handleRefresh}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          {/* Add more routes here as we build more components */}
        </Routes>
      </Container>

      {/* Global Notifications */}
      <Snackbar
        open={notification !== null}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification?.severity || 'info'}
          variant="filled"
        >
          {notification?.message || ''}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;