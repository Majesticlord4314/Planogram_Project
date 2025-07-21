import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Box,
    Typography,
    Grid,
    Card,
    CardContent,
    CardMedia,
    Chip,
    IconButton,
    Tabs,
    Tab,
    List,
    ListItem,
    ListItemText,
    ListItemIcon
} from '@mui/material';
import {
    Close as CloseIcon,
    Download as DownloadIcon,
    Image as ImageIcon,
    TableChart as TableChartIcon,
    Assessment as AssessmentIcon,
    Warning as WarningIcon
} from '@mui/icons-material';

import { apiService } from '../services/api';

interface ResultsViewerProps {
    open: boolean;
    jobId: string | null;
    onClose: () => void;
}

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

function TabPanel(props: TabPanelProps) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`results-tabpanel-${index}`}
            aria-labelledby={`results-tab-${index}`}
            {...other}
        >
            {value === index && (
                <Box sx={{ p: 3 }}>
                    {children}
                </Box>
            )}
        </div>
    );
}

const ResultsViewer: React.FC<ResultsViewerProps> = ({ open, jobId, onClose }) => {
    const [result, setResult] = useState<any>(null);
    const [tabValue, setTabValue] = useState(0);
    const [planogramImage, setPlanogramImage] = useState<string | null>(null);
    const [selectedPlanogramIndex, setSelectedPlanogramIndex] = useState(0);

    const [files, setFiles] = useState<any[]>([]);
    const [planograms, setPlanograms] = useState<any[]>([]);

    const fetchResultDetails = React.useCallback(async () => {
        if (!jobId) return;

        try {
            // Fetch job details
            const response = await apiService.getResultDetails(jobId);
            if (response.success && response.data) {
                setResult(response.data);
            }

            // Fetch associated files
            const filesResponse = await fetch(`http://localhost:5000/api/results/${jobId}/files`);
            if (filesResponse.ok) {
                const filesData = await filesResponse.json();
                if (filesData.success && filesData.data) {
                    // Set files and planograms separately
                    setFiles(filesData.data.files || []);
                    setPlanograms(filesData.data.planograms || []);

                    // Set the first planogram as default
                    const allPlanograms = filesData.data.planograms || [];
                    if (allPlanograms.length > 0) {
                        setPlanogramImage(`http://localhost:5000${allPlanograms[0].url}`);
                        setSelectedPlanogramIndex(0);
                    } else {
                        // Fallback to old behavior for backward compatibility
                        const imageFile = filesData.data.files?.find((f: any) =>
                            f.type === 'planogram' && f.name.toLowerCase().includes('.png')
                        );
                        if (imageFile) {
                            setPlanogramImage(`http://localhost:5000${imageFile.url}`);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Failed to fetch result details:', error);
        }
    }, [jobId]);

    useEffect(() => {
        if (open && jobId) {
            fetchResultDetails();
        }
    }, [open, jobId, fetchResultDetails]);

    const handleDownload = async (file: any) => {
        try {
            const response = await fetch(`http://localhost:5000${file.download_url}`);
            if (!response.ok) {
                throw new Error('Download failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Download failed:', error);
            alert('Download failed. File may not be available yet.');
        }
    };

    const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
        setTabValue(newValue);
    };

    if (!result) {
        return (
            <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
                <DialogContent>
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                        <Typography>Loading results...</Typography>
                    </Box>
                </DialogContent>
            </Dialog>
        );
    }

    return (
        <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
            <DialogTitle>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Typography variant="h6">
                        Optimization Results
                    </Typography>
                    <IconButton onClick={onClose} size="small">
                        <CloseIcon />
                    </IconButton>
                </Box>
            </DialogTitle>

            <DialogContent>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                    <Tabs value={tabValue} onChange={handleTabChange}>
                        <Tab label="Overview" />
                        <Tab label="Planogram" />
                        <Tab label="Details" />
                        <Tab label="Downloads" />
                    </Tabs>
                </Box>

                <TabPanel value={tabValue} index={0}>
                    {/* Overview Tab */}
                    <Grid container spacing={3}>
                        <Grid item xs={12} md={6}>
                            <Card>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        Job Information
                                    </Typography>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">
                                            Job ID: {result.job_id?.substring(0, 8)}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Type: {result.job_type}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Status: <Chip label={result.status} size="small" color="success" />
                                        </Typography>
                                    </Box>

                                    {result.parameters && (
                                        <Box>
                                            <Typography variant="subtitle2" gutterBottom>
                                                Parameters:
                                            </Typography>
                                            {Object.entries(result.parameters).map(([key, value]) => (
                                                <Typography key={key} variant="body2">
                                                    {key}: {String(value)}
                                                </Typography>
                                            ))}
                                        </Box>
                                    )}
                                </CardContent>
                            </Card>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <Card>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        Results Summary
                                    </Typography>
                                    {result.result && (
                                        <Grid container spacing={2}>
                                            {result.result.products_placed && (
                                                <Grid item xs={6}>
                                                    <Box textAlign="center">
                                                        <Typography variant="h4" color="success.main">
                                                            {result.result.products_placed}
                                                        </Typography>
                                                        <Typography variant="body2" color="text.secondary">
                                                            Products Placed
                                                        </Typography>
                                                    </Box>
                                                </Grid>
                                            )}
                                            {result.result.products_rejected && (
                                                <Grid item xs={6}>
                                                    <Box textAlign="center">
                                                        <Typography variant="h4" color="warning.main">
                                                            {result.result.products_rejected}
                                                        </Typography>
                                                        <Typography variant="body2" color="text.secondary">
                                                            Products Rejected
                                                        </Typography>
                                                    </Box>
                                                </Grid>
                                            )}
                                            {result.result.metrics?.average_utilization && (
                                                <Grid item xs={12}>
                                                    <Box textAlign="center">
                                                        <Typography variant="h4" color="primary">
                                                            {result.result.metrics.average_utilization.toFixed(1)}%
                                                        </Typography>
                                                        <Typography variant="body2" color="text.secondary">
                                                            Average Utilization
                                                        </Typography>
                                                    </Box>
                                                </Grid>
                                            )}
                                        </Grid>
                                    )}
                                </CardContent>
                            </Card>
                        </Grid>
                    </Grid>
                </TabPanel>

                <TabPanel value={tabValue} index={1}>
                    {/* Planogram Tab */}
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            Generated Planograms
                        </Typography>

                        {planograms.length > 0 ? (
                            <Box>
                                {/* Planogram Tabs if multiple planograms */}
                                {planograms.length > 1 && (
                                    <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                                        <Tabs
                                            value={selectedPlanogramIndex}
                                            onChange={(_, newValue) => {
                                                setSelectedPlanogramIndex(newValue);
                                                setPlanogramImage(`http://localhost:5000${planograms[newValue].url}`);
                                            }}
                                            variant="scrollable"
                                            scrollButtons="auto"
                                        >
                                            {planograms.map((planogram, index) => (
                                                <Tab
                                                    key={index}
                                                    label={planogram.name.replace(/\.(png|jpg|jpeg)$/i, '')}
                                                />
                                            ))}
                                        </Tabs>
                                    </Box>
                                )}

                                {/* Selected Planogram Display */}
                                <Card>
                                    {planogramImage && (
                                        <CardMedia
                                            component="img"
                                            image={planogramImage}
                                            alt={`Planogram ${selectedPlanogramIndex + 1}`}
                                            sx={{ maxHeight: 600, objectFit: 'contain' }}
                                        />
                                    )}
                                    {planograms[selectedPlanogramIndex] && (
                                        <CardContent>
                                            <Typography variant="body2" color="text.secondary">
                                                {planograms[selectedPlanogramIndex].name}
                                            </Typography>
                                            <Button
                                                variant="outlined"
                                                size="small"
                                                startIcon={<DownloadIcon />}
                                                sx={{ mt: 1 }}
                                                onClick={() => handleDownload(planograms[selectedPlanogramIndex])}
                                            >
                                                Download Image
                                            </Button>
                                        </CardContent>
                                    )}
                                </Card>
                            </Box>
                        ) : (
                            <Card sx={{ p: 4, textAlign: 'center', bgcolor: 'grey.100' }}>
                                <ImageIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
                                <Typography variant="h6" color="text.secondary">
                                    Planogram Image Not Available
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    The planogram image is being generated or may not be ready yet.
                                </Typography>
                                <Button
                                    variant="outlined"
                                    sx={{ mt: 2 }}
                                    onClick={() => {
                                        const imageFile = files.find(f => f.type === 'planogram' && f.name.toLowerCase().includes('.png'));
                                        if (imageFile) {
                                            handleDownload(imageFile);
                                        }
                                    }}
                                    disabled={!files.some(f => f.type === 'planogram' && f.name.toLowerCase().includes('.png'))}
                                >
                                    Try Download
                                </Button>
                            </Card>
                        )}
                    </Box>
                </TabPanel>

                <TabPanel value={tabValue} index={2}>
                    {/* Details Tab */}
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            Detailed Results
                        </Typography>

                        {result.result?.warnings && result.result.warnings.length > 0 && (
                            <Card sx={{ mb: 2 }}>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        <WarningIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                                        Warnings ({result.result.warnings.length})
                                    </Typography>
                                    <List dense>
                                        {result.result.warnings.slice(0, 10).map((warning: string, index: number) => (
                                            <ListItem key={index}>
                                                <ListItemIcon>
                                                    <WarningIcon color="warning" fontSize="small" />
                                                </ListItemIcon>
                                                <ListItemText primary={warning} />
                                            </ListItem>
                                        ))}
                                    </List>
                                </CardContent>
                            </Card>
                        )}

                        {result.logs && result.logs.length > 0 && (
                            <Card>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        Execution Logs
                                    </Typography>
                                    <Box
                                        sx={{
                                            maxHeight: 300,
                                            overflow: 'auto',
                                            bgcolor: '#1e1e1e',
                                            color: '#fff',
                                            p: 2,
                                            borderRadius: 1,
                                            fontFamily: 'monospace'
                                        }}
                                    >
                                        {result.logs.map((log: string, index: number) => (
                                            <Typography key={index} variant="body2" sx={{ mb: 0.5 }}>
                                                {log}
                                            </Typography>
                                        ))}
                                    </Box>
                                </CardContent>
                            </Card>
                        )}
                    </Box>
                </TabPanel>

                <TabPanel value={tabValue} index={3}>
                    {/* Downloads Tab */}
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            Available Downloads
                        </Typography>

                        {(files.length > 0 || planograms.length > 0) ? (
                            <Box>
                                {/* Planogram Images Section */}
                                {planograms.length > 0 && (
                                    <Box sx={{ mb: 4 }}>
                                        <Typography variant="h6" gutterBottom sx={{ color: 'primary.main' }}>
                                            Planogram Images
                                        </Typography>
                                        <Grid container spacing={2}>
                                            {planograms.map((planogram, index) => (
                                                <Grid item xs={12} sm={6} md={4} key={`planogram-${index}`}>
                                                    <Card>
                                                        <CardContent>
                                                            <Box display="flex" alignItems="center" mb={2}>
                                                                <ImageIcon color="primary" sx={{ mr: 1 }} />
                                                                <Typography variant="h6" noWrap>
                                                                    {planogram.name}
                                                                </Typography>
                                                            </Box>
                                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                                                High-resolution planogram visualization
                                                            </Typography>
                                                            <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                                                                Size: {planogram.size ? ((planogram.size / 1024).toFixed(1) + ' KB') : 'N/A'} • Created: {planogram.created ? new Date(planogram.created).toLocaleDateString() : 'N/A'}
                                                            </Typography>
                                                            <Button
                                                                variant="contained"
                                                                fullWidth
                                                                startIcon={<DownloadIcon />}
                                                                onClick={() => handleDownload(planogram)}
                                                            >
                                                                Download
                                                            </Button>
                                                        </CardContent>
                                                    </Card>
                                                </Grid>
                                            ))}
                                        </Grid>
                                    </Box>
                                )}

                                {/* Other Files Section */}
                                {files.length > 0 && (
                                    <Box>
                                        <Typography variant="h6" gutterBottom sx={{ color: 'secondary.main' }}>
                                            Reports & Data Files
                                        </Typography>
                                        <Grid container spacing={2}>
                                            {files.map((file, index) => {
                                                const getFileIcon = (fileName: string, fileType: string) => {
                                                    if (fileType === 'product_list' || (fileName.toLowerCase().includes('products') && fileName.toLowerCase().includes('.txt'))) {
                                                        return <AssessmentIcon color="secondary" sx={{ mr: 1 }} />;
                                                    } else if (fileName.toLowerCase().includes('.xlsx')) {
                                                        return <TableChartIcon color="primary" sx={{ mr: 1 }} />;
                                                    } else if (fileName.toLowerCase().includes('.txt') || fileName.toLowerCase().includes('.csv')) {
                                                        return <AssessmentIcon color="primary" sx={{ mr: 1 }} />;
                                                    }
                                                    return <AssessmentIcon color="primary" sx={{ mr: 1 }} />;
                                                };

                                                const getFileDescription = (fileName: string, fileType: string) => {
                                                    if (fileType === 'product_list' || (fileName.toLowerCase().includes('products') && fileName.toLowerCase().includes('.txt'))) {
                                                        return 'Product recommendations for each facing and category';
                                                    } else if (fileName.toLowerCase().includes('.xlsx')) {
                                                        return 'Detailed product placement data and metrics';
                                                    } else if (fileName.toLowerCase().includes('.txt')) {
                                                        return 'Text report with optimization details';
                                                    } else if (fileName.toLowerCase().includes('.csv')) {
                                                        return 'Raw data export for analysis';
                                                    }
                                                    return 'Generated file from optimization';
                                                };

                                                const formatFileSize = (bytes: number) => {
                                                    if (bytes === 0) return '0 Bytes';
                                                    const k = 1024;
                                                    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                                                    const i = Math.floor(Math.log(bytes) / Math.log(k));
                                                    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
                                                };

                                                return (
                                                    <Grid item xs={12} sm={6} md={4} key={`file-${index}`}>
                                                        <Card>
                                                            <CardContent>
                                                                <Box display="flex" alignItems="center" mb={2}>
                                                                    {getFileIcon(file.name, file.type)}
                                                                    <Typography variant="h6" noWrap>
                                                                        {file.name}
                                                                    </Typography>
                                                                </Box>
                                                                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                                                    {getFileDescription(file.name, file.type)}
                                                                </Typography>
                                                                <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                                                                    Size: {file.size ? formatFileSize(file.size) : 'N/A'} • Created: {file.created ? new Date(file.created).toLocaleDateString() : 'N/A'}
                                                                </Typography>
                                                                <Button
                                                                    variant="contained"
                                                                    fullWidth
                                                                    startIcon={<DownloadIcon />}
                                                                    onClick={() => handleDownload(file)}
                                                                >
                                                                    Download
                                                                </Button>
                                                            </CardContent>
                                                        </Card>
                                                    </Grid>
                                                );
                                            })}
                                        </Grid>
                                    </Box>
                                )}
                            </Box>
                        ) : (
                            <Card sx={{ p: 4, textAlign: 'center', bgcolor: 'grey.100' }}>
                                <AssessmentIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
                                <Typography variant="h6" color="text.secondary">
                                    No Files Available
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Files may still be generating or there was an issue with the optimization.
                                </Typography>
                            </Card>
                        )}
                    </Box>
                </TabPanel>
            </DialogContent>

            <DialogActions>
                <Button onClick={onClose} variant="contained">
                    Close
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default ResultsViewer;