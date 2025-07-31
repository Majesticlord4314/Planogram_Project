"""
Direct Integration for Planogram Generation
Uses the intelligent planogram generator to create professional-grade planograms
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.visualization.intelligent_planogram_generator import create_intelligent_cases_planogram

def generate_planograms_for_web(store_name):
    """Generate professional planograms for the web UI using the intelligent generator"""
    # Determine store type from store name
    store_type = 'large'  # Default (maps to flagship)
    if 'express' in store_name.lower():
        store_type = 'small'
        num_walls = 1
    elif 'standard' in store_name.lower():
        store_type = 'medium'
        num_walls = 2
    else:
        store_type = 'large'
        num_walls = 3
    
    # Generate planograms using the intelligent generator
    result = create_intelligent_cases_planogram(
        products=[],  # Empty products list (the generator will create sample products)
        store_type=store_type,
        store_name=store_name,
        num_walls=num_walls
    )
    
    return result
