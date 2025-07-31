#!/usr/bin/env python3
"""
Enhanced Retail Planogram Generator
Creates professional retail planograms with:
- Rectangle shapes mimicking phone dimensions
- Product dimensions affecting placement density
- Series-based wall allocation (Base, Plus, Pro, Pro Max)
- Column-wise brand grouping
- Realistic product categorization
- Screen protector/TG optimization
- Forced diversity while respecting dimensions
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import FancyBboxPatch, Rectangle
import seaborn as sns
from pathlib import Path
from datetime import datetime
import re
import logging
from collections import defaultdict, Counter
import random
import os
from itertools import cycle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedPlanogramGenerator:
    """Enhanced professional retail planogram generator"""
    
    def __init__(self):
        # Apple brand colors (blue tones)
        self.apple_colors = ['#007AFF', '#0051D5', '#003D82', '#5AC8FA', '#34AADC']
        
        # TPA brand colors (diverse palette)
        self.tpa_colors = {
            'Gripp': '#FF6B35', 
            'Pulse': '#8E44AD',
            'Hyphen': '#E74C3C',
            'Tekne': '#2ECC71',
            'UAG': '#F39C12',
            'AT Minimal': '#34495E',
            'Roskilde': '#9B59B6',
            'nmaxn': '#1ABC9C',
            'Peak Design': '#E67E22',
            'Robocare': '#3498DB',
            'Flayrr': '#E91E63',
            'PG': '#795548',
            'Default': '#95A5A6'
        }
        
        # Screen protector color
        self.screen_protector_color = '#F8F9FA'
        
        # Product dimensions mapping (width, height) in relative units
        self.product_dimensions = {
            'iPhone 16 Base': (0.8, 1.6),      # Standard iPhone size
            'iPhone 16 Plus': (0.9, 1.7),     # Larger iPhone
            'iPhone 16 Pro': (0.8, 1.6),      # Pro size
            'iPhone 16 Pro Max': (0.9, 1.7),  # Pro Max size
            'iPhone 15 Base': (0.8, 1.6),
            'iPhone 15 Plus': (0.9, 1.7),
            'iPhone 15 Pro': (0.8, 1.6),
            'iPhone 15 Pro Max': (0.9, 1.7),
            'screen_protector': (0.7, 1.5),   # Smaller footprint
            'lens_protector': (0.4, 0.4),     # Very small
            'default': (0.8, 1.6)
        }
        
        # Density multipliers based on product type
        self.density_multipliers = {
            'lens_protector': 4,      # 4x density (very small)
            'screen_protector': 2,    # 2x density (thin)
            'case_thin': 1,           # Normal density
            'case_thick': 0.8,        # Slightly less dense
            'case_bulky': 0.6         # Lower density (thick cases)
        }

    def categorize_products(self, products):
        """Enhanced product categorization with better logic for all accessory types"""
        apple_products = []
        tpa_products = []
        screen_protectors = []
        lens_protectors = []
        
        for product in products:
            product_name = str(product.product_name).lower()
            brand = str(product.brand).strip()
            
            # Lens protectors (very small items)
            if any(term in product_name for term in ['lens protector', 'camera lens', 'lens guard', 'camera protector']):
                lens_protectors.append(product)
            # Screen protectors and tempered glass - broader matching
            elif any(term in product_name for term in ['tg', 'tempered glass', 'screen protector', 'screen guard', 'protector', 'glass']):
                screen_protectors.append(product)
            # Apple products (including clear cases)
            elif (brand.lower() == 'apple' or 
                  brand.lower() == 'apple inc.' or
                  'apple' in brand.lower() or
                  ('clear' in product_name and any(apple_term in product_name for apple_term in ['magsafe', 'iphone']))):
                apple_products.append(product)
            # TPA products (everything else including cases, covers, etc.)
            else:
                tpa_products.append(product)
        
        return apple_products, tpa_products, screen_protectors, lens_protectors

    def extract_iphone_series(self, product_name):
        """Extract iPhone series from product name"""
        product_name = str(product_name).lower()
        
        # iPhone 16 series
        if 'iphone 16 pro max' in product_name:
            return 'iPhone 16 Pro Max'
        elif 'iphone 16 plus' in product_name:
            return 'iPhone 16 Plus'
        elif 'iphone 16 pro' in product_name:
            return 'iPhone 16 Pro'
        elif 'iphone 16' in product_name:
            return 'iPhone 16 Base'
        
        # iPhone 15 series
        elif 'iphone 15 pro max' in product_name:
            return 'iPhone 15 Pro Max'
        elif 'iphone 15 plus' in product_name:
            return 'iPhone 15 Plus'
        elif 'iphone 15 pro' in product_name:
            return 'iPhone 15 Pro'
        elif 'iphone 15' in product_name:
            return 'iPhone 15 Base'
        
        return 'Other'

    def get_product_density_type(self, product_name):
        """Determine product density type based on characteristics"""
        product_name = str(product_name).lower()
        
        if any(term in product_name for term in ['lens protector', 'camera lens']):
            return 'lens_protector'
        elif any(term in product_name for term in ['tg', 'tempered glass', 'screen protector']):
            return 'screen_protector'
        elif any(term in product_name for term in ['combat', 'defender', 'armor', 'armour', 'rugged']):
            return 'case_bulky'
        elif any(term in product_name for term in ['leather', 'wallet', 'folio']):
            return 'case_thick'
        else:
            return 'case_thin'

    def calculate_optimal_grid(self, total_products, wall_focus):
        """Calculate optimal grid size based on product count and focus"""
        # Base grid calculations with phone-like rectangles
        if wall_focus == 'screen_protectors':
            # More slots for small items
            return (10, 8)  # 80 slots
        elif total_products > 60:
            return (8, 6)   # 48 slots
        elif total_products > 30:
            return (6, 5)   # 30 slots
        else:
            return (5, 4)   # 20 slots

    def allocate_walls_by_series(self, apple_products, tpa_products, screen_protectors, lens_protectors, num_walls):
        """Allocate walls based on series strategy"""
        
        # Group Apple products by series
        apple_by_series = defaultdict(list)
        for product in apple_products:
            series = self.extract_iphone_series(product.product_name)
            if series != 'Other':
                apple_by_series[series].append(product)
        
        wall_allocations = {}
        
        if num_walls >= 4:
            # 4+ walls: Each wall dedicated to one series
            series_order = ['iPhone 16 Pro Max', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16 Base']
            
            for i, series in enumerate(series_order[:num_walls-1]):
                wall_num = i + 1
                wall_allocations[f'wall{wall_num}'] = {
                    'focus': f'{series} Series',
                    'apple': apple_by_series.get(series, []),
                    'tpa': [p for p in tpa_products if series.replace(' ', ' ').lower() in str(p.product_name).lower()],
                    'screen_protectors': [],
                    'lens_protectors': []
                }
            
            # Last wall for accessories
            wall_allocations[f'wall{num_walls}'] = {
                'focus': 'Screen Protectors & Accessories',
                'apple': [],
                'tpa': [],
                'screen_protectors': screen_protectors,
                'lens_protectors': lens_protectors
            }
            
        elif num_walls == 3:
            # 3 walls: 2 walls split between 4 series, 1 wall for accessories
            wall_allocations['wall1'] = {
                'focus': 'iPhone 16 Pro Max & Pro',
                'apple': apple_by_series.get('iPhone 16 Pro Max', []) + apple_by_series.get('iPhone 16 Pro', []),
                'tpa': [p for p in tpa_products if any(term in str(p.product_name).lower() for term in ['pro max', 'pro'])],
                'screen_protectors': [],
                'lens_protectors': []
            }
            
            wall_allocations['wall2'] = {
                'focus': 'iPhone 16 Plus & Base',
                'apple': apple_by_series.get('iPhone 16 Plus', []) + apple_by_series.get('iPhone 16 Base', []),
                'tpa': [p for p in tpa_products if any(term in str(p.product_name).lower() for term in ['plus', '16']) and 'pro' not in str(p.product_name).lower()],
                'screen_protectors': [],
                'lens_protectors': []
            }
            
            wall_allocations['wall3'] = {
                'focus': 'Screen Protectors & TPA Mix',
                'apple': [],
                'tpa': [p for p in tpa_products if p not in wall_allocations['wall1']['tpa'] + wall_allocations['wall2']['tpa']],
                'screen_protectors': screen_protectors,
                'lens_protectors': lens_protectors
            }
            
        elif num_walls == 2:
            # 2 walls: Split 4 series equally
            wall_allocations['wall1'] = {
                'focus': 'iPhone 16 Pro Max & Plus',
                'apple': apple_by_series.get('iPhone 16 Pro Max', []) + apple_by_series.get('iPhone 16 Plus', []),
                'tpa': [p for p in tpa_products if any(term in str(p.product_name).lower() for term in ['pro max', 'plus'])],
                'screen_protectors': screen_protectors[:len(screen_protectors)//2],
                'lens_protectors': lens_protectors[:len(lens_protectors)//2]
            }
            
            wall_allocations['wall2'] = {
                'focus': 'iPhone 16 Pro & Base + Accessories',
                'apple': apple_by_series.get('iPhone 16 Pro', []) + apple_by_series.get('iPhone 16 Base', []),
                'tpa': [p for p in tpa_products if p not in wall_allocations['wall1']['tpa']],
                'screen_protectors': screen_protectors[len(screen_protectors)//2:],
                'lens_protectors': lens_protectors[len(lens_protectors)//2:]
            }
            
        else:  # 1 wall
            # 1 wall: Split all 4 series equally
            wall_allocations['wall1'] = {
                'focus': 'All iPhone 16 Series + Accessories',
                'apple': apple_products,
                'tpa': tpa_products,
                'screen_protectors': screen_protectors,
                'lens_protectors': lens_protectors
            }
        
        return wall_allocations

    def create_column_brand_layout(self, products_by_type, grid_size):
        """Create realistic retail layout with Apple dominating first half of rows (top rows)"""
        rows, cols = grid_size
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        
        # Group products by brand
        all_products = []
        for product_list in products_by_type.values():
            all_products.extend(product_list)
        
        # Separate Apple and TPA products
        apple_products = []
        tpa_products = []
        screen_protectors = []
        
        for product in all_products:
            brand = str(product.brand).strip()
            product_name = str(product.product_name).lower()
            
            if 'screen' in product_name or 'protector' in product_name or 'tempered' in product_name:
                screen_protectors.append(product)
            elif brand == 'Apple':
                apple_products.append(product)
            else:
                tpa_products.append(product)
        
        # Calculate first half rows (Apple's premium zone)
        first_half_rows = rows // 2 + (rows % 2)  # Round up for Apple
        second_half_rows = rows - first_half_rows
        
        # Apple gets 50% placement in first half (premium eye-level positions)
        apple_slots_first_half = int((first_half_rows * cols) * 0.5)
        
        products_placed = 0
        
        # Phase 1: Fill first half rows with Apple products (50% requirement)
        apple_placed = 0
        for row in range(first_half_rows):
            for col in range(cols):
                if apple_placed < apple_slots_first_half and apple_placed < len(apple_products):
                    grid[row][col] = apple_products[apple_placed]
                    apple_placed += 1
                    products_placed += 1
                elif apple_placed < len(apple_products):
                    # Continue placing Apple if available
                    grid[row][col] = apple_products[apple_placed]
                    apple_placed += 1
                    products_placed += 1
        
        # Phase 2: Fill remaining first half slots with premium TPA brands
        tpa_placed = 0
        for row in range(first_half_rows):
            for col in range(cols):
                if grid[row][col] is None and tpa_placed < len(tpa_products):
                    grid[row][col] = tpa_products[tpa_placed]
                    tpa_placed += 1
                    products_placed += 1
        
        # Phase 3: Fill second half with remaining TPA and screen protectors
        for row in range(first_half_rows, rows):
            for col in range(cols):
                if grid[row][col] is None:
                    if tpa_placed < len(tpa_products):
                        grid[row][col] = tpa_products[tpa_placed]
                        tpa_placed += 1
                        products_placed += 1
                    elif len(screen_protectors) > 0:
                        grid[row][col] = screen_protectors.pop(0)
                        products_placed += 1
        
        # Phase 4: Fill any remaining slots with screen protectors
        for row in range(rows):
            for col in range(cols):
                if grid[row][col] is None and len(screen_protectors) > 0:
                    grid[row][col] = screen_protectors.pop(0)
                    products_placed += 1
        
        return grid, products_placed

    def draw_phone_rectangle(self, ax, row, col, rows, cols, product, product_type):
        """Draw rectangle that mimics phone dimensions with improved text formatting"""
        
        # Get product dimensions
        series = self.extract_iphone_series(product.product_name)
        if product_type == 'lens_protector':
            width, height = self.product_dimensions['lens_protector']
        elif product_type == 'screen_protector':
            width, height = self.product_dimensions['screen_protector']
        else:
            width, height = self.product_dimensions.get(series, self.product_dimensions['default'])
        
        # Calculate position (center the rectangle in the grid cell)
        cell_width = 1.0
        cell_height = 1.0
        
        x_offset = (cell_width - width) / 2
        y_offset = (cell_height - height) / 2
        
        x = col + x_offset
        y = rows - row - 1 + y_offset
        
        # Determine color based on product type and brand
        if product_type in ['lens_protector', 'screen_protector']:
            bg_color = self.screen_protector_color
            edge_color = '#6C757D'
            edge_style = '--'
            text_color = 'black'  # Better contrast for screen protectors
        elif str(product.brand).strip().lower() == 'apple':
            # Apple products get blue tones
            color_idx = hash(str(product.product_name)) % len(self.apple_colors)
            bg_color = self.apple_colors[color_idx]
            edge_color = '#2C3E50'
            edge_style = '-'
            text_color = 'white'
        else:
            # TPA products get brand-specific colors
            brand = str(product.brand).strip()
            bg_color = self.tpa_colors.get(brand, self.tpa_colors['Default'])
            edge_color = '#2C3E50'
            edge_style = '-'
            text_color = 'white'
        
        # Create rounded rectangle with phone-like proportions
        rect = FancyBboxPatch(
            (x, y),
            width, height,
            boxstyle="round,pad=0.03",
            facecolor=bg_color,
            edgecolor=edge_color,
            linewidth=1.5 if product_type not in ['lens_protector', 'screen_protector'] else 1,
            linestyle=edge_style,
            alpha=0.9
        )
        
        ax.add_patch(rect)
        
        # Improved text labels with better formatting
        brand_text = str(product.brand).strip()
        
        # Extract series information
        series_text = self.extract_iphone_series(product.product_name)
        if not series_text or series_text == 'default':
            series_text = 'iPhone'
        
        # Product type text
        if product_type == 'lens_protector':
            type_text = 'Lens Protector'
        elif product_type == 'screen_protector':
            type_text = 'Screen Protector'
        else:
            case_type = self.extract_case_type(product.product_name)
            type_text = case_type
        
        # Color text
        color_text = self.extract_color(product.product_name)
        
        # Calculate font sizes based on rectangle size
        base_font_size = min(width * 8, height * 4, 10)
        brand_font_size = max(base_font_size * 0.9, 6)
        series_font_size = max(base_font_size * 0.8, 5)
        type_font_size = max(base_font_size * 0.7, 5)
        color_font_size = max(base_font_size * 0.6, 4)
        
        # Add text in 4 lines: Brand, Series, Type, Color
        y_positions = [0.8, 0.6, 0.4, 0.2]  # From top to bottom
        texts = [brand_text, series_text, type_text, color_text]
        font_sizes = [brand_font_size, series_font_size, type_font_size, color_font_size]
        font_weights = ['bold', 'normal', 'normal', 'normal']
        
        for i, (text, font_size, font_weight) in enumerate(zip(texts, font_sizes, font_weights)):
            if text and text != 'Unknown':  # Only show non-empty text
                ax.text(x + width/2, y + height * y_positions[i], text, 
                       ha='center', va='center', 
                       fontsize=font_size, 
                       fontweight=font_weight, 
                       color=text_color,
                       wrap=True)
        
        return rect

    def extract_color(self, product_name):
        """Extract color from product name"""
        color_patterns = [
            'Black', 'White', 'Clear', 'Blue', 'Green', 'Red', 'Pink', 
            'Purple', 'Gray', 'Grey', 'Brown', 'Tan', 'Gold', 'Silver',
            'Denim', 'Fuchsia', 'Lake Green', 'Plum', 'Star Fruit', 
            'Stone Gray', 'Ultramarine', 'Natural Titanium', 'Gunmetal'
        ]
        
        product_name = str(product_name)
        for color in color_patterns:
            if color.lower() in product_name.lower():
                return color
        return 'Unknown'

    def extract_case_type(self, product_name):
        """Extract case type from product name"""
        product_name = str(product_name).lower()
        
        if 'clear' in product_name:
            return 'Clear'
        elif 'silicone' in product_name or 'silicon' in product_name:
            return 'Silicone'
        elif 'leather' in product_name:
            return 'Leather'
        elif 'magsafe' in product_name:
            return 'MagSafe'
        elif 'combat' in product_name:
            return 'Combat'
        elif 'defender' in product_name:
            return 'Defender'
        elif 'crystal' in product_name:
            return 'Crystal'
        elif 'armor' in product_name or 'armour' in product_name:
            return 'Armor'
        else:
            return 'Standard'

    def create_wall_planogram(self, wall_data, wall_num, store_name, store_type, output_dir, timestamp=None):
        """Create enhanced wall planogram with phone-like rectangles and column grouping"""
        
        # Get timestamp if not provided
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Collect all products for this wall
        all_products = (wall_data['apple'] + wall_data['tpa'] + 
                       wall_data['screen_protectors'] + wall_data['lens_protectors'])
        
        if not all_products:
            logger.warning(f"No products for wall {wall_num}")
            return None
        
        # Calculate optimal grid size
        grid_size = self.calculate_optimal_grid(len(all_products), wall_data['focus'])
        rows, cols = grid_size
        
        # Create column-wise brand layout
        products_by_type = {
            'apple': wall_data['apple'],
            'tpa': wall_data['tpa'],
            'screen_protectors': wall_data['screen_protectors'],
            'lens_protectors': wall_data['lens_protectors']
        }
        
        product_grid, products_placed = self.create_column_brand_layout(products_by_type, grid_size)
        
        # Create figure with better proportions
        fig, ax = plt.subplots(figsize=(cols * 2.5, rows * 2))
        ax.set_xlim(0, cols)
        ax.set_ylim(0, rows)
        ax.set_aspect('equal')
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Enhanced title positioned over the plot (inside the plot area)
        title = f"{store_name} - Wall {wall_num}\n{wall_data['focus']}"
        ax.text(cols/2, rows + 0.3, title, 
               ha='center', va='bottom', 
               fontsize=16, fontweight='bold', 
               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor='black', alpha=0.8))
        
        # Draw products with phone-like rectangles
        placement_details = []
        apple_count = tpa_count = screen_count = lens_count = 0
        
        for row in range(rows):
            for col in range(cols):
                product = product_grid[row][col]
                
                if product:
                    # Determine product type
                    product_type = self.get_product_density_type(product.product_name)
                    
                    # Count by type
                    if product in wall_data['apple']:
                        apple_count += 1
                    elif product in wall_data['tpa']:
                        tpa_count += 1
                    elif product in wall_data['screen_protectors']:
                        screen_count += 1
                    elif product in wall_data['lens_protectors']:
                        lens_count += 1
                    
                    # Draw phone-like rectangle
                    self.draw_phone_rectangle(ax, row, col, rows, cols, product, product_type)
                    
                    # Add to placement details
                    placement_details.append({
                        'position': f'R{row+1}C{col+1}',
                        'product': product,
                        'type': product_type,
                        'color': self.extract_color(product.product_name),
                        'case_type': self.extract_case_type(product.product_name)
                    })
        
        # Add legend
        self.add_enhanced_legend(ax, cols, rows, apple_count, tpa_count, screen_count, lens_count)
        
        # Save planogram
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"wall{wall_num}_planogram_{timestamp}.png"
        details_filename = f"wall{wall_num}_details_{timestamp}.txt"
        
        image_path = os.path.join(output_dir, image_filename)
        details_path = os.path.join(output_dir, details_filename)
        
        plt.tight_layout()
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate detailed placement report
        self.generate_enhanced_placement_details(
            placement_details, wall_data, store_name, wall_num, 
            products_placed, rows, cols, details_path
        )
        
        return image_filename, details_filename

    def add_enhanced_legend(self, ax, cols, rows, apple_count, tpa_count, screen_count, lens_count):
        """Add enhanced legend with product counts and categories"""
        legend_items = [
            'Apple Cases',
            'TPA Cases', 
            'Screen Protectors',
            'Lens Protectors'
        ]
        
        legend_colors = [
            self.apple_colors[0],
            self.tpa_colors['Default'],
            self.screen_protector_color,
            self.screen_protector_color
        ]
        
        # Position legend at bottom
        legend_y = -0.5
        for i, (item, color) in enumerate(zip(legend_items, legend_colors)):
            x_pos = i * (cols / 4) + 0.5
            
            # Add colored rectangle
            rect = Rectangle((x_pos, legend_y), 0.3, 0.2, 
                           facecolor=color, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # Add text
            ax.text(x_pos + 0.4, legend_y + 0.1, item, 
                   fontsize=8, va='center', fontweight='bold')
        
        # Add capacity info
        total_slots = rows * cols
        utilization = ((apple_count + tpa_count + screen_count + lens_count) / total_slots) * 100
        
        capacity_text = f"Capacity: {apple_count + tpa_count + screen_count + lens_count}/{total_slots} ({utilization:.1f}%) | Apple: {apple_count} | TPA: {tpa_count} | Screen: {screen_count} | Lens: {lens_count}"
        ax.text(cols/2, legend_y - 0.3, capacity_text, 
               ha='center', fontsize=8, fontweight='bold')

    def generate_enhanced_placement_details(self, placement_details, wall_data, store_name, 
                                          wall_num, products_placed, rows, cols, output_path):
        """Generate enhanced placement details report"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"ENHANCED RETAIL PLANOGRAM - {store_name} Wall {wall_num}\n")
            f.write(f"Focus: {wall_data['focus']}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary statistics
            f.write(f"GRID: {rows}x{cols} | PLACED: {products_placed} | UTILIZATION: {(products_placed/(rows*cols))*100:.1f}%\n")
            
            apple_count = len(wall_data['apple'])
            tpa_count = len(wall_data['tpa'])
            screen_count = len(wall_data['screen_protectors'])
            lens_count = len(wall_data['lens_protectors'])
            
            f.write(f"APPLE: {apple_count} | TPA: {tpa_count} | SCREEN: {screen_count} | LENS: {lens_count}\n\n")
            
            # Brand distribution
            brands = defaultdict(int)
            colors = defaultdict(int)
            
            for detail in placement_details:
                brands[detail['product'].brand] += 1
                colors[detail['color']] += 1
            
            f.write("BRAND DISTRIBUTION:\n")
            for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {brand}: {count}\n")
            f.write("\n")
            
            f.write("COLOR DISTRIBUTION:\n")
            for color, count in sorted(colors.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {color}: {count}\n")
            f.write("\n")
            
            # Detailed placement
            f.write("DETAILED PLACEMENT:\n")
            f.write("-" * 80 + "\n")
            
            for detail in placement_details:
                product = detail['product']
                f.write(f"{detail['position']}: {product.product_name[:80]}\n")
                f.write(f"  {product.brand} | {detail['case_type']} | {detail['color']} | Qty: {getattr(product, 'total_qty', 0)} | {product.brand}\n")
                f.write("-" * 40 + "\n")

    def generate_planograms(self, products, store_config, output_dir):
        """Main function to generate enhanced planograms"""
        
        store_name = store_config['store_name']
        store_type = store_config.get('store_type', 'standard')
        num_walls = store_config['num_walls']
        
        logger.info(f"Generating enhanced planograms for {store_name} with {num_walls} walls")
        
        # Enhanced categorization
        apple_products, tpa_products, screen_protectors, lens_protectors = self.categorize_products(products)
        
        logger.info(f"Categorized: {len(apple_products)} Apple, {len(tpa_products)} TPA, {len(screen_protectors)} Screen, {len(lens_protectors)} Lens")
        
        # Allocate walls by series strategy
        wall_allocations = self.allocate_walls_by_series(
            apple_products, tpa_products, screen_protectors, 
            lens_protectors, num_walls
        )
        
        generated_files = []
        
        # Generate each wall
        for wall_id, wall_data in wall_allocations.items():
            wall_num = wall_id.replace('wall', '')
            
            logger.info(f"Generating enhanced planogram for {wall_id}: {wall_data['focus']}")
            
            image_file, details_file = self.create_wall_planogram(
                wall_data, wall_num, store_name, store_type, output_dir
            )
            
            if image_file and details_file:
                generated_files.extend([
                    {
                        'type': 'planogram_image',
                        'filename': image_file,
                        'wall': wall_num,
                        'accessory': 'cases',
                        'description': f"Enhanced {wall_data['focus']} - Wall {wall_num}"
                    },
                    {
                        'type': 'product_details',
                        'filename': details_file,
                        'wall': wall_num,
                        'accessory': 'cases',
                        'description': f"Enhanced Product Details - Wall {wall_num}"
                    }
                ])
        
        logger.info(f"Successfully generated {len(generated_files)} enhanced planogram files")
        
        return {
            'success': True,
            'message': f"Successfully generated {len(wall_allocations)} enhanced planograms for {store_name}",
            'generated_files': generated_files,
            'wall_configuration': {wall_id: wall_data['focus'] for wall_id, wall_data in wall_allocations.items()}
        }
    
    def create_intelligent_cases_planogram(self, products, store_type, store_name, num_walls):
        """
        Wrapper method for compatibility with existing backend interface.
        Creates enhanced planograms with phone-like rectangles and smart allocation.
        """
        # Create output directory
        import os
        from datetime import datetime
        
        output_dir = os.path.join("output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create store configuration
        store_config = {
            'store_name': store_name,
            'store_type': store_type,
            'num_walls': num_walls
        }
        
        # Generate enhanced planograms using the main method
        result = self.generate_planograms(products, store_config, output_dir)
        
        # Convert to expected format for backend compatibility
        if result.get('success'):
            planograms = {}
            
            # Transform generated files into planogram format
            for file_info in result.get('generated_files', []):
                if file_info['type'] == 'planogram_image':
                    wall_key = f"wall{file_info['wall']}"
                    if wall_key not in planograms:
                        planograms[wall_key] = {}
                    planograms[wall_key]['planogram_image'] = os.path.join(output_dir, file_info['filename'])
                elif file_info['type'] == 'product_details':
                    wall_key = f"wall{file_info['wall']}"
                    if wall_key not in planograms:
                        planograms[wall_key] = {}
                    planograms[wall_key]['details_file'] = os.path.join(output_dir, file_info['filename'])
            
            return {
                'status': 'success',
                'message': result['message'],
                'planograms': planograms,
                'store_name': store_name,
                'store_type': store_type,
                'total_products': len(products)
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to generate enhanced planograms',
                'planograms': {}
            }
