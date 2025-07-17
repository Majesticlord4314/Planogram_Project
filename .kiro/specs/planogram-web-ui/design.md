# Design Document

## Overview

The Planogram Web UI will be a modern, responsive web application that provides a graphical interface for the Apple Planogram Optimization System. The solution will use a Flask-based backend API that interfaces with the existing Python optimization system, paired with a React frontend for an intuitive user experience.

The design leverages the existing system architecture while adding a web layer that maintains all current functionality through RESTful APIs. The web interface will provide real-time feedback, progress tracking, and inline result visualization.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  Flask Backend  │    │ Existing System │
│                 │    │                 │    │                 │
│ - Dashboard     │◄──►│ - REST APIs     │◄──►│ - Data Loaders  │
│ - Forms         │    │ - WebSocket     │    │ - Optimizers    │
│ - Results View  │    │ - File Handling │    │ - Visualizers   │
│ - Progress      │    │ - Process Mgmt  │    │ - Models        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Material-UI (MUI) for components
- Axios for HTTP requests
- Socket.IO client for real-time updates
- React Query for state management
- React Router for navigation

**Backend:**
- Flask with Flask-CORS
- Flask-SocketIO for WebSocket communication
- Threading for background processes
- JSON for API responses
- File system integration for outputs

**Integration:**
- Existing Python modules (no modifications needed)
- Current data structure and file organization
- Existing logging and monitoring systems

## Components and Interfaces

### Frontend Components

#### 1. Dashboard Component (`Dashboard.tsx`)
- **Purpose**: Main landing page with navigation and system status
- **Features**: 
  - Quick access buttons for each optimization type
  - System health indicators
  - Recent results preview
  - Data file status indicators

#### 2. Optimization Forms
- **CohortPlanogramForm.tsx**: LOB and store selection for cohort generation
- **LOBOptimizationForm.tsx**: LOB, store, and strategy selection
- **CategoryOptimizationForm.tsx**: Category, store, and strategy selection  
- **FullStoreForm.tsx**: Store and strategy selection

#### 3. Progress Component (`ProgressTracker.tsx`)
- **Purpose**: Real-time progress display during optimization
- **Features**:
  - Progress bar with percentage
  - Live log output stream
  - Cancel operation button
  - Status indicators

#### 4. Results Component (`ResultsViewer.tsx`)
- **Purpose**: Display optimization results and generated planograms
- **Features**:
  - Inline planogram image display
  - Metrics dashboard (products placed, utilization, etc.)
  - Download links for Excel exports
  - Zoom and pan for planogram images

#### 5. History Component (`ResultsHistory.tsx`)
- **Purpose**: Browse previous optimization results
- **Features**:
  - Filterable list of past results
  - Thumbnail previews
  - Re-run with same parameters
  - Delete old results

### Backend API Endpoints

#### Core Optimization APIs
```python
POST /api/optimize/cohort
POST /api/optimize/lob  
POST /api/optimize/category
POST /api/optimize/full-store
```

#### System Status APIs
```python
GET /api/status/system
GET /api/status/data-files
GET /api/status/store-templates
```

#### Results Management APIs
```python
GET /api/results/list
GET /api/results/{result_id}
DELETE /api/results/{result_id}
GET /api/results/{result_id}/download/{file_type}
```

#### WebSocket Events
```python
# Progress updates
emit('optimization_progress', {
    'progress': 45,
    'status': 'Running optimization...',
    'logs': ['Loading products...', 'Optimizing placement...']
})

# Completion events
emit('optimization_complete', {
    'result_id': 'uuid',
    'metrics': {...},
    'files': [...]
})
```

### Data Models

#### Frontend TypeScript Interfaces

```typescript
interface OptimizationRequest {
  type: 'cohort' | 'lob' | 'category' | 'full-store';
  parameters: {
    lob?: string;
    category?: string;
    store: string;
    strategy?: string;
  };
}

interface OptimizationResult {
  id: string;
  timestamp: string;
  type: string;
  parameters: OptimizationRequest['parameters'];
  status: 'running' | 'completed' | 'failed';
  metrics?: {
    products_placed: number;
    products_rejected: number;
    utilization: number;
    profit_density?: number;
  };
  files: {
    planogram_image?: string;
    excel_export?: string;
    detailed_report?: string;
  };
  warnings: string[];
  errors: string[];
}

interface SystemStatus {
  data_files: {
    [category: string]: boolean;
  };
  store_templates: string[];
  system_health: 'healthy' | 'warning' | 'error';
  recent_activity: OptimizationResult[];
}
```

#### Backend Data Structures

```python
class OptimizationJob:
    def __init__(self, job_id: str, request: dict):
        self.job_id = job_id
        self.request = request
        self.status = 'pending'
        self.progress = 0
        self.logs = []
        self.result = None
        self.error = None
        self.created_at = datetime.now()
```

## Error Handling

### Frontend Error Handling
- **Network Errors**: Retry mechanism with exponential backoff
- **Validation Errors**: Real-time form validation with clear error messages
- **Server Errors**: User-friendly error displays with technical details in console
- **File Errors**: Clear messaging about missing data files with guidance

### Backend Error Handling
- **Data Loading Errors**: Graceful fallbacks and detailed error responses
- **Optimization Failures**: Capture and return detailed error information
- **File System Errors**: Handle missing files and permission issues
- **Process Management**: Clean up failed or cancelled operations

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "DATA_FILE_MISSING",
    "message": "Required data file not found: cases_sales.csv",
    "details": {
      "file_path": "data/raw/accessories/cases_sales.csv",
      "suggestions": ["Check if file exists", "Verify file permissions"]
    }
  }
}
```

## Testing Strategy

### Frontend Testing
- **Unit Tests**: Jest and React Testing Library for component testing
- **Integration Tests**: API integration testing with mock backend
- **E2E Tests**: Cypress for full user workflow testing
- **Visual Tests**: Screenshot comparison for planogram rendering

### Backend Testing
- **Unit Tests**: pytest for individual API endpoints
- **Integration Tests**: Test integration with existing Python modules
- **Load Tests**: Test concurrent optimization requests
- **File System Tests**: Test file handling and cleanup

### Test Data
- **Mock Data**: Simplified test datasets for development
- **Sample Results**: Pre-generated results for UI testing
- **Error Scenarios**: Test data that triggers various error conditions

## Performance Considerations

### Frontend Optimization
- **Code Splitting**: Lazy load components for faster initial load
- **Image Optimization**: Compress planogram images for web display
- **Caching**: Cache API responses and static assets
- **Progressive Loading**: Load results incrementally

### Backend Optimization
- **Background Processing**: Run optimizations in separate threads
- **File Caching**: Cache generated planograms and results
- **Memory Management**: Clean up completed jobs to prevent memory leaks
- **Connection Pooling**: Efficient WebSocket connection management

### Scalability Considerations
- **Job Queue**: Implement job queuing for multiple concurrent requests
- **Result Storage**: Efficient storage and retrieval of optimization results
- **File Management**: Automatic cleanup of old result files
- **Resource Limits**: Prevent resource exhaustion from long-running operations

## Security Considerations

### Input Validation
- **Parameter Validation**: Strict validation of all optimization parameters
- **File Upload Security**: If file upload is added, implement proper validation
- **SQL Injection Prevention**: Use parameterized queries if database is added
- **XSS Prevention**: Sanitize all user inputs and outputs

### Access Control
- **CORS Configuration**: Properly configure CORS for production
- **Rate Limiting**: Prevent abuse of optimization endpoints
- **File Access**: Restrict file system access to designated directories
- **Error Information**: Limit sensitive information in error responses

## Deployment Strategy

### Development Environment
- **Local Development**: Docker Compose for full stack development
- **Hot Reloading**: React dev server and Flask debug mode
- **Development Database**: SQLite for storing results (if needed)

### Production Environment
- **Containerization**: Docker containers for both frontend and backend
- **Reverse Proxy**: Nginx for serving static files and API routing
- **Process Management**: Gunicorn for Flask application
- **File Storage**: Persistent volumes for result files

### Configuration Management
- **Environment Variables**: Separate configs for dev/staging/production
- **Feature Flags**: Toggle features without code deployment
- **Logging Configuration**: Structured logging for production monitoring