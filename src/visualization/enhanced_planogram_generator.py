#!/usr/bin/env python3
"""
Enhanced Intelligent Planogram Generator
Creates professional retail planograms with intelligent product placement following specific business rules.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import seaborn as sns
from pathlib import Path
from datetime import datetime
import re
import logging
from collections import defaultdict, Counter
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedPlanogramGenerator:
    """Enhanced planogram generator with intelligent product placement"""
    
    def __init__(self):
        self.colors = {
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
                for i in range(4, num_walls):
                    wall_allocations[f'wall{i+1}'] = {
                        'apple': [],
                        'tpa': tpa_products[i-4::num_walls-4] if i-4 < len(tpa_products) else [],
                        'screen_protectors': screen_protectors[i-4::num_walls-4] if i-4 < len(screen_protectors) else [],
                        'focus': 'TPA'
                    }
            else:
                # Add TPA and screen protectors to the 4th wall
                wall_allocations['wall4']['tpa'] = tpa_products
                wall_allocations['wall4']['screen_protectors'] = screen_protectors
                
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

    def optimize_color_diversity(self, products):
        """Optimize color diversity in product placement"""
        if not products:
            return products
            
        # Group by color
        color_groups = defaultdict(list)
        for product in products:
            color = self.extract_color(product.product_name)
            color_groups[color].append(product)
        
        # Interleave colors for maximum diversity
        optimized = []
        color_lists = list(color_groups.values())
        max_len = max(len(lst) for lst in color_lists) if color_lists else 0
        
        for i in range(max_len):
            for color_list in color_lists:
                if i < len(color_list):
                    optimized.append(color_list[i])
        
        return optimized

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
        """Create a single wall planogram"""
        rows, cols = self.calculate_grid_size(store_type, 4)  # Use consistent grid
        
        # Combine all products for this wall
        all_products = []
        
        # Add Apple products (first half)
        apple_products = self.optimize_color_diversity(wall_data['apple'])
        all_products.extend(apple_products)
        
        # Add TPA products (grouped by brand)
        tpa_products = self.group_tpa_by_brand(wall_data['tpa'])
        all_products.extend(tpa_products)
        
        # Add screen protectors
        all_products.extend(wall_data['screen_protectors'])
        
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_xlim(0, cols)
        ax.set_ylim(0, rows)
        ax.set_aspect('equal')
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        # Title
        title = f"{store_name} - Wall {wall_num}\n{wall_data['focus']}"
        plt.suptitle(title, fontsize=20, fontweight='bold', y=0.95)
        
        # Product placement details for text file
        placement_details = []
        
        # Place products in grid
        product_index = 0
        for row in range(rows):
            for col in range(cols):
                if product_index < len(all_products):
                    product = all_products[product_index]
                    
                    # Determine if this is Apple or TPA
                    is_apple = product in apple_products
                    is_screen_protector = product in wall_data['screen_protectors']
                    
                    # Create product rectangle
                    if is_screen_protector:
                        # Screen protectors - cardboard style
                        rect = FancyBboxPatch(
                            (col + 0.05, rows - row - 0.95),
                            0.9, 0.9,
                            boxstyle="round,pad=0.02",
                            facecolor='#F8F9FA',
                            edgecolor='#6C757D',
                            linewidth=2,
                            linestyle='--'
                        )
                    else:
                        # Cases - hanging style
                        rect = FancyBboxPatch(
                            (col + 0.05, rows - row - 0.95),
                            0.9, 0.9,
                            boxstyle="round,pad=0.02",
                            facecolor=self.colors.get(product.brand, self.colors['Default']),
                            edgecolor='black',
                            linewidth=1.5,
                            alpha=0.8
                        )
                    
                    ax.add_patch(rect)
                    
                    # Extract product details
                    color = self.extract_color(product.product_name)
                    case_type = self.extract_case_type(product.product_name)
                    brand = str(product.brand).strip()
                    
                    # Add text on the product
                    text_y = rows - row - 0.5
                    
                    # Brand name (top)
                    ax.text(col + 0.5, text_y + 0.25, brand, 
                           ha='center', va='center', fontsize=8, fontweight='bold',
                           color='white' if not is_screen_protector else 'black')
                    
                    # Case type (middle)
                    ax.text(col + 0.5, text_y, case_type, 
                           ha='center', va='center', fontsize=7,
                           color='white' if not is_screen_protector else 'black')
                    
                    # Color (bottom)
                    ax.text(col + 0.5, text_y - 0.25, color, 
                           ha='center', va='center', fontsize=6,
                           color='white' if not is_screen_protector else 'black')
                    
                    # Add to placement details
                    placement_details.append({
                        'row': row + 1,
                        'col': col + 1,
                        'position': f'R{row+1}C{col+1}',
                        'product_name': product.product_name,
                        'brand': brand,
                        'case_type': case_type,
                        'color': color,
                        'quantity': product.total_qty,
                        'type': 'Screen Protector' if is_screen_protector else ('Apple' if is_apple else 'TPA')
                    })
                    
                    product_index += 1
                else:
                    # Empty slot
                    rect = patches.Rectangle(
                        (col + 0.05, rows - row - 0.95),
                        0.9, 0.9,
                        facecolor='#ECEFF1',
                        edgecolor='#B0BEC5',
                        linewidth=1,
                        alpha=0.3
                    )
                    ax.add_patch(rect)
                    
                    ax.text(col + 0.5, rows - row - 0.5, 'EMPTY', 
                           ha='center', va='center', fontsize=8,
                           color='gray', alpha=0.7)
        
        # Add legend
        legend_elements = []
        if apple_products:
            legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=self.colors['Apple'], label='Apple Cases'))
        if tpa_products:
            legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=self.colors['Default'], label='TPA Cases'))
        if wall_data['screen_protectors']:
            legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor='#F8F9FA', edgecolor='#6C757D', 
                                               linestyle='--', label='Screen Protectors'))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))
        
        # Save planogram
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Enhanced_Cases_Layout_{store_type}_wall{wall_num}_{timestamp}.png"
        filepath = output_dir / filename
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Save placement details
        details_filename = f"Enhanced_Cases_Details_{store_type}_wall{wall_num}_{timestamp}.txt"
        details_filepath = output_dir / details_filename
        
        with open(details_filepath, 'w', encoding='utf-8') as f:
            f.write(f"PLANOGRAM DETAILS - {store_name} Wall {wall_num}\n")
            f.write(f"Focus: {wall_data['focus']}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"GRID LAYOUT: {rows} rows x {cols} columns\n")
            f.write(f"TOTAL PRODUCTS PLACED: {len(placement_details)}\n")
            f.write(f"TOTAL CAPACITY: {rows * cols}\n\n")
            
            # Summary by type
            apple_count = len([p for p in placement_details if p['type'] == 'Apple'])
            tpa_count = len([p for p in placement_details if p['type'] == 'TPA'])
            screen_count = len([p for p in placement_details if p['type'] == 'Screen Protector'])
            
            f.write("PRODUCT TYPE SUMMARY:\n")
            f.write(f"- Apple Cases: {apple_count}\n")
            f.write(f"- TPA Cases: {tpa_count}\n")
            f.write(f"- Screen Protectors: {screen_count}\n\n")
            
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
            'products_placed': len(placement_details),
            'total_capacity': rows * cols
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
            logger.info(f"Generating planogram for {wall_key} with focus: {wall_data['focus']}")
            
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
    """Main function to create intelligent cases planogram"""
    try:
        # Set up output directory
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / 'output'
        
        # Create generator
        generator = EnhancedPlanogramGenerator()
        
        # Generate planograms
        result = generator.generate_planograms(products, store_name, store_type, num_walls, output_dir)
        
        logger.info(f"Successfully generated {num_walls} planograms for {store_name}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating planograms: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


if __name__ == "__main__":
    # Test the generator
    print("Enhanced Planogram Generator ready!")