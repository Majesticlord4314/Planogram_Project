import React, { useState, useEffect } from 'react';
import {
    Grid,
    Card,
    CardContent,
    Typography,
    Button,
    Box,
    Alert,
    CircularProgress,
    Chip,
    LinearProgress,
    Divider
} from '@mui/material';
import {
    Analytics,
    Category,
    Store,
    CheckCircle,
    Error,
    Warning,
    Info
} from '@mui/icons-material';

import { apiService, SystemStatus } from '../services/api';
import { socketService } from '../services/socket';
import ProgressTracker from './ProgressTracker';
import ResultsViewer from './ResultsViewer';
import OptimizationForm from './OptimizationForm';

const Dashboard: React.FC = () => {
    const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');

    // Progress tracking state
    const [progressOpen, setProgressOpen] = useState(false);
    const [currentJobId, setCurrentJobId] = useState<string | null>(null);
    const [currentJobType, setCurrentJobType] = useState<string>('');

    // Results viewer state
    const [resultsOpen, setResultsOpen] = useState(false);
    const [completedJobId, setCompletedJobId] = useState<string | null>(null);

    // Optimization form state
    const [formOpen, setFormOpen] = useState(false);

    useEffect(() => {
        fetchSystemStatus();

        // Check WebSocket connection status
        setConnectionStatus(socketService.getConnectionState());

        // Set up periodic status updates
        const interval = setInterval(fetchSystemStatus, 30000); // Update every 30 seconds

        return () => clearInterval(interval);
    }, []);

    const fetchSystemStatus = async () => {
        try {
            const response = await apiService.getSystemStatus();

            if (response.success && response.data) {
                setSystemStatus(response.data);
                setError(null);
            } else {
                setError(response.error?.message || 'Failed to fetch system status');
            }
        } catch (err: any) {
            setError('Unable to connect to backend server');
            console.error('System status error:', err);
        } finally {
            setLoading(false);
        }
    };



    // Handler functions for progress tracker and results viewer
    const handleProgressClose = () => {
        setProgressOpen(false);
        setCurrentJobId(null);
        setCurrentJobType('');
    };

    const handleJobComplete = (result: any) => {
        // When job completes, close progress tracker and open results viewer
        setProgressOpen(false);
        setCompletedJobId(currentJobId);
        setResultsOpen(true);

        // Refresh system status to update job counts
        fetchSystemStatus();
    };

    const handleResultsClose = () => {
        setResultsOpen(false);
        setCompletedJobId(null);
    };

    // Handler for optimization form
    const handleOptimizationStart = (jobId: string, jobType: string) => {
        setCurrentJobId(jobId);
        setCurrentJobType(jobType);
        setProgressOpen(true);

        // Refresh system status to update active jobs count
        setTimeout(fetchSystemStatus, 1000);
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ mb: 2 }}>
                {error}
                <Button onClick={fetchSystemStatus} sx={{ ml: 2 }}>
                    Retry
                </Button>
            </Alert>
        );
    }

    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Planogram Optimization Dashboard
            </Typography>

            {/* System Status */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        System Status
                    </Typography>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={3}>
                            <Box>
                                <Typography variant="body2" color="text.secondary">
                                    System Health
                                </Typography>
                                <Chip
                                    label={systemStatus?.system_health || 'Unknown'}
                                    color="success"
                                    size="small"
                                />
                            </Box>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Box>
                                <Typography variant="body2" color="text.secondary">
                                    Active Jobs
                                </Typography>
                                <Typography variant="h6">
                                    {systemStatus?.active_jobs || 0}
                                </Typography>
                            </Box>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Box>
                                <Typography variant="body2" color="text.secondary">
                                    Store Templates
                                </Typography>
                                <Typography variant="h6">
                                    {systemStatus?.store_templates?.length || 0}
                                </Typography>
                            </Box>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Box>
                                <Typography variant="body2" color="text.secondary">
                                    Data Files
                                </Typography>
                                <Typography variant="h6">
                                    {systemStatus?.data_files ?
                                        Object.values(systemStatus.data_files).filter(Boolean).length : 0
                                    } / {systemStatus?.data_files ? Object.keys(systemStatus.data_files).length : 0}
                                </Typography>
                            </Box>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>

            {/* Optimization Actions */}
            <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
                Apple Planogram Optimization System
            </Typography>

            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                        <Typography variant="h6" gutterBottom>
                            Select optimization type
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 600, mx: 'auto' }}>
                            Choose your optimization type and configure your planogram. The system supports cohort-based planograms,
                            Line of Business optimization, and full store optimization with multiple strategies.
                        </Typography>

                        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap', mb: 3 }}>
                            <Chip icon={<Analytics />} label="1. Cohort Planogram" color="primary" variant="outlined" />
                            <Chip icon={<Store />} label="2. Line of Business" color="primary" variant="outlined" />
                            <Chip icon={<Category />} label="3. All Products (Full Store)" color="primary" variant="outlined" />
                        </Box>

                        <Button
                            variant="contained"
                            size="large"
                            onClick={() => setFormOpen(true)}
                            sx={{ px: 4, py: 1.5 }}
                        >
                            Start Optimization
                        </Button>
                    </Box>
                </CardContent>
            </Card>

            {/* Enhanced System Information */}
            <Grid container spacing={3} sx={{ mt: 2 }}>
                {/* Data Files Status */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Data Files Status
                            </Typography>
                            <Box sx={{ mb: 2 }}>
                                {systemStatus?.data_files && Object.entries(systemStatus.data_files).map(([category, available]) => (
                                    <Box key={category} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                        {available ? (
                                            <CheckCircle color="success" sx={{ mr: 1, fontSize: 20 }} />
                                        ) : (
                                            <Error color="error" sx={{ mr: 1, fontSize: 20 }} />
                                        )}
                                        <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                                            {category.replace('_', ' ')}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                            <Divider sx={{ my: 2 }} />
                            <Typography variant="body2" color="text.secondary">
                                Available: {systemStatus?.data_files ?
                                    Object.values(systemStatus.data_files).filter(Boolean).length : 0
                                } / {systemStatus?.data_files ? Object.keys(systemStatus.data_files).length : 0} files
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                {/* LOB Status */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Line of Business Status
                            </Typography>
                            <Box sx={{ mb: 2 }}>
                                {systemStatus?.lob_status && Object.entries(systemStatus.lob_status).map(([lob, available]) => (
                                    <Box key={lob} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                        {available ? (
                                            <CheckCircle color="success" sx={{ mr: 1, fontSize: 20 }} />
                                        ) : (
                                            <Warning color="warning" sx={{ mr: 1, fontSize: 20 }} />
                                        )}
                                        <Typography variant="body2">
                                            {lob}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                            <Divider sx={{ my: 2 }} />
                            <Typography variant="body2" color="text.secondary">
                                Ready: {systemStatus?.lob_status ?
                                    Object.values(systemStatus.lob_status).filter(Boolean).length : 0
                                } / {systemStatus?.lob_status ? Object.keys(systemStatus.lob_status).length : 0} LOBs
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                {/* System Resources */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                System Resources
                            </Typography>
                            {systemStatus?.disk_usage && (
                                <Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">
                                            Output Files: {systemStatus.disk_usage.output_mb} MB
                                        </Typography>
                                        <LinearProgress
                                            variant="determinate"
                                            value={Math.min((systemStatus.disk_usage.output_mb / 100) * 100, 100)}
                                            sx={{ mt: 0.5 }}
                                        />
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">
                                            Log Files: {systemStatus.disk_usage.logs_mb} MB
                                        </Typography>
                                        <LinearProgress
                                            variant="determinate"
                                            value={Math.min((systemStatus.disk_usage.logs_mb / 50) * 100, 100)}
                                            sx={{ mt: 0.5 }}
                                        />
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Data Files: {systemStatus.disk_usage.data_mb} MB
                                        </Typography>
                                        <LinearProgress
                                            variant="determinate"
                                            value={Math.min((systemStatus.disk_usage.data_mb / 200) * 100, 100)}
                                            sx={{ mt: 0.5 }}
                                        />
                                    </Box>
                                </Box>
                            )}
                        </CardContent>
                    </Card>
                </Grid>

                {/* Job Statistics */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Job Statistics
                            </Typography>
                            {systemStatus?.jobs && (
                                <Grid container spacing={2}>
                                    <Grid item xs={6}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="primary">
                                                {systemStatus.jobs.total}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                Total Jobs
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="success.main">
                                                {systemStatus.jobs.completed}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                Completed
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="warning.main">
                                                {systemStatus.jobs.running}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                Running
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="error.main">
                                                {systemStatus.jobs.failed}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                Failed
                                            </Typography>
                                        </Box>
                                    </Grid>
                                </Grid>
                            )}
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Connection Status Footer */}
            <Card sx={{ mt: 3 }}>
                <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Info color="primary" sx={{ mr: 1 }} />
                            <Typography variant="body2">
                                WebSocket: {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
                            </Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                            Last updated: {new Date().toLocaleTimeString()}
                        </Typography>
                    </Box>
                </CardContent>
            </Card>

            {/* Progress Tracker Dialog */}
            <ProgressTracker
                open={progressOpen}
                jobId={currentJobId}
                jobType={currentJobType}
                onClose={handleProgressClose}
                onComplete={handleJobComplete}
            />

            {/* Results Viewer Dialog */}
            <ResultsViewer
                open={resultsOpen}
                jobId={completedJobId}
                onClose={handleResultsClose}
            />

            {/* Optimization Form Dialog */}
            <OptimizationForm
                open={formOpen}
                onClose={() => setFormOpen(false)}
                onStart={handleOptimizationStart}
            />
        </Box>
    );
};

export default Dashboard;