import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Button,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Grid,
    Chip,
    Alert,
    CircularProgress,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Checkbox,
    FormControlLabel,
    FormGroup,
    Divider
} from '@mui/material';
import {
    ExpandMore,
    Store,
    ViewModule,
    PlayArrow,
    Info,
    Business,
    Category,
    Analytics,
    CheckCircle,
    Cancel
} from '@mui/icons-material';

import { apiService } from '../services/api';
import { socketService } from '../services/socket';
import ProgressTracker from './ProgressTracker';
import ResultsViewer from './ResultsViewer';

interface StoreTemplate {
    store_name: string;
    location: string;
    city: string;
    cm: string;
    walls: WallInfo[];
    total_walls: number;
}

interface WallInfo {
    wall_id: string;
    panel_name: string;
    brand: string;
    brand_type: string;
    product: string;
    product_type: string;
    total_facings: number;
    shelf_info: {
        shelf_count: number;
        per_shelf: number;
        shelf_capacity: number;
    };
    peg_info: {
        peg_count: number;
        per_peg: number;
        peg_capacity: number;
    };
}

interface StoreWalls {
    store_name: string;
    lob_groups: {
        [key: string]: WallInfo[];
    };
    summary: {
        [key: string]: {
            wall_count: number;
            total_facings: number;
        };
    };
    total_facings: number;
    total_walls: number;
}

const StoreOptimization: React.FC = () => {
    const [stores, setStores] = useState<StoreTemplate[]>([]);
    const [selectedStore, setSelectedStore] = useState<string>('');
    const [storeWalls, setStoreWalls] = useState<StoreWalls | null>(null);
    const [selectedLobs, setSelectedLobs] = useState<string[]>(['Apple Panel', 'TPA Panel', 'Mixed Panel']);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Progress tracking state
    const [progressOpen, setProgressOpen] = useState(false);
    const [currentJobId, setCurrentJobId] = useState<string | null>(null);
    
    // Results viewer state
    const [resultsOpen, setResultsOpen] = useState(false);
    const [completedJobId, setCompletedJobId] = useState<string | null>(null);

    useEffect(() => {
        loadStoreTemplates();
    }, []);

    const loadStoreTemplates = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await apiService.getStoreTemplates();
            if (response.success && response.data) {
                setStores(response.data.stores);
            } else {
                setError(response.error?.message || 'Failed to load store templates');
            }
        } catch (err: any) {
            setError('Unable to connect to backend server');
            console.error('Store templates error:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadStoreWalls = async (storeName: string) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await apiService.getStoreWalls(storeName);
            if (response.success && response.data) {
                setStoreWalls(response.data);
            } else {
                setError(response.error?.message || 'Failed to load store walls');
            }
        } catch (err: any) {
            setError('Unable to load store walls');
            console.error('Store walls error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleStoreChange = (storeName: string) => {
        setSelectedStore(storeName);
        setStoreWalls(null);
        if (storeName) {
            loadStoreWalls(storeName);
        }
    };

    const handleLobToggle = (lob: string) => {
        setSelectedLobs(prev => 
            prev.includes(lob) 
                ? prev.filter(l => l !== lob)
                : [...prev, lob]
        );
    };

    const startOptimization = async () => {
        if (!selectedStore || selectedLobs.length === 0) {
            setError('Please select a store and at least one LOB');
            return;
        }

        try {
            const response = await apiService.startStoreOptimization(selectedStore, {
                optimization_type: 'full_store',
                selected_lobs: selectedLobs,
                additional_params: {}
            });

            if (response.success && response.data) {
                setCurrentJobId(response.data.job_id);
                setProgressOpen(true);
                setError(null);
            } else {
                setError(response.error?.message || 'Failed to start optimization');
            }
        } catch (err: any) {
            setError('Unable to start optimization');
            console.error('Optimization error:', err);
        }
    };

    const handleProgressClose = () => {
        setProgressOpen(false);
        setCurrentJobId(null);
    };

    const handleJobComplete = (result: any) => {
        setProgressOpen(false);
        setCompletedJobId(currentJobId);
        setResultsOpen(true);
    };

    const handleResultsClose = () => {
        setResultsOpen(false);
        setCompletedJobId(null);
    };

    const getLobColor = (lob: string) => {
        switch (lob) {
            case 'Apple Panel': return 'primary';
            case 'TPA Panel': return 'secondary';
            case 'Mixed Panel': return 'success';
            default: return 'default';
        }
    };

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Box display="flex" alignItems="center" sx={{ mb: 1 }}>
                    <Business sx={{ mr: 1 }} />
                    <Typography variant="h5" component="h1">Optimization Options</Typography>
                </Box>
                <Typography variant="body1" color="text.secondary">
                    Choose your optimization type and configure your planogram. The system supports cohort-based planograms, 
                    Line of Business optimization, and full store optimization with multiple strategies.
                </Typography>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {/* Optimization Type Cards */}
            <Grid container spacing={3}>
                {/* Cohort Planogram */}
                <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { elevation: 4 } }}>
                        <CardContent>
                            <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
                                <Category color="primary" sx={{ mr: 1, fontSize: 32 }} />
                                <Typography variant="h6">1. Cohort Planogram</Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                Generate cohort-based planograms showing LOB-accessory relationships with 
                                variable product sizes based on store recommendations.
                            </Typography>
                            <Box sx={{ mb: 2 }}>
                                <Chip label="Recommended" color="success" size="small" sx={{ mr: 1 }} />
                                <Chip label="Size Variations" color="info" size="small" />
                            </Box>
                            <Button 
                                variant="contained" 
                                fullWidth 
                                startIcon={<PlayArrow />}
                                onClick={() => {/* Handle cohort generation */}}
                            >
                                Generate Cohort Planograms
                            </Button>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Line of Business */}
                <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { elevation: 4 } }}>
                        <CardContent>
                            <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
                                <ViewModule color="secondary" sx={{ mr: 1, fontSize: 32 }} />
                                <Typography variant="h6">2. Line of Business</Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                Optimize specific product categories like iPhone cases, iPad cases, 
                                or individual LOB segments with targeted strategies.
                            </Typography>
                            <Box sx={{ mb: 2 }}>
                                <Chip label="Category Specific" color="secondary" size="small" sx={{ mr: 1 }} />
                                <Chip label="Flexible" color="default" size="small" />
                            </Box>
                            <Button 
                                variant="outlined" 
                                fullWidth 
                                startIcon={<PlayArrow />}
                                onClick={() => {/* Handle LOB optimization */}}
                            >
                                Optimize by Category
                            </Button>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Full Store Optimization */}
                <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { elevation: 4 } }}>
                        <CardContent>
                            <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
                                <Analytics color="error" sx={{ mr: 1, fontSize: 32 }} />
                                <Typography variant="h6">3. All Products (Full Store)</Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                Complete store optimization with advanced algorithms, 
                                cross-category optimization, and comprehensive analysis.
                            </Typography>
                            <Box sx={{ mb: 2 }}>
                                <Chip label="Advanced" color="error" size="small" sx={{ mr: 1 }} />
                                <Chip label="Complete Analysis" color="warning" size="small" />
                            </Box>
                            <Button 
                                variant="outlined" 
                                color="error"
                                fullWidth 
                                startIcon={<PlayArrow />}
                                onClick={() => {/* Handle full store optimization */}}
                            >
                                Full Store Optimization
                            </Button>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Information Box */}
            <Alert severity="info" sx={{ mt: 3 }}>
                <Typography variant="body2">
                    <strong>Note:</strong> Please select a store from the "Store Selection & Analysis" tab first. 
                    The system will use the recommended wall counts and LOB distribution from your selected store 
                    to generate optimized planograms.
                </Typography>
            </Alert>

            <Grid container spacing={3} sx={{ mt: 1 }}>
                {/* Feature Comparison */}
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Feature Comparison
                            </Typography>
                            <TableContainer>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell><strong>Feature</strong></TableCell>
                                            <TableCell align="center"><strong>Cohort Planogram</strong></TableCell>
                                            <TableCell align="center"><strong>Line of Business</strong></TableCell>
                                            <TableCell align="center"><strong>Full Store</strong></TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        <TableRow>
                                            <TableCell>Variable Product Sizes</TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell>LOB-Based Distribution</TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell>Sales-Based Optimization</TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell>Cross-Category Analysis</TableCell>
                                            <TableCell align="center"><Cancel color="error" fontSize="small" /></TableCell>
                                            <TableCell align="center"><Typography variant="caption" color="warning.main">Limited</Typography></TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell>Custom Store Templates</TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                            <TableCell align="center"><CheckCircle color="success" fontSize="small" /></TableCell>
                                        </TableRow>
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Progress Tracker */}
            {progressOpen && currentJobId && (
                <ProgressTracker
                    jobId={currentJobId}
                    jobType="store_optimization"
                    open={progressOpen}
                    onClose={handleProgressClose}
                    onComplete={handleJobComplete}
                />
            )}

            {/* Results Viewer */}
            {resultsOpen && completedJobId && (
                <ResultsViewer
                    jobId={completedJobId}
                    open={resultsOpen}
                    onClose={handleResultsClose}
                />
            )}
        </Box>
    );
};

export default StoreOptimization;
