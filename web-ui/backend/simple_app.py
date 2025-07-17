#!/usr/bin/env python3
"""
Simplified Flask Backend for Testing
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time
import uuid
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Simple job storage
jobs = {}

class SimpleJob:
    def __init__(self, job_id, job_type, parameters):
        self.job_id = job_id
        self.job_type = job_type
        self.parameters = parameters
        self.status = 'pending'
        self.progress = 0
        self.logs = []
        self.result = None
        self.error = None
        self.created_at = datetime.now()

# WebSocket Event Handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Simple API'})

@socketio.on('join_job')
def handle_join_job(data):
    job_id = data.get('job_id')
    if job_id:
        join_room(job_id)
        logger.info(f"Client joined job room: {job_id}")

@socketio.on('leave_job')
def handle_leave_job(data):
    job_id = data.get('job_id')
    if job_id:
        leave_room(job_id)
        logger.info(f"Client left job room: {job_id}")

def simulate_job(job_id):
    """Simulate a job with real-time updates"""
    job = jobs[job_id]
    job.status = 'running'
    
    steps = [
        (10, "Initializing optimization"),
        (25, "Loading data files"),
        (40, "Processing products"),
        (60, "Calculating placements"),
        (80, "Generating planogram"),
        (100, "Optimization complete")
    ]
    
    for progress, message in steps:
        if job.status == 'cancelled':
            break
            
        job.progress = progress
        job.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
        # Emit progress update
        socketio.emit('job_status', {
            'job_id': job_id,
            'status': job.status,
            'progress': progress,
            'logs': job.logs,
            'timestamp': datetime.now().isoformat()
        }, room=job_id)
        
        # Also emit legacy format
        socketio.emit('optimization_progress', {
            'job_id': job_id,
            'status': job.status,
            'progress': progress,
            'logs': job.logs[-5:],
            'timestamp': datetime.now().isoformat()
        }, room=job_id)
        
        logger.info(f"Job {job_id}: {progress}% - {message}")
        time.sleep(2)  # Simulate work
    
    if job.status != 'cancelled':
        job.status = 'completed'
        job.result = {
            'products_placed': 150,
            'products_rejected': 25,
            'metrics': {'average_utilization': 85.5}
        }
        
        # Emit completion
        socketio.emit('optimization_complete', {
            'job_id': job_id,
            'result': job.result,
            'timestamp': datetime.now().isoformat()
        }, room=job_id)

# API Endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        }
    })

@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    return jsonify({
        'success': True,
        'data': {
            'data_files': {
                'cases': True,
                'cables': True,
                'screen_protectors': False,
                'others': True
            },
            'store_templates': ['flagship', 'standard', 'express'],
            'lob_status': {
                'iPhone': True,
                'iPad': True,
                'Mac': True,
                'Watch': True,
                'AirPods': False
            },
            'system_health': 'healthy',
            'active_jobs': len([j for j in jobs.values() if j.status == 'running']),
            'jobs': {
                'total': len(jobs),
                'running': len([j for j in jobs.values() if j.status == 'running']),
                'completed': len([j for j in jobs.values() if j.status == 'completed']),
                'failed': len([j for j in jobs.values() if j.status == 'failed'])
            },
            'disk_usage': {'output_mb': 25, 'logs_mb': 5, 'data_mb': 150}
        }
    })

@app.route('/api/validate/parameters', methods=['GET'])
def get_valid_parameters():
    return jsonify({
        'success': True,
        'data': {
            'lobs': ['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods'],
            'categories': ['cases', 'cables', 'screen_protectors', 'others'],
            'store_types': ['flagship', 'standard', 'express'],
            'strategies': ['balanced', 'sales_velocity', 'category_grouped'],
            'strategy_descriptions': {
                'balanced': 'Balanced approach considering multiple factors',
                'sales_velocity': 'Prioritize products by sales velocity',
                'category_grouped': 'Group similar products together'
            }
        }
    })

@app.route('/api/optimize/cohort', methods=['POST'])
def optimize_cohort():
    data = request.get_json()
    job_id = str(uuid.uuid4())
    
    job = SimpleJob(job_id, 'cohort', data)
    jobs[job_id] = job
    
    # Start job in background thread
    thread = threading.Thread(target=simulate_job, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'data': {
            'job_id': job_id,
            'message': f'Started cohort optimization'
        }
    })

@app.route('/api/optimize/lob', methods=['POST'])
def optimize_lob():
    data = request.get_json()
    job_id = str(uuid.uuid4())
    
    job = SimpleJob(job_id, 'lob', data)
    jobs[job_id] = job
    
    # Start job in background thread
    thread = threading.Thread(target=simulate_job, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'data': {
            'job_id': job_id,
            'message': f'Started LOB optimization'
        }
    })

@app.route('/api/optimize/category', methods=['POST'])
def optimize_category():
    data = request.get_json()
    job_id = str(uuid.uuid4())
    
    job = SimpleJob(job_id, 'category', data)
    jobs[job_id] = job
    
    # Start job in background thread
    thread = threading.Thread(target=simulate_job, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'data': {
            'job_id': job_id,
            'message': f'Started category optimization'
        }
    })

@app.route('/api/optimize/full-store', methods=['POST'])
def optimize_full_store():
    data = request.get_json()
    job_id = str(uuid.uuid4())
    
    job = SimpleJob(job_id, 'full_store', data)
    jobs[job_id] = job
    
    # Start job in background thread
    thread = threading.Thread(target=simulate_job, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'data': {
            'job_id': job_id,
            'message': f'Started full store optimization'
        }
    })

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_details(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'success': False, 'error': {'message': 'Job not found'}}), 404
    
    return jsonify({
        'success': True,
        'data': {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'parameters': job.parameters,
            'status': job.status,
            'progress': job.progress,
            'logs': job.logs,
            'result': job.result,
            'error': job.error,
            'created_at': job.created_at.isoformat()
        }
    })

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def cancel_job(job_id):
    job = jobs.get(job_id)
    if job and job.status == 'running':
        job.status = 'cancelled'
        return jsonify({'success': True, 'data': {'cancelled': job_id}})
    return jsonify({'success': False, 'error': {'message': 'Cannot cancel job'}}), 400

@app.route('/api/results/<job_id>', methods=['GET'])
def get_result_details(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'success': False, 'error': {'message': 'Result not found'}}), 404
    
    return jsonify({
        'success': True,
        'data': {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'status': job.status,
            'result': job.result,
            'logs': job.logs
        }
    })

if __name__ == '__main__':
    logger.info("Starting Simple Planogram API on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)