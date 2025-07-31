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
    Chip
} from '@mui/material';
import {
    Store
} from '@mui/icons-material';

import { apiService } from '../services/api';
import type { SystemStatus } from '../services/api';
import ProgressTracker from './ProgressTracker';
import ResultsViewer from './ResultsViewer';
import OptimizationForm from './OptimizationForm';
import StoreSelector from './StoreSelector';

const Dashboard: React.FC = () => {
    const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

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
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Store />
                Store Planogram Optimization System
            </Typography>

            {/* System Status Summary */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} md={3}>
                    <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                            <Typography variant="h5" color="primary">
                                {systemStatus?.active_jobs || 0}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                Active Jobs
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                    <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                            <Typography variant="h5" color="success.main">
                                {systemStatus?.store_templates?.length || 0}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                Store Templates
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                    <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                            <Chip
                                label={systemStatus?.system_health || 'Unknown'}
                                color="success"
                                size="small"
                            />
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                System Health
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                    <Card>
                        <CardContent sx={{ textAlign: 'center' }}>
                            <Typography variant="h5" color="info.main">
                                {systemStatus?.jobs?.completed || 0}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                Completed Jobs
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Main Store Optimization Interface */}
            <StoreSelector />

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