import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormLabel,
  Chip,
  Grid,
  Card,
  CardContent,
  Alert
} from '@mui/material';
import {
  Close as CloseIcon,
  PlayArrow as PlayArrowIcon
} from '@mui/icons-material';

import { apiService, ValidParameters } from '../services/api';

interface OptimizationFormProps {
  open: boolean;
  onClose: () => void;
  onStart: (jobId: string, jobType: string) => void;
}

const OptimizationForm: React.FC<OptimizationFormProps> = ({ open, onClose, onStart }) => {
  const [optimizationType, setOptimizationType] = useState<string>('cohort');
  const [lob, setLob] = useState<string>('iPhone');
  const [category, setCategory] = useState<string>('cases');
  const [storeType, setStoreType] = useState<string>('flagship');
  const [strategy, setStrategy] = useState<string>('sales_velocity');
  const [validParams, setValidParams] = useState<ValidParameters | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      fetchValidParameters();
    }
  }, [open]);

  const fetchValidParameters = async () => {
    try {
      const response = await apiService.getValidParameters();
      if (response.success && response.data) {
        setValidParams(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch valid parameters:', error);
    }
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      let response;

      switch (optimizationType) {
        case 'cohort':
          response = await apiService.startCohortOptimization(lob, storeType);
          break;
        case 'lob':
          response = await apiService.startLOBOptimization(lob, storeType, strategy);
          break;
        case 'category':
          response = await apiService.startCategoryOptimization(category, storeType, strategy);
          break;
        case 'full_store':
          response = await apiService.startFullStoreOptimization(storeType, strategy);
          break;
        default:
          throw new Error('Invalid optimization type');
      }

      if (response.success && response.data?.job_id) {
        onStart(response.data.job_id, optimizationType);
        onClose();
      } else {
        alert(`Failed to start optimization: ${response.error?.message || 'Unknown error'}`);
      }
    } catch (error: any) {
      console.error('Optimization error:', error);
      alert(`Error starting optimization: ${error.message || 'Network error'}`);
    } finally {
      setLoading(false);
    }
  };

  const getOptimizationDescription = () => {
    switch (optimizationType) {
      case 'cohort':
        return `Generate cohort-based planogram for ${lob} accessories in ${storeType} store. Uses customer behavior data and attach rates.`;
      case 'lob':
        return `Optimize ${lob} product line for ${storeType} store using ${strategy} strategy. Includes all product categories for this LOB.`;
      case 'category':
        return `Optimize ${category} category for ${storeType} store using ${strategy} strategy. Focuses on specific product type.`;
      case 'full_store':
        return `Complete store optimization for ${storeType} store using ${strategy} strategy. Includes all products and categories.`;
      default:
        return '';
    }
  };

  const getAvailableDatasets = () => {
    const datasets = [];
    
    if (optimizationType === 'cohort' || optimizationType === 'lob') {
      switch (lob) {
        case 'iPhone':
          datasets.push('iPhone Cases (cases_sales.csv)', 'iPhone Cohort Data (iphone_planogram_cohorts.csv)');
          break;
        case 'iPad':
          datasets.push('iPad Cases (ipad-cases-transformed.csv)', 'iPad Cohort Data (ipad_planogram_cohorts.csv)');
          break;
        case 'Mac':
          datasets.push('Mac Accessories (mac-accessories-transformed.csv)', 'Mac Cohort Data (mac_planogram_cohorts.csv)');
          break;
        case 'Watch':
          datasets.push('Watch Accessories (combined_watch.csv)', 'Watch Cohort Data (watch_planogram_cohorts.csv)');
          break;
        case 'AirPods':
          datasets.push('AirPods Data (if available)');
          break;
      }
    } else if (optimizationType === 'category') {
      switch (category) {
        case 'cases':
          datasets.push('Phone Cases (cases_sales.csv)');
          break;
        case 'cables':
          datasets.push('Cables & Adapters (cables_adapters_sales.csv)');
          break;
        case 'screen_protectors':
          datasets.push('Screen Protectors (screen_protectors_sales.csv)');
          break;
        case 'others':
          datasets.push('Mounts & Others (mounts_others_sales.csv)');
          break;
      }
    } else {
      datasets.push('All Available Datasets', 'Processed Data (planogram_sleeves_bags.csv)');
    }

    return datasets;
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">
            Configure Planogram Optimization
          </Typography>
          <Button onClick={onClose} size="small">
            <CloseIcon />
          </Button>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Grid container spacing={3}>
          {/* Optimization Type Selection */}
          <Grid item xs={12}>
            <FormControl component="fieldset">
              <FormLabel component="legend">Optimization Type</FormLabel>
              <RadioGroup
                value={optimizationType}
                onChange={(e) => setOptimizationType(e.target.value)}
                row
              >
                <FormControlLabel 
                  value="cohort" 
                  control={<Radio />} 
                  label="Cohort Planogram" 
                />
                <FormControlLabel 
                  value="lob" 
                  control={<Radio />} 
                  label="Line of Business" 
                />
                <FormControlLabel 
                  value="category" 
                  control={<Radio />} 
                  label="Product Category" 
                />
                <FormControlLabel 
                  value="full_store" 
                  control={<Radio />} 
                  label="Full Store" 
                />
              </RadioGroup>
            </FormControl>
          </Grid>

          {/* LOB Selection (for cohort and lob types) */}
          {(optimizationType === 'cohort' || optimizationType === 'lob') && (
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Line of Business</InputLabel>
                <Select
                  value={lob}
                  onChange={(e) => setLob(e.target.value)}
                  label="Line of Business"
                >
                  {validParams?.lobs.map((lobOption) => (
                    <MenuItem key={lobOption} value={lobOption}>
                      {lobOption}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}

          {/* Category Selection (for category type) */}
          {optimizationType === 'category' && (
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Product Category</InputLabel>
                <Select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  label="Product Category"
                >
                  {validParams?.categories.map((categoryOption) => (
                    <MenuItem key={categoryOption} value={categoryOption}>
                      {categoryOption.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}

          {/* Store Type Selection */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Store Type</InputLabel>
              <Select
                value={storeType}
                onChange={(e) => setStoreType(e.target.value)}
                label="Store Type"
              >
                {validParams?.store_types.map((storeOption) => (
                  <MenuItem key={storeOption} value={storeOption}>
                    {storeOption.charAt(0).toUpperCase() + storeOption.slice(1)} Store
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Strategy Selection (not for cohort) */}
          {optimizationType !== 'cohort' && (
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Optimization Strategy</InputLabel>
                <Select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                  label="Optimization Strategy"
                >
                  {validParams?.strategies.map((strategyOption) => (
                    <MenuItem key={strategyOption} value={strategyOption}>
                      {strategyOption.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}

          {/* Configuration Summary */}
          <Grid item xs={12}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Configuration Summary
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {getOptimizationDescription()}
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Data Sources:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {getAvailableDatasets().map((dataset, index) => (
                      <Chip key={index} label={dataset} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Box>

                {optimizationType !== 'cohort' && validParams?.strategy_descriptions[strategy] && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <strong>Strategy:</strong> {validParams.strategy_descriptions[strategy]}
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Cancel
        </Button>
        <Button 
          onClick={handleStart} 
          variant="contained" 
          disabled={loading}
          startIcon={<PlayArrowIcon />}
        >
          {loading ? 'Starting...' : 'Start Optimization'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default OptimizationForm;