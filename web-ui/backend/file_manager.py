"""
File management utilities for the planogram web UI
Handles output files, cleanup, and file serving
"""

import os
import glob
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FileManager:
    """Manages output files and system information"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.output_dir = project_root / "output"
        self.web_output_dir = project_root / "web-ui" / "output"
        
        # Ensure output directories exist
        self.output_dir.mkdir(exist_ok=True)
        self.web_output_dir.mkdir(exist_ok=True)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            # Check data directories
            data_dir = self.project_root / "data"
            raw_dir = data_dir / "raw"
            processed_dir = data_dir / "processed"
            
            # Count files in each directory
            raw_files = len(list(raw_dir.glob("*.csv"))) if raw_dir.exists() else 0
            processed_files = len(list(processed_dir.glob("*.csv"))) if processed_dir.exists() else 0
            output_files = len(list(self.output_dir.glob("*"))) if self.output_dir.exists() else 0
            
            # Check for key data files
            key_files = {
                'cases_sales.csv': (raw_dir / 'cases_sales.csv').exists(),
                'ipad-cases-transformed.csv': (processed_dir / 'ipad-cases-transformed.csv').exists(),
                'mac-accessories-transformed.csv': (processed_dir / 'mac-accessories-transformed.csv').exists(),
                'combined_watch.csv': (processed_dir / 'combined_watch.csv').exists(),
                'planogram_sleeves_bags.csv': (processed_dir / 'planogram_sleeves_bags.csv').exists()
            }
            
            return {
                'project_root': str(self.project_root),
                'directories': {
                    'data_raw': str(raw_dir),
                    'data_processed': str(processed_dir),
                    'output': str(self.output_dir),
                    'web_output': str(self.web_output_dir)
                },
                'file_counts': {
                    'raw_files': raw_files,
                    'processed_files': processed_files,
                    'output_files': output_files
                },
                'key_files': key_files,
                'disk_usage': self._get_disk_usage()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    def _get_disk_usage(self) -> Dict[str, int]:
        """Get disk usage information"""
        try:
            output_size = sum(f.stat().st_size for f in self.output_dir.rglob('*') if f.is_file())
            web_output_size = sum(f.stat().st_size for f in self.web_output_dir.rglob('*') if f.is_file())
            
            return {
                'output_dir_bytes': output_size,
                'web_output_dir_bytes': web_output_size,
                'total_bytes': output_size + web_output_size
            }
        except Exception as e:
            logger.error(f"Error calculating disk usage: {e}")
            return {'error': str(e)}
    
    def get_output_files(self, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of output files with metadata"""
        files = []
        
        try:
            # Search in both output directories
            search_dirs = [self.output_dir, self.web_output_dir]
            
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                
                if pattern:
                    # Use glob pattern
                    file_paths = list(search_dir.glob(f"*{pattern}*"))
                else:
                    # Get all files
                    file_paths = [f for f in search_dir.iterdir() if f.is_file()]
                
                for file_path in file_paths:
                    try:
                        stat = file_path.stat()
                        files.append({
                            'name': file_path.name,
                            'path': str(file_path),
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'directory': search_dir.name
                        })
                    except Exception as e:
                        logger.error(f"Error getting file info for {file_path}: {e}")
                        continue
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing output files: {e}")
        
        return files
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file from output directories"""
        try:
            # Try both output directories
            for search_dir in [self.output_dir, self.web_output_dir]:
                file_path = search_dir / filename
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    logger.info(f"Deleted file: {file_path}")
                    return True
            
            logger.warning(f"File not found for deletion: {filename}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            return False
    
    def cleanup_old_files(self, days: int = 7) -> List[str]:
        """Clean up files older than specified days"""
        deleted_files = []
        cutoff_time = datetime.now() - timedelta(days=days)
        
        try:
            for search_dir in [self.output_dir, self.web_output_dir]:
                if not search_dir.exists():
                    continue
                
                for file_path in search_dir.iterdir():
                    if not file_path.is_file():
                        continue
                    
                    try:
                        # Check file modification time
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_time < cutoff_time:
                            file_path.unlink()
                            deleted_files.append(file_path.name)
                            logger.info(f"Cleaned up old file: {file_path}")
                    
                    except Exception as e:
                        logger.error(f"Error cleaning up file {file_path}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        return deleted_files
    
    def get_file_path(self, filename: str) -> Optional[Path]:
        """Get the full path to a file in output directories"""
        for search_dir in [self.output_dir, self.web_output_dir]:
            file_path = search_dir / filename
            if file_path.exists() and file_path.is_file():
                return file_path
        return None
    
    def copy_to_web_output(self, source_path: Path, filename: str = None) -> Optional[Path]:
        """Copy a file to the web output directory for serving"""
        try:
            if not source_path.exists():
                return None
            
            target_name = filename or source_path.name
            target_path = self.web_output_dir / target_name
            
            # Copy file
            import shutil
            shutil.copy2(source_path, target_path)
            
            logger.info(f"Copied {source_path} to {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"Error copying file to web output: {e}")
            return None