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
            self._emit_progress(job_id, 10, "running", f"Starting {lob} cohort planogram for {store_type} store")
            
            # Use the existing cohort planogram system directly
            from src.cohort_planogram.runner import CohortPlanogramRunner
            
            self._emit_progress(job_id, 30, "running", f"Initializing cohort planogram runner for {lob}")
            
            # Create runner and generate planogram
            runner = CohortPlanogramRunner()
            
            self._emit_progress(job_id, 50, "running", f"Generating {lob} cohort planogram for {store_type} store")
            
            # Generate the cohort planogram using existing system
            output_path = runner.generate_cohort_planogram(lob, store_type)
            
            if output_path and Path(output_path).exists():
                self._emit_progress(job_id, 90, "running", f"Cohort planogram generated successfully")
                
                # Set result with file information
                job.result = {
                    'output_name': f"{lob}_{store_type}_cohort_{job_id[:8]}",
                    'lob': lob,
                    'store_type': store_type,
                    'output_path': output_path,
                    'files': [
                        {
                            'name': Path(output_path).name,
                            'type': 'planogram',
                            'path': output_path
                        }
                    ]
                }
                
                self._emit_progress(job_id, 100, "completed", f"Cohort planogram completed: {Path(output_path).name}")
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
            else:
                raise ValueError("Failed to generate cohort planogram - no output file created")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in cohort planogram job {job_id}: {error_msg}")
            self._emit_progress(job_id, 0, "failed", f"Error: {error_msg}")
            job.status = JobStatus.FAILED
            job.error = error_msg
            job.completed_at = datetime.now()
            
            # Emit error via WebSocket
            try:
                from app import socketio
                socketio.emit('job_status', {
                    'job_id': job_id,
                    'status': 'failed',
                    'progress': 0,
                    'error': error_msg,
                    'logs': job.logs[-10:] if job.logs else []
                }, room=job_id)
            except Exception as emit_error:
                logger.error(f"Failed to emit error for job {job_id}: {emit_error}")
    
    def run_lob_optimization(self, job_id: str, lob: str, store_type: str, strategy: str):
        """Run LOB optimization"""
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            self._emit_progress(job_id, 10, "running", f"Starting {lob} optimization with {strategy} strategy")
            
            # Import existing modules
            from src.data_processing.data_loader import DataLoader
            from src.data_processing.data_transformer import DataTransformer
            from src.optimization.product_optimizer import ProductOptimizer
            
            loader = DataLoader(str(project_root / "data" / "raw"))
            transformer = DataTransformer()
            
            self._emit_progress(job_id, 20, "running", f"Loading {lob} products")
            
            # Load products
            products = loader.load_products_by_lob(lob)
            if not products:
                raise ValueError(f"No products found for {lob}")
            
            self._emit_progress(job_id, 40, "running", f"Found {len(products)} products")
            
            # Load store
            store = loader.load_store_template(store_type)
            
            self._emit_progress(job_id, 60, "running", "Transforming products for optimization")
            
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
            
            # Run optimization
            optimizer = ProductOptimizer(store, gap_size=1.0, strategy=strategy)
            result = optimizer.create_planogram(products)
            
            self._emit_progress(job_id, 100, "completed", "LOB optimization completed successfully")
            
            # Set result
            job.result = {
                'products_placed': len(result.products_placed),
                'products_rejected': len(result.products_rejected),
                'metrics': result.metrics,
                'warnings': result.warnings[:10] if result.warnings else [],
                'lob': lob,
                'store_type': store_type,
                'strategy': strategy
            }
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in LOB optimization job {job_id}: {error_msg}")
            self._emit_progress(job_id, 0, "failed", f"Error: {error_msg}")
            job.status = JobStatus.FAILED
            job.error = error_msg
            job.completed_at = datetime.now()
            
            # Emit error via WebSocket
            try:
                from app import socketio
                socketio.emit('job_status', {
                    'job_id': job_id,
                    'status': 'failed',
                    'progress': 0,
                    'error': error_msg,
                    'logs': job.logs[-10:] if job.logs else []
                }, room=job_id)
            except Exception as emit_error:
                logger.error(f"Failed to emit error for job {job_id}: {emit_error}")
    
    def run_category_optimization(self, job_id: str, category: str, store_type: str, strategy: str):
        """Run category optimization"""
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            self._emit_progress(job_id, 10, "running", f"Starting {category} optimization")
            
            # Import existing modules
            from src.data_processing.data_loader import DataLoader
            from src.data_processing.data_transformer import DataTransformer
            from src.optimization.product_optimizer import ProductOptimizer
            
            loader = DataLoader(str(project_root / "data" / "raw"))
            transformer = DataTransformer()
            
            self._emit_progress(job_id, 30, "running", f"Loading {category} products")
            
            # Load products
            products = loader.load_products_by_category(category)
            if not products:
                raise ValueError(f"No products found for category {category}")
            
            self._emit_progress(job_id, 50, "running", f"Found {len(products)} products")
            
            # Load store
            store = loader.load_store_template(store_type)
            
            self._emit_progress(job_id, 70, "running", "Transforming products for optimization")
            
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
            
            # Run optimization
            optimizer = ProductOptimizer(store, gap_size=1.0, strategy=strategy)
            result = optimizer.create_planogram(products)
            
            self._emit_progress(job_id, 100, "completed", "Category optimization completed")
            
            # Set result
            job.result = {
                'products_placed': len(result.products_placed),
                'products_rejected': len(result.products_rejected),
                'metrics': result.metrics,
                'warnings': result.warnings[:10] if result.warnings else [],
                'category': category,
                'store_type': store_type,
                'strategy': strategy
            }
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in category optimization job {job_id}: {error_msg}")
            self._emit_progress(job_id, 0, "failed", f"Error: {error_msg}")
            job.status = JobStatus.FAILED
            job.error = error_msg
            job.completed_at = datetime.now()
            
            # Emit error via WebSocket
            try:
                from app import socketio
                socketio.emit('job_status', {
                    'job_id': job_id,
                    'status': 'failed',
                    'progress': 0,
                    'error': error_msg,
                    'logs': job.logs[-10:] if job.logs else []
                }, room=job_id)
            except Exception as emit_error:
                logger.error(f"Failed to emit error for job {job_id}: {emit_error}")
    
    def run_full_store_optimization(self, job_id: str, store_type: str, strategy: str):
        """Run full store optimization"""
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            self._emit_progress(job_id, 10, "running", "Loading all products")
            
            # Import existing modules
            from src.data_processing.data_loader import DataLoader
            from src.data_processing.data_transformer import DataTransformer
            from src.optimization.product_optimizer import ProductOptimizer
            
            loader = DataLoader(str(project_root / "data" / "raw"))
            transformer = DataTransformer()
            
            self._emit_progress(job_id, 30, "running", "Loading products from all categories")
            
            # Load all products
            products = loader.load_all_products()
            if not products:
                raise ValueError("No products found")
            
            self._emit_progress(job_id, 50, "running", f"Found {len(products)} total products")
            
            # Load store
            store = loader.load_store_template(store_type)
            
            self._emit_progress(job_id, 70, "running", "Transforming all products for optimization")
            
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
            
            # Run optimization
            optimizer = ProductOptimizer(store, gap_size=1.0, strategy=strategy)
            result = optimizer.create_planogram(products)
            
            self._emit_progress(job_id, 100, "completed", "Full store optimization completed")
            
            # Set result
            job.result = {
                'products_placed': len(result.products_placed),
                'products_rejected': len(result.products_rejected),
                'metrics': result.metrics,
                'warnings': result.warnings[:10] if result.warnings else [],
                'store_type': store_type,
                'strategy': strategy,
                'total_products_processed': len(products)
            }
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in full store optimization job {job_id}: {error_msg}")
            self._emit_progress(job_id, 0, "failed", f"Error: {error_msg}")
            job.status = JobStatus.FAILED
            job.error = error_msg
            job.completed_at = datetime.now()
            
            # Emit error via WebSocket
            try:
                from app import socketio
                socketio.emit('job_status', {
                    'job_id': job_id,
                    'status': 'failed',
                    'progress': 0,
                    'error': error_msg,
                    'logs': job.logs[-10:] if job.logs else []
                }, room=job_id)
            except Exception as emit_error:
                logger.error(f"Failed to emit error for job {job_id}: {emit_error}")
    
    def run_job_async(self, job_id: str):
        """Run a job asynchronously in a separate thread"""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        def run_job():
            try:
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
                logger.error(f"Job {job_id} failed: {e}")
                # Error is already set in the individual run methods
        
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
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            return True
        return False

# Global instance
planogram_system = PlanogramSystemWrapper()