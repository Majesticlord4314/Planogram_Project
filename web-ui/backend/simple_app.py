#!/usr/bin/env python3
"""
Simplified Flask Backend for Planogram Web UI
Directly runs main.py and cohort_planogram.py instead of complex integration
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

# Add the parent directory to Python path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / "logs" / "simple_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'planogram-simple-web-ui')
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure SocketIO
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    logger=True, 
    engineio_logger=True,
    async_mode='eventlet'
)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Import simple runner
from simple_runner import simple_runner, JobStatus

# Set socketio for the runner
simple_runner.socketio = socketio

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
        job = simple_runner.get_job(job_id)
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

# API Endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0-simple',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    """Get comprehensive system information"""
    try:
        # Check main.py and cohort_planogram.py
        main_py = project_root / 'main.py'
        cohort_py = project_root / 'cohort_planogram.py'
        
        # Check data directories
        data_dir = project_root / 'data' / 'raw'
        output_dir = project_root / 'output'
        
        # Check for data files
        data_files = {
            'cases': False,
            'cables': False,
            'screen_protectors': False,
            'others': False
        }
        
        if data_dir.exists():
            for file_path in data_dir.rglob('*.csv'):
                filename = file_path.name.lower()
                if 'case' in filename:
                    data_files['cases'] = True
                elif 'cable' in filename or 'adapter' in filename:
                    data_files['cables'] = True
                elif 'screen' in filename or 'protector' in filename:
                    data_files['screen_protectors'] = True
                else:
                    data_files['others'] = True
        
        # LOB status
        lob_status = {
            'iPhone': True,  # Always available
            'iPad': True,
            'Mac': True,
            'Watch': True,
            'AirPods': False  # Not implemented yet
        }
        
        system_health = 'healthy' if any(data_files.values()) else 'warning'
        
        system_info = {
            'main_py_available': main_py.exists(),
            'cohort_py_available': cohort_py.exists(),
            'data_files': data_files,
            'store_templates': ['flagship', 'standard', 'express'],
            'lob_status': lob_status,
            'system_health': system_health,
            'active_jobs': len([j for j in simple_runner.get_all_jobs() if j.status == JobStatus.RUNNING]),
            'project_root': str(project_root),
            'jobs': {
                'total': len(simple_runner.get_all_jobs()),
                'running': len([j for j in simple_runner.get_all_jobs() if j.status == JobStatus.RUNNING]),
                'completed': len([j for j in simple_runner.get_all_jobs() if j.status == JobStatus.COMPLETED]),
                'failed': len([j for j in simple_runner.get_all_jobs() if j.status == JobStatus.FAILED])
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
    """Generate cohort-based planogram using cohort_planogram.py"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")[0]), 400
        
        lob = data.get('lob')
        store_type = data.get('store_type')
        
        if not lob or not store_type:
            return jsonify(APIResponse.error("MISSING_PARAMETERS", "Both 'lob' and 'store_type' are required")[0]), 400
        
        # Create and start job
        job_id = simple_runner.create_job('cohort', {
            'lob': lob,
            'store_type': store_type
        })
        
        # Start job asynchronously
        simple_runner.run_job_async(job_id)
        
        return jsonify(APIResponse.success({
            'job_id': job_id,
            'message': f'Started cohort planogram generation for {lob} - {store_type} store'
        }))
    except Exception as e:
        logger.error(f"Error starting cohort optimization: {e}")
        return jsonify(APIResponse.error("OPTIMIZATION_ERROR", str(e))[0]), 500

@app.route('/api/optimize/lob', methods=['POST'])
def optimize_lob():
    """Run LOB optimization using main.py"""
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
        job_id = simple_runner.create_job('lob', {
            'lob': lob,
            'store_type': store_type,
            'strategy': strategy
        })
        
        # Start job asynchronously
        simple_runner.run_job_async(job_id)
        
        return jsonify(APIResponse.success({
            'job_id': job_id,
            'message': f'Started LOB optimization for {lob} - {store_type} store with {strategy} strategy'
        }))
    except Exception as e:
        logger.error(f"Error starting LOB optimization: {e}")
        return jsonify(APIResponse.error("OPTIMIZATION_ERROR", str(e))[0]), 500

@app.route('/api/optimize/category', methods=['POST'])
def optimize_category():
    """Run category optimization using main.py"""
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
        job_id = simple_runner.create_job('category', {
            'category': category,
            'store_type': store_type,
            'strategy': strategy
        })
        
        # Start job asynchronously
        simple_runner.run_job_async(job_id)
        
        return jsonify(APIResponse.success({
            'job_id': job_id,
            'message': f'Started category optimization for {category} - {store_type} store with {strategy} strategy'
        }))
    except Exception as e:
        logger.error(f"Error starting category optimization: {e}")
        return jsonify(APIResponse.error("OPTIMIZATION_ERROR", str(e))[0]), 500

@app.route('/api/optimize/full-store', methods=['POST'])
def optimize_full_store():
    """Run full store optimization using main.py"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(APIResponse.error("MISSING_DATA", "Request body is required")[0]), 400
        
        store_type = data.get('store_type')
        strategy = data.get('strategy', 'balanced')
        
        if not store_type:
            return jsonify(APIResponse.error("MISSING_PARAMETERS", "'store_type' is required")[0]), 400
        
        # Create and start job
        job_id = simple_runner.create_job('full_store', {
            'store_type': store_type,
            'strategy': strategy
        })
        
        # Start job asynchronously
        simple_runner.run_job_async(job_id)
        
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
        jobs = simple_runner.get_all_jobs()
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
        job = simple_runner.get_job(job_id)
        if not job:
            return jsonify(APIResponse.error("JOB_NOT_FOUND", f"Job {job_id} not found")[0]), 404
        
        job_data = {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'parameters': job.parameters,
            'status': job.status.value,
            'progress': job.progress,
            'logs': job.logs[-20:] if job.logs else [],
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error': job.error,
            'result': job.result
        }
        
        return jsonify(APIResponse.success(job_data))
    except Exception as e:
        logger.error(f"Error getting job details: {e}")
        return jsonify(APIResponse.error("JOB_ERROR", str(e))[0]), 500

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def cancel_job(job_id: str):
    """Cancel a running job"""
    try:
        success = simple_runner.cancel_job(job_id)
        if success:
            return jsonify(APIResponse.success({'cancelled': job_id}))
        else:
            return jsonify(APIResponse.error("CANNOT_CANCEL", "Job cannot be cancelled (not running or not found)")[0]), 400
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        return jsonify(APIResponse.error("CANCEL_ERROR", str(e))[0]), 500

@app.route('/api/results/<job_id>', methods=['GET'])
def get_result_details(job_id: str):
    """Get detailed result information for a specific job (alias for job details)"""
    return get_job_details(job_id)

@app.route('/api/results/<job_id>/files')
def get_result_files(job_id: str):
    """Get list of files associated with a specific job result"""
    try:
        job = simple_runner.get_job(job_id)
        if not job:
            return jsonify(APIResponse.error("JOB_NOT_FOUND", f"Job {job_id} not found")[0]), 404
        
        files = []
        planograms = []  # Separate list for planogram files
        
        # Get files from job result
        if job.result and 'files' in job.result:
            files = job.result['files']
        
        # Filter files generated for this specific job based on job parameters
        job_specific_patterns = get_job_file_patterns(job)
        
        # Look for files in output directory that match job patterns
        output_dir = project_root / 'output'
        if output_dir.exists():
            # Use job start time as baseline, or fallback to recent files (last 30 minutes)
            # Add a 30-second buffer before job start time to catch files generated at the exact start time
            if hasattr(job, 'start_time') and job.start_time:
                job_start_time = job.start_time.timestamp() - 30  # 30 second buffer
            elif hasattr(job, 'created_at') and job.created_at:
                # Fallback to job creation time with buffer
                job_start_time = job.created_at.timestamp() - 30
            else:
                # Last resort: files from last 30 minutes
                job_start_time = datetime.now().timestamp() - 1800
            
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        file_mtime = file_path.stat().st_mtime
                        
                        # Only include files modified after job start time
                        if file_mtime > job_start_time:
                            # Check if file matches job parameters
                            if matches_job_patterns(file_path.name, job_specific_patterns):
                                relative_path = file_path.relative_to(output_dir)
                                url_path = str(relative_path).replace('\\', '/')
                                
                                # Check if already in files list (avoid duplicates)
                                existing_files = [f.get('path') for f in files] + [p.get('path') for p in planograms]
                                if str(relative_path) not in existing_files:
                                    file_stat = file_path.stat()
                                    file_type = get_file_type(file_path)
                                    file_info = {
                                        'name': file_path.name,
                                        'path': str(relative_path),
                                        'type': file_type,
                                        'size': file_stat.st_size,
                                        'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                        'url': f'/api/files/{url_path}',
                                        'download_url': f'/api/files/{url_path}/download'
                                    }
                                    
                                    if file_type == 'planogram':
                                        planograms.append(file_info)
                                    else:
                                        files.append(file_info)
                    except Exception as e:
                        logger.warning(f"Error processing file {file_path}: {e}")
            
            # Debug logging
            logger.info(f"Job {job_id}: Found {len(planograms)} planograms and {len(files)} other files")
            logger.info(f"Job type: {job.job_type}, Job parameters: {job.parameters}")
            logger.info(f"Job patterns: {job_specific_patterns}")
            logger.info(f"Job start time: {job_start_time} ({datetime.fromtimestamp(job_start_time)})")
            if planograms:
                logger.info(f"Planogram files: {[p['name'] for p in planograms]}")
            if files:
                logger.info(f"Other files: {[f['name'] for f in files]}")
            
            # Debug: show all files that match the time filter but not the pattern filter
            debug_files = []
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        file_mtime = file_path.stat().st_mtime
                        if file_mtime > job_start_time:
                            debug_files.append(f"{file_path.name} (mtime: {datetime.fromtimestamp(file_mtime)})")
                    except:
                        pass
            if debug_files:
                logger.info(f"All recent files: {debug_files[:10]}")  # Show first 10
            
            # If no files found, list all recent files for debugging
            if len(planograms) == 0 and len(files) == 0:
                logger.warning("No matching files found. Listing all recent files for debugging:")
                for file_path in output_dir.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_mtime = file_path.stat().st_mtime
                            matches_pattern = matches_job_patterns(file_path.name, job_specific_patterns)
                            logger.info(f"  {file_path.name}: mtime={datetime.fromtimestamp(file_mtime)}, matches={matches_pattern}, recent={file_mtime > job_start_time}")
                        except Exception as e:
                            logger.warning(f"  Error checking {file_path}: {e}")
        
        return jsonify(APIResponse.success({'files': files, 'planograms': planograms}))
    except Exception as e:
        logger.error(f"Error getting result files for job {job_id}: {e}")
        return jsonify(APIResponse.error("FILES_ERROR", str(e))[0]), 500

def get_job_file_patterns(job):
    """Generate file patterns that match the job parameters"""
    patterns = []
    
    if not job.parameters:
        return patterns
    
    # Extract job parameters - note: job_type is used instead of optimization_type
    job_type = job.job_type  
    lob = job.parameters.get('lob', '')
    store_type = job.parameters.get('store_type', '')
    strategy = job.parameters.get('strategy', '')
    
    if job_type == 'cohort':
        # Cohort patterns: iphone_cohort_detailed_flagship.png, iphone_cohort_products_flagship.txt
        patterns.extend([
            f"{lob.lower()}_cohort_detailed_{store_type}",
            f"{lob.lower()}_cohort_products_{store_type}",
            f"{lob.lower()}_cohort_planogram_{store_type}",
            f"{lob.lower()}_cohort_{store_type}"
        ])
    elif job_type == 'lob':
        # LOB patterns: iPhone_flagship_balanced.png, iPhone_flagship_balanced_details.xlsx
        patterns.extend([
            f"{lob}_{store_type}_{strategy}",
            f"{lob.lower()}_{store_type}_{strategy}",
            f"{lob}_{store_type}",
            f"{lob.lower()}_{store_type}"
        ])
    elif job_type == 'full_store':
        # Full store patterns: full_store_flagship_balanced.png
        patterns.extend([
            f"full_store_{store_type}_{strategy}",
            f"full_store_{store_type}"
        ])
    
    return patterns

def matches_job_patterns(filename, patterns):
    """Check if filename matches any of the job patterns"""
    if not patterns:
        return True  # If no patterns, include all recent files
    
    filename_lower = filename.lower()
    # Use more specific matching to avoid cross-LOB file inclusion
    for pattern in patterns:
        pattern_lower = pattern.lower()
        if pattern_lower in filename_lower:
            return True
    
    return False

def get_file_type(file_path):
    """Determine file type based on extension and content"""
    suffix = file_path.suffix.lower()
    name = file_path.name.lower()
    
    if suffix in ['.png', '.jpg', '.jpeg']:
        return 'planogram'
    elif suffix in ['.xlsx', '.xls']:
        return 'excel'
    elif suffix in ['.txt']:
        if 'products' in name or 'list' in name or 'cohort' in name:
            return 'product_list'
        return 'report'
    elif suffix in ['.csv']:
        return 'data'
    else:
        return 'other'

# File serving endpoints
@app.route('/api/files/<path:filename>')
def serve_file(filename):
    """Serve generated files from the output directory"""
    try:
        # Normalize the filename to use the correct path separators
        filename = filename.replace('/', os.path.sep)
        
        # Try multiple possible locations for the file
        possible_paths = [
            project_root / 'output' / filename,
            Path(__file__).parent / 'output' / filename,
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            logger.error(f"File not found: {filename}")
            return jsonify(APIResponse.error("FILE_NOT_FOUND", f"File not found: {filename}")[0]), 404
        
        # Security check
        allowed_dirs = [str(project_root / 'output'), str(Path(__file__).parent / 'output')]
        if not any(str(file_path).startswith(allowed_dir) for allowed_dir in allowed_dirs):
            return jsonify(APIResponse.error("INVALID_PATH", "File path not allowed")[0]), 403
        
        # Determine MIME type
        mime_type = 'application/octet-stream'
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
        # Normalize the filename to use the correct path separators
        filename = filename.replace('/', os.path.sep)
        
        # Try multiple possible locations for the file
        possible_paths = [
            project_root / 'output' / filename,
            Path(__file__).parent / 'output' / filename,
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            return jsonify(APIResponse.error("FILE_NOT_FOUND", f"File not found: {filename}")[0]), 404
        
        # Security check
        allowed_dirs = [str(project_root / 'output'), str(Path(__file__).parent / 'output')]
        if not any(str(file_path).startswith(allowed_dir) for allowed_dir in allowed_dirs):
            return jsonify(APIResponse.error("INVALID_PATH", "File path not allowed")[0]), 403
        
        return send_file(str(file_path), as_attachment=True, download_name=file_path.name)
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        return jsonify(APIResponse.error("FILE_ERROR", str(e))[0]), 500

if __name__ == '__main__':
    logger.info("Starting simplified Planogram Web UI backend")
    logger.info(f"Project root: {project_root}")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
