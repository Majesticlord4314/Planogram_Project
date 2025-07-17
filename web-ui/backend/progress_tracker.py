"""
Real-time Progress Tracking System

This module provides functionality for tracking and reporting progress of optimization jobs
through WebSockets, including log streaming and job cancellation capabilities.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ProgressEvent(Enum):
    """Types of progress events"""
    STARTED = "started"
    PROGRESS = "progress"
    LOG = "log"
    WARNING = "warning"
    ERROR = "error"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProgressTracker:
    """
    Tracks progress of optimization jobs and emits updates via WebSockets
    """
    
    def __init__(self, socketio=None):
        """
        Initialize the progress tracker
        
        Args:
            socketio: Flask-SocketIO instance for emitting events
        """
        self.socketio = socketio
        self.job_logs: Dict[str, List[Dict[str, Any]]] = {}
        self.job_progress: Dict[str, int] = {}
        self.job_status: Dict[str, str] = {}
        self.job_cancel_flags: Dict[str, bool] = {}
        self.log_retention_limit = 1000  # Maximum number of log entries to keep per job
    
    def set_socketio(self, socketio):
        """Set the SocketIO instance after initialization"""
        self.socketio = socketio
    
    def track_job(self, job_id: str) -> None:
        """
        Initialize tracking for a new job
        
        Args:
            job_id: Unique identifier for the job
        """
        self.job_logs[job_id] = []
        self.job_progress[job_id] = 0
        self.job_status[job_id] = "pending"
        self.job_cancel_flags[job_id] = False
        
        # Emit initial status
        self._emit_event(job_id, ProgressEvent.STARTED, {
            "message": "Job initialized and ready to start",
            "timestamp": datetime.now().isoformat()
        })
    
    def update_progress(self, job_id: str, progress: int, message: str = None) -> None:
        """
        Update job progress percentage
        
        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            message: Optional status message
        """
        if job_id not in self.job_progress:
            self.track_job(job_id)
        
        # Validate progress value
        progress = max(0, min(100, progress))
        
        # Only emit if progress has changed
        if progress != self.job_progress.get(job_id, -1):
            self.job_progress[job_id] = progress
            self.job_status[job_id] = "running" if progress < 100 else "completed"
            
            data = {
                "progress": progress,
                "timestamp": datetime.now().isoformat()
            }
            
            if message:
                data["message"] = message
                self.add_log(job_id, message)
            
            self._emit_event(job_id, ProgressEvent.PROGRESS, data)
    
    def add_log(self, job_id: str, message: str, level: str = "info") -> None:
        """
        Add a log entry for a job
        
        Args:
            job_id: Job identifier
            message: Log message
            level: Log level (info, warning, error)
        """
        if job_id not in self.job_logs:
            self.job_logs[job_id] = []
            self.job_progress[job_id] = 0
            self.job_status[job_id] = "pending"
            self.job_cancel_flags[job_id] = False
        
        timestamp = datetime.now().isoformat()
        
        # Create log entry
        log_entry = {
            "message": message,
            "level": level,
            "timestamp": timestamp
        }
        
        # Add to job logs with retention limit
        self.job_logs[job_id].append(log_entry)
        if len(self.job_logs[job_id]) > self.log_retention_limit:
            self.job_logs[job_id] = self.job_logs[job_id][-self.log_retention_limit:]
        
        # Don't emit events to prevent infinite loops
    
    def complete_job(self, job_id: str, result: Dict[str, Any] = None) -> None:
        """
        Mark a job as completed
        
        Args:
            job_id: Job identifier
            result: Optional result data
        """
        if job_id not in self.job_status:
            self.track_job(job_id)
        
        self.job_status[job_id] = "completed"
        self.job_progress[job_id] = 100
        
        # Add log entry directly without triggering events to avoid recursion
        timestamp = datetime.now().isoformat()
        log_entry = {
            "message": "Job completed successfully",
            "level": "info",
            "timestamp": timestamp
        }
        
        if job_id not in self.job_logs:
            self.job_logs[job_id] = []
        self.job_logs[job_id].append(log_entry)
        
        data = {
            "message": "Job completed successfully",
            "timestamp": timestamp
        }
        
        if result:
            data["result"] = result
        
        self._emit_event(job_id, ProgressEvent.COMPLETED, data)
    
    def fail_job(self, job_id: str, error: str) -> None:
        """
        Mark a job as failed
        
        Args:
            job_id: Job identifier
            error: Error message
        """
        if job_id not in self.job_status:
            self.track_job(job_id)
        
        self.job_status[job_id] = "failed"
        
        data = {
            "message": f"Job failed: {error}",
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        self._emit_event(job_id, ProgressEvent.ERROR, data)
        self.add_log(job_id, f"Job failed: {error}", "error")
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Request cancellation of a job
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if cancellation was requested, False if job not found or already completed
        """
        if job_id not in self.job_status:
            return False
        
        # Only allow cancellation of pending or running jobs
        if self.job_status[job_id] in ["pending", "running"]:
            self.job_cancel_flags[job_id] = True
            self.job_status[job_id] = "cancelling"
            
            data = {
                "message": "Job cancellation requested",
                "timestamp": datetime.now().isoformat()
            }
            
            self._emit_event(job_id, ProgressEvent.CANCELLED, data)
            self.add_log(job_id, "Job cancellation requested", "warning")
            return True
        
        return False
    
    def confirm_cancelled(self, job_id: str) -> None:
        """
        Confirm that a job has been successfully cancelled
        
        Args:
            job_id: Job identifier
        """
        if job_id not in self.job_status:
            return
        
        self.job_status[job_id] = "cancelled"
        
        data = {
            "message": "Job cancelled successfully",
            "timestamp": datetime.now().isoformat()
        }
        
        self._emit_event(job_id, ProgressEvent.CANCELLED, data)
        self.add_log(job_id, "Job cancelled successfully", "warning")
    
    def is_cancelled(self, job_id: str) -> bool:
        """
        Check if a job has been requested to be cancelled
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if cancellation was requested, False otherwise
        """
        return self.job_cancel_flags.get(job_id, False)
    
    def get_logs(self, job_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get logs for a specific job
        
        Args:
            job_id: Job identifier
            limit: Maximum number of logs to return (most recent)
            
        Returns:
            List of log entries
        """
        if job_id not in self.job_logs:
            return []
        
        logs = self.job_logs[job_id]
        if limit:
            return logs[-limit:]
        return logs
    
    def get_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get current status of a job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dict with job status information
        """
        if job_id not in self.job_status:
            return {"status": "unknown", "progress": 0}
        
        return {
            "status": self.job_status[job_id],
            "progress": self.job_progress.get(job_id, 0),
            "logs": self.get_logs(job_id, 10)  # Last 10 logs
        }
    
    def _emit_event(self, job_id: str, event_type: ProgressEvent, data: Dict[str, Any]) -> None:
        """
        Emit a WebSocket event for a job
        
        Args:
            job_id: Job identifier
            event_type: Type of event
            data: Event data
        """
        # Disable WebSocket emissions from progress tracker to prevent infinite loops
        # The main app.py will handle WebSocket emissions directly
        pass

# Create a global instance
progress_tracker = ProgressTracker()

def create_progress_callback(job_id: str) -> Callable:
    """
    Create a progress callback function for a specific job
    
    Args:
        job_id: Job identifier
        
    Returns:
        Callable: Progress callback function
    """
    def progress_callback(progress: int, message: str = None):
        progress_tracker.update_progress(job_id, progress, message)
        
        # Check for cancellation
        if progress_tracker.is_cancelled(job_id):
            return True  # Signal that job should be cancelled
        return False
    
    return progress_callback

def create_log_callback(job_id: str) -> Callable:
    """
    Create a log callback function for a specific job
    
    Args:
        job_id: Job identifier
        
    Returns:
        Callable: Log callback function
    """
    def log_callback(message: str, level: str = "info"):
        progress_tracker.add_log(job_id, message, level)
    
    return log_callback

class LogCapture(logging.Handler):
    """
    Logging handler that captures logs and forwards them to the progress tracker
    """
    
    def __init__(self, job_id: str, level=logging.INFO):
        super().__init__(level)
        self.job_id = job_id
        self.formatter = logging.Formatter('%(message)s')
    
    def emit(self, record):
        try:
            # Map logging levels to progress tracker levels
            level_map = {
                logging.DEBUG: "debug",
                logging.INFO: "info",
                logging.WARNING: "warning",
                logging.ERROR: "error",
                logging.CRITICAL: "error"
            }
            level = level_map.get(record.levelno, "info")
            
            # Format the message
            message = self.formatter.format(record)
            
            # Send to progress tracker
            progress_tracker.add_log(self.job_id, message, level)
            
        except Exception:
            self.handleError(record)

def setup_log_capture(job_id: str, logger_name: str = None) -> LogCapture:
    """
    Set up log capture for a specific job
    
    Args:
        job_id: Job identifier
        logger_name: Name of logger to capture (None for root logger)
        
    Returns:
        LogCapture: The log capture handler
    """
    # Get the logger
    target_logger = logging.getLogger(logger_name)
    
    # Create and add the handler
    handler = LogCapture(job_id)
    target_logger.addHandler(handler)
    
    return handler

def remove_log_capture(handler: LogCapture, logger_name: str = None) -> None:
    """
    Remove log capture handler
    
    Args:
        handler: The log capture handler to remove
        logger_name: Name of logger (None for root logger)
    """
    target_logger = logging.getLogger(logger_name)
    target_logger.removeHandler(handler)