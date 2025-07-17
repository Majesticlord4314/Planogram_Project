#!/usr/bin/env python3
"""
Flask Backend for Planogram Web UI
Backend API that interfaces with the existing planogram optimization system
"""

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import sys
import threading
import uuid
import traceback
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable

# Add the parent directory to Python path to import existing modules
# The actual project root is two levels up from web-ui/backend/
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / "logs" / "api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'planogram-web-ui-dev-key')
app.config['JSON_SORT_KEYS'] = False  # Preserve key order in JSON responses
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Configure CORS - allow all origins for both API and WebSocket
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure SocketIO
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    logger=True, 
    engineio_logger=True,
    async_mode='eventlet'  # Use eventlet for better performance
)

# Import and configure progress tracker
from progress_tracker import progress_tracker
progress_tracker.set_socketio(socketio)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Import integration components
try:
    from integration import planogram_system, OptimizationJob, JobStatus
    logger.info("Successfully imported integration components")
except Exception as e:
    logger.error(f"Failed to import integration components: {e}")
    # Create a fallback system
    from enum import Enum
    from dataclasses import dataclass
    from datetime import datetime
    import threading
    import time
    
    class JobStatus(Enum):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
    
    @dataclass
    class OptimizationJob:
        job_id: str
        job_type: str
        parameters: dict
        status: JobStatus = JobStatus.PENDING
        progress: int = 0
        logs: list = None
        result: dict = None
        error: str = None
        created_at: datetime = None
        started_at: datetime = None
        completed_at: datetime = None
        
        def __post_init__(self):
            if self.logs is None:
                self.logs = []
            if self.created_at is None:
                self.created_at = datetime.now()
    
    class SimplePlanogramSystem:
        def __init__(self):
            self.jobs = {}
        
        def create_job(self, job_type: str, parameters: dict) -> str:
            job_id = str(uuid.uuid4())
            job = OptimizationJob(job_id=job_id, job_type=job_type, parameters=parameters)
            self.jobs[job_id] = job
            logger.info(f"Created job {job_id} of type {job_type}")
            return job_id
        
        def get_job(self, job_id: str):
            return self.jobs.get(job_id)
        
        def get_all_jobs(self):
            return list(self.jobs.values())
        
        def cancel_job(self, job_id: str) -> bool:
            job = self.jobs.get(job_id)
            if job and job.status == JobStatus.RUNNING:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return True
            return False
        
        def run_job_async(self, job_id: str):
            job = self.jobs.get(job_id)
            if not job:
                return
            
            def simulate_optimization():
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now()
                
                # Initialize progress tracking
                progress_tracker.track_job(job_id)
                
                steps = [
                    (10, "Initializing optimization system"),
                    (20, "Loading data files and configurations"),
                    (35, "Processing product catalog"),
                    (50, "Analyzing customer behavior patterns"),
                    (65, "Calculating optimal placements"),
                    (80, "Generating planogram layout"),
                    (95, "Finalizing optimization results"),
                    (100, "Optimization completed successfully")
                ]
                
                try:
                    for progress, message in steps:
                        if progress_tracker.is_cancelled(job_id):
                            job.status = JobStatus.CANCELLED
                            job.completed_at = datetime.now()
                            progress_tracker.confirm_cancelled(job_id)
                            return
                        
                        # Update progress in both systems
                        job.progress = progress
                        job.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
                        progress_tracker.update_progress(job_id, progress, message)
                        
                        # Emit WebSocket events
                        socketio.emit('job_status', {
                            'job_id': job_id,
                            'status': job.status.value,
                            'progress': progress,
                            'logs': job.logs,
                            'timestamp': datetime.now().isoformat()
                        }, room=job_id)
                        
                        socketio.emit('optimization_progress', {
                            'job_id': job_id,
                            'status': job.status.value,
                            'progress': progress,
                            'logs': job.logs[-5:],
                            'timestamp': datetime.now().isoformat()
                        }, room=job_id)
                        
                        logger.info(f"Job {job_id}: {progress}% - {message}")
                        time.sleep(2)  # Simulate work
                    
                    # Complete the job
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now()
                    job.result = {
                        'products_placed': 150,
                        'products_rejected': 25,
                        'metrics': {'average_utilization': 85.5},
                        'lob': job.parameters.get('lob', 'Unknown'),
                        'store_type': job.parameters.get('store_type', 'Unknown')
                    }
                    
                    progress_tracker.complete_job(job_id, job.result)
                    
                    # Emit completion event
                    socketio.emit('optimization_complete', {
                        'job_id': job_id,
                        'result': job.result,
                        'timestamp': datetime.now().isoformat()
                    }, room=job_id)
                    
                except Exception as e:
                    error_msg = str(e)
                    job.status = JobStatus.FAILED
                    job.error = error_msg
                    job.completed_at = datetime.now()
                    progress_tracker.fail_job(job_id, error_msg)
                    
                    socketio.emit('optimization_error', {
                        'job_id': job_id,
                        'error': {'message': error_msg},
                        'timestamp': datetime.now().isoformat()
                    }, room=job_id)
            
            thread = threading.Thread(target=simulate_optimization, daemon=True)
            thread.start()
    
    planogram_system = SimplePlanogramSystem()
    logger.info("Using fallback planogram system")

# WebSocket Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Planogram API'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_job')
def handle_join_job(data):
    """Join a specific job room for updates"""
    job_id = data.get('job_id')
    if job_id:
        join_room(job_id)
        logger.info(f"Client {request.sid} joined job room: {job_id}")
        
        # Send current job status
        job = planogram_system.get_job(job_id)
        if job:
            emit('job_status', {
                'job_id': job_id,
                'status': job.status.value,
                'progress': job.progress,
                'logs': job.logs[-5:] if job.logs else []
            })

@socketio.on('leave_job')
def handle_leave_job(data):
    """Leave a job room"""
    job_id = data.get('job_id')
    if job_id:
        leave_room(job_id)
        logger.info(f"Client {request.sid} left job room: {job_id}")

# New WebSocket event handlers for real-time progress tracking

@socketio.on('get_job_status')
def handle_get_job_status(data):
    """Get current status of a job using the new progress tracking system"""
    job_id = data.get('job_id')
    logger.info(f"Received get_job_status request for job: {job_id}")
    
    if job_id:
        # Check the planogram system first
        job = planogram_system.get_job(job_id)
        if job:
            status = {
                'status': job.status.value,
                'progress': job.progress,
                'logs': job.logs[-10:] if job.logs else []
            }
            
            emit('job_status', {
                'job_id': job_id,
                'status': status['status'],
                'progress': status['progress'],
                'logs': status['logs'],
                'timestamp': datetime.now().isoformat()
            })
            logger.info(f"Sent job status for {job_id}: {status['status']} ({status['progress']}%)")
        else:
            # Job doesn't exist, send a not found status
            emit('job_status', {
                'job_id': job_id,
                'status': 'not_found',
                'progress': 0,
                'logs': [],
                'timestamp': datetime.now().isoformat()
            })
            logger.info(f"Job {job_id} not found")
    else:
        logger.warning("No job_id provided in get_job_status request")

@socketio.on('get_job_logs_stream')
def handle_get_job_logs_stream(data):
    """Get logs for a job with streaming support"""
    job_id = data.get('job_id')
    limit = data.get('limit', 50)
    logger.info(f"Received get_job_logs_stream request for job: {job_id}")
    
    if job_id:
        # Get logs from progress tracker
        logs = progress_tracker.get_logs(job_id, limit)
        
        # Also check the planogram system
        job = planogram_system.get_job(job_id)
        if job and job.logs:
            # Format logs properly
            formatted_logs = []
            for log in job.logs[-limit:]:
                if isinstance(log, str):
                    formatted_logs.append({
                        'message': log,
                        'level': 'info',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    formatted_logs.append(log)
            logs = formatted_logs
        
        emit('job_logs_stream', {
            'job_id': job_id,
            'logs': logs,
            'total_logs': len(logs),
            'timestamp': datetime.now().isoformat()
        })
        logger.info(f"Sent {len(logs)} logs for job {job_id}")
    else:
        logger.warning("No job_id provided in get_job_logs_stream request")

@socketio.on('cancel_job_request')
def handle_cancel_job_request(data):
    """Request cancellation of a job using the new progress tracking system"""
    job_id = data.get('job_id')
    if job_id:
        # Request cancellation through progress tracker
        success = progress_tracker.cancel_job(job_id)
        
        # Also cancel through the old system for compatibility
        planogram_system.cancel_job(job_id)
        
        emit('job_cancellation_response', {
            'job_id': job_id,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })

# Helper functions for emitting events
def emit_progress(job_id: str, progress: int, status: str, logs: list = None):
    """Emit progress update to connected clients"""
    socketio.emit('optimization_progress', {
        'job_id': job_id,
        'progress': progress,
        'status': status,
        'logs': logs or [],
        'timestamp': datetime.now().isoformat()
    })

def emit_progress_to_room(job_id: str, progress: int, status: str, logs: list = None):
    """Emit progress update to specific job room"""
    socketio.emit('optimization_progress', {
        'job_id': job_id,
        'progress': progress,
        'status': status,
        'logs': logs or [],
        'timestamp': datetime.now().isoformat()
    }, room=job_id)

def emit_completion_to_room(job_id: str, result: Dict[str, Any]):
    """Emit completion event to specific job room"""
    socketio.emit('optimization_complete', {
        'job_id': job_id,
        'result': result,
        'timestamp': datetime.now().isoformat()
    }, room=job_id)

def emit_error_to_room(job_id: str, error: Dict[str, Any]):
    """Emit error event to specific job room"""
    socketio.emit('optimization_error', {
        'job_id': job_id,
        'error': error,
        'timestamp': datetime.now().isoformat()
    }, room=job_id)

# API Response helper class
class APIResponse:
    """Standardized API response format"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if data is not None:
            response["data"] = data
        return response
    
    @staticmethod
    def error(code: str, message: str, details: Optional[Dict[str, Any]] = None, status_code: int = 400) -> tuple[Dict[str, Any], int]:
        response = {
            "success": False,
            "error": {
                "code": code,
                "message": message
            },
            "timestamp": datetime.now().isoformat()
        }
        if details:
            response["error"]["details"] = details
        return response, status_code

# API Endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    """Get comprehensive system information"""
    try:
        # Check actual data files
        data_dir = project_root / 'data' / 'raw'
        processed_dir = project_root / 'data' / 'processed'
        
        data_files = {
            'cases': False,
            'cables': False,
            'screen_protectors': False,
            'others': False
        }
        
        # Check for actual data files in accessories directory
        accessories_dir = data_dir / 'accessories'
        if accessories_dir.exists():
            for file_path in accessories_dir.glob('*.csv'):
                filename = file_path.name.lower()
                if 'case' in filename:
                    data_files['cases'] = True
                elif 'cable' in filename or 'adapter' in filename:
                    data_files['cables'] = True
                elif 'screen' in filename or 'protector' in filename:
                    data_files['screen_protectors'] = True
                elif 'watch' in filename or 'mac' in filename or 'ipad' in filename:
                    data_files['others'] = True
        
        # Also check processed directory
        if processed_dir.exists():
            for file_path in processed_dir.glob('*.csv'):
                filename = file_path.name.lower()
                if 'case' in filename:
                    data_files['cases'] = True
                elif 'cable' in filename or 'adapter' in filename:
                    data_files['cables'] = True
                elif 'screen' in filename or 'protector' in filename:
                    data_files['screen_protectors'] = True
                elif 'sleeve' in filename or 'bag' in filename or 'accessories' in filename:
                    data_files['others'] = True
        
        # Check LOB data availability
        lob_status = {
            'iPhone': False,
            'iPad': False,
            'Mac': False,
            'Watch': False,
            'AirPods': False
        }
        
        # Check for cohort data files
        cohort_files = []
        cohorts_dir = data_dir / 'cohorts'
        if cohorts_dir.exists():
            cohort_files.extend(cohorts_dir.glob('*cohort*.csv'))
        if data_dir.exists():
            cohort_files.extend(data_dir.glob('*cohort*.csv'))
        if processed_dir.exists():
            cohort_files.extend(processed_dir.glob('*cohort*.csv'))
        
        for file_path in cohort_files:
            filename = file_path.name.lower()
            if 'iphone' in filename:
                lob_status['iPhone'] = True
            elif 'ipad' in filename:
                lob_status['iPad'] = True
            elif 'mac' in filename:
                lob_status['Mac'] = True
            elif 'watch' in filename:
                lob_status['Watch'] = True
            elif 'airpod' in filename:
                lob_status['AirPods'] = True
        
        # Also check for general product files by LOB
        all_files = []
        if data_dir.exists():
            all_files.extend(data_dir.glob('*.csv'))
        if processed_dir.exists():
            all_files.extend(processed_dir.glob('*.csv'))
        
        for file_path in all_files:
            filename = file_path.name.lower()
            if 'iphone' in filename or 'case' in filename:  # Cases are mostly iPhone
                lob_status['iPhone'] = True
            elif 'ipad' in filename:
                lob_status['iPad'] = True
            elif 'mac' in filename:
                lob_status['Mac'] = True
            elif 'watch' in filename:
                lob_status['Watch'] = True
            elif 'airpod' in filename:
                lob_status['AirPods'] = True
        
        # Calculate disk usage
        def get_dir_size(path):
            total = 0
            try:
                if path.exists():
                    for file_path in path.rglob('*'):
                        if file_path.is_file():
                            total += file_path.stat().st_size
            except Exception:
                pass
            return total // (1024 * 1024)  # Convert to MB
        
        disk_usage = {
            'output_mb': get_dir_size(project_root / 'output'),
            'logs_mb': get_dir_size(project_root / 'logs'),
            'data_mb': get_dir_size(project_root / 'data')
        }
        
        # Determine system health
        system_health = 'healthy'
        if not any(data_files.values()) and not any(lob_status.values()):
            system_health = 'error'
        elif not any(data_files.values()) or not any(lob_status.values()):
            system_health = 'warning'
        
        system_info = {
            'data_files': data_files,
            'store_templates': ['flagship', 'standard', 'express'],
            'lob_status': lob_status,
            'system_health': system_health,
            'active_jobs': len([j for j in planogram_system.get_all_jobs() if j.status == JobStatus.RUNNING]),
            'project_root': str(project_root),
            'directories': {
                'data': str(project_root / 'data'),
                'output': str(project_root / 'output'),
                'logs': str(project_root / 'logs')
            },
            'disk_usage': disk_usage,
            'jobs': {
                'total': len(planogram_system.get_all_jobs()),
                'running': len([j for j in planogram_system.get_all_jobs() if j.status == JobStatus.RUNNING]),
                'completed': len([j for j in planogram_system.get_all_jobs() if j.status == JobStatus.COMPLETED]),
                'failed': len([j for j in planogram_system.get_all_jobs() if j.status == JobStatus.FAILED])
            }
        }
        
        return jsonify(APIResponse.success(system_info))
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify(APIResponse.error("SYSTEM_ERROR", str(e))[0]), 500

@app.route('/api/validate/parameters', methods=['GET'])
def get_valid_parameters():
    """Get all valid parameter options"""
    return jsonify(APIResponse.success({
        'lobs': ['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods'],
        'categories': ['cases', 'cables', 'screen_protectors', 'others'],
        'store_types': ['flagship', 'standard', 'express'],
        'strategies': ['balanced', 'sales_velocity', 'category_grouped', 'value_density', 'profit_efficiency'],
        'strategy_descriptions': {
            'balanced': 'Balanced approach considering multiple factors',
            'sales_velocity': 'Prioritize products by sales velocity',
            'category_grouped': 'Group similar products together',
            'value_density': 'Maximize revenue per shelf space',
            'profit_efficiency': 'Maximize profit per shelf space'
        }
    }))

@app.route('/api/optimize/cohort', methods=['POST'])
def optimize_cohort():
    """Generate cohort-based planogram"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")[0]), 400
        
        lob = data.get('lob')
        store_type = data.get('store_type')
        
        if not lob or not store_type:
            return jsonify(APIResponse.error("MISSING_PARAMETERS", "Both 'lob' and 'store_type' are required")[0]), 400
        
        # Create and start job
        job_id = planogram_system.create_job('cohort', {
            'lob': lob,
            'store_type': store_type
        })
        
        # Start job asynchronously
        planogram_system.run_job_async(job_id)
        
        return jsonify(APIResponse.success({
            'job_id': job_id,
            'message': f'Started cohort planogram generation for {lob} - {store_type} store'
        }))
    except Exception as e:
        logger.error(f"Error starting cohort optimization: {e}")
        return jsonify(APIResponse.error("OPTIMIZATION_ERROR", str(e))[0]), 500

@app.route('/api/optimize/lob', methods=['POST'])
def optimize_lob():
    """Run LOB optimization"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")[0]), 400
        
        lob = data.get('lob')
        store_type = data.get('store_type')
        strategy = data.get('strategy', 'balanced')
        
        if not lob or not store_type:
            return jsonify(APIResponse.error("MISSING_PARAMETERS", "Both 'lob' and 'store_type' are required")[0]), 400
        
        # Create and start job
        job_id = planogram_system.create_job('lob', {
            'lob': lob,
            'store_type': store_type,
            'strategy': strategy
        })
        
        # Start job asynchronously
        planogram_system.run_job_async(job_id)
        
        return jsonify(APIResponse.success({
            'job_id': job_id,
            'message': f'Started LOB optimization for {lob} - {store_type} store with {strategy} strategy'
        }))
    except Exception as e:
        logger.error(f"Error starting LOB optimization: {e}")
        return jsonify(APIResponse.error("OPTIMIZATION_ERROR", str(e))[0]), 500

@app.route('/api/optimize/category', methods=['POST'])
def optimize_category():
    """Run category optimization"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")[0]), 400
        
        category = data.get('category')
        store_type = data.get('store_type')
        strategy = data.get('strategy', 'balanced')
        
        if not category or not store_type:
            return jsonify(APIResponse.error("MISSING_PARAMETERS", "Both 'category' and 'store_type' are required")[0]), 400
        
        # Create and start job
        job_id = planogram_system.create_job('category', {
            'category': category,
            'store_type': store_type,
            'strategy': strategy
        })
        
        # Start job asynchronously
        planogram_system.run_job_async(job_id)
        
        return jsonify(APIResponse.success({
            'job_id': job_id,
            'message': f'Started category optimization for {category} - {store_type} store with {strategy} strategy'
        }))
    except Exception as e:
        logger.error(f"Error starting category optimization: {e}")
        return jsonify(APIResponse.error("OPTIMIZATION_ERROR", str(e))[0]), 500

@app.route('/api/optimize/full-store', methods=['POST'])
def optimize_full_store():
    """Run full store optimization"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")[0]), 400
        
        store_type = data.get('store_type')
        strategy = data.get('strategy', 'balanced')
        
        if not store_type:
            return jsonify(APIResponse.error("MISSING_PARAMETERS", "'store_type' is required")[0]), 400
        
        # Create and start job
        job_id = planogram_system.create_job('full_store', {
            'store_type': store_type,
            'strategy': strategy
        })
        
        # Start job asynchronously
        planogram_system.run_job_async(job_id)
        
        return jsonify(APIResponse.success({
            'job_id': job_id,
            'message': f'Started full store optimization for {store_type} store with {strategy} strategy'
        }))
    except Exception as e:
        logger.error(f"Error starting full store optimization: {e}")
        return jsonify(APIResponse.error("OPTIMIZATION_ERROR", str(e))[0]), 500

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all optimization jobs"""
    try:
        jobs = planogram_system.get_all_jobs()
        jobs_data = []
        
        for job in jobs:
            jobs_data.append({
                'job_id': job.job_id,
                'job_type': job.job_type,
                'parameters': job.parameters,
                'status': job.status.value,
                'progress': job.progress,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error': job.error,
                'has_result': job.result is not None,
                'has_error': job.error is not None
            })
        
        return jsonify(APIResponse.success({'jobs': jobs_data}))
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        return jsonify(APIResponse.error("JOBS_ERROR", str(e))[0]), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_details(job_id: str):
    """Get detailed information about a specific job"""
    try:
        job = planogram_system.get_job(job_id)
        if not job:
            return jsonify(APIResponse.error("JOB_NOT_FOUND", f"Job {job_id} not found")[0]), 404
        
        # Convert any Path objects to strings for JSON serialization
        result = convert_paths_to_strings(job.result) if job.result else None
        logs = convert_paths_to_strings(job.logs[-20:]) if job.logs else []
        parameters = convert_paths_to_strings(job.parameters) if job.parameters else {}
        error = convert_paths_to_strings(job.error) if job.error else None
        
        job_data = {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'parameters': parameters,
            'status': job.status.value,
            'progress': job.progress,
            'logs': logs,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error': error,
            'result': result
        }
        
        return jsonify(APIResponse.success(job_data))
    except Exception as e:
        logger.error(f"Error getting job details: {e}")
        return jsonify(APIResponse.error("JOB_ERROR", str(e))[0]), 500

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def cancel_job(job_id: str):
    """Cancel a running job"""
    try:
        success = planogram_system.cancel_job(job_id)
        if success:
            return jsonify(APIResponse.success({'cancelled': job_id}))
        else:
            return jsonify(APIResponse.error("CANNOT_CANCEL", "Job cannot be cancelled (not running or not found)")[0]), 400
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        return jsonify(APIResponse.error("CANCEL_ERROR", str(e))[0]), 500

def convert_paths_to_strings(obj):
    """Recursively convert Path objects to strings for JSON serialization"""
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_paths_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_paths_to_strings(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_paths_to_strings(item) for item in obj)
    else:
        return obj

@app.route('/api/results/<job_id>', methods=['GET'])
def get_result_details(job_id: str):
    """Get detailed result information for a specific job"""
    try:
        job = planogram_system.get_job(job_id)
        if not job:
            return jsonify(APIResponse.error("RESULT_NOT_FOUND", f"Result {job_id} not found")[0]), 404
        
        # Convert any Path objects to strings for JSON serialization
        result = convert_paths_to_strings(job.result) if job.result else None
        logs = convert_paths_to_strings(job.logs) if job.logs else []
        parameters = convert_paths_to_strings(job.parameters) if job.parameters else {}
        
        result_data = {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'parameters': parameters,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'result': result,
            'logs': logs,
            'files': []  # Add file information if available
        }
        
        return jsonify(APIResponse.success(result_data))
    except Exception as e:
        logger.error(f"Error getting result details: {e}")
        return jsonify(APIResponse.error("RESULT_ERROR", str(e))[0]), 500

# File serving endpoints
@app.route('/api/files/<path:filename>')
def serve_file(filename):
    """Serve generated files from the output directory"""
    try:
        # Try multiple possible locations for the file
        possible_paths = [
            project_root / 'output' / filename,  # Main project output
            Path(__file__).parent / 'output' / filename,  # Backend output
            Path.cwd() / 'output' / filename,  # Current working directory output
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            logger.error(f"File not found in any location: {filename}")
            logger.error(f"Searched paths: {[str(p) for p in possible_paths]}")
            return jsonify(APIResponse.error("FILE_NOT_FOUND", f"File not found: {filename}")[0]), 404
        
        # Security check - ensure the file is within an allowed output directory
        allowed_dirs = [str(project_root / 'output'), str(Path(__file__).parent / 'output')]
        if not any(str(file_path).startswith(allowed_dir) for allowed_dir in allowed_dirs):
            return jsonify(APIResponse.error("INVALID_PATH", "File path not allowed")[0]), 403
        
        # Determine MIME type based on file extension
        mime_type = 'application/octet-stream'  # Default
        if filename.lower().endswith('.png'):
            mime_type = 'image/png'
        elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif filename.lower().endswith('.xlsx'):
            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.lower().endswith('.csv'):
            mime_type = 'text/csv'
        elif filename.lower().endswith('.txt'):
            mime_type = 'text/plain'
        
        return send_file(str(file_path), mimetype=mime_type, as_attachment=False)
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        return jsonify(APIResponse.error("FILE_ERROR", str(e))[0]), 500

@app.route('/api/files/<path:filename>/download')
def download_file(filename):
    """Download generated files from the output directory"""
    try:
        # Try multiple possible locations for the file
        possible_paths = [
            project_root / 'output' / filename,  # Main project output
            Path(__file__).parent / 'output' / filename,  # Backend output
            Path.cwd() / 'output' / filename,  # Current working directory output
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            logger.error(f"File not found in any location for download: {filename}")
            logger.error(f"Searched paths: {[str(p) for p in possible_paths]}")
            return jsonify(APIResponse.error("FILE_NOT_FOUND", f"File not found: {filename}")[0]), 404
        
        # Security check - ensure the file is within an allowed output directory
        allowed_dirs = [str(project_root / 'output'), str(Path(__file__).parent / 'output')]
        if not any(str(file_path).startswith(allowed_dir) for allowed_dir in allowed_dirs):
            return jsonify(APIResponse.error("INVALID_PATH", "File path not allowed")[0]), 403
        
        # Determine MIME type and download name
        mime_type = 'application/octet-stream'
        download_name = file_path.name
        
        if filename.lower().endswith('.png'):
            mime_type = 'image/png'
        elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif filename.lower().endswith('.xlsx'):
            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.lower().endswith('.csv'):
            mime_type = 'text/csv'
        elif filename.lower().endswith('.txt'):
            mime_type = 'text/plain'
        
        return send_file(str(file_path), mimetype=mime_type, as_attachment=True, download_name=download_name)
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        return jsonify(APIResponse.error("FILE_ERROR", str(e))[0]), 500

@app.route('/api/results/<job_id>/files')
def get_result_files(job_id: str):
    """Get list of files associated with a specific job result"""
    try:
        job = planogram_system.get_job(job_id)
        if not job:
            return jsonify(APIResponse.error("JOB_NOT_FOUND", f"Job {job_id} not found")[0]), 404
        
        files = []
        
        # Check if job has result with file information
        if job.result and 'files' in job.result:
            for file_info in job.result['files']:
                file_path = Path(file_info['path'])
                if file_path.exists():
                    # Try to get relative path from different output directories
                    relative_path = None
                    for base_dir in [project_root / 'output', Path(__file__).parent / 'output']:
                        try:
                            relative_path = file_path.relative_to(base_dir)
                            break
                        except ValueError:
                            continue
                    
                    if relative_path:
                        files.append({
                            'name': file_path.name,
                            'path': str(relative_path),
                            'type': file_info.get('type', 'unknown'),
                            'size': file_path.stat().st_size,
                            'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                            'url': f'/api/files/{relative_path}',
                            'download_url': f'/api/files/{relative_path}/download'
                        })
        
        # Also check for common file patterns based on job type and parameters
        if job.job_type == 'cohort' and job.result:
            lob = job.parameters.get('lob', '').lower()
            store_type = job.parameters.get('store_type', '').lower()
            
            # Look for cohort planogram files in multiple locations
            possible_cohort_dirs = [
                project_root / 'output' / 'cohort_planograms',
                Path(__file__).parent / 'output' / 'cohort_planograms'
            ]
            
            for cohort_dir in possible_cohort_dirs:
                if cohort_dir.exists():
                    for file_path in cohort_dir.glob(f'{lob}_cohort_*_{store_type}.*'):
                        # Get relative path from the appropriate base directory
                        if str(file_path).startswith(str(project_root / 'output')):
                            relative_path = file_path.relative_to(project_root / 'output')
                        else:
                            relative_path = file_path.relative_to(Path(__file__).parent / 'output')
                        
                        # Check if already added
                        if not any(f['path'] == str(relative_path) for f in files):
                            file_type = 'planogram' if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg'] else 'report'
                            files.append({
                                'name': file_path.name,
                                'path': str(relative_path),
                                'type': file_type,
                                'size': file_path.stat().st_size,
                                'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                                'url': f'/api/files/{relative_path}',
                                'download_url': f'/api/files/{relative_path}/download'
                            })
        
        return jsonify(APIResponse.success({'files': files}))
    except Exception as e:
        logger.error(f"Error getting result files for job {job_id}: {e}")
        return jsonify(APIResponse.error("FILES_ERROR", str(e))[0]), 500

# Serve the WebSocket test page
@app.route('/socket-test')
def socket_test():
    """Serve the WebSocket test page"""
    return send_file('static/socket-test.html')

# Main entry point
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Planogram Web UI API on {host}:{port} (debug={debug})")
    socketio.run(app, host=host, port=port, debug=debug)