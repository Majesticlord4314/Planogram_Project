"""
Base Class for Cohort-Based Planogram Generation

This module provides the base class and common functionality
for all cohort-based planogram generators.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib import patches
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from .store_template_loader import StoreTemplateLoader

class CohortPlanogramBase:
    """Base class for cohort-based planogram generation"""
    
    def __init__(self, lob: str):
        self.lob = lob
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path("output/cohort_planograms")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.store_template_loader = StoreTemplateLoader()

        # Common visual properties
        self.bg_color = '#F8F9FA'
        self.border_color = '#D1D1D6'
        self.text_color = '#1D1D1F'
        
        # Common color schemes for accessory categories
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
            'Watch Band': '#2E2E2E',
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
        self.low_attach_threshold = 0.03
        
    def create_figure(self, store_type: str = 'flagship') -> Tuple[plt.Figure, plt.Axes]:
        """Create standardized figure for cohort planogram based on store type"""
        figsize, (xlim, ylim) = self.store_template_loader.get_planogram_dimensions(store_type)
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_facecolor('#F8F9FA')
        ax.set_xlim(0, xlim)
        ax.set_ylim(0, ylim)
        ax.axis('off')
        return fig, ax
    
    def add_title(self, ax: plt.Axes, title: str, y_pos: int = 265) -> None:
        """Add title to planogram"""
        ax.text(190, y_pos, title, 
                fontsize=22, fontweight='bold', ha='center', va='center', 
                color='#1D1D1F')
    
    def add_section_label(self, ax: plt.Axes, label: str, x_pos: int, y_pos: int, ha: str = 'center') -> None:
        """Add section label"""
        ax.text(x_pos, y_pos, label, 
                fontsize=14, fontweight='bold', ha=ha, color='#1D1D1F')
    
    def get_performance_color(self, attach_rate: float) -> str:
        """Get color based on attach rate performance"""
        if attach_rate > self.high_attach_threshold:
            return '#007AFF'  # Blue for high performance
        elif attach_rate > self.medium_attach_threshold:
            return '#34C759'  # Green for medium performance
        elif attach_rate > self.low_attach_threshold:
            return '#FF9500'  # Orange for low performance
        else:
            return '#8E8E93'  # Gray for very low performance
    
    def add_performance_indicator(self, ax: plt.Axes, x_pos: float, y_pos: float, 
                                 attach_rate: float, size: int = 3) -> None:
        """Add performance indicator (star for high performance)"""
        if attach_rate > self.high_attach_threshold:
            star = patches.Circle((x_pos, y_pos), size, color='gold', alpha=0.9)
            ax.add_patch(star)
    
    def format_product_name(self, name: str, max_length: int = 15) -> str:
        """Format product name for display"""
        # Remove common prefixes
        name = name.replace('iPhone ', '').replace('iPad ', '').replace('Mac ', '')
        name = name.replace('Apple Watch ', '').replace('AirPods ', '')
        
        # Shorten common terms
        replacements = {
            'Pro Max': 'PM',
            'Plus': '+',
            'Standard': 'Std',
            'Generation': 'Gen',
            '2nd Gen': '2G',
            '3rd Gen': '3G'
        }
        
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        # Truncate if still too long
        if len(name) > max_length:
            name = name[:max_length-2] + '..'
        
        return name
    
    def save_planogram(self, fig: plt.Figure, filename: str) -> Path:
        """Save planogram to file"""
        output_path = self.output_dir / filename
        plt.tight_layout()
        fig.savefig(output_path, dpi=200, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        
        self.logger.info(f"Saved {self.lob} cohort planogram: {output_path}")
        return output_path
    
    def create_legend(self, ax: plt.Axes, categories: List[str], 
                     x_pos: int = 250, y_pos: int = 60) -> None:
        """Create legend for accessory categories"""
        ax.text(x_pos, y_pos + 35, "CATEGORIES", 
                fontsize=11, fontweight='bold', color='#1D1D1F', ha='left')
        
        # Show up to 8 categories for more compact display
        display_categories = categories[:8]
        
        for i, category in enumerate(display_categories):
            color = self.category_colors.get(category, '#8E8E93')
            
            # Draw color square
            legend_rect = Rectangle((x_pos, y_pos + 25 - i*6), 6, 4, 
                                  facecolor=color, edgecolor='#86868B', linewidth=1)
            ax.add_patch(legend_rect)
            
            # Add category name
            ax.text(x_pos + 10, y_pos + 27 - i*6, category, 
                   fontsize=7, ha='left', va='center', color='#1D1D1F')
        
        # Add performance indicators legend
        ax.text(x_pos, y_pos - 30, "PERFORMANCE", 
                fontsize=11, fontweight='bold', color='#1D1D1F', ha='left')
        
        # High performance
        star = patches.Circle((x_pos + 3, y_pos - 36), 1.5, color='gold', alpha=0.9)
        ax.add_patch(star)
        ax.text(x_pos + 8, y_pos - 36, f"> {self.high_attach_threshold:.0%} (High)", 
               fontsize=7, ha='left', va='center', color='#1D1D1F')
        
        # Medium performance
        medium_rect = Rectangle((x_pos + 1, y_pos - 46), 4, 3, 
                              facecolor='#34C759', alpha=0.7, edgecolor='#86868B', linewidth=1)
        ax.add_patch(medium_rect)
        ax.text(x_pos + 8, y_pos - 44, f"> {self.medium_attach_threshold:.0%} (Medium)", 
               fontsize=7, ha='left', va='center', color='#1D1D1F')
        
        # Low performance
        low_rect = Rectangle((x_pos + 1, y_pos - 56), 4, 3, 
                           facecolor='#FF9500', alpha=0.7, edgecolor='#86868B', linewidth=1)
        ax.add_patch(low_rect)
        ax.text(x_pos + 8, y_pos - 54, f"> {self.low_attach_threshold:.0%} (Low)", 
               fontsize=7, ha='left', va='center', color='#1D1D1F')
    
    def generate_cohort_planogram(self, store_type: str) -> Path:
        """Generate cohort planogram - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement generate_cohort_planogram")
