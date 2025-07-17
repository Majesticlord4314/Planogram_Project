#!/usr/bin/env python3
"""
Test script for the real-time progress tracking system
"""

import time
import threading
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import progress tracker
from progress_tracker import progress_tracker, create_progress_callback, create_log_callback, setup_log_capture, remove_log_capture

def simulate_job(job_id):
    """Simulate a job with progress updates and logs"""
    logger.info(f"Starting simulated job {job_id}")
    
    # Initialize progress tracking
    progress_tracker.track_job(job_id)
    
    # Create progress callback
    progress_callback = create_progress_callback(job_id)
    
    # Create log callback
    log_callback = create_log_callback(job_id)
    
    # Set up log capture
    log_handler = setup_log_capture(job_id)
    
    try:
        # Simulate job steps
        progress_callback(10, "Initializing job")
        time.sleep(1)
        
        # Check for cancellation
        if progress_tracker.is_cancelled(job_id):
            logger.info(f"Job {job_id} was cancelled")
            progress_tracker.confirm_cancelled(job_id)
            return
        
        progress_callback(20, "Loading data")
        log_callback("Loading product data from database", "info")
        time.sleep(1)
        
        # Check for cancellation
        if progress_tracker.is_cancelled(job_id):
            logger.info(f"Job {job_id} was cancelled")
            progress_tracker.confirm_cancelled(job_id)
            return
        
        progress_callback(40, "Processing data")
        log_callback("Processing 1,234 products", "info")
        time.sleep(1)
        
        # Check for cancellation
        if progress_tracker.is_cancelled(job_id):
            logger.info(f"Job {job_id} was cancelled")
            progress_tracker.confirm_cancelled(job_id)
            return
        
        # Add a warning
        log_callback("Some products have missing attributes", "warning")
        
        progress_callback(60, "Optimizing placement")
        time.sleep(1)
        
        # Check for cancellation
        if progress_tracker.is_cancelled(job_id):
            logger.info(f"Job {job_id} was cancelled")
            progress_tracker.confirm_cancelled(job_id)
            return
        
        progress_callback(80, "Generating results")
        log_callback("Placed 987 products successfully", "info")
        time.sleep(1)
        
        # Check for cancellation
        if progress_tracker.is_cancelled(job_id):
            logger.info(f"Job {job_id} was cancelled")
            progress_tracker.confirm_cancelled(job_id)
            return
        
        # Complete the job
        result = {
            'products_placed': 987,
            'products_rejected': 247,
            'utilization': 0.85,
            'warnings': ['Some products have missing attributes']
        }
        
        progress_tracker.complete_job(job_id, result)
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in job {job_id}: {error_msg}")
        progress_tracker.fail_job(job_id, error_msg)
    finally:
        # Clean up log capture
        remove_log_capture(log_handler)

def test_progress_tracking():
    """Test the progress tracking system"""
    logger.info("Testing progress tracking system")
    
    # Create a job ID
    job_id = str(uuid.uuid4())
    
    # Start the job in a separate thread
    job_thread = threading.Thread(target=simulate_job, args=(job_id,))
    job_thread.start()
    
    # Monitor job status
    while True:
        status = progress_tracker.get_status(job_id)
        logger.info(f"Job status: {status['status']}, progress: {status['progress']}%")
        
        if status['status'] in ['completed', 'failed', 'cancelled']:
            break
        
        time.sleep(0.5)
    
    # Wait for job thread to complete
    job_thread.join()
    
    # Get final logs
    logs = progress_tracker.get_logs(job_id)
    logger.info(f"Job logs ({len(logs)} entries):")
    for log in logs:
        logger.info(f"[{log['level']}] {log['message']}")
    
    logger.info("Progress tracking test completed")

def test_job_cancellation():
    """Test job cancellation"""
    logger.info("Testing job cancellation")
    
    # Create a job ID
    job_id = str(uuid.uuid4())
    
    # Start the job in a separate thread
    job_thread = threading.Thread(target=simulate_job, args=(job_id,))
    job_thread.start()
    
    # Wait a bit then cancel the job
    time.sleep(2)
    logger.info(f"Requesting cancellation of job {job_id}")
    success = progress_tracker.cancel_job(job_id)
    logger.info(f"Cancellation request {'succeeded' if success else 'failed'}")
    
    # Wait for job thread to complete
    job_thread.join()
    
    # Get final status
    status = progress_tracker.get_status(job_id)
    logger.info(f"Final job status: {status['status']}")
    
    # Get final logs
    logs = progress_tracker.get_logs(job_id)
    logger.info(f"Job logs ({len(logs)} entries):")
    for log in logs:
        logger.info(f"[{log['level']}] {log['message']}")
    
    logger.info("Job cancellation test completed")

if __name__ == "__main__":
    # Run tests
    test_progress_tracking()
    time.sleep(1)
    test_job_cancellation()