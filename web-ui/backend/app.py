#!/usr/bin/env python3
"""
Flask Backend for Planogram Web UI
Backend API that interfaces with the existing planogram optimization system
"""

from flask import Flask, request, jsonify
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
from typing import Dict, Any, Optional

# Add the parent directory to Python path to import existing modules
# The actual project root is two levels up from web-ui/backend/
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'planogram-web-ui-dev-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active jobs and results
active_jobs: Dict[str, Dict[str, Any]] = {}
completed_results: Dict[str, Dict[str, Any]] = {}

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
    def error(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        return response

def handle_api_error(func):
    """Decorator for handling API errors consistently"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"File not found in {func.__name__}: {e}")
            return jsonify(APIResponse.error(
                "FILE_NOT_FOUND",
                str(e),
                {"suggestions": ["Check if data files exist", "Verify file paths"]}
            )), 404
        except ValueError as e:
            logger.error(f"Value error in {func.__name__}: {e}")
            return jsonify(APIResponse.error(
                "INVALID_PARAMETER",
                str(e)
            )), 400
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            return jsonify(APIResponse.error(
                "INTERNAL_ERROR",
                "An unexpected error occurred",
                {"technical_details": str(e)}
            )), 500
    wrapper.__name__ = func.__name__
    return wrapper

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

def emit_progress(job_id: str, progress: int, status: str, logs: list = None):
    """Emit progress update to connected clients"""
    socketio.emit('optimization_progress', {
        'job_id': job_id,
        'progress': progress,
        'status': status,
        'logs': logs or [],
        'timestamp': datetime.now().isoformat()
    })

def emit_completion(job_id: str, result: Dict[str, Any]):
    """Emit completion event to connected clients"""
    socketio.emit('optimization_complete', {
        'job_id': job_id,
        'result': result,
        'timestamp': datetime.now().isoformat()
    })

def emit_error(job_id: str, error: Dict[str, Any]):
    """Emit error event to connected clients"""
    socketio.emit('optimization_error', {
        'job_id': job_id,
        'error': error,
        'timestamp': datetime.now().isoformat()
    })

# Enhanced WebSocket Events for Progress Tracking
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

@socketio.on('cancel_job')
def handle_cancel_job(data):
    """Cancel a running job via WebSocket"""
    job_id = data.get('job_id')
    if job_id:
        success = planogram_system.cancel_job(job_id)
        emit('job_cancelled', {
            'job_id': job_id,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })
        
        if success:
            # Notify all clients in the job room
            socketio.emit('job_status', {
                'job_id': job_id,
                'status': 'cancelled',
                'message': 'Job was cancelled by user'
            }, room=job_id)

@socketio.on('get_job_logs')
def handle_get_job_logs(data):
    """Get recent logs for a job"""
    job_id = data.get('job_id')
    limit = data.get('limit', 20)
    
    if job_id:
        job = planogram_system.get_job(job_id)
        if job:
            logs = job.logs[-limit:] if job.logs else []
            emit('job_logs', {
                'job_id': job_id,
                'logs': logs,
                'total_logs': len(job.logs) if job.logs else 0
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

# API Endpoints
@app.route('/api/health', methods=['GET'])
@handle_api_error
def health_check():
    """Health check endpoint"""
    return jsonify(APIResponse.success({
        'status': 'healthy',
        'version': '1.0.0',
        'active_jobs': len(active_jobs),
        'completed_results': len(completed_results)
    }))

@app.route('/api/status/system', methods=['GET'])
@handle_api_error
def get_system_status():
    """Get system status including data files and templates"""
    # Import existing system components
    from src.data_processing.data_loader import DataLoader
    
    loader = DataLoader()
    
    # Check data files
    data_files = {}
    categories = ['cases', 'cables', 'screen_protectors', 'others']
    
    for category in categories:
        try:
            products = loader.load_products_by_category(category)
            data_files[category] = len(products) > 0
        except:
            data_files[category] = False
    
    # Check store templates
    store_templates = loader.get_available_stores()
    
    # Check LOBs
    lobs = ['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods']
    lob_status = {}
    for lob in lobs:
        try:
            products = loader.load_products_by_lob(lob)
            lob_status[lob] = len(products) > 0
        except:
            lob_status[lob] = False
    
    return jsonify(APIResponse.success({
        'data_files': data_files,
        'store_templates': store_templates,
        'lob_status': lob_status,
        'system_health': 'healthy',
        'active_jobs': len(active_jobs),
        'project_root': str(project_root)
    }))

@app.route('/api/status/logs', methods=['GET'])
@handle_api_error
def get_recent_logs():
    """Get recent system logs"""
    logs_dir = project_root / 'logs'
    recent_logs = []
    
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob('*.log'), key=lambda x: x.stat().st_mtime, reverse=True)
        for log_file in log_files[:5]:  # Get 5 most recent log files
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-10:]  # Last 10 lines
                    recent_logs.append({
                        'file': log_file.name,
                        'lines': [line.strip() for line in lines]
                    })
            except:
                continue
    
    return jsonify(APIResponse.success({
        'logs': recent_logs
    }))

# Import integration components
from integration import planogram_system, OptimizationJob, JobStatus
from file_manager import FileManager

# Initialize file manager
file_manager = FileManager(project_root)

@app.route('/api/system/info', methods=['GET'])
@handle_api_error
def get_system_info():
    """Get comprehensive system information"""
    system_info = file_manager.get_system_info()
    
    # Add job information
    all_jobs = planogram_system.get_all_jobs()
    system_info['jobs'] = {
        'total': len(all_jobs),
        'running': len([j for j in all_jobs if j.status == JobStatus.RUNNING]),
        'completed': len([j for j in all_jobs if j.status == JobStatus.COMPLETED]),
        'failed': len([j for j in all_jobs if j.status == JobStatus.FAILED])
    }
    
    return jsonify(APIResponse.success(system_info))

@app.route('/api/files/list', methods=['GET'])
@handle_api_error
def list_output_files():
    """List output files"""
    pattern = request.args.get('pattern')
    files = file_manager.get_output_files(pattern)
    return jsonify(APIResponse.success({'files': files}))

@app.route('/api/files/<filename>', methods=['DELETE'])
@handle_api_error
def delete_output_file(filename: str):
    """Delete an output file"""
    success = file_manager.delete_file(filename)
    if success:
        return jsonify(APIResponse.success({'deleted': filename}))
    else:
        return jsonify(APIResponse.error("FILE_NOT_FOUND", f"File {filename} not found or could not be deleted")), 404

@app.route('/api/files/<filename>', methods=['GET'])
@handle_api_error
def serve_output_file(filename: str):
    """Serve an output file"""
    from flask import send_file
    
    file_path = file_manager.output_dir / filename
    if not file_path.exists():
        return jsonify(APIResponse.error("FILE_NOT_FOUND", f"File {filename} not found")), 404
    
    return send_file(str(file_path))

@app.route('/api/jobs', methods=['GET'])
@handle_api_error
def list_jobs():
    """List all optimization jobs"""
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
            'result_summary': {
                'has_result': job.result is not None,
                'products_placed': job.result.get('products_placed') if job.result else None,
                'products_rejected': job.result.get('products_rejected') if job.result else None
            } if job.result else None
        })
    
    return jsonify(APIResponse.success({'jobs': jobs_data}))

@app.route('/api/jobs/<job_id>', methods=['GET'])
@handle_api_error
def get_job_details(job_id: str):
    """Get detailed information about a specific job"""
    job = planogram_system.get_job(job_id)
    if not job:
        return jsonify(APIResponse.error("JOB_NOT_FOUND", f"Job {job_id} not found")), 404
    
    job_data = {
        'job_id': job.job_id,
        'job_type': job.job_type,
        'parameters': job.parameters,
        'status': job.status.value,
        'progress': job.progress,
        'logs': job.logs[-20:],  # Last 20 log entries
        'created_at': job.created_at.isoformat(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error': job.error,
        'result': job.result
    }
    
    return jsonify(APIResponse.success(job_data))

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
@handle_api_error
def cancel_job(job_id: str):
    """Cancel a running job"""
    success = planogram_system.cancel_job(job_id)
    if success:
        return jsonify(APIResponse.success({'cancelled': job_id}))
    else:
        return jsonify(APIResponse.error("CANNOT_CANCEL", "Job cannot be cancelled (not running or not found)")), 400

# Core Optimization API Endpoints

@app.route('/api/optimize/cohort', methods=['POST'])
@handle_api_error
def optimize_cohort():
    """Generate cohort-based planogram"""
    data = request.get_json()
    
    # Validate required parameters
    if not data:
        return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")), 400
    
    lob = data.get('lob')
    store_type = data.get('store_type')
    
    if not lob or not store_type:
        return jsonify(APIResponse.error(
            "MISSING_PARAMETERS", 
            "Both 'lob' and 'store_type' are required",
            {"required": ["lob", "store_type"], "received": list(data.keys())}
        )), 400
    
    # Validate parameter values
    valid_lobs = ['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods']
    valid_stores = ['flagship', 'standard', 'express']
    
    if lob not in valid_lobs:
        return jsonify(APIResponse.error(
            "INVALID_LOB", 
            f"Invalid LOB: {lob}",
            {"valid_options": valid_lobs}
        )), 400
    
    if store_type not in valid_stores:
        return jsonify(APIResponse.error(
            "INVALID_STORE_TYPE", 
            f"Invalid store type: {store_type}",
            {"valid_options": valid_stores}
        )), 400
    
    # Create and start job
    job_id = planogram_system.create_job('cohort', {
        'lob': lob,
        'store_type': store_type
    })
    
    # Set up progress callback
    def progress_callback(job_id, progress, status, logs):
        emit_progress(job_id, progress, status, logs)
    
    planogram_system.set_progress_callback(job_id, progress_callback)
    
    # Start job asynchronously
    planogram_system.run_job_async(job_id)
    
    return jsonify(APIResponse.success({
        'job_id': job_id,
        'message': f'Started cohort planogram generation for {lob} - {store_type} store'
    }))

@app.route('/api/optimize/lob', methods=['POST'])
@handle_api_error
def optimize_lob():
    """Run LOB optimization"""
    data = request.get_json()
    
    if not data:
        return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")), 400
    
    lob = data.get('lob')
    store_type = data.get('store_type')
    strategy = data.get('strategy', 'balanced')  # Default strategy
    
    if not lob or not store_type:
        return jsonify(APIResponse.error(
            "MISSING_PARAMETERS", 
            "Both 'lob' and 'store_type' are required",
            {"required": ["lob", "store_type"], "optional": ["strategy"]}
        )), 400
    
    # Validate parameters
    valid_lobs = ['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods']
    valid_stores = ['flagship', 'standard', 'express']
    valid_strategies = ['balanced', 'sales_velocity', 'category_grouped', 'value_density', 'profit_efficiency']
    
    if lob not in valid_lobs:
        return jsonify(APIResponse.error("INVALID_LOB", f"Invalid LOB: {lob}", {"valid_options": valid_lobs})), 400
    
    if store_type not in valid_stores:
        return jsonify(APIResponse.error("INVALID_STORE_TYPE", f"Invalid store type: {store_type}", {"valid_options": valid_stores})), 400
    
    if strategy not in valid_strategies:
        return jsonify(APIResponse.error("INVALID_STRATEGY", f"Invalid strategy: {strategy}", {"valid_options": valid_strategies})), 400
    
    # Create and start job
    job_id = planogram_system.create_job('lob', {
        'lob': lob,
        'store_type': store_type,
        'strategy': strategy
    })
    
    # Set up progress callback
    def progress_callback(job_id, progress, status, logs):
        emit_progress(job_id, progress, status, logs)
    
    planogram_system.set_progress_callback(job_id, progress_callback)
    
    # Start job asynchronously
    planogram_system.run_job_async(job_id)
    
    return jsonify(APIResponse.success({
        'job_id': job_id,
        'message': f'Started LOB optimization for {lob} - {store_type} store with {strategy} strategy'
    }))

@app.route('/api/optimize/category', methods=['POST'])
@handle_api_error
def optimize_category():
    """Run category optimization"""
    data = request.get_json()
    
    if not data:
        return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")), 400
    
    category = data.get('category')
    store_type = data.get('store_type')
    strategy = data.get('strategy', 'balanced')
    
    if not category or not store_type:
        return jsonify(APIResponse.error(
            "MISSING_PARAMETERS", 
            "Both 'category' and 'store_type' are required",
            {"required": ["category", "store_type"], "optional": ["strategy"]}
        )), 400
    
    # Validate parameters
    valid_categories = ['cases', 'cables', 'screen_protectors', 'others']
    valid_stores = ['flagship', 'standard', 'express']
    valid_strategies = ['balanced', 'sales_velocity', 'category_grouped', 'value_density', 'profit_efficiency']
    
    if category not in valid_categories:
        return jsonify(APIResponse.error("INVALID_CATEGORY", f"Invalid category: {category}", {"valid_options": valid_categories})), 400
    
    if store_type not in valid_stores:
        return jsonify(APIResponse.error("INVALID_STORE_TYPE", f"Invalid store type: {store_type}", {"valid_options": valid_stores})), 400
    
    if strategy not in valid_strategies:
        return jsonify(APIResponse.error("INVALID_STRATEGY", f"Invalid strategy: {strategy}", {"valid_options": valid_strategies})), 400
    
    # Create and start job
    job_id = planogram_system.create_job('category', {
        'category': category,
        'store_type': store_type,
        'strategy': strategy
    })
    
    # Set up progress callback
    def progress_callback(job_id, progress, status, logs):
        emit_progress(job_id, progress, status, logs)
    
    planogram_system.set_progress_callback(job_id, progress_callback)
    
    # Start job asynchronously
    planogram_system.run_job_async(job_id)
    
    return jsonify(APIResponse.success({
        'job_id': job_id,
        'message': f'Started category optimization for {category} - {store_type} store with {strategy} strategy'
    }))

@app.route('/api/optimize/full-store', methods=['POST'])
@handle_api_error
def optimize_full_store():
    """Run full store optimization"""
    data = request.get_json()
    
    if not data:
        return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")), 400
    
    store_type = data.get('store_type')
    strategy = data.get('strategy', 'balanced')
    
    if not store_type:
        return jsonify(APIResponse.error(
            "MISSING_PARAMETERS", 
            "'store_type' is required",
            {"required": ["store_type"], "optional": ["strategy"]}
        )), 400
    
    # Validate parameters
    valid_stores = ['flagship', 'standard', 'express']
    valid_strategies = ['balanced', 'sales_velocity', 'category_grouped', 'value_density', 'profit_efficiency']
    
    if store_type not in valid_stores:
        return jsonify(APIResponse.error("INVALID_STORE_TYPE", f"Invalid store type: {store_type}", {"valid_options": valid_stores})), 400
    
    if strategy not in valid_strategies:
        return jsonify(APIResponse.error("INVALID_STRATEGY", f"Invalid strategy: {strategy}", {"valid_options": valid_strategies})), 400
    
    # Create and start job
    job_id = planogram_system.create_job('full_store', {
        'store_type': store_type,
        'strategy': strategy
    })
    
    # Set up progress callback
    def progress_callback(job_id, progress, status, logs):
        emit_progress(job_id, progress, status, logs)
    
    planogram_system.set_progress_callback(job_id, progress_callback)
    
    # Start job asynchronously
    planogram_system.run_job_async(job_id)
    
    return jsonify(APIResponse.success({
        'job_id': job_id,
        'message': f'Started full store optimization for {store_type} store with {strategy} strategy'
    }))

# Validation endpoints
@app.route('/api/validate/parameters', methods=['GET'])
@handle_api_error
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

# Results Management API Endpoints

@app.route('/api/results/list', methods=['GET'])
@handle_api_error
def list_results():
    """List all optimization results"""
    # Get query parameters
    job_type = request.args.get('type')  # Filter by job type
    status = request.args.get('status')  # Filter by status
    limit = int(request.args.get('limit', 50))  # Limit results
    
    jobs = planogram_system.get_all_jobs()
    
    # Filter jobs
    if job_type:
        jobs = [j for j in jobs if j.job_type == job_type]
    if status:
        jobs = [j for j in jobs if j.status.value == status]
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    # Limit results
    jobs = jobs[:limit]
    
    # Format results
    results = []
    for job in jobs:
        result_data = {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'parameters': job.parameters,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'duration_seconds': None,
            'has_result': job.result is not None,
            'has_error': job.error is not None
        }
        
        # Calculate duration if completed
        if job.started_at and job.completed_at:
            duration = job.completed_at - job.started_at
            result_data['duration_seconds'] = duration.total_seconds()
        
        # Add summary metrics if available
        if job.result:
            result_data['summary'] = {
                'products_placed': job.result.get('products_placed'),
                'products_rejected': job.result.get('products_rejected'),
                'utilization': job.result.get('metrics', {}).get('average_utilization'),
                'warnings_count': len(job.result.get('warnings', []))
            }
        
        results.append(result_data)
    
    return jsonify(APIResponse.success({
        'results': results,
        'total_count': len(planogram_system.get_all_jobs()),
        'filtered_count': len(results)
    }))

@app.route('/api/results/<job_id>', methods=['GET'])
@handle_api_error
def get_result_details(job_id: str):
    """Get detailed result information for a specific job"""
    job = planogram_system.get_job(job_id)
    if not job:
        return jsonify(APIResponse.error("RESULT_NOT_FOUND", f"Result {job_id} not found")), 404
    
    # Get associated files
    output_files = file_manager.get_output_files(job_id[:8])  # Files containing job ID prefix
    
    result_data = {
        'job_id': job.job_id,
        'job_type': job.job_type,
        'parameters': job.parameters,
        'status': job.status.value,
        'progress': job.progress,
        'created_at': job.created_at.isoformat(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'logs': job.logs,
        'error': job.error,
        'result': job.result,
        'files': output_files
    }
    
    # Calculate duration
    if job.started_at and job.completed_at:
        duration = job.completed_at - job.started_at
        result_data['duration_seconds'] = duration.total_seconds()
    
    return jsonify(APIResponse.success(result_data))

@app.route('/api/results/<job_id>/download/<file_type>', methods=['GET'])
@handle_api_error
def download_result_file(job_id: str, file_type: str):
    """Download a specific result file"""
    from flask import send_file
    
    job = planogram_system.get_job(job_id)
    if not job:
        return jsonify(APIResponse.error("RESULT_NOT_FOUND", f"Result {job_id} not found")), 404
    
    # Map file types to potential filenames
    file_patterns = {
        'planogram': f"*{job_id[:8]}*retail.png",
        'excel': f"*{job_id[:8]}*details.xlsx", 
        'image': f"*{job_id[:8]}*.png",
        'report': f"*{job_id[:8]}*.csv"
    }
    
    if file_type not in file_patterns:
        return jsonify(APIResponse.error(
            "INVALID_FILE_TYPE", 
            f"Invalid file type: {file_type}",
            {"valid_types": list(file_patterns.keys())}
        )), 400
    
    # Find matching files
    import glob
    pattern = str(file_manager.output_dir / file_patterns[file_type])
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        return jsonify(APIResponse.error(
            "FILE_NOT_FOUND", 
            f"No {file_type} file found for job {job_id}"
        )), 404
    
    # Return the first matching file
    file_path = matching_files[0]
    return send_file(file_path, as_attachment=True)

@app.route('/api/results/<job_id>', methods=['DELETE'])
@handle_api_error
def delete_result(job_id: str):
    """Delete a result and its associated files"""
    job = planogram_system.get_job(job_id)
    if not job:
        return jsonify(APIResponse.error("RESULT_NOT_FOUND", f"Result {job_id} not found")), 404
    
    # Delete associated files
    output_files = file_manager.get_output_files(job_id[:8])
    deleted_files = []
    
    for file_info in output_files:
        if file_manager.delete_file(file_info['name']):
            deleted_files.append(file_info['name'])
    
    # Remove job from system
    if job_id in planogram_system.jobs:
        del planogram_system.jobs[job_id]
    
    # Clean up progress callback
    if job_id in planogram_system.progress_callbacks:
        del planogram_system.progress_callbacks[job_id]
    
    return jsonify(APIResponse.success({
        'deleted_job': job_id,
        'deleted_files': deleted_files,
        'files_count': len(deleted_files)
    }))

@app.route('/api/results/cleanup', methods=['POST'])
@handle_api_error
def cleanup_old_results():
    """Clean up old results and files"""
    data = request.get_json() or {}
    days = data.get('days', 7)  # Default to 7 days
    
    if days < 1:
        return jsonify(APIResponse.error("INVALID_DAYS", "Days must be at least 1")), 400
    
    # Clean up old files
    deleted_files = file_manager.cleanup_old_files(days)
    
    # Clean up old jobs
    cutoff_time = datetime.now() - timedelta(days=days)
    deleted_jobs = []
    
    jobs_to_delete = []
    for job_id, job in planogram_system.jobs.items():
        if job.completed_at and job.completed_at < cutoff_time:
            jobs_to_delete.append(job_id)
    
    for job_id in jobs_to_delete:
        del planogram_system.jobs[job_id]
        if job_id in planogram_system.progress_callbacks:
            del planogram_system.progress_callbacks[job_id]
        deleted_jobs.append(job_id)
    
    return jsonify(APIResponse.success({
        'deleted_files': deleted_files,
        'deleted_jobs': deleted_jobs,
        'cleanup_days': days
    }))

@app.route('/api/results/stats', methods=['GET'])
@handle_api_error
def get_results_stats():
    """Get statistics about results"""
    jobs = planogram_system.get_all_jobs()
    
    # Calculate stats
    stats = {
        'total_jobs': len(jobs),
        'by_status': {},
        'by_type': {},
        'success_rate': 0,
        'average_duration': None,
        'total_products_optimized': 0
    }
    
    # Count by status
    for status in JobStatus:
        stats['by_status'][status.value] = len([j for j in jobs if j.status == status])
    
    # Count by type
    job_types = set(j.job_type for j in jobs)
    for job_type in job_types:
        stats['by_type'][job_type] = len([j for j in jobs if j.job_type == job_type])
    
    # Calculate success rate
    completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]
    if jobs:
        stats['success_rate'] = len(completed_jobs) / len(jobs) * 100
    
    # Calculate average duration
    durations = []
    total_products = 0
    
    for job in completed_jobs:
        if job.started_at and job.completed_at:
            duration = job.completed_at - job.started_at
            durations.append(duration.total_seconds())
        
        if job.result:
            products_placed = job.result.get('products_placed', 0)
            if isinstance(products_placed, int):
                total_products += products_placed
    
    if durations:
        stats['average_duration'] = sum(durations) / len(durations)
    
    stats['total_products_optimized'] = total_products
    
    return jsonify(APIResponse.success(stats))

if __name__ == '__main__':
    print("🚀 Starting Planogram Web UI Backend...")
    print("📊 Dashboard will be available at: http://localhost:3000")
    print("🔧 API server running on: http://localhost:5000")
    print(f"📁 Project root: {project_root}")
    print(f"📊 Data directory: {project_root / 'data'}")
    print(f"📤 Output directory: {project_root / 'output'}")
    
    # Validate system on startup
    try:
        system_info = file_manager.get_system_info()
        print(f"✅ Data files: {sum(system_info['data_files'].values())}/{len(system_info['data_files'])}")
        print(f"✅ Store templates: {len(system_info['store_templates'])}")
        print(f"✅ LOB data: {sum(system_info['lob_status'].values())}/{len(system_info['lob_status'])}")
    except Exception as e:
        print(f"⚠️  System validation warning: {e}")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)