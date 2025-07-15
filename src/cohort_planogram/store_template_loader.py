"""
Store Template Loader for Cohort Planograms

This module loads store templates and provides store-specific configuration
for cohort planogram generation.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

class StoreTemplateLoader:
    """Load and manage store templates for cohort planograms"""
    
    def __init__(self):
        self.templates_dir = Path("data/raw/store_templates")
        self.store_configs = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all store templates"""
        template_files = {
            'flagship': 'flagship_store.json',
            'standard': 'standard_store.json',
            'express': 'express_store.json'
        }
        
        for store_type, filename in template_files.items():
            template_path = self.templates_dir / filename
            if template_path.exists():
                with open(template_path, 'r') as f:
                    self.store_configs[store_type] = json.load(f)
    
    def get_store_config(self, store_type: str) -> Dict:
        """Get configuration for a specific store type"""
        return self.store_configs.get(store_type, self.store_configs.get('flagship'))
    
    def get_planogram_dimensions(self, store_type: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Get figure size and axis limits for store type"""
        config = self.get_store_config(store_type)
        
        # Map store area to figure dimensions
        area_sqm = config['store_info']['total_area_sqm']
        
        if store_type == 'flagship':
            # Large format: 24x18 inches, 380x280 units
            return (24, 18), (380, 280)
        elif store_type == 'standard':
            # Medium format: 20x15 inches, 320x240 units
            return (20, 15), (320, 240)
        elif store_type == 'express':
            # Compact format: 16x12 inches, 260x200 units
            return (16, 12), (260, 200)
        else:
            # Default to flagship
            return (24, 18), (380, 280)
    
    def get_matrix_config(self, store_type: str) -> Dict:
        """Get matrix configuration for store type"""
        config = self.get_store_config(store_type)
        
        if store_type == 'flagship':
            return {
                'cell_width': 32,
                'cell_height': 16,
                'x_spacing': 3,
                'y_spacing': 3,
                'x_start': 90,
                'max_categories': config['product_mix_rules']['max_categories'],
                'max_models': 6
            }
        elif store_type == 'standard':
            return {
                'cell_width': 28,
                'cell_height': 14,
                'x_spacing': 2,
                'y_spacing': 2,
                'x_start': 80,
                'max_categories': config['product_mix_rules']['max_categories'],
                'max_models': 5
            }
        elif store_type == 'express':
            return {
                'cell_width': 24,
                'cell_height': 12,
                'x_spacing': 2,
                'y_spacing': 2,
                'x_start': 70,
                'max_categories': config['product_mix_rules']['max_categories'],
                'max_models': 4
            }
        else:
            return self.get_matrix_config('flagship')
    
    def get_core_product_config(self, store_type: str) -> Dict:
        """Get core product zone configuration for store type"""
        if store_type == 'flagship':
            return {
                'zone_width': 20,
                'zone_height': 10,
                'x_start': 250,
                'y_start': 230,
                'x_spacing': 3
            }
        elif store_type == 'standard':
            return {
                'zone_width': 18,
                'zone_height': 9,
                'x_start': 220,
                'y_start': 200,
                'x_spacing': 2
            }
        elif store_type == 'express':
            return {
                'zone_width': 16,
                'zone_height': 8,
                'x_start': 180,
                'y_start': 170,
                'x_spacing': 2
            }
        else:
            return self.get_core_product_config('flagship')
    
    def get_layout_positions(self, store_type: str) -> Dict:
        """Get layout positions for different store types"""
        if store_type == 'flagship':
            return {
                'title_y': 270,
                'matrix_y': 200,
                'insights_x': 20,
                'insights_y': 60,
                'recommended_x': 270,
                'recommended_y': 150,
                'legend_x': 310,
                'legend_y': 100
            }
        elif store_type == 'standard':
            return {
                'title_y': 230,
                'matrix_y': 170,
                'insights_x': 15,
                'insights_y': 50,
                'recommended_x': 230,
                'recommended_y': 120,
                'legend_x': 270,
                'legend_y': 80
            }
        elif store_type == 'express':
            return {
                'title_y': 190,
                'matrix_y': 140,
                'insights_x': 10,
                'insights_y': 40,
                'recommended_x': 190,
                'recommended_y': 100,
                'legend_x': 220,
                'legend_y': 60
            }
        else:
            return self.get_layout_positions('flagship')
    
    def get_shelf_config(self, store_type: str) -> List[Dict]:
        """Get shelf configuration for recommended layout"""
        config = self.get_store_config(store_type)
        return config.get('shelves', [])
    
    def get_optimization_weights(self, store_type: str) -> Dict:
        """Get optimization weights for store type"""
        config = self.get_store_config(store_type)
        return config.get('optimization_weights', {})
