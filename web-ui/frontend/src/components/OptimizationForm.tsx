import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Box,
    Typography,
    RadioGroup,
    FormControlLabel,
    Radio,
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
    const [step, setStep] = useState<number>(1);
    const [optimizationType, setOptimizationType] = useState<string>('');
    const [cohortMode, setCohortMode] = useState<string>(''); // For cohort sub-options
    const [lob, setLob] = useState<string>('iPhone');
    const [storeType, setStoreType] = useState<string>('flagship');
    const [strategy, setStrategy] = useState<string>('balanced');
    const [validParams, setValidParams] = useState<ValidParameters | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (open) {
            fetchValidParameters();
            // Reset form when opening
            setStep(1);
            setOptimizationType('');
            setLob('iPhone');
            setStoreType('flagship');
            setStrategy('balanced');
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
                case 'full_store':
                    response = await apiService.startFullStoreOptimization(storeType, strategy);
                    break;
                default:
                    throw new Error('Invalid optimization type');
            }

            if (!response) {
                throw new Error('No response received from server');
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
            case 'full_store':
                return `Complete store optimization for ${storeType} store using ${strategy} strategy. Includes all products and categories.`;
            default:
                return 'Select an optimization type to see description.';
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
        } else {
            datasets.push('All Available Datasets', 'Processed Data (planogram_sleeves_bags.csv)');
        }

        return datasets;
    };

    const nextStep = () => {
        setStep(step + 1);
    };

    const prevStep = () => {
        setStep(step - 1);
    };

    const canGoNext = () => {
        switch (step) {
            case 1:
                return !!optimizationType;
            case 2:
                if (optimizationType === 'cohort' || optimizationType === 'lob') {
                    return !!lob;
                }
                return !!storeType; // full_store goes to store type
            case 3:
                if (optimizationType === 'lob') {
                    return !!storeType;
                } else {
                    return !!storeType; // cohort and full_store need store type
                }
            case 4:
                if (optimizationType === 'lob') {
                    return !!strategy;
                }
                return true; // cohort and full_store don't need strategy
            default:
                return false;
        }
    };

    const isFormValid = () => {
        if (!optimizationType) return false;

        switch (optimizationType) {
            case 'cohort':
                if (!lob) return false;
                break;
            case 'lob':
                if (!lob || !strategy) return false;
                break;
            case 'full_store':
                if (!strategy) return false;
                break;
        }

        return !!storeType;
    };

    const getMaxSteps = () => {
        if (optimizationType === 'cohort') {
            return 3;
        } else if (optimizationType === 'lob') {
            return 4;
        } else if (optimizationType === 'full_store') {
            return 3;
        }
        return 4;
    };

    const renderCurrentStep = () => {
        switch (step) {
            case 1:
                return renderOptimizationTypeStep();
            case 2:
                if (optimizationType === 'cohort') {
                    return renderLOBSelectionStep();
                } else if (optimizationType === 'lob') {
                    return renderLOBSelectionStep();
                } else {
                    return renderStoreTypeStep();
                }
            case 3:
                if (optimizationType === 'cohort' || optimizationType === 'full_store') {
                    return renderStoreTypeStep();
                } else {
                    return renderStoreTypeStep();
                }
            case 4:
                if (optimizationType === 'lob') {
                    return renderStrategyStep();
                } else {
                    return renderSummaryStep();
                }
            case 5:
                return renderSummaryStep();
            default:
                return renderOptimizationTypeStep();
        }
    };

    const renderOptimizationTypeStep = () => (
        <Card variant="outlined">
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    Select optimization type:
                </Typography>
                <RadioGroup
                    value={optimizationType}
                    onChange={(e) => {
                        setOptimizationType(e.target.value);
                    }}
                >
                    <FormControlLabel
                        value="cohort"
                        control={<Radio />}
                        label="1. Cohort Planogram (Generate cohort-based planograms)"
                    />
                    <FormControlLabel
                        value="lob"
                        control={<Radio />}
                        label="2. Line of Business (iPhone, iPad, Mac, etc.)"
                    />
                    <FormControlLabel
                        value="full_store"
                        control={<Radio />}
                        label="3. All Products (Full store optimization)"
                    />
                </RadioGroup>
            </CardContent>
        </Card>
    );



    const renderLOBSelectionStep = () => (
        <Card variant="outlined">
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    Available Lines of Business:
                </Typography>
                <RadioGroup
                    value={lob}
                    onChange={(e) => setLob(e.target.value)}
                >
                    <FormControlLabel value="iPhone" control={<Radio />} label="1. iPhone" />
                    <FormControlLabel value="iPad" control={<Radio />} label="2. iPad" />
                    <FormControlLabel value="Mac" control={<Radio />} label="3. Mac" />
                    <FormControlLabel value="Watch" control={<Radio />} label="4. Watch" />
                    <FormControlLabel value="AirPods" control={<Radio />} label="5. AirPods" />
                </RadioGroup>
            </CardContent>
        </Card>
    );

    const renderStoreTypeStep = () => (
        <Card variant="outlined">
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    Available store types:
                </Typography>
                <RadioGroup
                    value={storeType}
                    onChange={(e) => setStoreType(e.target.value)}
                >
                    {validParams?.store_types.map((storeOption, index) => (
                        <FormControlLabel
                            key={storeOption}
                            value={storeOption}
                            control={<Radio />}
                            label={`${index + 1}. ${storeOption.charAt(0).toUpperCase() + storeOption.slice(1)} Store`}
                        />
                    ))}
                </RadioGroup>
            </CardContent>
        </Card>
    );

    const renderStrategyStep = () => (
        <Card variant="outlined">
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    Optimization strategies:
                </Typography>
                <RadioGroup
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value)}
                >
                    <FormControlLabel
                        value="balanced"
                        control={<Radio />}
                        label="1. Balanced (considers multiple factors)"
                    />
                    <FormControlLabel
                        value="sales_velocity"
                        control={<Radio />}
                        label="2. Sales Velocity (prioritize high-quantity items)"
                    />
                    <FormControlLabel
                        value="category_grouped"
                        control={<Radio />}
                        label="3. Category Grouped (group similar products)"
                    />
                    <FormControlLabel
                        value="value_density"
                        control={<Radio />}
                        label="4. Value Density (maximize revenue per cm)"
                    />
                    <FormControlLabel
                        value="profit_efficiency"
                        control={<Radio />}
                        label="5. Profit Efficiency (maximize profit per cm)"
                    />
                </RadioGroup>
            </CardContent>
        </Card>
    );

    const renderSummaryStep = () => (
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

                {(optimizationType === 'lob' || optimizationType === 'full_store') && validParams?.strategy_descriptions[strategy] && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                        <strong>Strategy:</strong> {validParams.strategy_descriptions[strategy]}
                    </Alert>
                )}
            </CardContent>
        </Card>
    );

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
                <Box sx={{ textAlign: 'center', mb: 4 }}>
                    <Typography variant="h5" gutterBottom>
                        APPLE PLANOGRAM OPTIMIZATION SYSTEM
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Step {step} of {getMaxSteps()}
                    </Typography>
                </Box>

                {renderCurrentStep()}
            </DialogContent>

            <DialogActions>
                <Button onClick={onClose}>
                    Cancel
                </Button>
                <Box sx={{ flexGrow: 1 }} />
                {step > 1 && (
                    <Button onClick={prevStep}>
                        Back
                    </Button>
                )}
                {step < getMaxSteps() ? (
                    <Button
                        onClick={nextStep}
                        variant="contained"
                        disabled={!canGoNext()}
                    >
                        Next
                    </Button>
                ) : (
                    <Button
                        onClick={handleStart}
                        variant="contained"
                        disabled={loading || !isFormValid()}
                        startIcon={<PlayArrowIcon />}
                    >
                        {loading ? 'Starting...' : 'Start Optimization'}
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
};

export default OptimizationForm;