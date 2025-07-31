#!/usr/bin/env python3
"""
Professional Cases & Covers Planogram Generator
Based on the established professional planogram system with proper grid sizing,
brand distribution, and aesthetic requirements matching the reference images.
"""

# Configure matplotlib backend for thread-safe operation BEFORE importing pyplot
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend to prevent threading issues

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import textwrap
from datetime import datetime
import re
import pandas as pd
from collections import defaultdict, Counter
from itertools import cycle

class CasesCoversGenerator:
    """Professional Cases & Covers planogram generator matching reference aesthetics"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.output_path = self.project_root / 'output'
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Ensure matplotlib backend is configured for thread-safe operation
        self._configure_matplotlib_backend()
        
        # Professional brand color scheme (matching your reference)
        self.brand_colors = {
            'Apple': '#FFD700',      # Yellow/Gold (as in your reference)
            'Gripp': '#00BFFF',      # Bright Blue (as in your reference)
            'Pulse': '#8B4B8C',      # Purple/Magenta 
            'Hyphen': '#FF1493',     # Hot Pink (as in your reference)
            'Tekne': '#32CD32',      # Green
            'UAG': '#696969',        # Dark Gray
            'AT Minimal': '#9370DB', # Medium Purple
            'Roskilde': '#FF6347',   # Tomato Red
            'nmaxn': '#20B2AA',      # Light Sea Green
            'Robocare': '#32CD32',   # Lime Green (as in your reference)
            'Flayrr': '#FF69B4',     # Hot Pink
            'Default': '#B0C4DE'     # Light Steel Blue
        }
        
        # Supporting colors
        self.colors = {
            'background': '#FFFFFF',
            'border': '#D1D1D6',
            'text_primary': '#1D1D1F',
            'text_secondary': '#6D6D70',
            'grid_line': '#F2F2F7',
            'header_bg': '#F2F2F7'
        }
    
    def _configure_matplotlib_backend(self):
        """Configure matplotlib backend for thread-safe operation"""
        import matplotlib
        current_backend = matplotlib.get_backend()
        
        # Only change backend if it's not already set to Agg
        if current_backend != 'Agg':
            try:
                matplotlib.use('Agg')
                print(f"Matplotlib backend configured: {current_backend} -> Agg (thread-safe)")
            except Exception as e:
                print(f"Warning: Could not set matplotlib backend to Agg: {e}")
        else:
            print(f"Matplotlib backend already configured: {current_backend}")
    
    def filter_tpa_products(self, products: List[Dict]) -> List[Dict]:
        """Filter TPA products to only include Tekne, Pulse, and Gripp brands"""
        allowed_tpa_brands = ['tekne', 'pulse', 'gripp']
        
        filtered_products = []
        tpa_filtered_count = 0
        tpa_total_count = 0
        
        for product in products:
            brand = product.get('brand', '').lower().strip()
            
            # Keep Apple products unchanged
            if brand == 'apple':
                filtered_products.append(product)
            # Filter TPA products to only allowed brands
            elif brand in allowed_tpa_brands:
                filtered_products.append(product)
                tpa_filtered_count += 1
            # Count other TPA brands that are being filtered out
            elif brand not in ['apple'] and product.get('category') != 'case':
                tpa_total_count += 1
            # Keep non-TPA case products (other case brands)
            else:
                # Check if this is a TPA product by looking at subcategory
                subcategory = product.get('subcategory', '').lower()
                if any(keyword in subcategory for keyword in ['screen', 'lens', 'protector', 'glass']):
                    tpa_total_count += 1  # This is a TPA product being filtered out
                else:
                    filtered_products.append(product)  # Keep other case products
        
        print(f"TPA Brand Filtering: Kept {tpa_filtered_count} products from Tekne/Pulse/Gripp, filtered out {tpa_total_count - tpa_filtered_count} from other TPA brands")
        
        return filtered_products
    
    def is_tpa_brand(self, brand: str) -> bool:
        """Check if a brand is one of the allowed TPA brands"""
        allowed_tpa_brands = ['tekne', 'pulse', 'gripp']
        return brand.lower().strip() in allowed_tpa_brands
    
    def is_apple_or_tpa_product(self, product: Dict) -> bool:
        """Check if a product is Apple or allowed TPA brand"""
        brand = product.get('brand', '').lower().strip()
        return brand == 'apple' or self.is_tpa_brand(brand)
    
    def calculate_grid_size(self, total_store_walls: int, wall_number: int) -> Tuple[int, int]:
        """Calculate grid size based on total store size and your established logic for Cases & Covers"""
        # Grid size should reflect store size - flagship stores get more density
        # Based on your reference images showing 46+ products for major stores
        
        if total_store_walls >= 8:  # Flagship stores (like KORAMANGALA with 11 walls total)
            return (8, 6)  # 8 rows, 6 columns (48 products like your reference)
        elif total_store_walls >= 5:  # Standard stores  
            return (7, 6)  # 7 rows, 6 columns (42 products)
        else:  # Express/small stores
            return (6, 6)  # 6 rows, 6 columns (36 products)
    
    def get_cases_wall_count(self) -> int:
        """Get the number of walls allocated to Cases & Covers from stored config"""
        try:
            config_path = self.project_root / 'data' / 'processed' / 'final_wall_configs.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    configs = json.load(f)
                    
                # Look for KORAMANGALA config
                for store_name, config in configs.items():
                    if 'koramangala' in store_name.lower():
                        wall_counts = config.get('wall_counts', {})
                        cases_walls = wall_counts.get('Cases & Covers', 2)
                        print(f"Found Cases & Covers wall count: {cases_walls}")
                        return cases_walls
            
            # Default to 2 walls for Cases & Covers
            return 2
            
        except Exception as e:
            print(f"Error getting wall count: {e}")
            return 2
    
    def load_real_cases_data(self) -> List[Dict]:
        """Load real Cases & Covers data with filtered TPA products (Tekne, Pulse, Gripp only)"""
        try:
            # Load all Cases & Covers data (includes Apple cases and TPA products)
            cases_path = self.project_root / 'data' / 'raw' / 'accessories' / 'cases_sales.csv'
            
            products = []
            
            if cases_path.exists():
                df = pd.read_csv(cases_path)
                df.columns = df.columns.str.strip()
                df_with_sales = df[df['pureqty'].notna() & (df['pureqty'] > 0)]
                df_sorted = df_with_sales.sort_values('pureqty', ascending=False)
                
                for _, row in df_sorted.iterrows():
                    sales = int(row['pureqty'])
                    brand = row['brand'].strip() if pd.notna(row['brand']) else 'Default'
                    subcategory = row['subcategory'].strip() if pd.notna(row['subcategory']) else 'case'
                    
                    # Determine if this is a TPA product (screen protectors, lens protectors, etc.)
                    is_tpa_product = any(keyword in subcategory.lower() for keyword in ['screen', 'lens', 'protector', 'glass'])
                    
                    # Set facings based on product type
                    if brand.lower() == 'apple':
                        facings = max(1, min(6, sales // 50))  # Apple cases get more facings
                    elif is_tpa_product:
                        facings = max(1, min(4, sales // 30))  # TPA products get fewer facings
                    else:
                        facings = max(1, min(5, sales // 40))  # Other case brands
                    
                    # Determine category
                    if is_tpa_product:
                        category = 'tpa'
                    else:
                        category = 'case'
                    
                    product_data = {
                        'product_name': row['product_name'],
                        'brand': brand,  # Preserve actual brand name
                        'series': row['series'].strip() if pd.notna(row['series']) else 'iPhone',
                        'subcategory': subcategory,
                        'category': category,
                        'sales': sales,
                        'facings': facings
                    }
                    
                    for _ in range(facings):
                        products.append(product_data.copy())
            
            # Apply TPA brand filtering to only include Tekne, Pulse, and Gripp
            filtered_products = self.filter_tpa_products(products)
            
            print(f"Loaded {len(filtered_products)} total products (Cases + filtered TPA products)")
            return filtered_products
            
        except Exception as e:
            print(f"Error loading Cases + TPA data: {e}")
            return []
    
    def extract_series_info(self, product_name: str, series: str) -> str:
        """Extract iPhone series information"""
        combined = f"{product_name} {series}".lower()
        
        if 'pro max' in combined:
            return 'Pro Max'
        elif 'pro' in combined:
            return 'Pro'
        elif 'plus' in combined:
            return 'Plus'
        else:
            return 'Base'
    
    def get_brand_color(self, brand: str) -> str:
        """Get brand color matching your reference"""
        brand_clean = brand.strip().replace(',', '').split()[0] if brand else 'Default'
        
        # TPA products (Tekne, Pulse, Gripp) get their own brand colors
        if self.is_tpa_brand(brand_clean):
            return self.brand_colors.get(brand_clean.title(), self.brand_colors['Default'])
        
        return self.brand_colors.get(brand_clean, self.brand_colors['Default'])
    
    def get_series_wall_allocation(self, total_walls: int, wall_number: int) -> List[str]:
        """Determine which series go on which wall - prioritize Apple series"""
        # Apple has Base and Plus series available, so prioritize these
        apple_series = ['Base', 'Plus']
        other_series = ['Pro', 'Pro Max']
        
        if total_walls >= 4:
            # 4+ walls: Each series gets its own wall, prioritize Apple series first
            all_series = apple_series + other_series
            series_idx = (wall_number - 1) % len(all_series)
            return [all_series[series_idx]]
        
        elif total_walls == 3:
            # 3 walls: Proper series split - Apple first, then Pro series, then TPA with series split
            if wall_number == 1:
                return apple_series  # Base and Plus together (Apple priority)
            elif wall_number == 2:
                return other_series  # Pro and Pro Max together
            else:
                return apple_series + other_series  # All TPA with proper series split column-wise

        elif total_walls == 2:
            # 2 walls: Proper series split between Apple and Pro series
            if wall_number == 1:
                return apple_series  # Base and Plus (Apple available)
            else:
                return other_series  # Pro and Pro Max
        
        else:
            # 1 wall: All series including Apple
            return apple_series + other_series
    
    def create_dense_product_grid(self, products: List[Dict], grid_size: Tuple[int, int], wall_number: int, total_walls: int) -> List[List]:
        """Create dense grid with column-based series allocation and all colors represented"""
        rows, cols = grid_size
        total_slots = rows * cols
        
        if not products:
            return [[None for _ in range(cols)] for _ in range(rows)]
        
        # Separate Apple, TPA, and other products
        apple_products = [p for p in products if p['brand'].lower().strip() == 'apple']
        tpa_products = [p for p in products if self.is_tpa_brand(p['brand'])]
        other_products = [p for p in products if p['brand'].lower().strip() != 'apple' and not self.is_tpa_brand(p['brand'])]

        # Write debug info to file
        with open('debug_wall_generation.txt', 'a') as f:
            f.write(f"Wall {wall_number}: Total products loaded: {len(products)}\n")
            f.write(f"Wall {wall_number}: Apple products: {len(apple_products)}\n")
            f.write(f"Wall {wall_number}: TPA products: {len(tpa_products)}\n")
            f.write(f"Wall {wall_number}: Other products: {len(other_products)}\n")

            # Debug: Show what brands are in TPA and Other
            if tpa_products:
                tpa_brands = {}
                for p in tpa_products:
                    brand = p['brand']
                    tpa_brands[brand] = tpa_brands.get(brand, 0) + 1
                f.write(f"Wall {wall_number}: TPA brands: {dict(list(tpa_brands.items())[:5])}\n")

            if other_products:
                other_brands = {}
                for p in other_products:
                    brand = p['brand']
                    other_brands[brand] = other_brands.get(brand, 0) + 1
                f.write(f"Wall {wall_number}: Other brands: {dict(list(other_brands.items())[:5])}\n")

        # Get series allocation for this wall
        wall_series = self.get_series_wall_allocation(total_walls, wall_number)
        print(f"  Wall {wall_number} series: {', '.join(wall_series)}")

        # Debug: Check wall series allocation
        with open('debug_wall_generation.txt', 'a') as f:
            f.write(f"Wall {wall_number}: Wall series allocation: {wall_series} (length: {len(wall_series)})\n")

        # Filter products by series for this wall
        series_1_products = []  # First series (Base or Pro)
        series_2_products = []  # Second series (Plus or Pro Max)
        series_3_products = []  # Third series (Pro for Wall 3)
        series_4_products = []  # Fourth series (Pro Max for Wall 3)

        # Determine which series to use based on wall allocation
        with open('debug_wall_generation.txt', 'a') as f:
            f.write(f"Wall {wall_number}: Checking series allocation - len(wall_series)={len(wall_series)}, wall_series={wall_series}\n")

        if len(wall_series) >= 4:
            # Wall 3 with all 4 series
            target_series_1 = wall_series[0]  # Base
            target_series_2 = wall_series[1]  # Plus
            target_series_3 = wall_series[2]  # Pro
            target_series_4 = wall_series[3]  # Pro Max
            use_four_series = True
            with open('debug_wall_generation.txt', 'a') as f:
                f.write(f"Wall {wall_number}: Using 4-series mode: {target_series_1}, {target_series_2}, {target_series_3}, {target_series_4}\n")
        elif len(wall_series) >= 2:
            target_series_1 = wall_series[0]
            target_series_2 = wall_series[1]
            target_series_3 = None
            target_series_4 = None
            use_four_series = False
        else:
            target_series_1 = wall_series[0] if wall_series else 'Base'
            target_series_2 = 'Plus'  # Default fallback
            target_series_3 = None
            target_series_4 = None
            use_four_series = False

        # For walls 1 and 2, prioritize Apple products
        if wall_number <= 2:
            # Filter Apple products by series
            apple_series_1 = []
            apple_series_2 = []

            for product in apple_products:
                product_series = self.extract_series_info(product['product_name'], product['series'])
                if product_series == target_series_1:
                    apple_series_1.append(product)
                elif product_series == target_series_2:
                    apple_series_2.append(product)

            # Debug: Check Apple products found
            with open('debug_wall_generation.txt', 'a') as f:
                f.write(f"Wall {wall_number}: Apple {target_series_1} found: {len(apple_series_1)}\n")
                f.write(f"Wall {wall_number}: Apple {target_series_2} found: {len(apple_series_2)}\n")
                if apple_series_1:
                    f.write(f"Wall {wall_number}: Sample Apple {target_series_1}: {[p['product_name'][:30] for p in apple_series_1[:3]]}\n")
                if apple_series_2:
                    f.write(f"Wall {wall_number}: Sample Apple {target_series_2}: {[p['product_name'][:30] for p in apple_series_2[:3]]}\n")

            # Add Apple products first
            series_1_products.extend(apple_series_1)
            series_2_products.extend(apple_series_2)

        # For Wall 3 with 4 series, filter all series
        elif use_four_series:
            apple_series_1 = []
            apple_series_2 = []
            apple_series_3 = []
            apple_series_4 = []

            for product in apple_products:
                product_series = self.extract_series_info(product['product_name'], product['series'])
                if product_series == target_series_1:
                    apple_series_1.append(product)
                elif product_series == target_series_2:
                    apple_series_2.append(product)
                elif product_series == target_series_3:
                    apple_series_3.append(product)
                elif product_series == target_series_4:
                    apple_series_4.append(product)

            # Debug: Check Apple products found for all 4 series
            with open('debug_wall_generation.txt', 'a') as f:
                f.write(f"Wall {wall_number}: Apple {target_series_1} found: {len(apple_series_1)}\n")
                f.write(f"Wall {wall_number}: Apple {target_series_2} found: {len(apple_series_2)}\n")
                f.write(f"Wall {wall_number}: Apple {target_series_3} found: {len(apple_series_3)}\n")
                f.write(f"Wall {wall_number}: Apple {target_series_4} found: {len(apple_series_4)}\n")

            # Add Apple products (TPA priority for Wall 3, so Apple goes after TPA)
            series_1_products.extend(apple_series_1)
            series_2_products.extend(apple_series_2)
            series_3_products.extend(apple_series_3)
            series_4_products.extend(apple_series_4)

            # Fill remaining slots with TPA products if needed
            for product in tpa_products:
                product_series = self.extract_series_info(product['product_name'], product['series'])
                if product_series == target_series_1 and len(series_1_products) < 18:
                    series_1_products.append(product)
                elif product_series == target_series_2 and len(series_2_products) < 18:
                    series_2_products.append(product)
                elif product_series == target_series_3 and len(series_3_products) < 18:
                    series_3_products.append(product)
                elif product_series == target_series_4 and len(series_4_products) < 18:
                    series_4_products.append(product)
        else:
            # For walls without 4-series (should not happen with current logic)
            for product in tpa_products:
                product_series = self.extract_series_info(product['product_name'], product['series'])
                if product_series == target_series_1:
                    series_1_products.append(product)
                elif product_series == target_series_2:
                    series_2_products.append(product)

            # Add some Apple products for diversity
            for product in apple_products[:6]:  # Limit Apple products on TPA-focused walls
                product_series = self.extract_series_info(product['product_name'], product['series'])
                if product_series == target_series_1 and len(series_1_products) < 18:
                    series_1_products.append(product)
                elif product_series == target_series_2 and len(series_2_products) < 18:
                    series_2_products.append(product)
        
        # Calculate Apple/TPA allocation (50% of top rows)
        apple_rows = max(1, rows // 2)
        apple_slots = apple_rows * cols
        series_1_slots = apple_rows * 3  # First 3 columns
        series_2_slots = apple_rows * 3  # Last 3 columns

        print(f"  Apple/TPA allocation: {apple_rows} rows × {cols} cols = {apple_slots} slots")
        if use_four_series:
            print(f"  4-series distribution: {target_series_1}(0-1), {target_series_2}(2-3), {target_series_3}(4), {target_series_4}(5)")
        else:
            print(f"  {target_series_1} slots: {series_1_slots} (columns 0-2), {target_series_2} slots: {series_2_slots} (columns 3-5)")

        # Create grid
        grid = [[None for _ in range(cols)] for _ in range(rows)]

        # For 50% Apple reservation, separate Apple and TPA products
        apple_series_1 = [p for p in series_1_products if p['brand'].lower().strip() == 'apple']
        apple_series_2 = [p for p in series_2_products if p['brand'].lower().strip() == 'apple']
        tpa_series_1 = [p for p in series_1_products if self.is_tpa_brand(p['brand'])]
        tpa_series_2 = [p for p in series_2_products if self.is_tpa_brand(p['brand'])]

        # For 4-series walls, also separate series 3 and 4
        if use_four_series:
            apple_series_3 = [p for p in series_3_products if p['brand'].lower().strip() == 'apple']
            apple_series_4 = [p for p in series_4_products if p['brand'].lower().strip() == 'apple']
            tpa_series_3 = [p for p in series_3_products if self.is_tpa_brand(p['brand'])]
            tpa_series_4 = [p for p in series_4_products if self.is_tpa_brand(p['brand'])]

        # Sort each category by sales
        sorted_apple_series_1 = sorted(apple_series_1, key=lambda p: p['sales'], reverse=True) if apple_series_1 else []
        sorted_apple_series_2 = sorted(apple_series_2, key=lambda p: p['sales'], reverse=True) if apple_series_2 else []
        sorted_tpa_series_1 = sorted(tpa_series_1, key=lambda p: p['sales'], reverse=True) if tpa_series_1 else []
        sorted_tpa_series_2 = sorted(tpa_series_2, key=lambda p: p['sales'], reverse=True) if tpa_series_2 else []

        if use_four_series:
            sorted_apple_series_3 = sorted(apple_series_3, key=lambda p: p['sales'], reverse=True) if apple_series_3 else []
            sorted_apple_series_4 = sorted(apple_series_4, key=lambda p: p['sales'], reverse=True) if apple_series_4 else []
            sorted_tpa_series_3 = sorted(tpa_series_3, key=lambda p: p['sales'], reverse=True) if tpa_series_3 else []
            sorted_tpa_series_4 = sorted(tpa_series_4, key=lambda p: p['sales'], reverse=True) if tpa_series_4 else []

        # For Apple-priority walls (1 & 2), Apple products go first to enforce 50% reservation
        if wall_number <= 2:
            sorted_series_1 = sorted_apple_series_1 + sorted_tpa_series_1
            sorted_series_2 = sorted_apple_series_2 + sorted_tpa_series_2
            with open('debug_wall_generation.txt', 'a') as f:
                f.write(f"Wall {wall_number}: APPLE PRIORITY - Apple first in sorted lists\n")
                f.write(f"Wall {wall_number}: Series 1 = {len(sorted_apple_series_1)} Apple + {len(sorted_tpa_series_1)} TPA\n")
                f.write(f"Wall {wall_number}: Series 2 = {len(sorted_apple_series_2)} Apple + {len(sorted_tpa_series_2)} TPA\n")
        elif use_four_series:
            # For 4-series wall (Wall 3), TPA products go first
            sorted_series_1 = sorted_tpa_series_1 + sorted_apple_series_1
            sorted_series_2 = sorted_tpa_series_2 + sorted_apple_series_2
            sorted_series_3 = sorted_tpa_series_3 + sorted_apple_series_3
            sorted_series_4 = sorted_tpa_series_4 + sorted_apple_series_4
            with open('debug_wall_generation.txt', 'a') as f:
                f.write(f"Wall {wall_number}: TPA PRIORITY - TPA first in sorted lists (4 series)\n")
                f.write(f"Wall {wall_number}: Series 1 ({target_series_1}) = {len(sorted_tpa_series_1)} TPA + {len(sorted_apple_series_1)} Apple\n")
                f.write(f"Wall {wall_number}: Series 2 ({target_series_2}) = {len(sorted_tpa_series_2)} TPA + {len(sorted_apple_series_2)} Apple\n")
                f.write(f"Wall {wall_number}: Series 3 ({target_series_3}) = {len(sorted_tpa_series_3)} TPA + {len(sorted_apple_series_3)} Apple\n")
                f.write(f"Wall {wall_number}: Series 4 ({target_series_4}) = {len(sorted_tpa_series_4)} TPA + {len(sorted_apple_series_4)} Apple\n")
        else:
            # For TPA-focus wall (fallback), TPA products go first
            sorted_series_1 = sorted_tpa_series_1 + sorted_apple_series_1
            sorted_series_2 = sorted_tpa_series_2 + sorted_apple_series_2
            with open('debug_wall_generation.txt', 'a') as f:
                f.write(f"Wall {wall_number}: TPA PRIORITY - TPA first in sorted lists\n")

        # Write series debug info to file
        with open('debug_wall_generation.txt', 'a') as f:
            f.write(f"Wall {wall_number}: Target series 1: {target_series_1}, products: {len(sorted_series_1)}\n")
            f.write(f"Wall {wall_number}: Target series 2: {target_series_2}, products: {len(sorted_series_2)}\n")
            if use_four_series:
                f.write(f"Wall {wall_number}: Target series 3: {target_series_3}, products: {len(sorted_series_3)}\n")
                f.write(f"Wall {wall_number}: Target series 4: {target_series_4}, products: {len(sorted_series_4)}\n")
            if sorted_series_1:
                f.write(f"Wall {wall_number}: Sample {target_series_1}: {[p['product_name'][:30] for p in sorted_series_1[:3]]}\n")
            if sorted_series_2:
                f.write(f"Wall {wall_number}: Sample {target_series_2}: {[p['product_name'][:30] for p in sorted_series_2[:3]]}\n")
            if use_four_series:
                if sorted_series_3:
                    f.write(f"Wall {wall_number}: Sample {target_series_3}: {[p['product_name'][:30] for p in sorted_series_3[:3]]}\n")
                if sorted_series_4:
                    f.write(f"Wall {wall_number}: Sample {target_series_4}: {[p['product_name'][:30] for p in sorted_series_4[:3]]}\n")

        if use_four_series:
            # 4-series distribution for Wall 3: Base(0-1), Plus(2-3), Pro(4), Pro Max(5)
            series_1_index = series_2_index = series_3_index = series_4_index = 0

            with open('debug_wall_generation.txt', 'a') as f:
                f.write(f"Wall {wall_number}: 4-SERIES GRID FILLING - Base(0-1), Plus(2-3), Pro(4), Pro Max(5)\n")

            for row in range(apple_rows):
                # Base series (columns 0-1)
                for col in range(2):
                    if series_1_index < len(sorted_series_1):
                        product = sorted_series_1[series_1_index % len(sorted_series_1)].copy()
                        product['is_vertical_phone'] = True
                        grid[row][col] = product
                        series_1_index += 1

                # Plus series (columns 2-3)
                for col in range(2, 4):
                    if series_2_index < len(sorted_series_2):
                        product = sorted_series_2[series_2_index % len(sorted_series_2)].copy()
                        product['is_vertical_phone'] = True
                        grid[row][col] = product
                        series_2_index += 1

                # Pro series (column 4)
                if series_3_index < len(sorted_series_3):
                    product = sorted_series_3[series_3_index % len(sorted_series_3)].copy()
                    product['is_vertical_phone'] = True
                    grid[row][4] = product
                    series_3_index += 1

                # Pro Max series (column 5)
                if series_4_index < len(sorted_series_4):
                    product = sorted_series_4[series_4_index % len(sorted_series_4)].copy()
                    product['is_vertical_phone'] = True
                    grid[row][5] = product
                    series_4_index += 1

            with open('debug_wall_generation.txt', 'a') as f:
                f.write(f"Wall {wall_number}: 4-SERIES PLACEMENT COMPLETE - Base:{series_1_index}, Plus:{series_2_index}, Pro:{series_3_index}, Pro Max:{series_4_index}\n")
        else:
            # 2-series distribution for Walls 1 & 2: Series 1(0-2), Series 2(3-5)
            series_1_index = 0
            for row in range(apple_rows):
                for col in range(3):  # First 3 columns
                    if series_1_index < len(sorted_series_1):
                        product = sorted_series_1[series_1_index % len(sorted_series_1)].copy()
                        product['is_vertical_phone'] = True
                        grid[row][col] = product
                        series_1_index += 1

            # Fill Series 2 products (columns 3-5)
            series_2_index = 0
            for row in range(apple_rows):
                for col in range(3, 6):  # Last 3 columns
                    if series_2_index < len(sorted_series_2):
                        product = sorted_series_2[series_2_index % len(sorted_series_2)].copy()
                        product['is_vertical_phone'] = True
                        grid[row][col] = product
                        series_2_index += 1
        
        # Fill remaining rows with TPA brands only (Gripp, Pulse, Tekne)
        remaining_slots = total_slots - apple_slots
        # Use only TPA products for remaining slots, not other_products
        tpa_grid_products = self._ensure_all_colors_represented(tpa_products, remaining_slots)
        
        # Fill remaining rows with TPA products only
        tpa_index = 0
        for row in range(apple_rows, rows):
            for col in range(cols):
                if tpa_index < len(tpa_grid_products):
                    grid[row][col] = tpa_grid_products[tpa_index]
                    grid[row][col]['is_vertical_phone'] = False
                    tpa_index += 1
        
        return grid
    
    def _ensure_product_diversity(self, products: List[Dict], target_slots: int) -> List[Dict]:
        """Ensure product diversity like your reference - high sellers get more but slow sellers aren't skipped"""
        if not products:
            return []
        
        # Filter out Apple and TPA products since they're handled separately in top rows
        non_apple_tpa_products = [p for p in products if p['brand'].lower().strip() not in ['apple', 'tpa']]
        
        if not non_apple_tpa_products:
            return []
        
        # Group by brand for diversity
        brand_groups = defaultdict(list)
        for product in non_apple_tpa_products:
            brand_groups[product['brand']].append(product)
        
        # Sort brands by total sales
        brand_sales = {}
        for brand, prods in brand_groups.items():
            brand_sales[brand] = sum(p['sales'] for p in prods)
        
        sorted_brands = sorted(brand_groups.keys(), key=lambda b: brand_sales[b], reverse=True)
        
        # Calculate fair allocation ensuring everyone gets representation
        diversified_products = []
        total_brands = len(brand_groups)
        
        if total_brands == 0:
            return []
        
        # Base allocation per brand (ensuring representation)
        if total_brands <= 3:  # Few brands - give everyone good representation
            base_allocation = max(3, target_slots // total_brands)
        else:  # Many brands - ensure representation but prioritize top performers
            base_allocation = max(2, target_slots // (total_brands + 1))
        
        allocated_slots = 0
        brand_allocations = {}
        
        # First pass - ensure minimum representation
        for brand in sorted_brands:
            brand_products = sorted(brand_groups[brand], key=lambda p: p['sales'], reverse=True)
            allocation = min(len(brand_products), base_allocation, target_slots - allocated_slots)
            brand_allocations[brand] = allocation
            allocated_slots += allocation
            
            if allocated_slots >= target_slots:
                break
        
        # Second pass - distribute remaining slots to top performers
        remaining_slots = target_slots - allocated_slots
        for brand in sorted_brands[:min(3, len(sorted_brands))]:  # Top 3 brands get extra slots
            if remaining_slots <= 0:
                break
            
            brand_products = brand_groups[brand]
            current_allocation = brand_allocations[brand]
            
            if current_allocation < len(brand_products):
                extra_slots = min(remaining_slots, len(brand_products) - current_allocation, max(1, remaining_slots // 3))
                brand_allocations[brand] += extra_slots
                remaining_slots -= extra_slots
        
        # Build final product list
        for brand in sorted_brands:
            brand_products = sorted(brand_groups[brand], key=lambda p: p['sales'], reverse=True)
            allocation = brand_allocations.get(brand, 0)
            
            for i in range(min(allocation, len(brand_products))):
                if len(diversified_products) < target_slots:
                    diversified_products.append(brand_products[i].copy())
        
        # Fill any remaining slots with top sellers
        while len(diversified_products) < target_slots and non_apple_tpa_products:
            top_products = sorted(non_apple_tpa_products, key=lambda p: p['sales'], reverse=True)
            for product in top_products:
                if len(diversified_products) < target_slots:
                    # Add as a facing (additional representation for high sellers)
                    diversified_products.append(product.copy())
                else:
                    break
        
    def _ensure_all_colors_represented(self, products: List[Dict], target_slots: int) -> List[Dict]:
        """Ensure ALL colors are represented with slight preference to high sellers"""
        if not products:
            return []
        
        # Filter out Apple and TPA products since they're handled separately
        non_apple_tpa_products = [p for p in products if p['brand'].lower().strip() not in ['apple', 'tpa']]
        
        if not non_apple_tpa_products:
            return []
        
        # Group by brand for color representation
        brand_groups = defaultdict(list)
        for product in non_apple_tpa_products:
            brand_groups[product['brand']].append(product)
        
        # Sort brands by total sales (high sellers get slight preference)
        brand_sales = {}
        for brand, prods in brand_groups.items():
            brand_sales[brand] = sum(p['sales'] for p in prods)
        
        sorted_brands = sorted(brand_groups.keys(), key=lambda b: brand_sales[b], reverse=True)
        
        # Force ALL brands to be represented (mandatory diversity)
        diversified_products = []
        total_brands = len(brand_groups)
        
        if total_brands == 0:
            return []
        
        # FORCE representation: Every brand gets at least 1 slot
        min_per_brand = max(1, target_slots // (total_brands * 2))  # Ensure everyone gets space
        allocated_slots = 0
        brand_allocations = {}
        
        # First pass - MANDATORY representation for ALL brands
        for brand in sorted_brands:
            brand_products = sorted(brand_groups[brand], key=lambda p: p['sales'], reverse=True)
            allocation = min(len(brand_products), min_per_brand, target_slots - allocated_slots)
            brand_allocations[brand] = max(1, allocation)  # Force at least 1
            allocated_slots += brand_allocations[brand]
            
            if allocated_slots >= target_slots:
                break
        
        # Second pass - Give extra slots to high sellers (slight preference)
        remaining_slots = target_slots - allocated_slots
        high_seller_bonus = max(1, remaining_slots // 3)  # Distribute bonus slots
        
        for brand in sorted_brands[:3]:  # Top 3 brands get bonus
            if remaining_slots <= 0:
                break
            
            brand_products = brand_groups[brand]
            current_allocation = brand_allocations[brand]
            
            if current_allocation < len(brand_products):
                bonus_slots = min(remaining_slots, high_seller_bonus, len(brand_products) - current_allocation)
                brand_allocations[brand] += bonus_slots
                remaining_slots -= bonus_slots
        
        # Build final product list with forced diversity
        for brand in sorted_brands:
            brand_products = sorted(brand_groups[brand], key=lambda p: p['sales'], reverse=True)
            allocation = brand_allocations.get(brand, 1)  # At least 1
            
            for i in range(min(allocation, len(brand_products))):
                if len(diversified_products) < target_slots:
                    diversified_products.append(brand_products[i].copy())
        
        # Fill any remaining slots by cycling through all brands
        while len(diversified_products) < target_slots and non_apple_tpa_products:
            for brand in sorted_brands:
                if len(diversified_products) >= target_slots:
                    break
                brand_products = sorted(brand_groups[brand], key=lambda p: p['sales'], reverse=True)
                # Add another product from this brand
                for product in brand_products:
                    if len(diversified_products) < target_slots:
                        diversified_products.append(product.copy())
                        break
        
        print(f"  Color diversity: {len(set(p['brand'] for p in diversified_products[:target_slots]))} brands represented")
        return diversified_products[:target_slots]
    
    def generate_store_planograms(self, store_name: str, total_walls: int) -> Dict[str, bool]:
        """Generate multiple walls for a store like frontend would do"""
        results = {}
        
        # Load real data
        real_products = self.load_real_cases_data()
        if not real_products:
            print("No real Cases & Covers data found")
            return {}
        
        # Get Cases & Covers wall allocation
        cases_wall_count = min(total_walls, self.get_cases_wall_count())
        
        print(f"Generating {cases_wall_count} Cases & Covers walls for {store_name}")
        
        # Generate each wall
        for wall_num in range(1, cases_wall_count + 1):
            success = self.generate_planogram(
                products=real_products,
                capacity=48,  # High capacity for dense layout
                output_path=str(self.output_path / f'{store_name.lower()}_wall{wall_num}_cases_covers_planogram.png'),
                details_path=str(self.output_path / f'{store_name.lower()}_wall{wall_num}_cases_covers_details.txt'),
                wall_number=wall_num,
                store_name=store_name,
                total_walls=cases_wall_count,
                total_store_walls=total_walls  # Pass total store walls for flagship logic
            )
            results[f'wall_{wall_num}'] = success
        
        return results
    def generate_planogram(self, products: List[Dict], capacity: int, output_path: str, 
                          details_path: str, wall_number: int, store_name: str, total_walls: int = 2, total_store_walls: int = 11) -> bool:
        """Generate professional Cases & Covers planogram matching reference style"""
        try:
            # Load real data instead of using passed products
            real_products = self.load_real_cases_data()
            if not real_products:
                print("No real Cases & Covers data found, using provided products")
                real_products = products
            
            # Get actual Cases & Covers wall count from your stored config
            cases_wall_count = total_walls or self.get_cases_wall_count()
            
            # Calculate grid size based on TOTAL STORE SIZE (flagship logic)
            grid_size = self.calculate_grid_size(total_store_walls, wall_number)
            rows, cols = grid_size
            
            print(f"Generating Cases & Covers planogram:")
            print(f"  Wall {wall_number} of {cases_wall_count} Cases & Covers walls")
            print(f"  Store type: {'Flagship' if total_store_walls >= 8 else 'Standard' if total_store_walls >= 5 else 'Express'} ({total_store_walls} total walls)")
            print(f"  Grid: {rows}x{cols} = {rows*cols} products (flagship density)")
            print(f"  Apple allocation: 50% of top rows (vertical rectangles)")
            print(f"  Brand colors: Apple=Yellow, Gripp=Blue, Pulse=Purple, Hyphen=Pink")
            
            # Create dense grid with Apple vertical placement and diversity
            product_grid = self.create_dense_product_grid(real_products, grid_size, wall_number, cases_wall_count)
            
            # Create professional visualization with proper dimensions
            fig, ax = plt.subplots(figsize=(18, 14))  # Increased size
            ax.set_facecolor(self.colors['background'])
            
            # Draw header
            self._draw_professional_header(ax, wall_number, store_name, len(real_products), cases_wall_count)
            
            # Draw dense product grid with Apple vertical rectangles
            self._draw_dense_product_grid_with_apple_vertical(ax, product_grid, grid_size)
            
            # Draw legend
            self._draw_professional_legend(ax, real_products)
            
            # Draw statistics
            self._draw_professional_stats(ax, real_products, grid_size)
            
            # Finalize with proper bounds to prevent cutoff
            ax.set_xlim(0, 17)   # Extended width
            ax.set_ylim(-1, 12)  # Extended height to prevent bottom cutoff
            ax.axis('off')
            
            # Save
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # Generate details
            self._generate_professional_details(details_path, wall_number, store_name, real_products, grid_size, cases_wall_count, total_store_walls)
            
            print(f"Professional Cases & Covers planogram saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating planogram: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _draw_professional_header(self, ax, wall_number: int, store_name: str, product_count: int, total_walls: int = 2):
        """Draw professional header matching your reference"""
        # Header background
        header_rect = Rectangle((0, 10.5), 16, 1.5, facecolor=self.colors['header_bg'], alpha=0.3)
        ax.add_patch(header_rect)
        
        # Main title
        ax.text(8, 11.5, f"Wall {wall_number} of {total_walls} - Cases & Covers", 
                ha='center', va='center', fontsize=18, fontweight='bold',
                color=self.colors['text_primary'])
        
        # Store name
        ax.text(8, 11.0, f"IMAGINE: {store_name.upper()}", 
                ha='center', va='center', fontsize=12,
                color=self.colors['text_secondary'])
        
        # Product count (like your reference shows "46 Products")
        ax.text(8, 10.7, f"({product_count} Products)", 
                ha='center', va='center', fontsize=10,
                color=self.colors['text_secondary'])
    
    def _draw_dense_product_grid_with_apple_vertical(self, ax, product_grid: List[List], grid_size: Tuple[int, int]):
        """Draw product grid with vertical rectangles, realistic gaps, and color diversity"""
        rows, cols = grid_size
        
        # Grid parameters for realistic retail layout with proper gaps
        start_x = 0.5
        start_y = 8.0  # Moved up to prevent cutoff
        uniform_width = 0.7    # Narrow for vertical rectangles
        uniform_height = 1.4   # Tall for vertical rectangles
        gap_x = 0.15          # Realistic gap between each facing
        gap_y = 0.15          # Realistic vertical gap between rows
        
        # Calculate Apple/TPA rows (top 50%)
        apple_rows = max(1, rows // 2)
        
        for row in range(rows):
            for col in range(cols):
                product = product_grid[row][col]
                if product is None:
                    continue
                
                # Calculate position with realistic gaps
                x_pos = start_x + col * (uniform_width + gap_x)
                y_pos = start_y - row * (uniform_height + gap_y)
                
                # Get diverse brand colors with forced diversity for Apple/TPA
                brand_color = self.get_brand_color(product['brand'])
                is_apple_tpa = product['brand'].lower().strip() in ['apple', 'tpa']
                
                # Force color diversity for Apple products (not just fallback colors)
                if is_apple_tpa and product['brand'].lower().strip() == 'apple':
                    # Extract color from actual Apple product names (handle trailing spaces)
                    product_name = product.get('product_name', '').lower().strip()
                    
                    # Apple-specific color mapping with MORE VIBRANT colors
                    if 'clear' in product_name:
                        brand_color = '#E8E8E8'  # Clearer light gray
                    elif 'black' in product_name:
                        brand_color = '#000000'  # Pure black
                    elif 'denim' in product_name:
                        brand_color = '#1E3A8A'  # Deep denim blue
                    elif 'fuchsia' in product_name:
                        brand_color = '#EC4899'  # Bright fuchsia
                    elif 'lake green' in product_name:
                        brand_color = '#059669'  # Vibrant green
                    elif 'plum' in product_name:
                        brand_color = '#7C3AED'  # Vibrant purple
                    elif 'star fruit' in product_name:
                        brand_color = '#EAB308'  # Bright yellow
                    elif 'stone gray' in product_name:
                        brand_color = '#6B7280'  # Medium gray
                    elif 'ultramarine' in product_name:
                        brand_color = '#2563EB'  # Bright ultramarine blue
                    else:
                        # Fallback diverse colors for other Apple products
                        apple_colors = ['#FFD700', '#FF8C00', '#FF6347', '#DC143C', '#4169E1', '#228B22']
                        color_index = (row * cols + col) % len(apple_colors)
                        brand_color = apple_colors[color_index]
                
                # Force color diversity for TPA products too
                elif is_apple_tpa and product['brand'].lower().strip() == 'tpa':
                    tpa_colors = [
                        '#4169E1',  # Blue (screen protectors)
                        '#228B22',  # Green (lens protectors) 
                        '#FF6347',  # Red
                        '#9370DB',  # Purple
                        '#FF8C00',  # Orange
                        '#00CED1'   # Turquoise
                    ]
                    color_index = (row * cols + col) % len(tpa_colors)
                    brand_color = tpa_colors[color_index]
                
                # Vertical rectangle for ALL products
                product_rect = FancyBboxPatch(
                    (x_pos, y_pos - uniform_height), uniform_width, uniform_height,
                    boxstyle="round,pad=0.02",
                    facecolor=brand_color,
                    edgecolor='#2C2C2E',
                    linewidth=1.0,
                    alpha=0.95
                )
                ax.add_patch(product_rect)
                
                # Premium section header (only once for Apple/TPA section)
                if row == 0 and col == 2 and is_apple_tpa:
                    premium_width = cols * (uniform_width + gap_x) - gap_x
                    premium_rect = Rectangle(
                        (start_x, y_pos + 0.15), premium_width, 0.25,
                        facecolor='#FF6B35', alpha=0.9, zorder=10
                    )
                    ax.add_patch(premium_rect)
                    section_name = "APPLE + TPA PREMIUM SECTION"
                    ax.text(start_x + premium_width / 2, y_pos + 0.275, 
                           section_name,
                           ha='center', va='center', fontsize=8, fontweight='bold', color='white')
                
                # Series indicators for Apple section (column-based)
                if row == 0 and is_apple_tpa:
                    if col < 3:  # First 3 columns = Base
                        series_indicator = "BASE"
                        indicator_color = '#FF8C00'
                    else:  # Last 3 columns = Plus
                        series_indicator = "PLUS"
                        indicator_color = '#FF4500'
                    
                    # Series indicator bar
                    series_rect = Rectangle(
                        (x_pos, y_pos - 0.05), uniform_width, 0.1,
                        facecolor=indicator_color, alpha=1.0, zorder=5
                    )
                    ax.add_patch(series_rect)
                    
                    ax.text(x_pos + uniform_width/2, y_pos, series_indicator,
                           ha='center', va='center', fontsize=5, fontweight='bold', color='white')
                
                # Brand header
                brand_header = Rectangle(
                    (x_pos, y_pos - 0.2), uniform_width, 0.12,
                    facecolor=brand_color, alpha=1.0
                )
                ax.add_patch(brand_header)
                
                # Brand text
                text_color = 'white' if brand_color not in ['#FFD700', '#32CD32', '#FF8C00'] else 'black'
                brand_text = product['brand'][:5]
                ax.text(x_pos + uniform_width/2, y_pos - 0.14, brand_text,
                       ha='center', va='center', fontsize=6, fontweight='bold', color=text_color)
                
                # Color name with proper Apple product name mapping
                color_names = {
                    '#F5F5F5': 'Clear', '#1C1C1E': 'Black', '#4A90E2': 'Denim', '#FF69B4': 'Fuchsia',
                    '#50C878': 'Lake Green', '#8E4585': 'Plum', '#FFD700': 'Star Fruit', 
                    '#8E8E93': 'Stone Gray', '#007AFF': 'Ultramarine', '#30D158': 'Green',
                    '#FF2D92': 'Pink', '#AF52DE': 'Purple', '#FF3B30': 'Red', '#FF9500': 'Orange',
                    '#FFCC00': 'Yellow', '#4169E1': 'Blue', '#228B22': 'Forest Green',
                    '#FF8C00': 'Dark Orange', '#FF6347': 'Tomato', '#DC143C': 'Crimson',
                    '#00CED1': 'Turquoise', '#696969': 'Gray'
                }
                
                # For Apple products, try to extract color from product name first
                if is_apple_tpa and product['brand'].lower().strip() == 'apple':
                    product_name = product.get('product_name', '').lower().strip()
                    if 'clear' in product_name:
                        color_name = 'Clear'
                    elif 'black' in product_name:
                        color_name = 'Black'
                    elif 'denim' in product_name:
                        color_name = 'Denim'
                    elif 'fuchsia' in product_name:
                        color_name = 'Fuchsia'
                    elif 'lake green' in product_name:
                        color_name = 'Lake Green'
                    elif 'plum' in product_name:
                        color_name = 'Plum'
                    elif 'star fruit' in product_name:
                        color_name = 'Star Fruit'
                    elif 'stone gray' in product_name:
                        color_name = 'Stone Gray'
                    elif 'ultramarine' in product_name:
                        color_name = 'Ultramarine'
                    elif 'green' in product_name:
                        color_name = 'Green'
                    elif 'blue' in product_name:
                        color_name = 'Blue'
                    elif 'pink' in product_name:
                        color_name = 'Pink'
                    elif 'purple' in product_name:
                        color_name = 'Purple'
                    elif 'red' in product_name:
                        color_name = 'Red'
                    elif 'orange' in product_name:
                        color_name = 'Orange'
                    elif 'yellow' in product_name:
                        color_name = 'Yellow'
                    else:
                        color_name = color_names.get(brand_color, 'Apple')
                else:
                    color_name = color_names.get(brand_color, 'Color')
                ax.text(x_pos + uniform_width/2, y_pos - 0.35, color_name,
                       ha='center', va='center', fontsize=5, color=text_color)
                
                # Series info
                series = self.extract_series_info(product['product_name'], product['series'])
                if is_apple_tpa:
                    series_display = "Base" if col < 3 else "Plus"
                else:
                    series_display = series
                
                ax.text(x_pos + uniform_width/2, y_pos - 0.6, series_display,
                       ha='center', va='center', fontsize=6, color=text_color, fontweight='bold')
                
                # Product type
                if is_apple_tpa and product['brand'].lower().strip() == 'tpa':
                    product_type = 'Screen' if 'screen' in product.get('subcategory', '').lower() else 'Lens'
                else:
                    product_type = product.get('subcategory', 'Case')[:5]
                
                ax.text(x_pos + uniform_width/2, y_pos - 0.9, product_type,
                       ha='center', va='center', fontsize=5, color=text_color)
                
                # Sales number
                ax.text(x_pos + uniform_width/2, y_pos - 1.4, str(product['sales']),
                       ha='center', va='center', fontsize=4, color=text_color, alpha=0.8)
    
    def _draw_professional_legend(self, ax, products: List[Dict]):
        """Draw professional legend without overlapping"""
        legend_x = 14.5  # Moved further right
        legend_y = 8.5   # Moved down to avoid overlap
        
        # Legend title
        ax.text(legend_x, legend_y, "Legend", 
                fontsize=10, fontweight='bold',
                color=self.colors['text_primary'])
        
        # Brand colors (top brands only)
        brands = list(set(p['brand'] for p in products))
        brand_counts = Counter(p['brand'] for p in products)
        top_brands = [brand for brand, _ in brand_counts.most_common(5)]  # Reduced to 5
        
        y_offset = 0.4
        for i, brand in enumerate(top_brands):
            y_pos = legend_y - y_offset * (i + 1)
            
            # Color box
            brand_color = self.get_brand_color(brand)
            color_box = Rectangle((legend_x, y_pos - 0.08), 0.25, 0.15,
                                facecolor=brand_color, alpha=0.9)
            ax.add_patch(color_box)
            
            # Brand name and count
            count = brand_counts[brand]
            ax.text(legend_x + 0.3, y_pos, f"{brand}: {count}",
                   fontsize=7, va='center',
                   color=self.colors['text_primary'])
    
    def _draw_professional_stats(self, ax, products: List[Dict], grid_size: Tuple[int, int]):
        """Draw professional statistics at proper position"""
        rows, cols = grid_size
        total_slots = rows * cols
        total_sales = sum(p['sales'] for p in products[:total_slots])
        
        stats_text = f"Total Products: {total_slots} | Total Sales: {total_sales:,} | Utilization: 100%"
        
        ax.text(8.5, -0.3, stats_text,  # Moved up from 0.5 to -0.3
               ha='center', va='center', fontsize=10,
               color=self.colors['text_secondary'],
               bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors['header_bg']))
    
    def _generate_professional_details(self, details_path: str, wall_number: int, 
                                     store_name: str, products: List[Dict], grid_size: Tuple[int, int], total_walls: int, total_store_walls: int = 11):
        """Generate professional details file"""
        rows, cols = grid_size
        total_products = rows * cols
        apple_rows = max(1, rows // 2)
        apple_allocation = apple_rows * cols
        
        # Determine store type
        store_type = 'Flagship' if total_store_walls >= 8 else 'Standard' if total_store_walls >= 5 else 'Express'
        
        # Count actual products in the grid (not from original product list)
        grid = self.create_dense_product_grid(products, grid_size, wall_number, total_walls)
        
        # Extract actual grid products
        grid_products = []
        for row in grid:
            for cell in row:
                if cell:
                    grid_products.append(cell)
        
        with open(details_path, 'w', encoding='utf-8') as f:
            f.write(f"CASES & COVERS PLANOGRAM DETAILS - Wall {wall_number} of {total_walls}\n")
            f.write(f"Store: IMAGINE {store_name.upper()} ({store_type} - {total_store_walls} walls)\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Grid Size: {rows}x{cols} = {total_products} products ({store_type} density)\n")
            f.write(f"Apple Premium Section: Top {apple_rows} rows ({apple_allocation} slots, 50%)\n")
            f.write(f"Other Brands Section: Bottom {rows - apple_rows} rows\n\n")
            
            # Brand breakdown from actual grid
            brand_counts = Counter(p['brand'] for p in grid_products)
            f.write("BRAND DISTRIBUTION (ACTUAL GRID):\n")
            for brand, count in brand_counts.most_common():
                percentage = (count / total_products) * 100
                f.write(f"  • {brand}: {count} products ({percentage:.1f}%)\n")
            
            # Apple analysis
            apple_count = brand_counts.get('Apple', 0)
            f.write(f"\nAPPLE ANALYSIS:\n")
            f.write(f"  • Apple products in grid: {apple_count}\n")
            f.write(f"  • Apple allocation: {apple_allocation} slots (50% of top rows)\n")
            f.write(f"  • Apple utilization: {(apple_count/apple_allocation*100):.1f}% of allocated slots\n")
            f.write(f"  • Vertical phone-like rectangles in premium section\n")
            
            # Diversity analysis
            f.write(f"\nDIVERSITY METRICS:\n")
            f.write(f"  • Total brands represented: {len(brand_counts)}\n")
            f.write(f"  • High sellers with enhanced representation\n")
            f.write(f"  • All brands get minimum visibility\n")
            
            # Top rows analysis
            apple_in_top_rows = sum(1 for row in range(apple_rows) for col in range(cols) 
                                  if grid[row][col] and grid[row][col]['brand'].lower() == 'apple')
            f.write(f"  • Apple products in top {apple_rows} rows: {apple_in_top_rows}/{apple_allocation}\n")
            
            f.write(f"\nSTORE ANALYSIS:\n")
            f.write(f"  • Store type: {store_type} ({total_store_walls} total walls)\n")
            f.write(f"  • Grid density: {rows}x{cols} = {total_products} products\n")
            f.write(f"  • Layout strategy: Flagship density for major stores\n")
            
            f.write(f"\nTOTAL PRODUCTS: {total_products}\n")
            f.write(f"UTILIZATION: 100% (Dense {store_type.lower()} layout matching reference)\n")
            f.write(f"LAYOUT: Apple vertical rectangles + brand diversity\n")

# Add new store-wise generation function
def generate_store_cases_planograms(store_name: str, total_store_walls: int = 11) -> Dict[str, bool]:
    """Generate Cases & Covers planograms for a store (frontend-like functionality)"""
    generator = CasesCoversGenerator('c:/Users/Shivansh Pal/Desktop/Planogram_Project')
    return generator.generate_store_planograms(store_name, total_store_walls)

# Maintain compatibility with existing system
def generate_wall_planogram(wall_data: Dict, capacity: int, wall_number: int, store_name: str) -> bool:
    """Legacy compatibility function"""
    generator = CasesCoversGenerator('c:/Users/Shivansh Pal/Desktop/Planogram_Project')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = str(generator.output_path / f'wall{wall_number}_cases_and_covers_planogram_{timestamp}.png')
    details_path = str(generator.output_path / f'wall{wall_number}_cases_and_covers_details_{timestamp}.txt')
    
    products = wall_data.get('products', [])
    
    return generator.generate_planogram(products, capacity, output_path, details_path, 
                                      wall_number, store_name, total_walls=2, total_store_walls=11)
