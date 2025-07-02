from typing import Any, Dict, List, Optional
import json
from datetime import datetime
from pathlib import Path

class PlanogramDebugger:
    """Debug utilities for planogram system"""
    
    def __init__(self, debug_dir: str = "debug"):
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.checkpoints = []
    
    def checkpoint(self, name: str, data: Any, description: str = ""):
        """Save a checkpoint for debugging"""
        self.checkpoints.append({
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'description': description
        })
    
    def generate_debug_report(self) -> str:
        """Generate a debug report"""
        return f"Debug session {self.session_id}: {len(self.checkpoints)} checkpoints"