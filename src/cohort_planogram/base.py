"""
Base class for cohort-based planogram generators
Provides common functionality and styling for all LOB planograms
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import logging
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

class CohortPlanogramBase:
    """Base class for cohort planogram generators"""
    
    def __init__(self, lob: str):
        self.lob = lob
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path("output/cohort_planograms")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Common styling
        self.text_color = '#1D1D1F'
        self.background_color = '#F8F9FA'
        
        # Color schemes for different categories
        self.category_colors = {
            'Case': '#007AFF',
            'Screen Protector': '#34C759',
            'Cable': '#FF9500',
            'Charger/Adapter': '#FF3B30',
            'Wireless Charger': '#AF52DE',
            'Car Mount': '#FFCC00',
            'PopSocket': '#FF2D92',
            'Power Bank': '#8E8E93',
            'Headphones': '#00C7BE',
            'Cleaning Kit': '#A2845E',
            'Ring Holder': '#5856D6',
            'Wallet': '#32ADE6',
            'Stand': '#FF6B35',
            'Tracking': '#6AC4DC',
            'Apple Pencil': '#1D1D1F',
            'Keyboard': '#48484A',
            'Mouse/Trackpad': '#636366',
            'Watch Band': '#F2F2F7',
            'Hooks/Holders': '#D1D1D6',
            'Hub/Adapter': '#8E8E93',
            'Sleeve': '#E5E5EA',
            'Bag': '#F2F2F7',
            'Storage': '#D1D1D6',
            'Privacy Filter': '#A2845E',
            'Peripheral': '#636366'
        }
        
        # Performance thresholds
        self.high_attach_threshold = 0.15
        self.medium_attach_threshold = 0.08
        
        # Store template configurations
        self.store_configs = {
            'flagship': {
                'figure_size': (24, 18),
                'max_models': 6,
                'max_categories': 8,
                'title_y': 265,
                'matrix_y': 200,
                'insights_x': 20,
                'insights_y': 90,
                'recommended_x': 300,
                'recommended_y': 90,
                'legend_x': 310,
                'legend_y': 100
            },
            'standard': {
                'figure_size': (20, 15),
                'max_models': 5,
                'max_categories': 6,
                'title_y': 220,
                'matrix_y': 170,
                'insights_x': 15,
                'insights_y': 70,
                'recommended_x': 250,
                'recommended_y': 70,
                'legend_x': 260,
                'legend_y': 80
            },
            'express': {
                'figure_size': (16, 12),
                'max_models': 4,
                'max_categories': 5,
                'title_y': 180,
                'matrix_y': 140,
                'insights_x': 10,
                'insights_y': 50,
                'recommended_x': 200,
                'recommended_y': 50,
                'legend_x': 210,
                'legend_y': 60
            }
        }
    
    def create_figure(self, store_type: str):
        """Create matplotlib figure with store-specific dimensions"""
        config = self.store_configs.get(store_type, self.store_configs['flagship'])
        fig, ax = plt.subplots(figsize=config['figure_size'])
        ax.set_facecolor(self.background_color)
        ax.set_xlim(0, config['figure_size'][0] * 16)  # Scale for coordinate system
        ax.set_ylim(0, config['figure_size'][1] * 16)
        ax.axis('off')
        return fig, ax
    
    def add_title(self, ax, title: str, y_pos: int):
        """Add title to the planogram"""
        ax.text(ax.get_xlim()[1]/2, y_pos, title, 
                fontsize=22, fontweight='bold', ha='center', va='center', 
                color=self.text_color)
    
    def add_section_label(self, ax, label: str, x_pos: int, y_pos: int, ha='left'):
        """Add section label"""
        ax.text(x_pos, y_pos, label, fontsize=14, fontweight='bold', 
                color=self.text_color, ha=ha)
    
    def get_performance_color(self, attach_rate: float) -> str:
        """Get color based on performance thresholds"""
        if attach_rate > self.high_attach_threshold:
            return '#007AFF'  # Blue for high performance
        elif attach_rate > self.medium_attach_threshold:
            return '#34C759'  # Green for medium performance
        else:
            return '#8E8E93'  # Gray for low performance
    
    def format_product_name(self, name: str, max_length: int = 12) -> str:
        """Format product name for display"""
        if not name:
            return ""
        
        # Remove common prefixes
        name = name.replace(f'{self.lob} ', '').replace('Apple ', '')
        
        # Truncate if too long
        if len(name) > max_length:
            name = name[:max_length-2] + '..'
        
        return name
    
    def add_performance_indicator(self, ax, x_pos: int, y_pos: int, 
                                attach_rate: float, size: int = 3):
        """Add performance indicator (star for high performance)"""
        if attach_rate > self.high_attach_threshold:
            from matplotlib import patches
            star = patches.Circle((x_pos, y_pos), size, color='gold', alpha=0.9)
            ax.add_patch(star)
    
    def create_legend(self, ax, categories: List[str], x_pos: int, y_pos: int):
        """Create legend for categories and performance indicators"""
        self.add_section_label(ax, "LEGEND", x_pos, y_pos + 30)
        
        # Category colors
        for i, category in enumerate(categories[:6]):  # Limit to 6 for space
            color = self.category_colors.get(category, '#8E8E93')
            
            # Draw color square
            from matplotlib.patches import Rectangle
            legend_rect = Rectangle((x_pos, y_pos + 18 - i*8), 8, 6, 
                                  facecolor=color, edgecolor='#86868B', linewidth=1)
            ax.add_patch(legend_rect)
            
            # Add category name
            ax.text(x_pos + 12, y_pos + 21 - i*8, category, 
                   fontsize=8, ha='left', va='center', color=self.text_color)
    
    def save_planogram(self, fig, filename: str) -> Path:
        """Save planogram to file"""
        output_path = self.output_dir / filename
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        
        self.logger.info(f"Saved planogram: {output_path}")
        return output_path
    
    def generate_cohort_planogram(self, store_type: str) -> Path:
        """Generate cohort planogram - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement generate_cohort_planogram")


class StoreTemplateLoader:
    """Loads store-specific configuration templates"""
    
    def __init__(self):
        self.templates = {
            'flagship': {
                'max_models': 6,
                'max_categories': 8,
                'cell_width': 32,
                'cell_height': 16,
                'x_spacing': 3,
                'y_spacing': 3,
                'x_start': 90
            },
            'standard': {
                'max_models': 5,
                'max_categories': 6,
                'cell_width': 28,
                'cell_height': 14,
                'x_spacing': 2,
                'y_spacing': 2,
                'x_start': 80
            },
            'express': {
                'max_models': 4,
                'max_categories': 5,
                'cell_width': 24,
                'cell_height': 12,
                'x_spacing': 2,
                'y_spacing': 2,
                'x_start': 70
            }
        }
    
    def get_matrix_config(self, store_type: str) -> Dict[str, Any]:
        """Get matrix configuration for store type"""
        return self.templates.get(store_type, self.templates['flagship'])
    
    def get_layout_positions(self, store_type: str) -> Dict[str, int]:
        """Get layout positions for store type"""
        positions = {
            'flagship': {
                'title_y': 265,
                'matrix_y': 200,
                'insights_x': 20,
                'insights_y': 90,
                'recommended_x': 300,
                'recommended_y': 90,
                'legend_x': 310,
                'legend_y': 100
            },
            'standard': {
                'title_y': 220,
                'matrix_y': 170,
                'insights_x': 15,
                'insights_y': 70,
                'recommended_x': 250,
                'recommended_y': 70,
                'legend_x': 260,
                'legend_y': 80
            },
            'express': {
                'title_y': 180,
                'matrix_y': 140,
                'insights_x': 10,
                'insights_y': 50,
                'recommended_x': 200,
                'recommended_y': 50,
                'legend_x': 210,
                'legend_y': 60
            }
        }
        return positions.get(store_type, positions['flagship'])
    
    def get_core_product_config(self, store_type: str) -> Dict[str, int]:
        """Get core product zone configuration"""
        configs = {
            'flagship': {
                'zone_width': 22,
                'zone_height': 12,
                'x_start': 240,
                'y_start': 240,
                'x_spacing': 3
            },
            'standard': {
                'zone_width': 20,
                'zone_height': 10,
                'x_start': 200,
                'y_start': 200,
                'x_spacing': 2
            },
            'express': {
                'zone_width': 18,
                'zone_height': 8,
                'x_start': 160,
                'y_start': 160,
                'x_spacing': 2
            }
        }
        return configs.get(store_type, configs['flagship'])