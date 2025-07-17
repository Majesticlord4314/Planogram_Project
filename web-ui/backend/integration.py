"""
Integration layer between Flask API and existing planogram system
Provides wrapper classes and job management for optimization processes
"""

import sys
import threading
import time
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Import progress tracking system
from progress_tracker import progress_tracker, create_progress_callback, create_log_callback, setup_log_capture, remove_log_capture

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class OptimizationJob:
    """Represents an optimization job"""
    job_id: str
    job_type: str
    parameters: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    logs: List[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []
        if self.created_at is None:
            self.created_at = datetime.now()

class PlanogramSystemWrapper:
    """Wrapper for the existing planogram optimization system"""
    
    def __init__(self):
        self.jobs: Dict[str, OptimizationJob] = {}
        self.progress_callbacks: Dict[str, Callable] = {}
        
    def create_job(self, job_type: str, parameters: Dict[str, Any]) -> str:
        """Create a new optimization job"""
        job_id = str(uuid.uuid4())
        job = OptimizationJob(
            job_id=job_id,
            job_type=job_type,
            parameters=parameters
        )
        self.jobs[job_id] = job
        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id
    
    def set_progress_callback(self, job_id: str, callback: Callable):
        """Set progress callback for a job"""
        self.progress_callbacks[job_id] = callback
    
    def _emit_progress(self, job_id: str, progress: int, status: str, log_message: str = None):
        """Emit progress update"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.progress = progress
            if log_message:
                job.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {log_message}")
            
            # Always emit progress via WebSocket
            try:
                from app import socketio
                socketio.emit('job_status', {
                    'job_id': job_id,
                    'status': status,
                    'progress': progress,
                    'logs': job.logs[-10:] if job.logs else []
                }, room=job_id)
            except Exception as e:
                logger.error(f"Failed to emit progress for job {job_id}: {e}")
            
            # Also call callback if available
            if job_id in self.progress_callbacks:
                try:
                    self.progress_callbacks[job_id](job_id, progress, status, job.logs[-10:])
                except Exception as e:
                    logger.error(f"Progress callback failed for job {job_id}: {e}")
    
    def _emit_completion(self, job_id: str):
        """Emit job completion"""
        if job_id in self.progress_callbacks:
            job = self.jobs[job_id]
            # Import here to avoid circular imports
            from app import emit_completion_to_room
            emit_completion_to_room(job_id, job.result or {})
    
    def _emit_error(self, job_id: str, error_message: str):
        """Emit job error"""
        if job_id in self.progress_callbacks:
            # Import here to avoid circular imports
            from app import emit_error_to_room
            emit_error_to_room(job_id, {"message": error_message})
    
    def run_cohort_planogram(self, job_id: str, lob: str, store_type: str):
        """Run cohort planogram generation"""
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            # Update both the old progress system and the new one
            self._emit_progress(job_id, 10, "running", f"Starting {lob} cohort planogram for {store_type} store")
            progress_tracker.update_progress(job_id, 10, f"Starting {lob} cohort planogram for {store_type} store")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Use the existing cohort planogram system directly
            from src.cohort_planogram.runner import CohortPlanogramRunner
            
            self._emit_progress(job_id, 30, "running", f"Initializing cohort planogram runner for {lob}")
            progress_tracker.update_progress(job_id, 30, f"Initializing cohort planogram runner for {lob}")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Create runner and generate planogram
            runner = CohortPlanogramRunner()
            
            self._emit_progress(job_id, 50, "running", f"Generating {lob} cohort planogram for {store_type} store")
            progress_tracker.update_progress(job_id, 50, f"Generating {lob} cohort planogram for {store_type} store")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Generate the cohort planogram using existing system
            output_path = runner.generate_cohort_planogram(lob, store_type)
            
            if output_path and Path(output_path).exists():
                self._emit_progress(job_id, 90, "running", f"Cohort planogram generated successfully")
                progress_tracker.update_progress(job_id, 90, f"Cohort planogram generated successfully")
                
                # Set result with file information
                job.result = {
                    'output_name': f"{lob}_{store_type}_cohort_{job_id[:8]}",
                    'lob': lob,
                    'store_type': store_type,
                    'output_path': str(output_path),  # Convert Path to string
                    'files': [
                        {
                            'name': Path(output_path).name,
                            'type': 'planogram',
                            'path': str(output_path)  # Convert Path to string
                        }
                    ]
                }
                
                self._emit_progress(job_id, 100, "completed", f"Cohort planogram completed: {Path(output_path).name}")
                progress_tracker.complete_job(job_id, job.result)
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
            else:
                raise ValueError("Failed to generate cohort planogram - no output file created")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in cohort planogram job {job_id}: {error_msg}")
            self._emit_progress(job_id, 0, "failed", f"Error: {error_msg}")
            progress_tracker.fail_job(job_id, error_msg)
            job.status = JobStatus.FAILED
            job.error = error_msg
            job.completed_at = datetime.now()
    
    def run_lob_optimization(self, job_id: str, lob: str, store_type: str, strategy: str):
        """Run LOB optimization"""
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            # Update both the old progress system and the new one
            self._emit_progress(job_id, 10, "running", f"Starting {lob} optimization with {strategy} strategy")
            progress_tracker.update_progress(job_id, 10, f"Starting {lob} optimization with {strategy} strategy")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Import existing modules
            from src.data_processing.data_loader import DataLoader
            from src.data_processing.data_transformer import DataTransformer
            from src.optimization.product_optimizer import ProductOptimizer
            
            loader = DataLoader(str(project_root / "data" / "raw"))
            transformer = DataTransformer()
            
            self._emit_progress(job_id, 20, "running", f"Loading {lob} products")
            progress_tracker.update_progress(job_id, 20, f"Loading {lob} products")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Load products
            products = loader.load_products_by_lob(lob)
            if not products:
                raise ValueError(f"No products found for {lob}")
            
            self._emit_progress(job_id, 40, "running", f"Found {len(products)} products")
            progress_tracker.update_progress(job_id, 40, f"Found {len(products)} products")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Load store
            store = loader.load_store_template(store_type)
            
            self._emit_progress(job_id, 60, "running", "Transforming products for optimization")
            progress_tracker.update_progress(job_id, 60, "Transforming products for optimization")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Fix products with missing attributes
            for product in products:
                if not hasattr(product, 'attach_rate'):
                    product.attach_rate = 0.0
                if not hasattr(product, 'bundle_frequency'):
                    product.bundle_frequency = 0
                if not hasattr(product, 'current_stock'):
                    product.current_stock = 100
                if not hasattr(product, 'min_stock'):
                    product.min_stock = 10
                if not hasattr(product, 'avg_weekly_sales'):
                    product.avg_weekly_sales = getattr(product, 'total_qty', 0) / 4
                if not hasattr(product, 'price'):
                    product.price = getattr(product, 'unit_price', 0)
            
            # Transform products
            products = transformer.prepare_products_for_store(products, store, strategy)
            
            self._emit_progress(job_id, 80, "running", f"Optimizing with {strategy} strategy")
            progress_tracker.update_progress(job_id, 80, f"Optimizing with {strategy} strategy")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Run optimization
            optimizer = ProductOptimizer(store, gap_size=1.0, strategy=strategy)
            result = optimizer.create_planogram(products)
            
            # Set result with JSON-serializable data
            job.result = {
                'products_placed': len(result.products_placed),
                'products_rejected': len(result.products_rejected),
                'metrics': self._serialize_metrics(result.metrics) if result.metrics else {},
                'warnings': [str(w) for w in result.warnings[:10]] if result.warnings else [],
                'lob': lob,
                'store_type': store_type,
                'strategy': strategy
            }
            
            self._emit_progress(job_id, 100, "completed", "LOB optimization completed successfully")
            progress_tracker.complete_job(job_id, job.result)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in LOB optimization job {job_id}: {error_msg}")
            self._emit_progress(job_id, 0, "failed", f"Error: {error_msg}")
            progress_tracker.fail_job(job_id, error_msg)
            job.status = JobStatus.FAILED
            job.error = error_msg
            job.completed_at = datetime.now()
    
    def run_category_optimization(self, job_id: str, category: str, store_type: str, strategy: str):
        """Run category optimization"""
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            # Update both the old progress system and the new one
            self._emit_progress(job_id, 10, "running", f"Starting {category} optimization")
            progress_tracker.update_progress(job_id, 10, f"Starting {category} optimization")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Import existing modules
            from src.data_processing.data_loader import DataLoader
            from src.data_processing.data_transformer import DataTransformer
            from src.optimization.product_optimizer import ProductOptimizer
            
            loader = DataLoader(str(project_root / "data" / "raw"))
            transformer = DataTransformer()
            
            self._emit_progress(job_id, 30, "running", f"Loading {category} products")
            progress_tracker.update_progress(job_id, 30, f"Loading {category} products")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Load products
            products = loader.load_products_by_category(category)
            if not products:
                raise ValueError(f"No products found for category {category}")
            
            self._emit_progress(job_id, 50, "running", f"Found {len(products)} products")
            progress_tracker.update_progress(job_id, 50, f"Found {len(products)} products")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Load store
            store = loader.load_store_template(store_type)
            
            self._emit_progress(job_id, 70, "running", "Transforming products for optimization")
            progress_tracker.update_progress(job_id, 70, "Transforming products for optimization")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Fix products with missing attributes
            for product in products:
                if not hasattr(product, 'attach_rate'):
                    product.attach_rate = 0.0
                if not hasattr(product, 'bundle_frequency'):
                    product.bundle_frequency = 0
                if not hasattr(product, 'current_stock'):
                    product.current_stock = 100
                if not hasattr(product, 'min_stock'):
                    product.min_stock = 10
                if not hasattr(product, 'avg_weekly_sales'):
                    product.avg_weekly_sales = getattr(product, 'total_qty', 0) / 4
                if not hasattr(product, 'price'):
                    product.price = getattr(product, 'unit_price', 0)
            
            # Transform products
            products = transformer.prepare_products_for_store(products, store, strategy)
            
            self._emit_progress(job_id, 90, "running", f"Optimizing with {strategy} strategy")
            progress_tracker.update_progress(job_id, 90, f"Optimizing with {strategy} strategy")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Run optimization
            optimizer = ProductOptimizer(store, gap_size=1.0, strategy=strategy)
            result = optimizer.create_planogram(products)
            
            # Set result
            job.result = {
                'products_placed': len(result.products_placed),
                'products_rejected': len(result.products_rejected),
                'metrics': self._serialize_metrics(result.metrics) if result.metrics else {},
                'warnings': [str(w) for w in result.warnings[:10]] if result.warnings else [],
                'category': category,
                'store_type': store_type,
                'strategy': strategy
            }
            
            self._emit_progress(job_id, 100, "completed", "Category optimization completed")
            progress_tracker.complete_job(job_id, job.result)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in category optimization job {job_id}: {error_msg}")
            self._emit_progress(job_id, 0, "failed", f"Error: {error_msg}")
            progress_tracker.fail_job(job_id, error_msg)
            job.status = JobStatus.FAILED
            job.error = error_msg
            job.completed_at = datetime.now()
    
    def run_full_store_optimization(self, job_id: str, store_type: str, strategy: str):
        """Run full store optimization"""
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            # Update both the old progress system and the new one
            self._emit_progress(job_id, 10, "running", "Loading all products")
            progress_tracker.update_progress(job_id, 10, "Loading all products")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Import existing modules
            from src.data_processing.data_loader import DataLoader
            from src.data_processing.data_transformer import DataTransformer
            from src.optimization.product_optimizer import ProductOptimizer
            
            loader = DataLoader(str(project_root / "data" / "raw"))
            transformer = DataTransformer()
            
            self._emit_progress(job_id, 30, "running", "Loading products from all categories")
            progress_tracker.update_progress(job_id, 30, "Loading products from all categories")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Load all products
            products = loader.load_all_products()
            if not products:
                raise ValueError("No products found")
            
            self._emit_progress(job_id, 50, "running", f"Found {len(products)} total products")
            progress_tracker.update_progress(job_id, 50, f"Found {len(products)} total products")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Load store
            store = loader.load_store_template(store_type)
            
            self._emit_progress(job_id, 70, "running", "Transforming all products for optimization")
            progress_tracker.update_progress(job_id, 70, "Transforming all products for optimization")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Fix products with missing attributes
            for product in products:
                if not hasattr(product, 'attach_rate'):
                    product.attach_rate = 0.0
                if not hasattr(product, 'bundle_frequency'):
                    product.bundle_frequency = 0
                if not hasattr(product, 'current_stock'):
                    product.current_stock = 100
                if not hasattr(product, 'min_stock'):
                    product.min_stock = 10
                if not hasattr(product, 'avg_weekly_sales'):
                    product.avg_weekly_sales = getattr(product, 'total_qty', 0) / 4
                if not hasattr(product, 'price'):
                    product.price = getattr(product, 'unit_price', 0)
            
            # Transform products
            products = transformer.prepare_products_for_store(products, store, strategy)
            
            self._emit_progress(job_id, 90, "running", f"Optimizing entire store with {strategy} strategy")
            progress_tracker.update_progress(job_id, 90, f"Optimizing entire store with {strategy} strategy")
            
            # Check for cancellation
            if progress_tracker.is_cancelled(job_id):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return
            
            # Run optimization
            optimizer = ProductOptimizer(store, gap_size=1.0, strategy=strategy)
            result = optimizer.create_planogram(products)
            
            # Set result
            job.result = {
                'products_placed': len(result.products_placed),
                'products_rejected': len(result.products_rejected),
                'metrics': self._serialize_metrics(result.metrics) if result.metrics else {},
                'warnings': [str(w) for w in result.warnings[:10]] if result.warnings else [],
                'store_type': store_type,
                'strategy': strategy,
                'total_products_processed': len(products)
            }
            
            self._emit_progress(job_id, 100, "completed", "Full store optimization completed")
            progress_tracker.complete_job(job_id, job.result)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in full store optimization job {job_id}: {error_msg}")
            self._emit_progress(job_id, 0, "failed", f"Error: {error_msg}")
            progress_tracker.fail_job(job_id, error_msg)
            job.status = JobStatus.FAILED
            job.error = error_msg
            job.completed_at = datetime.now()
    
    def run_job_async(self, job_id: str):
        """Run a job asynchronously in a separate thread"""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Initialize progress tracking for this job
        progress_tracker.track_job(job_id)
        
        def run_job():
            # Set up log capture for this job
            log_handler = setup_log_capture(job_id)
            
            try:
                progress_tracker.add_log(job_id, f"Starting {job.job_type} job with parameters: {job.parameters}")
                
                if job.job_type == "cohort":
                    self.run_cohort_planogram(
                        job_id, 
                        job.parameters['lob'], 
                        job.parameters['store_type']
                    )
                elif job.job_type == "lob":
                    self.run_lob_optimization(
                        job_id,
                        job.parameters['lob'],
                        job.parameters['store_type'],
                        job.parameters['strategy']
                    )
                elif job.job_type == "category":
                    self.run_category_optimization(
                        job_id,
                        job.parameters['category'],
                        job.parameters['store_type'],
                        job.parameters['strategy']
                    )
                elif job.job_type == "full_store":
                    self.run_full_store_optimization(
                        job_id,
                        job.parameters['store_type'],
                        job.parameters['strategy']
                    )
                else:
                    raise ValueError(f"Unknown job type: {job.job_type}")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Job {job_id} failed: {error_msg}")
                progress_tracker.fail_job(job_id, error_msg)
                # Error is already set in the individual run methods
            finally:
                # Clean up log capture
                remove_log_capture(log_handler)
                
                # Check if job was cancelled
                if progress_tracker.is_cancelled(job_id):
                    progress_tracker.confirm_cancelled(job_id)
        
        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()
        return thread
    
    def get_job(self, job_id: str) -> Optional[OptimizationJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[OptimizationJob]:
        """Get all jobs"""
        return list(self.jobs.values())
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        job = self.jobs.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            # Update job status
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            
            # Also update progress tracker
            progress_tracker.cancel_job(job_id)
            
            # Log cancellation
            logger.info(f"Job {job_id} cancelled by user")
            
            return True
        return False
    
    def _serialize_metrics(self, metrics: Any) -> Dict[str, Any]:
        """Serialize metrics to JSON-safe format"""
        if not metrics:
            return {}
        
        try:
            # Convert metrics to a JSON-serializable dictionary
            serialized = {}
            
            if hasattr(metrics, '__dict__'):
                # If it's an object with attributes
                for key, value in metrics.__dict__.items():
                    serialized[str(key)] = self._serialize_value(value)
            elif isinstance(metrics, dict):
                # If it's already a dictionary
                for key, value in metrics.items():
                    serialized[str(key)] = self._serialize_value(value)
            else:
                # If it's a simple value
                serialized = self._serialize_value(metrics)
            
            return serialized
            
        except Exception as e:
            logger.error(f"Error serializing metrics: {e}")
            return {'error': 'Failed to serialize metrics'}
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a single value to JSON-safe format"""
        try:
            # Handle basic types
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            
            # Handle lists and tuples
            if isinstance(value, (list, tuple)):
                return [self._serialize_value(item) for item in value]
            
            # Handle dictionaries - avoid sorting keys that might not be comparable
            if isinstance(value, dict):
                result = {}
                for k, v in value.items():
                    try:
                        result[str(k)] = self._serialize_value(v)
                    except Exception as e:
                        logger.warning(f"Error serializing dict key {k}: {e}")
                        result[f"key_{id(k)}"] = str(v)
                return result
            
            # Handle enum types
            if hasattr(value, 'name') and hasattr(value, 'value'):
                return {'name': str(value.name), 'value': str(value.value)}
            
            # Handle objects with __dict__
            if hasattr(value, '__dict__'):
                return self._serialize_value(value.__dict__)
            
            # Handle objects with string representation
            if hasattr(value, '__str__'):
                return str(value)
            
            # Fallback to string representation
            return str(value)
            
        except Exception as e:
            logger.error(f"Error serializing value {value}: {e}")
            return f"<serialization_error: {type(value).__name__}>"

# Global instance
planogram_system = PlanogramSystemWrapper()