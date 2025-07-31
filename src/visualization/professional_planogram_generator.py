#!/usr/bin/env python3
"""
Professional Planogram Generator
Creates high-quality retail planograms with intelligent product placement, proper color distribution,
and professional visual design following retail best practices.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import seaborn as sns
from pathlib import Path
from datetime import datetime
import re
import logging
from collections import defaultdict, Counter
import random
from itertools import cycle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfessionalPlanogramGenerator:
    """Professional planogram generator with intelligent product placement"""
    
    def __init__(self):
        # Professional brand color scheme
        self.brand_colors = {
            'Apple': '#007AFF',
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
        
        # Color palette for diversity
        self.color_palette = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
        ]
        
        # iPhone series mapping
        self.iphone_series = {
            'iPhone 16 Base': ['iPhone 16'],
            'iPhone 16 Plus': ['iPhone 16 Plus'],
            'iPhone 16 Pro': ['iPhone 16 Pro'],
            'iPhone 16 Pro Max': ['iPhone 16 Pro Max'],
            'iPhone 15 Base': ['iPhone 15'],
            'iPhone 15 Plus': ['iPhone 15 Plus'],
            'iPhone 15 Pro': ['iPhone 15 Pro'],
            'iPhone 15 Pro Max': ['iPhone 15 Pro Max']
        }
        
        # Color extraction patterns
        self.color_patterns = [
            'Black', 'White', 'Clear', 'Blue', 'Green', 'Red', 'Pink', 
            'Purple', 'Gray', 'Grey', 'Brown', 'Tan', 'Gold', 'Silver',
            'Denim', 'Fuchsia', 'Lake Green', 'Plum', 'Star Fruit', 
            'Stone Gray', 'Ultramarine', 'Natural Titanium', 'Gunmetal'
        ]

    def categorize_products(self, products):
        """Categorize products into Apple and TPA (Third Party Accessories)"""
        apple_products = []
        tpa_products = []
        screen_protectors = []
        
        for product in products:
            product_name = str(product.product_name).lower()
            brand = str(product.brand).strip()
            
            # Screen protectors and lens protectors
            if any(term in product_name for term in ['tg', 'tempered glass', 'screen protector', 'lens protector', 'camera lens']):
                screen_protectors.append(product)
            # Apple products
            elif brand.lower() == 'apple':
                apple_products.append(product)
            # TPA products
            else:
                tpa_products.append(product)
        
        return apple_products, tpa_products, screen_protectors

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

    def extract_color(self, product_name):
        """Extract color from product name"""
        product_name = str(product_name)
        for color in self.color_patterns:
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

    def calculate_grid_size(self, store_type, num_walls):
        """Calculate grid size based on store type and number of walls"""
        if store_type == 'flagship' or num_walls >= 4:
            return (8, 6)  # 8 rows, 6 columns
        elif store_type == 'standard' or num_walls == 3:
            return (6, 5)  # 6 rows, 5 columns
        else:  # express or 2 walls
            return (5, 4)  # 5 rows, 4 columns

    def create_balanced_product_grid(self, products, grid_size):
        """Create a balanced grid with proper color and brand distribution"""
        rows, cols = grid_size
        total_slots = rows * cols
        
        if not products:
            return [[None for _ in range(cols)] for _ in range(rows)]
        
        # Duplicate products to fill the grid based on their quantities
        expanded_products = []
        for product in products:
            # Calculate how many facings this product should have
            facings = max(1, min(8, product.total_qty // 10))  # 1-8 facings based on quantity
            for _ in range(facings):
                expanded_products.append(product)
        
        # If we still don't have enough products, cycle through them
        while len(expanded_products) < total_slots:
            expanded_products.extend(products[:total_slots - len(expanded_products)])
        
        # Truncate if we have too many
        expanded_products = expanded_products[:total_slots]
        
        # Group by color for better distribution
        color_groups = defaultdict(list)
        for product in expanded_products:
            color = self.extract_color(product.product_name)
            color_groups[color].append(product)
        
        # Create grid with balanced color distribution
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        product_index = 0
        
        # Fill grid in a pattern that ensures color diversity
        colors = list(color_groups.keys())
        color_cycle = cycle(colors)
        
        for row in range(rows):
            for col in range(cols):
                if product_index < len(expanded_products):
                    # Try to get a product of the next color in cycle
                    target_color = next(color_cycle)
                    if color_groups[target_color]:
                        product = color_groups[target_color].pop(0)
                    else:
                        # If no products of target color, get any available
                        for color, products_list in color_groups.items():
                            if products_list:
                                product = products_list.pop(0)
                                break
                        else:
                            product = expanded_products[product_index]
                    
                    grid[row][col] = product
                    product_index += 1
        
        return grid

    def allocate_products_to_walls(self, apple_products, tpa_products, screen_protectors, num_walls):
        """Allocate products to walls based on business rules"""
        wall_allocations = {}
        
        if num_walls >= 4:
            # 4+ walls: Each wall for each iPhone series
            series_groups = self.group_by_series(apple_products)
            
            # Allocate first 4 walls to iPhone series
            series_priority = ['iPhone 16 Pro Max', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16 Base']
            for i, series in enumerate(series_priority[:4]):
                if i < num_walls:
                    wall_allocations[f'wall{i+1}'] = {
                        'apple': series_groups.get(series, []),
                        'tpa': [],
                        'screen_protectors': [],
                        'focus': series
                    }
            
            # Remaining walls for TPA and screen protectors
            if num_walls > 4:
                tpa_per_wall = len(tpa_products) // (num_walls - 4) if num_walls > 4 else len(tpa_products)
                screen_per_wall = len(screen_protectors) // (num_walls - 4) if num_walls > 4 else len(screen_protectors)
                
                for i in range(4, num_walls):
                    start_idx = (i - 4) * tpa_per_wall
                    end_idx = start_idx + tpa_per_wall
                    
                    screen_start = (i - 4) * screen_per_wall
                    screen_end = screen_start + screen_per_wall
                    
                    wall_allocations[f'wall{i+1}'] = {
                        'apple': [],
                        'tpa': tpa_products[start_idx:end_idx],
                        'screen_protectors': screen_protectors[screen_start:screen_end],
                        'focus': 'TPA & Accessories'
                    }
            else:
                # Add TPA and screen protectors to the 4th wall
                wall_allocations['wall4']['tpa'] = tpa_products
                wall_allocations['wall4']['screen_protectors'] = screen_protectors
                wall_allocations['wall4']['focus'] = f"{series_priority[3]} + TPA"
                
        elif num_walls == 3:
            # 3 walls: Split series across walls
            series_groups = self.group_by_series(apple_products)
            
            wall_allocations['wall1'] = {
                'apple': series_groups.get('iPhone 16 Base', []) + series_groups.get('iPhone 16 Plus', []),
                'tpa': [],
                'screen_protectors': [],
                'focus': 'iPhone 16 Base + Plus'
            }
            
            wall_allocations['wall2'] = {
                'apple': series_groups.get('iPhone 16 Pro', []),
                'tpa': [],
                'screen_protectors': [],
                'focus': 'iPhone 16 Pro'
            }
            
            wall_allocations['wall3'] = {
                'apple': series_groups.get('iPhone 16 Pro Max', []),
                'tpa': tpa_products,
                'screen_protectors': screen_protectors,
                'focus': 'iPhone 16 Pro Max + TPA'
            }
            
        else:  # 2 walls
            # 2 walls: Split all series across both walls
            series_groups = self.group_by_series(apple_products)
            
            wall_allocations['wall1'] = {
                'apple': series_groups.get('iPhone 16 Base', []) + series_groups.get('iPhone 16 Pro', []),
                'tpa': tpa_products[:len(tpa_products)//2],
                'screen_protectors': screen_protectors[:len(screen_protectors)//2],
                'focus': 'iPhone 16 Base + Pro'
            }
            
            wall_allocations['wall2'] = {
                'apple': series_groups.get('iPhone 16 Plus', []) + series_groups.get('iPhone 16 Pro Max', []),
                'tpa': tpa_products[len(tpa_products)//2:],
                'screen_protectors': screen_protectors[len(screen_protectors)//2:],
                'focus': 'iPhone 16 Plus + Pro Max'
            }
        
        return wall_allocations

    def group_by_series(self, products):
        """Group products by iPhone series"""
        series_groups = defaultdict(list)
        for product in products:
            series = self.extract_iphone_series(product.product_name)
            series_groups[series].append(product)
        return dict(series_groups)

    def group_tpa_by_brand(self, tpa_products):
        """Group TPA products by brand for better organization"""
        if not tpa_products:
            return tpa_products
            
        brand_groups = defaultdict(list)
        for product in tpa_products:
            brand = str(product.brand).strip()
            brand_groups[brand].append(product)
        
        # Sort brands by total quantity (descending)
        sorted_brands = sorted(brand_groups.items(), 
                             key=lambda x: sum(p.total_qty for p in x[1]), 
                             reverse=True)
        
        grouped_products = []
        for brand, products in sorted_brands:
            grouped_products.extend(products)
        
        return grouped_products

    def create_wall_planogram(self, wall_data, wall_num, store_name, store_type, output_dir):
        """Create a single wall planogram with professional design"""
        rows, cols = self.calculate_grid_size(store_type, 4)  # Use consistent grid
        
        # Combine all products for this wall
        all_products = []
        
        # Add Apple products (first half)
        apple_products = wall_data['apple']
        all_products.extend(apple_products)
        
        # Add TPA products (grouped by brand)
        tpa_products = self.group_tpa_by_brand(wall_data['tpa'])
        all_products.extend(tpa_products)
        
        # Add screen protectors
        all_products.extend(wall_data['screen_protectors'])
        
        # Create balanced grid
        product_grid = self.create_balanced_product_grid(all_products, (rows, cols))
        
        # Create figure with proper aspect ratio
        fig, ax = plt.subplots(figsize=(18, 12))
        ax.set_xlim(0, cols)
        ax.set_ylim(0, rows)
        ax.set_aspect('equal')
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Title
        title = f"{store_name} - Wall {wall_num}\n{wall_data['focus']}"
        plt.suptitle(title, fontsize=24, fontweight='bold', y=0.95)
        
        # Product placement details for text file
        placement_details = []
        products_placed = 0
        
        # Place products in grid
        for row in range(rows):
            for col in range(cols):
                product = product_grid[row][col]
                
                if product:
                    products_placed += 1
                    
                    # Determine product type
                    is_apple = product in apple_products
                    is_screen_protector = product in wall_data['screen_protectors']
                    
                    # Create product rectangle (proper rectangle, not square)
                    if is_screen_protector:
                        # Screen protectors - cardboard style
                        rect = FancyBboxPatch(
                            (col + 0.05, rows - row - 0.95),
                            0.9, 0.85,  # Slightly rectangular
                            boxstyle="round,pad=0.02",
                            facecolor='#F8F9FA',
                            edgecolor='#6C757D',
                            linewidth=2,
                            linestyle='--'
                        )
                    else:
                        # Cases - hanging style rectangles
                        brand = str(product.brand).strip()
                        color = self.brand_colors.get(brand, self.brand_colors['Default'])
                        
                        rect = FancyBboxPatch(
                            (col + 0.05, rows - row - 0.95),
                            0.9, 0.85,  # Proper rectangle ratio
                            boxstyle="round,pad=0.02",
                            facecolor=color,
                            edgecolor='#2C3E50',
                            linewidth=1.5,
                            alpha=0.9
                        )
                    
                    ax.add_patch(rect)
                    
                    # Extract product details
                    color_name = self.extract_color(product.product_name)
                    case_type = self.extract_case_type(product.product_name)
                    brand = str(product.brand).strip()
                    
                    # Add text on the product
                    text_y = rows - row - 0.5
                    text_color = 'white' if not is_screen_protector else 'black'
                    
                    # Brand name (top)
                    ax.text(col + 0.5, text_y + 0.25, brand, 
                           ha='center', va='center', fontsize=10, fontweight='bold',
                           color=text_color)
                    
                    # Case type (middle)
                    ax.text(col + 0.5, text_y, case_type, 
                           ha='center', va='center', fontsize=8,
                           color=text_color)
                    
                    # Color (bottom)
                    ax.text(col + 0.5, text_y - 0.25, color_name, 
                           ha='center', va='center', fontsize=7,
                           color=text_color)
                    
                    # Add to placement details
                    placement_details.append({
                        'row': row + 1,
                        'col': col + 1,
                        'position': f'R{row+1}C{col+1}',
                        'product_name': product.product_name,
                        'brand': brand,
                        'case_type': case_type,
                        'color': color_name,
                        'quantity': product.total_qty,
                        'type': 'Screen Protector' if is_screen_protector else ('Apple' if is_apple else 'TPA')
                    })
                    
                else:
                    # Empty slot - subtle styling
                    rect = Rectangle(
                        (col + 0.05, rows - row - 0.95),
                        0.9, 0.85,
                        facecolor='#ECEFF1',
                        edgecolor='#B0BEC5',
                        linewidth=1,
                        alpha=0.3
                    )
                    ax.add_patch(rect)
                    
                    ax.text(col + 0.5, rows - row - 0.5, 'EMPTY', 
                           ha='center', va='center', fontsize=8,
                           color='gray', alpha=0.7)
        
        # Add professional legend
        legend_elements = []
        if apple_products:
            legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=self.brand_colors['Apple'], label='Apple Cases'))
        if tpa_products:
            legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=self.brand_colors['Default'], label='TPA Cases'))
        if wall_data['screen_protectors']:
            legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor='#F8F9FA', edgecolor='#6C757D', 
                                               linestyle='--', label='Screen Protectors'))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1), fontsize=12)
        
        # Add capacity utilization info
        utilization = (products_placed / (rows * cols)) * 100
        ax.text(0.02, 0.02, f'Capacity Utilization: {products_placed}/{rows * cols} ({utilization:.1f}%)', 
                transform=ax.transAxes, fontsize=10, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Save planogram
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Professional_Cases_Layout_{store_type}_wall{wall_num}_{timestamp}.png"
        filepath = output_dir / filename
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Save placement details
        details_filename = f"Professional_Cases_Details_{store_type}_wall{wall_num}_{timestamp}.txt"
        details_filepath = output_dir / details_filename
        
        with open(details_filepath, 'w', encoding='utf-8') as f:
            f.write(f"PROFESSIONAL PLANOGRAM DETAILS - {store_name} Wall {wall_num}\n")
            f.write(f"Focus: {wall_data['focus']}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"GRID LAYOUT: {rows} rows x {cols} columns\n")
            f.write(f"TOTAL PRODUCTS PLACED: {products_placed}\n")
            f.write(f"TOTAL CAPACITY: {rows * cols}\n")
            f.write(f"CAPACITY UTILIZATION: {utilization:.1f}%\n\n")
            
            # Summary by type
            apple_count = len([p for p in placement_details if p['type'] == 'Apple'])
            tpa_count = len([p for p in placement_details if p['type'] == 'TPA'])
            screen_count = len([p for p in placement_details if p['type'] == 'Screen Protector'])
            
            f.write("PRODUCT TYPE SUMMARY:\n")
            f.write(f"- Apple Cases: {apple_count}\n")
            f.write(f"- TPA Cases: {tpa_count}\n")
            f.write(f"- Screen Protectors: {screen_count}\n\n")
            
            # Brand distribution
            brand_counts = Counter([p['brand'] for p in placement_details])
            f.write("BRAND DISTRIBUTION:\n")
            for brand, count in brand_counts.most_common():
                f.write(f"- {brand}: {count}\n")
            f.write("\n")
            
            # Color distribution
            color_counts = Counter([p['color'] for p in placement_details])
            f.write("COLOR DISTRIBUTION:\n")
            for color, count in color_counts.most_common():
                f.write(f"- {color}: {count}\n")
            f.write("\n")
            
            # Detailed placement
            f.write("DETAILED PLACEMENT:\n")
            f.write("-" * 80 + "\n")
            for detail in placement_details:
                f.write(f"Position {detail['position']}: {detail['product_name']}\n")
                f.write(f"  Brand: {detail['brand']} | Type: {detail['case_type']} | Color: {detail['color']}\n")
                f.write(f"  Quantity: {detail['quantity']} | Category: {detail['type']}\n")
                f.write("-" * 80 + "\n")
        
        return {
            'planogram_image': str(filepath),
            'product_details_file': str(details_filepath),
            'products_placed': products_placed,
            'total_capacity': rows * cols,
            'utilization': utilization
        }

    def generate_planograms(self, products, store_name, store_type, num_walls, output_dir):
        """Generate planograms for all walls"""
        # Ensure output directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Categorize products
        apple_products, tpa_products, screen_protectors = self.categorize_products(products)
        
        logger.info(f"Categorized products: {len(apple_products)} Apple, {len(tpa_products)} TPA, {len(screen_protectors)} Screen Protectors")
        
        # Allocate products to walls
        wall_allocations = self.allocate_products_to_walls(apple_products, tpa_products, screen_protectors, num_walls)
        
        # Generate planograms for each wall
        results = {}
        for wall_key, wall_data in wall_allocations.items():
            wall_num = wall_key.replace('wall', '')
            logger.info(f"Generating professional planogram for {wall_key} with focus: {wall_data['focus']}")
            
            wall_result = self.create_wall_planogram(wall_data, wall_num, store_name, store_type, output_dir)
            results[wall_key] = wall_result
        
        return {
            'status': 'success',
            'planograms': results,
            'summary': {
                'total_walls': num_walls,
                'apple_products': len(apple_products),
                'tpa_products': len(tpa_products),
                'screen_protectors': len(screen_protectors)
            }
        }


def create_intelligent_cases_planogram(products, store_type, store_name, num_walls):
    """Main function to create professional cases planogram"""
    try:
        # Set up output directory
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / 'output'
        
        # Create generator
        generator = ProfessionalPlanogramGenerator()
        
        # Generate planograms
        result = generator.generate_planograms(products, store_name, store_type, num_walls, output_dir)
        
        logger.info(f"Successfully generated {num_walls} professional planograms for {store_name}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating professional planograms: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


if __name__ == "__main__":
    # Test the generator
    print("Professional Planogram Generator ready!")