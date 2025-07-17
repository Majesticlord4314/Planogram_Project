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

  const fetchResultDetails = React.useCallback(async () => {
    if (!jobId) return;

    try {
      const response = await apiService.getResultDetails(jobId);
      if (response.success && response.data) {
        setResult(response.data);
        
        // Try to load planogram image if available
        if (response.data.files && response.data.files.length > 0) {
          const imageFile = response.data.files.find((f: any) => 
            f.name.includes('retail.png') || f.name.includes('.png')
          );
          if (imageFile) {
            // Load the actual image from the backend
            setPlanogramImage(`http://localhost:5000/api/files/${imageFile.name}`);
          }
        } else if (response.data.result && response.data.result.files) {
          // Check if files are in the result object
          const imageFile = response.data.result.files.find((f: any) => 
            f.name.includes('retail.png') || f.name.includes('.png')
          );
          if (imageFile) {
            setPlanogramImage(`http://localhost:5000/api/files/${imageFile.name}`);
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

  const handleDownload = async (fileType: string) => {
    if (!jobId) return;

    try {
      const blob = await apiService.downloadResultFile(jobId, fileType);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `planogram_${jobId.substring(0, 8)}_${fileType}`;
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
              Generated Planogram
            </Typography>
            {planogramImage ? (
              <Card>
                <CardMedia
                  component="img"
                  image={planogramImage}
                  alt="Generated Planogram"
                  sx={{ maxHeight: 600, objectFit: 'contain' }}
                />
              </Card>
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
                  onClick={() => handleDownload('planogram')}
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
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={4}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      <ImageIcon color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6">
                        Planogram Image
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      High-resolution planogram visualization
                    </Typography>
                    <Button 
                      variant="contained" 
                      fullWidth 
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload('planogram')}
                    >
                      Download PNG
                    </Button>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      <TableChartIcon color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6">
                        Excel Report
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Detailed product placement data
                    </Typography>
                    <Button 
                      variant="contained" 
                      fullWidth 
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload('excel')}
                    >
                      Download XLSX
                    </Button>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      <AssessmentIcon color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6">
                        CSV Report
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Raw data export for analysis
                    </Typography>
                    <Button 
                      variant="contained" 
                      fullWidth 
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload('report')}
                    >
                      Download CSV
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
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