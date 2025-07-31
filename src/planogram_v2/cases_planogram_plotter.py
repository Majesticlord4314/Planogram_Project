#!/usr/bin/env python3
"""
Cases & Covers Planogram Plotter - Modular Visual Generation
Creates clean, professional planogram visualizations for cases
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple
import textwrap
from datetime import datetime

class CasesPlanogramPlotter:
    """Generate visual planograms for cases & covers"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.color_scheme = self._init_color_scheme()
        self.layout_config = self._init_layout_config()
        
    def _init_color_scheme(self) -> Dict:
        """Initialize color scheme for different case types"""
        return {
            'clear': '#E8F4FD',      # Light blue
            'silicone': '#F0F8E8',   # Light green  
            'magsafe': '#FFF2E8',    # Light orange
            'case': '#F8F0FF',       # Light purple
            'leather': '#F5E6D3',    # Light brown
            'other': '#F5F5F5',      # Light gray
            
            # Brand colors
            'Apple': '#007AFF',      # Apple blue
            'Gripp': '#FF6B35',      # Orange
            'Pulse': '#8E44AD',      # Purple
            'Hyphen': '#2ECC71',     # Green
            'Tekne': '#E74C3C',      # Red
            'UAG': '#34495E',        # Dark gray
            
            # Accent colors
            'border': '#D1D1D6',
            'text_primary': '#1D1D1F',
            'text_secondary': '#6D6D70',
            'background': '#FFFFFF'
        }
    
    def _init_layout_config(self) -> Dict:
        """Initialize layout configuration"""
        return {
            'wall_width': 20,
            'wall_height': 14,
            'product_width': 3.2,
            'product_height': 2.4,
            'gap_x': 0.3,
            'gap_y': 0.3,
            'margin_x': 1.0,
            'margin_y': 1.0,
            'cols': 5,
            'rows': 5,
            'title_height': 1.5,
            'legend_width': 4
        }
    
    def create_wall_planogram(self, wall_data: Dict, wall_name: str, store_name: str, output_path: str = None) -> str:
        """Create a single wall planogram"""
        
        # Setup figure
        fig, ax = plt.subplots(figsize=(self.layout_config['wall_width'], self.layout_config['wall_height']))
        ax.set_facecolor(self.color_scheme['background'])
        
        # Calculate layout
        products = wall_data['products']
        cols = self.layout_config['cols']
        rows = self.layout_config['rows']
        
        # Draw title
        self._draw_title(ax, wall_name, store_name)
        
        # Draw products grid
        self._draw_products_grid(ax, products, cols, rows)
        
        # Draw legend
        self._draw_legend(ax, wall_data)
        
        # Draw statistics
        self._draw_statistics(ax, wall_data)
        
        # Finalize plot
        ax.set_xlim(0, self.layout_config['wall_width'])
        ax.set_ylim(0, self.layout_config['wall_height'])
        ax.axis('off')
        
        # Save
        if output_path is None:
            output_path = self.data_path / 'output' / 'planograms' / f"{store_name}_{wall_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"Planogram saved: {output_path}")
        return str(output_path)
    
    def _draw_title(self, ax, wall_name: str, store_name: str):
        """Draw planogram title"""
        title_y = self.layout_config['wall_height'] - 0.8
        
        # Main title
        ax.text(self.layout_config['wall_width'] / 2, title_y, 
                f"Cases & Covers - {wall_name}",
                fontsize=18, fontweight='bold', ha='center',
                color=self.color_scheme['text_primary'])
        
        # Store name
        ax.text(self.layout_config['wall_width'] / 2, title_y - 0.4,
                store_name,
                fontsize=12, ha='center',
                color=self.color_scheme['text_secondary'])
        
        # Date
        ax.text(self.layout_config['wall_width'] - 0.5, title_y,
                datetime.now().strftime('%Y-%m-%d'),
                fontsize=10, ha='right',
                color=self.color_scheme['text_secondary'])
    
    def _draw_products_grid(self, ax, products: List[Dict], cols: int, rows: int):
        """Draw the main products grid"""
        start_x = self.layout_config['margin_x']
        start_y = self.layout_config['wall_height'] - self.layout_config['title_height'] - self.layout_config['margin_y']
        
        product_width = self.layout_config['product_width']
        product_height = self.layout_config['product_height']
        gap_x = self.layout_config['gap_x']
        gap_y = self.layout_config['gap_y']
        
        for i, product in enumerate(products[:cols * rows]):
            row = i // cols
            col = i % cols
            
            x = start_x + col * (product_width + gap_x)
            y = start_y - row * (product_height + gap_y) - product_height
            
            self._draw_product_box(ax, product, x, y, product_width, product_height)
    
    def _draw_product_box(self, ax, product: Dict, x: float, y: float, width: float, height: float):
        """Draw individual product box"""
        
        # Get colors
        category = product.get('category', 'other')
        brand = product.get('brand', 'Other')
        
        bg_color = self.color_scheme.get(category, self.color_scheme['other'])
        brand_color = self.color_scheme.get(brand, self.color_scheme['text_primary'])
        
        # Draw background
        box = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.05",
            facecolor=bg_color,
            edgecolor=self.color_scheme['border'],
            linewidth=1.5,
            alpha=0.9
        )
        ax.add_patch(box)
        
        # Draw brand indicator
        brand_height = 0.2
        brand_box = Rectangle(
            (x, y + height - brand_height), width, brand_height,
            facecolor=brand_color,
            alpha=0.8
        )
        ax.add_patch(brand_box)
        
        # Add text
        self._add_product_text(ax, product, x, y, width, height)
    
    def _add_product_text(self, ax, product: Dict, x: float, y: float, width: float, height: float):
        """Add text to product box"""
        
        # Brand name (top)
        brand = product.get('brand', 'N/A')
        ax.text(x + width/2, y + height - 0.1, brand,
                fontsize=8, fontweight='bold', ha='center', va='center',
                color='white')
        
        # Series (middle-top)
        series = product.get('series', '').replace('iPhone ', '')
        ax.text(x + width/2, y + height - 0.5, series,
                fontsize=7, ha='center', va='center',
                color=self.color_scheme['text_primary'])
        
        # Category (middle)
        category = product.get('category', '').title()
        ax.text(x + width/2, y + height/2, category,
                fontsize=6, ha='center', va='center',
                color=self.color_scheme['text_secondary'],
                style='italic')
        
        # Sales (bottom)
        sales = product.get('total_sales', 0)
        ax.text(x + width/2, y + 0.2, f"{sales}",
                fontsize=7, fontweight='bold', ha='center', va='center',
                color=self.color_scheme['text_primary'])
        
        # Priority indicator (corner)
        priority = product.get('priority_score', 0)
        if priority > 150:  # High priority
            circle = plt.Circle((x + width - 0.2, y + height - 0.2), 0.1, 
                              color='#FF3B30', alpha=0.8)
            ax.add_patch(circle)
        elif priority > 100:  # Medium priority
            circle = plt.Circle((x + width - 0.2, y + height - 0.2), 0.1, 
                              color='#FF9500', alpha=0.8)
            ax.add_patch(circle)
    
    def _draw_legend(self, ax, wall_data: Dict):
        """Draw legend for categories and brands"""
        legend_x = self.layout_config['wall_width'] - self.layout_config['legend_width']
        legend_y = self.layout_config['wall_height'] - 3
        
        # Category legend
        ax.text(legend_x, legend_y, "Categories:", 
                fontsize=10, fontweight='bold',
                color=self.color_scheme['text_primary'])
        
        categories = wall_data.get('category_distribution', {})
        y_offset = 0.3
        
        for i, (category, count) in enumerate(categories.items()):
            y_pos = legend_y - y_offset * (i + 1)
            
            # Color box
            color_box = Rectangle((legend_x, y_pos - 0.1), 0.2, 0.2,
                                facecolor=self.color_scheme.get(category, self.color_scheme['other']),
                                edgecolor=self.color_scheme['border'])
            ax.add_patch(color_box)
            
            # Text
            ax.text(legend_x + 0.3, y_pos, f"{category.title()}: {count}",
                    fontsize=8, va='center',
                    color=self.color_scheme['text_primary'])
    
    def _draw_statistics(self, ax, wall_data: Dict):
        """Draw wall statistics"""
        stats_x = 0.5
        stats_y = 1.5
        
        # Statistics box
        stats_box = FancyBboxPatch(
            (stats_x, stats_y - 1), 6, 1,
            boxstyle="round,pad=0.1",
            facecolor='#F2F2F7',
            edgecolor=self.color_scheme['border'],
            linewidth=1
        )
        ax.add_patch(stats_box)
        
        # Statistics text
        total_products = wall_data.get('total_products', 0)
        total_capacity = wall_data.get('total_capacity', 0)
        
        stats_text = f"Products: {total_products} | Total Sales: {total_capacity:,} | Avg Sales/Product: {total_capacity//max(total_products,1):,}"
        
        ax.text(stats_x + 3, stats_y - 0.5, stats_text,
                fontsize=9, ha='center', va='center',
                color=self.color_scheme['text_primary'])
    
    def create_store_planogram_set(self, store_name: str) -> List[str]:
        """Create complete planogram set for a store"""
        
        # Load processed data
        data_file = self.data_path / 'data' / 'processed' / 'cases_planogram_data.json'
        if not data_file.exists():
            raise FileNotFoundError(f"Processed data not found: {data_file}")
        
        # Load wall layouts (this would come from the data processor)
        from .cases_data_processor import CasesDataProcessor
        processor = CasesDataProcessor(str(self.data_path))
        processor.load_cases_data()
        wall_layouts = processor.generate_wall_layouts(store_name)
        
        # Generate planograms for each wall
        generated_files = []
        
        for wall_name, wall_data in wall_layouts.items():
            output_file = self.create_wall_planogram(wall_data, wall_name, store_name)
            generated_files.append(output_file)
        
        # Create summary report
        summary_file = self._create_summary_report(store_name, wall_layouts, generated_files)
        generated_files.append(summary_file)
        
        return generated_files
    
    def _create_summary_report(self, store_name: str, wall_layouts: Dict, planogram_files: List[str]) -> str:
        """Create a summary report for the planogram set"""
        
        summary_data = {
            'store_name': store_name,
            'generation_date': datetime.now().isoformat(),
            'total_walls': len(wall_layouts),
            'total_products': sum(layout['total_products'] for layout in wall_layouts.values()),
            'total_sales_capacity': sum(layout['total_capacity'] for layout in wall_layouts.values()),
            'wall_breakdown': {},
            'generated_files': planogram_files
        }
        
        for wall_name, layout in wall_layouts.items():
            summary_data['wall_breakdown'][wall_name] = {
                'products': layout['total_products'],
                'sales_capacity': layout['total_capacity'],
                'series_distribution': layout['series_distribution'],
                'category_distribution': layout['category_distribution']
            }
        
        # Save summary
        summary_file = self.data_path / 'output' / 'planograms' / f"{store_name}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        print(f"Summary report saved: {summary_file}")
        return str(summary_file)

# Example usage
if __name__ == "__main__":
    # Initialize plotter
    plotter = CasesPlanogramPlotter("c:/Users/Shivansh Pal/Desktop/Planogram_Project")
    
    # Generate planograms for KORAMANGALA
    try:
        generated_files = plotter.create_store_planogram_set("IMAGINE- KORAMANGALA BENGALURU")
        
        print("\n=== PLANOGRAM GENERATION COMPLETE ===")
        print(f"Generated {len(generated_files)} files:")
        for file in generated_files:
            print(f"  - {file}")
            
    except Exception as e:
        print(f"Error generating planograms: {e}")
        import traceback
        traceback.print_exc()