import React, { useState, useEffect } from 'react';
import { apiService, getFullApiUrl } from '../services/api';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Box,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormGroup,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Alert,
  Divider,
  LinearProgress,
  TextField,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  Store,
  LocationOn as MapPin,
  Business as Building,
  BarChart,
  TrendingUp,
  Inventory as Package,

  CheckCircle,
  Edit,
  Save,
  Cancel,
  DonutLarge,
  Timeline
} from '@mui/icons-material';

interface StoreData {
  location: string;
  city: string;
  total_walls: number;
  lob_breakdown: Record<string, string>;
  capacity_summary: Record<string, number>;
  wall_details: Record<string, {
    walls: string[];
    total_capacity: number | string;
    wall_count: number;
    products: string[];
  }>;
}

interface LOBRecommendation {
  priority_score: number;
  current_walls: number;
  current_capacity: number;
  target_allocation: number;
  recommendation: string;
}

interface StoreRecommendations {
  optimization: {
    current_distribution: Record<string, number>;
    optimal_distribution: Record<string, number>;
    changes_needed: Record<string, any>;
  };
  lob_priorities: Record<string, LOBRecommendation>;
  summary: string;
}

interface GenerationResult {
  store_name: string;
  generation_mode?: string;
  total_planograms?: number;
  lob_categories?: string[];
  planograms?: Record<string, string[]>;
  generated_files?: Array<{
    type: string;
    accessory: string;
    filename: string;
    description: string;
  }>;
  // Smart accessory optimization fields
  optimization_type?: string;
  optimization_results?: string[];
  total_accessories?: number;
  message?: string;
}

// New workflow states
type WorkflowStep = 'store-selection' | 'analysis' | 'optimization-selection' | 'category-selection' | 'generation' | 'results';
type OptimizationType = 'cohort' | 'accessory' | 'full-store';

// Apple product ecosystems for cohort selection
const COHORT_CATEGORIES = [
  'iphone',
  'ipad',
  'mac',
  'watch',
  'airpods'
];

// Accessory types for accessory-based optimization
const ACCESSORY_CATEGORIES = [
  'cases',
  'charging_cables',
  'audio',
  'bags_sleeves',
  'gaming',
  'organizers',
  'misc_accessories'
];

const StoreSelector: React.FC = () => {
  // Workflow state
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('store-selection');
  const [selectedOptimization, setSelectedOptimization] = useState<OptimizationType | null>(null);
  
  // Data states
  const [storeAnalysis, setStoreAnalysis] = useState<any>(null);
  const [selectedStore, setSelectedStore] = useState<string>('');
  const [storeDetails, setStoreDetails] = useState<StoreData | null>(null);
  const [recommendations, setRecommendations] = useState<StoreRecommendations | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Selection states
  const [selectedCohorts, setSelectedCohorts] = useState<string[]>([]);
  const [selectedAccessories, setSelectedAccessories] = useState<string[]>([]);
  
  // Generation states
  const [generating, setGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<GenerationResult | null>(null);
  
  // Wall editing state
  const [editingWalls, setEditingWalls] = useState(false);
  const [editedWallCounts, setEditedWallCounts] = useState<Record<string, number>>({});
  const [originalWallCounts, setOriginalWallCounts] = useState<Record<string, number>>({});
  
  // Optimization adjustments
  const [optimizationAdjustments, setOptimizationAdjustments] = useState<Record<string, number>>({});
  const [appliedRecommendations, setAppliedRecommendations] = useState(false);
  
  // Force re-render trigger for charts
  const [chartUpdateTrigger, setChartUpdateTrigger] = useState(0);

  useEffect(() => {
    fetchStoreAnalysis();
  }, []);

  useEffect(() => {
    if (selectedStore && currentStep === 'store-selection') {
      fetchStoreDetails();
      fetchRecommendations();
      setCurrentStep('analysis');
    }
  }, [selectedStore, currentStep]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchStoreAnalysis = async () => {
    try {
      setLoading(true);
      console.log('Fetching store analysis...');
      const response = await fetch('/api/stores/analysis');
      console.log('Store analysis response status:', response.status);
      const data = await response.json();
      console.log('Store analysis data:', data);
      
      if (data.success) {
        setStoreAnalysis(data.data);
        console.log('Store analysis loaded, available stores:', Object.keys(data.data.store_selector || {}));
      } else {
        console.error('Store analysis API error:', data.error);
      }
    } catch (error) {
      console.error('Error fetching store analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStoreDetails = async () => {
    if (!selectedStore) return;
    
    try {
      console.log('Fetching store details for:', selectedStore);
      const response = await fetch(`/api/stores/${encodeURIComponent(selectedStore)}/lob-details`);
      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);
      
      if (data.success) {
        setStoreDetails(data.data);
      } else {
        console.error('API error:', data.error);
      }
    } catch (error) {
      console.error('Error fetching store details:', error);
    }
  };

  const fetchRecommendations = async () => {
    if (!selectedStore) return;
    
    try {
      console.log('Fetching recommendations for:', selectedStore);
      const response = await fetch(`/api/stores/${encodeURIComponent(selectedStore)}/recommendations`);
      console.log('Recommendations response status:', response.status);
      const data = await response.json();
      console.log('Recommendations data:', data);
      
      if (data.success) {
        setRecommendations(data.data);
      } else {
        console.error('Recommendations API error:', data.error);
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  const generatePlanograms = async () => {
    if (!selectedStore) return;

    try {
      setGenerating(true);
      setCurrentStep('generation');

      const response = await apiService.generatePlanogram(selectedStore, selectedAccessories);
      if (response.data && response.data.job_id) {
        pollJobStatus(response.data.job_id);
      }

    } catch (error) {
      console.error('Error generating planograms:', error);
      setGenerating(false);
      setCurrentStep('category-selection');
    }
  };

  const pollJobStatus = async (jobId: string) => {
    console.log(`Starting to poll job status for job ID: ${jobId}`);
    
    // Set a timeout to prevent infinite polling
    const maxPollTime = 300000; // 5 minutes (increased from 2 minutes)
    const startTime = Date.now();
    
    const interval = setInterval(async () => {
      try {
        const elapsedTime = Date.now() - startTime;
        console.log(`Polling job ${jobId} - elapsed time: ${Math.round(elapsedTime / 1000)}s`);
        
        // Check if we've exceeded the max poll time
        if (elapsedTime > maxPollTime) {
          console.warn('Polling timeout reached, checking job result anyway');
          const finalResponse = await fetch(`/api/jobs/${jobId}`);
          const finalData = await finalResponse.json();
          console.log('Final timeout check response:', finalData);
          
          // Check if the response has the job data directly (not nested under data)
          if (finalData.result) {
            console.log('Found result in timeout check, showing results');
            setGenerationResult(finalData.result);
            setGenerating(false);
            setCurrentStep('results');
          } else {
            console.log('No result found in timeout, creating fallback');
            // Create a fallback result
            setGenerationResult({
              store_name: selectedStore,
              optimization_type: 'accessory',
              generated_files: selectedAccessories.map(acc => ({
                type: 'planogram_image',
                accessory: acc,
                filename: `${acc}_fallback.txt`,
                description: `${acc.replace('_', ', ').replace(/\b\w/g, c => c.toUpperCase())} (Timeout)`
              })),
              message: 'Job processing took too long, showing partial results'
            });
            setGenerating(false);
            setCurrentStep('results');
          }
          clearInterval(interval);
          return;
        }
        
        const response = await fetch(`/api/jobs/${jobId}`);
        const data = await response.json();
        console.log(`Job ${jobId} status response:`, data);
        
        // The backend returns job data directly, not nested under 'data'
        if (data.status === 'completed') {
          console.log('Job completed! Result:', data.result);
          setGenerationResult(data.result);
          setGenerating(false);
          setCurrentStep('results');
          clearInterval(interval);
        } else if (data.status === 'failed') {
          console.error('Job failed:', data.error);
          // Even if job failed, check if there's a partial result
          if (data.result) {
            console.log('Job failed but has partial result, showing it');
            setGenerationResult(data.result);
            setGenerating(false);
            setCurrentStep('results');
          } else {
            console.log('Job failed with no result, going back to category selection');
            setGenerating(false);
            setCurrentStep('category-selection');
          }
          clearInterval(interval);
        } else if (data.status === 'running') {
          console.log('Job is still running...');
        } else if (data.status === 'pending') {
          console.log('Job is pending...');
        } else {
          console.log(`Job status: ${data.status}`);
        }
      } catch (error) {
        console.error('Error polling job status:', error);
        setGenerating(false);
        setCurrentStep('category-selection');
        clearInterval(interval);
      }
    }, 2000); // Poll every 2 seconds
    
    // Return the interval ID so it can be cleared if needed
    return interval;
  };

  const getStoreOptions = () => {
    if (!storeAnalysis?.store_selector) return [];
    return Object.keys(storeAnalysis.store_selector);
  };

  const getStoreDisplayName = (storeName: string) => {
    if (!storeAnalysis?.store_selector?.[storeName]) return storeName;
    const storeData = storeAnalysis.store_selector[storeName];
    return `${storeName} (${storeData.city})`;
  };

  const formatLOBName = (lob: string) => {
    return lob.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatCohortName = (cohort: string) => {
    const formatMap: Record<string, string> = {
      'iphone': 'iPhone',
      'ipad': 'iPad',
      'mac': 'Mac', 
      'watch': 'Apple Watch',
      'airpods': 'AirPods'
    };
    return formatMap[cohort] || formatLOBName(cohort);
  };

  const formatAccessoryName = (accessory: string) => {
    const formatMap: Record<string, string> = {
      'cases': 'Cases & Covers',
      'charging_cables': 'Charging & Cables',
      'ipad_accessories': 'iPad Accessories',
      'audio': 'Audio Products',
      'bags_sleeves': 'Bags & Sleeves',
      'organizers': 'Organizers & Hubs',
      'misc_accessories': 'Miscellaneous'
    };
    return formatMap[accessory] || formatLOBName(accessory);
  };

  const handleOptimizationSelect = (type: OptimizationType) => {
    setSelectedOptimization(type);
    if (type === 'full-store') {
      setCurrentStep('generation');
      generatePlanograms();
    } else {
      setCurrentStep('category-selection');
    }
  };

  const handleBackToAnalysis = () => {
    setCurrentStep('analysis');
    setSelectedOptimization(null);
    setSelectedCohorts([]);
    setSelectedAccessories([]);
  };

  const handleBackToSelection = () => {
    setCurrentStep('store-selection');
    setSelectedStore('');
    setStoreDetails(null);
    setRecommendations(null);
    setSelectedOptimization(null);
    setSelectedCohorts([]);
    setSelectedAccessories([]);
    setGenerationResult(null);
    setEditingWalls(false);
    setEditedWallCounts({});
    setOriginalWallCounts({});
    setOptimizationAdjustments({});
    setAppliedRecommendations(false);
  };

  const startEditingWalls = () => {
    if (!storeDetails) return;
    
    const currentCounts: Record<string, number> = {};
    Object.entries(storeDetails.wall_details).forEach(([lob, details]) => {
      currentCounts[lob] = details.wall_count;
    });
    
    setOriginalWallCounts(currentCounts);
    setEditedWallCounts(currentCounts);
    setEditingWalls(true);
  };

  const saveWallChanges = async () => {
    if (!storeDetails) return;
    
    // Validate that total walls haven't changed (should be conserved)
    const originalTotal = Object.values(originalWallCounts).reduce((sum, count) => sum + count, 0);
    const newTotal = Object.values(editedWallCounts).reduce((sum, count) => sum + count, 0);
    
    if (originalTotal !== newTotal) {
      alert(`Total walls must remain ${originalTotal}. Current total: ${newTotal}`);
      return;
    }
    
    try {
      console.log('Saving wall changes:', editedWallCounts);
      const response = await fetch(
        `/api/stores/${encodeURIComponent(selectedStore)}/save-wall-config`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ wall_counts: editedWallCounts })
        }
      );
      const data = await response.json();
      console.log('Save response:', data);
      
      if (data.success) {
        // Create a deep copy of store details
        const updatedStoreDetails: StoreData = {
          ...storeDetails,
          total_walls: newTotal,
          wall_details: {}
        };
        
        // Update all wall details with new counts
        Object.entries(storeDetails.wall_details).forEach(([lob, details]) => {
          updatedStoreDetails.wall_details[lob] = {
            ...details,
            wall_count: editedWallCounts[lob] ?? details.wall_count
          };
        });
        
        // Update state immediately for UI responsiveness
        setStoreDetails(updatedStoreDetails);
        setEditingWalls(false);
        
        // Clear editing states
        setEditedWallCounts({});
        setOriginalWallCounts({});
        
        // Force chart update
        setChartUpdateTrigger(prev => prev + 1);
        
        // Re-fetch recommendations to reflect backend changes
        console.log('Refetching recommendations...');
        await fetchRecommendations();
        
        // Reset optimization adjustments
        setOptimizationAdjustments({});
        setAppliedRecommendations(false);
        
        console.log('Wall configuration saved successfully');
      } else {
        console.error('Save failed:', data.error);
        alert('Failed to save wall configuration: ' + data.error);
      }
    } catch (error) {
      console.error('Error saving wall configuration:', error);
      alert('Error saving wall configuration: ' + error);
    }
  };

  const cancelWallChanges = () => {
    setEditedWallCounts(originalWallCounts);
    setEditingWalls(false);
  };

  const updateWallCount = (lob: string, count: number) => {
    const newCount = Math.max(0, count);
    console.log(`Updating wall count for ${lob}: ${count} -> ${newCount}`);
    
    setEditedWallCounts(prev => {
      const updated = {
        ...prev,
        [lob]: newCount
      };
      console.log('Updated wall counts:', updated);
      return updated;
    });
    
    // Trigger chart update
    setChartUpdateTrigger(prev => prev + 1);
  };

  const adjustOptimization = (lob: string, adjustment: number) => {
    if (!recommendations?.optimization?.changes_needed) return;
    
    const currentAdjustments = { ...optimizationAdjustments };
    const currentValue = currentAdjustments[lob] || 0;
    const newValue = currentValue + adjustment;
    
    // Check if this would make the final wall count negative
    const currentWalls = storeDetails?.wall_details[lob]?.wall_count || 0;
    const finalWalls = currentWalls + newValue;
    
    if (finalWalls < 0) {
      console.log('Cannot reduce walls below 0');
      return;
    }
    
    // Calculate current total
    const currentTotal = Object.values(currentAdjustments).reduce((sum: number, val: number) => sum + val, 0);
    const newTotal = currentTotal - currentValue + newValue;
    
    // For zero-sum constraint: if total would become non-zero, try to balance it
    if (newTotal !== 0) {
      // Find another LOB to balance the change
      const otherLobs = Object.keys(recommendations.optimization.changes_needed).filter(l => l !== lob);
      
      if (otherLobs.length > 0) {
        // Distribute the imbalance across other LOBs
        const balancePerLob = -newTotal / otherLobs.length;
        
        // Check if this balancing is feasible (won't make any LOB negative)
        let canBalance = true;
        for (const otherLob of otherLobs) {
          const otherCurrentValue = currentAdjustments[otherLob] || 0;
          const otherCurrentWalls = storeDetails?.wall_details[otherLob]?.wall_count || 0;
          const otherFinalWalls = otherCurrentWalls + otherCurrentValue + balancePerLob;
          
          if (otherFinalWalls < 0) {
            canBalance = false;
            break;
          }
        }
        
        if (canBalance) {
          // Apply the main change
          currentAdjustments[lob] = newValue;
          
          // Balance with other LOBs
          otherLobs.forEach(otherLob => {
            const otherCurrentValue = currentAdjustments[otherLob] || 0;
            const newOtherValue = otherCurrentValue + balancePerLob;
            
            if (Math.abs(newOtherValue) < 0.001) {
              delete currentAdjustments[otherLob];
            } else {
              currentAdjustments[otherLob] = Math.round(newOtherValue);
            }
          });
        } else {
          console.log('Cannot balance the adjustment without making other LOBs negative');
          return;
        }
      } else {
        // Only one LOB, can't balance
        console.log('Cannot maintain zero-sum with only one LOB');
        return;
      }
    } else {
      // Total is zero, just apply the change
      currentAdjustments[lob] = newValue;
    }
    
    // Remove entries that are zero to keep the object clean
    if (Math.abs(currentAdjustments[lob]) < 0.001) {
      delete currentAdjustments[lob];
    }
    
    setOptimizationAdjustments(currentAdjustments);
  };

  const applyRecommendations = () => {
    if (!recommendations?.optimization?.changes_needed) return;
    
    const newAdjustments: Record<string, number> = {};
    let totalChange = 0;
    
    // First pass: collect all changes
    Object.entries(recommendations.optimization.changes_needed).forEach(([lob, change]: [string, any]) => {
      const wallsAffected = change.walls_affected || 0;
      newAdjustments[lob] = wallsAffected;
      totalChange += wallsAffected;
    });
    
    // If total is not zero, we need to balance it
    // This should not happen with proper recommendations, but let's handle it
    if (totalChange !== 0) {
      console.warn('Recommendations do not sum to zero:', totalChange);
      // Find the largest positive change and adjust it to balance
      const entries = Object.entries(newAdjustments);
      if (entries.length > 0) {
        const [largestLob] = entries.reduce((max, current) => 
          Math.abs(current[1]) > Math.abs(max[1]) ? current : max
        );
        newAdjustments[largestLob] -= totalChange;
      }
    }
    
    setOptimizationAdjustments(newAdjustments);
    setAppliedRecommendations(true);
  };

  const resetOptimizationAdjustments = () => {
    setOptimizationAdjustments({});
    setAppliedRecommendations(false);
  };

  // Generate data for charts
  const getChartData = () => {
    if (!storeDetails) return { pieData: [], barData: [] };
    
    // Determine which wall counts to use
    const useEditedCounts = editingWalls && Object.keys(editedWallCounts).length > 0;
    const totalWalls = useEditedCounts 
      ? Object.values(editedWallCounts).reduce((sum, count) => sum + count, 0)
      : storeDetails.total_walls;
    
    const pieData = Object.entries(storeDetails.wall_details)
      .map(([lob, details]) => {
        const wallCount = useEditedCounts 
          ? (editedWallCounts[lob] ?? details.wall_count) 
          : details.wall_count;
        return {
          name: formatLOBName(lob),
          value: wallCount,
          percentage: totalWalls > 0 ? Math.round((wallCount / totalWalls) * 100) : 0
        };
      })
      .filter(entry => entry.value > 0);

    const barData = Object.entries(storeDetails.wall_details)
      .map(([lob, details]) => {
        const wallCount = useEditedCounts 
          ? (editedWallCounts[lob] ?? details.wall_count) 
          : details.wall_count;
        return {
          lob: formatLOBName(lob),
          walls: wallCount,
          capacity: typeof details.total_capacity === 'number' ? details.total_capacity : 0
        };
      })
      .filter(entry => entry.walls > 0);

    return { pieData, barData };
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d'];
  
  // Use the trigger to force chart recalculation
  const { pieData, barData } = React.useMemo(() => getChartData(), [
    storeDetails, 
    editingWalls, 
    editedWallCounts, 
    chartUpdateTrigger
  ]);

  if (loading) {
    return (
      <Box display="flex" alignItems="center" justifyContent="center" minHeight="300px">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading store analysis...</Typography>
      </Box>
    );
  }

  // Step-by-step render based on workflow
  const renderStoreSelection = () => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
          <MapPin sx={{ mr: 1 }} />
          <Typography variant="h6">Select Store</Typography>
        </Box>
        
        <FormControl fullWidth>
          <InputLabel>Choose a store to analyze</InputLabel>
          <Select
            value={selectedStore}
            onChange={(e) => setSelectedStore(e.target.value)}
            label="Choose a store to analyze"
          >
            {getStoreOptions().map(store => (
              <MenuItem key={store} value={store}>
                {getStoreDisplayName(store)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </CardContent>
    </Card>
  );

  const renderAnalysis = () => (
    <Box>
      {/* Store Info Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
            <Box display="flex" alignItems="center">
              <Store sx={{ mr: 1 }} />
              <Typography variant="h6">{getStoreDisplayName(selectedStore)}</Typography>
            </Box>
            <Button variant="outlined" size="small" onClick={handleBackToSelection}>
              Change Store
            </Button>
          </Box>
          
          {storeDetails && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center">
                  <Building sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>Location:</Typography>
                  <Typography variant="body2" fontWeight="medium">{storeDetails.location}</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center">
                  <MapPin sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>City:</Typography>
                  <Typography variant="body2" fontWeight="medium">{storeDetails.city}</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center">
                  <Package sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>Total Walls:</Typography>
                  <Typography variant="body2" fontWeight="medium">{storeDetails.total_walls}</Typography>
                </Box>
              </Grid>
            </Grid>
          )}
        </CardContent>
      </Card>

      {/* Current LOB Breakdown with Visualizations */}
      {storeDetails && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
              <Box display="flex" alignItems="center">
                <BarChart sx={{ mr: 1 }} />
                <Typography variant="h6">Current Wall Distribution</Typography>
              </Box>
              <Box>
                {!editingWalls ? (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Edit />}
                    onClick={startEditingWalls}
                  >
                    Edit Wall Counts
                  </Button>
                ) : (
                  <Box display="flex" gap={1}>
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<Save />}
                      onClick={saveWallChanges}
                    >
                      Save
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<Cancel />}
                      onClick={cancelWallChanges}
                    >
                      Cancel
                    </Button>
                  </Box>
                )}
              </Box>
            </Box>

            {/* Visual Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
                    <DonutLarge sx={{ mr: 1 }} />
                    <Typography variant="subtitle1">Wall Distribution Overview</Typography>
                  </Box>
                  {pieData.map((entry, index) => (
                    <Box key={entry.name} sx={{ mb: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                        <Typography variant="body2" fontWeight="medium">{entry.name}</Typography>
                        <Typography variant="body2" color="text.secondary">{entry.percentage}%</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={entry.percentage} 
                        sx={{ 
                          height: 8, 
                          borderRadius: 4,
                          bgcolor: 'grey.200',
                          '& .MuiLinearProgress-bar': {
                            bgcolor: COLORS[index % COLORS.length]
                          }
                        }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {entry.value} walls
                      </Typography>
                    </Box>
                  ))}
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Box display="flex" alignItems="center" sx={{ mb: 1 }}>
                    <Timeline sx={{ mr: 1 }} />
                    <Typography variant="subtitle1">Capacity Analysis</Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                    Total number of products that can be displayed on walls for each category
                  </Typography>
                  {barData.map((entry, index) => {
                    // Calculate proportional bar length based on capacity, not walls
                    const maxCapacity = Math.max(...barData.map(d => d.capacity));
                    const capacityPercentage = maxCapacity > 0 ? (entry.capacity / maxCapacity) * 100 : 0;
                    
                    return (
                      <Box key={entry.lob} sx={{ mb: 2 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                          <Typography variant="body2" fontWeight="medium">{entry.lob}</Typography>
                          <Typography variant="body2" color="text.secondary">{entry.walls} walls</Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={Math.min(capacityPercentage, 100)} 
                          sx={{ 
                            height: 8, 
                            borderRadius: 4,
                            bgcolor: 'grey.200',
                            '& .MuiLinearProgress-bar': {
                              bgcolor: COLORS[index % COLORS.length]
                            }
                          }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          Capacity: {entry.capacity}
                        </Typography>
                      </Box>
                    );
                  })}
                </Card>
              </Grid>
            </Grid>

            {/* Editable Wall Count Table */}
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Line of Business</TableCell>
                    <TableCell align="center">Current Walls</TableCell>
                    <TableCell align="center">Total Capacity</TableCell>
                    {editingWalls && <TableCell align="center">New Wall Count</TableCell>}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(storeDetails.wall_details).map(([lob, details]) => {
                    if (details.wall_count === 0 && !editingWalls) return null;
                    
                    const currentCount = editingWalls ? editedWallCounts[lob] || details.wall_count : details.wall_count;
                    
                    return (
                      <TableRow key={lob}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {formatLOBName(lob)}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={details.wall_count} 
                            size="small" 
                            color={details.wall_count > 0 ? 'primary' : 'default'}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2">
                            {details.total_capacity}
                          </Typography>
                        </TableCell>
                        {editingWalls && (
                          <TableCell align="center">
                            <TextField
                              type="number"
                              size="small"
                              value={currentCount}
                              onChange={(e) => updateWallCount(lob, parseInt(e.target.value) || 0)}
                              inputProps={{ min: 0, max: 50 }}
                              sx={{ width: 80 }}
                            />
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {recommendations && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
              <TrendingUp sx={{ mr: 1 }} />
              <Typography variant="h6">Optimization Analysis</Typography>
            </Box>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              {recommendations.summary}
            </Alert>

            {recommendations.optimization?.changes_needed && Object.keys(recommendations.optimization.changes_needed).length > 0 && (
              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                  <Typography variant="subtitle1">Recommended Changes:</Typography>
                  <Box display="flex" gap={1}>
                    {!appliedRecommendations && (
                      <Button 
                        variant="contained" 
                        size="small" 
                        onClick={applyRecommendations}
                        color="primary"
                      >
                        Apply Recommendations
                      </Button>
                    )}
                    <Button 
                      variant="outlined" 
                      size="small" 
                      onClick={resetOptimizationAdjustments}
                      disabled={Object.keys(optimizationAdjustments).length === 0}
                    >
                      Reset Changes
                    </Button>
                  </Box>
                </Box>
                
                {/* Wall Balance Indicator */}
                {Object.keys(optimizationAdjustments).length > 0 && (
                  <Alert 
                    severity={Object.values(optimizationAdjustments).reduce((sum: number, val: number) => sum + val, 0) === 0 ? "success" : "warning"}
                    sx={{ mb: 2 }}
                  >
                    Total Wall Change: {Object.values(optimizationAdjustments).reduce((sum: number, val: number) => sum + val, 0) > 0 ? '+' : ''}{Object.values(optimizationAdjustments).reduce((sum: number, val: number) => sum + val, 0)}
                    {Object.values(optimizationAdjustments).reduce((sum: number, val: number) => sum + val, 0) === 0 ? ' (Balanced)' : ' (Must be 0)'}
                  </Alert>
                )}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {Object.entries(recommendations.optimization.changes_needed).map(([lob, change]: [string, any]) => {
                    const currentWalls = storeDetails?.wall_details[lob]?.wall_count || 0;
                    const recommendedChange = change.walls_affected || 0;
                    const totalAdjustment = optimizationAdjustments[lob] || 0;
                    const appliedRecommendationChange = appliedRecommendations ? recommendedChange : 0;
                    const userAdjustment = totalAdjustment - appliedRecommendationChange;
                    const finalWalls = currentWalls + totalAdjustment;
                    
                    return (
                      <Box key={lob} sx={{ p: 2, border: 1, borderColor: 'grey.300', borderRadius: 1 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                          <Typography variant="body2" fontWeight="medium">{formatLOBName(lob)}</Typography>
                          <Box display="flex" gap={1} alignItems="center">
                            <Button
                              variant="outlined"
                              size="small"
                              onClick={() => adjustOptimization(lob, -1)}
                              disabled={finalWalls <= 0}
                            >
                              -
                            </Button>
                            <Button
                              variant="outlined"
                              size="small"
                              onClick={() => adjustOptimization(lob, 1)}
                            >
                              +
                            </Button>
                          </Box>
                        </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            Current: {currentWalls} → Recommended: {change.action} {Math.abs(recommendedChange)}
                            {appliedRecommendations && ` (Applied: ${appliedRecommendationChange > 0 ? '+' : ''}${appliedRecommendationChange})`}
                          </Typography>
                          <Chip 
                            label={`${change.action} ${Math.abs(recommendedChange)} wall(s)`}
                            color={change.action === 'ADD' ? 'success' : 'error'}
                            size="small"
                            variant={appliedRecommendations ? "filled" : "outlined"}
                          />
                        </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="body2" color="primary" fontWeight="medium">
                            Final: {finalWalls} walls
                          </Typography>
                          <Box display="flex" gap={1}>
                            {appliedRecommendations && appliedRecommendationChange !== 0 && (
                              <Chip 
                                label={`${appliedRecommendationChange > 0 ? '+' : ''}${appliedRecommendationChange} recommended`}
                                color="primary"
                                size="small"
                                variant="outlined"
                              />
                            )}
                            {userAdjustment !== 0 && (
                              <Chip 
                                label={`${userAdjustment > 0 ? '+' : ''}${userAdjustment} user adjustment`}
                                color="info"
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </Box>
                      </Box>
                    );
                  })}
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Optimization Options */}
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" sx={{ mb: 2 }}>
            <Typography variant="h6">Choose Optimization Type</Typography>
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Based on the analysis above, select how you want to generate planograms:
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card 
                variant="outlined" 
                sx={{ 
                  p: 2, 
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': { 
                    bgcolor: 'action.hover',
                    transform: 'translateY(-2px)',
                    boxShadow: 2
                  }
                }}
                onClick={() => handleOptimizationSelect('cohort')}
              >
                <Typography variant="h6" color="primary" sx={{ mb: 1 }}>
                  Cohort Optimization (Product Ecosystem)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Generate planograms for specific Apple product ecosystems. Choose which product cohorts to optimize (iPhone, iPad, Mac, etc.).
                </Typography>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card 
                variant="outlined" 
                sx={{ 
                  p: 2, 
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': { 
                    bgcolor: 'action.hover',
                    transform: 'translateY(-2px)',
                    boxShadow: 2
                  }
                }}
                onClick={() => handleOptimizationSelect('accessory')}
              >
                <Typography variant="h6" color="primary" sx={{ mb: 1 }}>
                  Accessory-Based Optimization
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Generate planograms for specific accessory categories like cases, charging cables, audio products, etc.
                </Typography>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card 
                variant="outlined" 
                sx={{ 
                  p: 2, 
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': { 
                    bgcolor: 'action.hover',
                    transform: 'translateY(-2px)',
                    boxShadow: 2
                  }
                }}
                onClick={() => handleOptimizationSelect('full-store')}
              >
                <Typography variant="h6" color="primary" sx={{ mb: 1 }}>
                  Full Store Optimization
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Generate planograms for all walls in the store using the recommended wall distribution.
                </Typography>
              </Card>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );

  const renderCategorySelection = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
            <Typography variant="h6">
            {selectedOptimization === 'cohort' ? 'Select Product Cohorts' : 'Select Accessory Categories'}
            </Typography>
            <Button variant="outlined" size="small" onClick={handleBackToAnalysis}>
              Back to Analysis
            </Button>
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {selectedOptimization === 'cohort' ? 'Choose which Apple product ecosystems to optimize (e.g., everything related to iPhone, iPad, etc.):' : 'Choose which accessory types to optimize (e.g., all cases, all charging accessories, etc.):'}
          </Typography>

          <FormGroup>
            <Grid container spacing={1}>
              {(selectedOptimization === 'cohort' ? COHORT_CATEGORIES : ACCESSORY_CATEGORIES).map(item => {
                const isSelected = selectedOptimization === 'cohort' ? selectedCohorts.includes(item)
                  : selectedAccessories.includes(item);
                
                const handleChange = (checked: boolean) => {
                  if (selectedOptimization === 'cohort') {
                    if (checked) {
                      setSelectedCohorts([...selectedCohorts, item]);
                    } else {
                      setSelectedCohorts(selectedCohorts.filter(l => l !== item));
                    }
                  } else {
                    if (checked) {
                      setSelectedAccessories([...selectedAccessories, item]);
                    } else {
                      setSelectedAccessories(selectedAccessories.filter(p => p !== item));
                    }
                  }
                };

                return (
                  <Grid item xs={6} md={4} key={item}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={isSelected}
                          onChange={(e) => handleChange(e.target.checked)}
                        />
                      }
                      label={
                        <Typography variant="body2">
                          {selectedOptimization === 'cohort' ? formatCohortName(item) : formatAccessoryName(item)}
                        </Typography>
                      }
                    />
                  </Grid>
                );
              })}
            </Grid>
          </FormGroup>

          <Divider sx={{ my: 3 }} />

          <Button
            variant="contained"
            fullWidth
            onClick={generatePlanograms}
            disabled={
              (selectedOptimization === 'cohort' && selectedCohorts.length === 0) ||
              (selectedOptimization === 'accessory' && selectedAccessories.length === 0)
            }

          >
            Generate Planograms
          </Button>
        </CardContent>
      </Card>
    </Box>
  );

  const renderGeneration = () => (
    <Card>
      <CardContent sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress size={60} sx={{ mb: 2 }} />
        <Typography variant="h6" sx={{ mb: 1 }}>Generating Planograms</Typography>
        <Typography variant="body2" color="text.secondary">
          This may take a few minutes. Please wait...
        </Typography>
        <LinearProgress sx={{ mt: 3 }} />
      </CardContent>
    </Card>
  );

  const renderResults = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
            <Box display="flex" alignItems="center">
              <CheckCircle sx={{ mr: 1, color: 'success.main' }} />
              <Typography variant="h6">Generation Complete</Typography>
            </Box>
            <Button variant="outlined" size="small" onClick={handleBackToAnalysis}>
              Generate More
            </Button>
          </Box>
          
          {generationResult && (
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} md={4}>
                <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h4" color="primary">{generationResult.generated_files?.length || 0}</Typography>
                  <Typography variant="body2" color="text.secondary">Generated Files</Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h4" color="success.main">{generationResult.total_accessories || generationResult.optimization_results?.length || 0}</Typography>
                  <Typography variant="body2" color="text.secondary">Accessories</Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined" sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h6" color="secondary">{selectedOptimization}</Typography>
                  <Typography variant="body2" color="text.secondary">Optimization Type</Typography>
                </Card>
              </Grid>
            </Grid>
          )}
        </CardContent>
      </Card>

      {generationResult && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Generated Files</Typography>
            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
              {generationResult.generated_files ? (
                // New smart accessory format
                generationResult.generated_files.map((file: any, index: number) => {
                  // Check if filename ends with .txt (for fallback text files)
                  const isTxtFile = file.filename.toLowerCase().endsWith('.txt');
                  const isPngFile = file.filename.toLowerCase().endsWith('.png');
                  const isJpgFile = file.filename.toLowerCase().endsWith('.jpg') || file.filename.toLowerCase().endsWith('.jpeg');
                  const isImageFile = isPngFile || isJpgFile;
                  
                  return (
                    <Box key={index} sx={{ mb: 2, p: 2, border: 1, borderColor: 'grey.300', borderRadius: 1 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Box>
                          <Typography variant="subtitle2" fontWeight="medium">
                            {file.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {file.accessory} - {file.type}
                          </Typography>
                        </Box>
                        <Box display="flex" gap={1}>
                          {(file.type === 'planogram_image' || isImageFile) && (
                            <Button
                              variant="contained"
                              size="small"
                              href={getFullApiUrl(`/output/${encodeURIComponent(file.filename)}`)}
                              target="_blank"
                              rel="noopener noreferrer"
                              component="a"
                              sx={{ mr: 1 }}
                            >
                              View Planogram
                            </Button>
                          )}
                          {isTxtFile && (
                            <Button
                              variant="contained"
                              size="small"
                              color="info"
                              href={getFullApiUrl(`/output/${encodeURIComponent(file.filename)}`)}
                              target="_blank"
                              rel="noopener noreferrer"
                              component="a"
                              sx={{ mr: 1 }}
                            >
                              View Details
                            </Button>
                          )}
                          <Button
                            variant="outlined"
                            size="small"
                            href={getFullApiUrl(`/output/${encodeURIComponent(file.filename)}`)}
                            download={file.filename}
                            component="a"
                          >
                            Download
                          </Button>
                        </Box>
                      </Box>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', mt: 1, color: 'text.secondary' }}>
                        {file.filename}
                      </Typography>
                    </Box>
                  );
                })
              ) : (
                // Legacy format
                Object.entries(generationResult.planograms || {}).map(([category, files]) => (
                  <Box key={category} sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" fontWeight="medium" color="text.primary" sx={{ mb: 1 }}>
                      {formatLOBName(category)} ({files.length} files)
                    </Typography>
                    {files.map((file, index) => (
                      <Typography key={index} variant="body2" component="div" 
                                sx={{ fontFamily: 'monospace', bgcolor: 'grey.50', p: 1, borderRadius: 0.5, mb: 0.5 }}>
                        {file}
                      </Typography>
                    ))}
                  </Box>
                ))
              )}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Box display="flex" alignItems="center" sx={{ mb: 1 }}>
          <Store sx={{ mr: 1 }} />
          <Typography variant="h5" component="h1">Store Planogram System</Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          {currentStep === 'store-selection' && 'Choose your store to begin analysis'}
          {currentStep === 'analysis' && 'Review store analysis and choose optimization type'}
          {currentStep === 'optimization-selection' && 'Select optimization approach'}
          {currentStep === 'category-selection' && 'Choose categories to generate'}
          {currentStep === 'generation' && 'Generating planograms...'}
          {currentStep === 'results' && 'View generation results'}
        </Typography>
      </Box>

      {loading && (
        <Box display="flex" alignItems="center" justifyContent="center" minHeight="300px">
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Loading store analysis...</Typography>
        </Box>
      )}

      {!loading && (
        <>
          {currentStep === 'store-selection' && renderStoreSelection()}
          {currentStep === 'analysis' && renderAnalysis()}
          {currentStep === 'category-selection' && renderCategorySelection()}
          {currentStep === 'generation' && renderGeneration()}
          {currentStep === 'results' && renderResults()}
        </>
      )}
    </Box>
  );
};

export default StoreSelector;