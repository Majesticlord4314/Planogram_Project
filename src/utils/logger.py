import logging
import sys
from datetime import datetime
from pathlib import Path

class PlanogramLogger:
    """Centralized logging system for the planogram project"""
    
    def __init__(self, log_dir: str = "logs", console_level: str = "INFO", file_level: str = "DEBUG"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('planogram_system')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level))
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.log_dir / f"planogram_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, file_level))
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)-15s | %(funcName)-20s | %(message)s'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"Logging initialized. Log file: {log_file}")
    
    def get_logger(self):
        return self.logger

# Global logger instance
_logger_instance = None

def get_logger():
    """Get or create logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PlanogramLogger()
    return _logger_instance.get_logger()
