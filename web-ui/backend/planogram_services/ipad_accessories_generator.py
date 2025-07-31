#!/usr/bin/env python3
"""
iPad Accessories Planogram Generator
Professional planogram generator optimized for iPad accessories with support for:
- Larger accessory dimensions (iPad Pro 12.9" up to 28×21.5cm)
- Multiple categories (cases, folios, keyboard cases, armor cases)
- iPad model compatibility (Mini, Base, Air, Pro 11", Pro 12.9")
- Sales-based prioritization and brand allocation
"""

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

class IPadAccessoriesGenerator:
    """Professional iPad accessories planogram generator"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
        # iPad-specific brand color scheme
        self.brand_colors = {
            'Apple': '#007AFF',      # Apple Blue (official iPad color)
            'Gripp': '#00C851',      # Green (volume leader)
            'STM': '#FF6B35',        # Orange (professional)
            'Logitech': '#0066CC',   # Blue (productivity)
            'Tucano': '#8E44AD',     # Purple (fashion)
            'tomtoc': '#E74C3C',     # Red (minimalist)
            'DBramante1928': '#2C3E50',  # Dark gray (premium)
            'Muvtech': '#F39C12',    # Orange (specialty)
            'Default': '#95A5A6'     # Light gray
        }
        
        # Supporting colors for professional appearance
        self.colors = {
            'background': '#FFFFFF',
            'border': '#BDC3C7',
            'text_primary': '#2C3E50',
            'text_secondary': '#7F8C8D',
            'grid_line': '#ECF0F1',
            'header_bg': '#F8F9FA',
            'apple_premium': '#E8F4FD',  # Light blue for Apple section
            'productivity': '#FFF3E0'     # Light orange for keyboard section
        }
        
        # iPad model specifications - Limited to 4 series with dedicated columns
        self.ipad_models = {
            'iPad Mini': {
                'dimensions': (20.0, 13.4, 0.65),  # Smallest
                'display_size': '7.9"',
                'columns': [0],  # Dedicated column 0
                'priority_multiplier': 0.8,
                'size_scale': 0.6  # Smallest visual size
            },
            'iPad Base': {
                'dimensions': (25.0, 17.4, 0.75),  # Medium
                'display_size': '10.2"/10.9"',
                'columns': [1],  # Dedicated column 1
                'priority_multiplier': 1.0,
                'size_scale': 0.8  # Medium visual size
            },
            'iPad Air': {
                'dimensions': (25.0, 17.8, 0.75),  # Same as Pro
                'display_size': '10.9"/11"',
                'columns': [2],  # Dedicated column 2
                'priority_multiplier': 1.2,
                'size_scale': 1.0  # Standard visual size (same as Pro)
            },
            'iPad Pro': {
                'dimensions': (25.0, 17.8, 0.75),  # Same as Air
                'display_size': '11"/12.9"',  # Combined Pro models
                'columns': [3],  # Dedicated column 3
                'priority_multiplier': 1.3,
                'size_scale': 1.0  # Standard visual size (same as Air)
            }
        }
        
        # Category specifications
        self.categories = {
            'case': {
                'rows': [0, 1, 2],  # Rows 0-2
                'priority': 1.0,
                'description': 'Basic Protection'
            },
            'folio': {
                'rows': [3, 4],     # Rows 3-4
                'priority': 1.2,    # Premium category
                'description': 'Premium Folios'
            },
            'keyboard case': {
                'rows': [5, 6],     # Rows 5-6
                'priority': 1.5,    # Highest priority (productivity)
                'description': 'Productivity'
            },
            'armor case': {
                'rows': [2, 7],     # Mixed with cases and specialty
                'priority': 1.1,
                'description': 'Heavy Duty'
            },
            'hardshell': {
                'rows': [7],        # Row 7 (specialty)
                'priority': 0.9,
                'description': 'Basic Shell'
            }
        }
    
    def load_ipad_data(self) -> List[Dict]:
        """Load and process iPad accessories data with validation and cleaning"""
        try:
            # Load main iPad accessories dataset
            csv_path = self.project_root / 'data' / 'raw' / 'accessories' / 'ipad-cases-transformed.csv'
            if not csv_path.exists():
                print(f"iPad data file not found: {csv_path}")
                return []
            
            df = pd.read_csv(csv_path)
            df.columns = df.columns.str.strip()  # Clean column names
            
            print(f"Loaded {len(df)} iPad accessories from dataset")
            
            # Validate and clean data
            validated_products = []
            warnings = []
            
            for _, row in df.iterrows():
                try:
                    # Extract and validate basic fields
                    product_name = str(row.get('product_name', '')).strip()
                    if not product_name or product_name == 'nan':
                        warnings.append(f"Skipping product with empty name")
                        continue
                    
                    # Process iPad model/series
                    series = str(row.get('series', 'iPad Base')).strip()
                    ipad_model = self._classify_ipad_model(product_name, series)
                    
                    # Process category
                    category = str(row.get('category', 'case')).strip().lower()
                    if category not in self.categories:
                        category = 'case'  # Default fallback
                    
                    # Process brand
                    brand = str(row.get('brand', 'Default')).strip()
                    if not brand or brand == 'nan':
                        brand = 'Default'
                    
                    # Process dimensions with validation
                    width = float(row.get('width', 25.0))
                    height = float(row.get('height', 17.8))
                    depth = float(row.get('depth', 0.75))
                    
                    # Validate dimensions are reasonable for iPad accessories
                    if not (15.0 <= width <= 35.0):
                        warnings.append(f"Unusual width {width}cm for {product_name}, using default")
                        width = self.ipad_models.get(ipad_model, {}).get('dimensions', (25.0, 17.8, 0.75))[0]
                    
                    if not (10.0 <= height <= 25.0):
                        warnings.append(f"Unusual height {height}cm for {product_name}, using default")
                        height = self.ipad_models.get(ipad_model, {}).get('dimensions', (25.0, 17.8, 0.75))[1]
                    
                    # Process sales frequency
                    frequency = int(row.get('frequency', 1))
                    if frequency < 0:
                        frequency = 1
                        warnings.append(f"Negative frequency for {product_name}, set to 1")
                    
                    # Calculate priority score
                    priority_score = self._calculate_priority_score(
                        frequency, brand, category, ipad_model
                    )
                    
                    # Extract color/subcategory information
                    subcategory = str(row.get('subcategory', '')).strip()
                    color = self._extract_color_info(product_name, subcategory)
                    
                    # Create validated product record
                    product_data = {
                        'product_name': product_name,
                        'series': series,
                        'ipad_model': ipad_model,
                        'category': category,
                        'subcategory': subcategory,
                        'color': color,
                        'brand': brand,
                        'width': width,
                        'height': height,
                        'depth': depth,
                        'frequency': frequency,
                        'priority_score': priority_score,
                        'core_product': 'iPad'
                    }
                    
                    validated_products.append(product_data)
                    
                except Exception as e:
                    warnings.append(f"Error processing product {product_name}: {str(e)}")
                    continue
            
            # Print validation summary
            print(f"Successfully processed {len(validated_products)} iPad accessories")
            if warnings:
                print(f"Validation warnings: {len(warnings)}")
                for warning in warnings[:5]:  # Show first 5 warnings
                    print(f"  - {warning}")
                if len(warnings) > 5:
                    print(f"  ... and {len(warnings) - 5} more warnings")
            
            # Load compatible accessories from Mac dataset
            compatible_accessories = self._load_compatible_mac_accessories()
            if compatible_accessories:
                print(f"Added {len(compatible_accessories)} compatible accessories from Mac dataset")
                validated_products.extend(compatible_accessories)
            
            return validated_products
            
        except Exception as e:
            print(f"Error loading iPad data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _classify_ipad_model(self, product_name: str, series: str) -> str:
        """Advanced iPad model classification with size-based detection and compatibility mapping"""
        combined = f"{product_name} {series}".lower()
        
        # Priority-based classification with size detection
        classification_rules = [
            # iPad Mini (7.9") - Smallest form factor
            {
                'model': 'iPad Mini',
                'patterns': ['mini', '7.9', 'ipad mini'],
                'size_indicators': ['7.9'],
                'priority': 1
            },
            # iPad Pro 12.9" - Largest form factor
            {
                'model': 'iPad Pro 12.9',
                'patterns': ['12.9', 'pro 12', 'pro max', 'large pro'],
                'size_indicators': ['12.9'],
                'priority': 1
            },
            # iPad Pro 11" - Professional 11-inch
            {
                'model': 'iPad Pro',
                'patterns': ['pro 11', '11 pro', 'pro (11', 'pro 2024', 'pro 2022', 'pro 2021'],
                'size_indicators': ['11.0', '11"'],
                'priority': 2
            },
            # iPad Air - Mid-range with 10.9"/11" sizes
            {
                'model': 'iPad Air',
                'patterns': ['air', 'ipad air', 'air 10.9', 'air 11'],
                'size_indicators': ['10.9', '11'],
                'priority': 3
            },
            # iPad Base - Entry level with 10.2"/10.9" sizes
            {
                'model': 'iPad Base',
                'patterns': ['base', '10.2', '10.9', '10th generation', '9th generation', '8th generation'],
                'size_indicators': ['10.2', '10.9'],
                'priority': 4
            }
        ]
        
        # Score each model based on pattern matches
        model_scores = {}
        
        for rule in classification_rules:
            score = 0
            model = rule['model']
            
            # Check for pattern matches
            for pattern in rule['patterns']:
                if pattern in combined:
                    score += 10  # Base score for pattern match
                    
                    # Bonus for exact size indicators
                    for size in rule['size_indicators']:
                        if size in combined:
                            score += 20  # High bonus for size match
            
            # Check series field specifically
            if rule['model'].replace('iPad ', '').lower() in series.lower():
                score += 15
            
            # Priority penalty (lower priority = higher penalty)
            score -= rule['priority'] * 2
            
            if score > 0:
                model_scores[model] = score
        
        # Return highest scoring model
        if model_scores:
            best_model = max(model_scores.items(), key=lambda x: x[1])[0]
            return best_model
        
        # Fallback classification based on series only
        series_lower = series.lower()
        if 'mini' in series_lower:
            return 'iPad Mini'
        elif 'pro' in series_lower:
            # Check for size indicators in product name for Pro models
            if '12.9' in product_name or '12.9' in series:
                return 'iPad Pro 12.9'
            else:
                return 'iPad Pro'
        elif 'air' in series_lower:
            return 'iPad Air'
        else:
            return 'iPad Base'  # Default fallback
    
    def _calculate_priority_score(self, frequency: int, brand: str, category: str, ipad_model: str) -> int:
        """Calculate priority score for product placement"""
        score = frequency
        
        # Brand multipliers
        if brand.lower() == 'apple':
            score *= 1.3  # Premium positioning
        elif brand.lower() == 'gripp':
            score *= 1.2  # Volume leader
        elif brand.lower() in ['stm', 'logitech']:
            score *= 1.1  # Professional brands
        
        # Category multipliers
        category_multiplier = self.categories.get(category, {}).get('priority', 1.0)
        score *= category_multiplier
        
        # iPad model multipliers
        model_multiplier = self.ipad_models.get(ipad_model, {}).get('priority_multiplier', 1.0)
        score *= model_multiplier
        
        return int(score)
    
    def _extract_color_info(self, product_name: str, subcategory: str) -> str:
        """Extract color information from product name and subcategory"""
        # Check subcategory first (often contains color)
        if subcategory and subcategory not in ['Size 7.9-Inch', 'Size 10.2-Inch', 'Size 10.9-Inch', 'Size 11.0-Inch', 'Size 12.9-Inch', 'Size 13.0-Inch']:
            return subcategory
        
        # Extract from product name
        product_lower = product_name.lower()
        
        # Common iPad accessory colors
        colors = [
            'black', 'white', 'blue', 'red', 'green', 'yellow', 'orange', 'purple',
            'pink', 'gray', 'grey', 'silver', 'gold', 'clear', 'transparent',
            'navy', 'sky blue', 'dark blue', 'light blue', 'electric orange',
            'mallard green', 'dark cherry', 'english lavender', 'rainbow',
            'camouflage', 'denim', 'stone', 'midnight'
        ]
        
        for color in colors:
            if color in product_lower:
                return color.title()
        
        return 'Default'
    
    def _load_compatible_mac_accessories(self) -> List[Dict]:
        """Load iPad-compatible accessories from Mac accessories dataset"""
        try:
            mac_csv_path = self.project_root / 'data' / 'raw' / 'accessories' / 'mac-accessories-transformed.csv'
            if not mac_csv_path.exists():
                return []
            
            df = pd.read_csv(mac_csv_path)
            df.columns = df.columns.str.strip()
            
            # Filter for iPad-compatible accessories
            ipad_compatible = df[df['product_name'].str.contains('iPad|ipad', case=False, na=False)]
            
            compatible_products = []
            for _, row in ipad_compatible.iterrows():
                try:
                    product_name = str(row.get('product_name', '')).strip()
                    category = str(row.get('category', 'accessory')).strip().lower()
                    brand = str(row.get('brand', 'Default')).strip()
                    frequency = int(row.get('frequency', 1))
                    
                    # Map Mac categories to iPad categories
                    if category in ['hub']:
                        ipad_category = 'accessory'
                    elif category in ['stand']:
                        ipad_category = 'accessory'
                    else:
                        continue  # Skip non-relevant categories
                    
                    # Determine iPad model compatibility
                    if 'pro' in product_name.lower():
                        if '12.9' in product_name:
                            ipad_model = 'iPad Pro 12.9'
                        else:
                            ipad_model = 'iPad Pro'
                    elif 'air' in product_name.lower():
                        ipad_model = 'iPad Air'
                    else:
                        ipad_model = 'iPad Base'  # Universal compatibility
                    
                    # Use default dimensions for accessories
                    width = float(row.get('width', 15.0))
                    height = float(row.get('height', 10.0))
                    depth = float(row.get('depth', 2.0))
                    
                    priority_score = self._calculate_priority_score(
                        frequency, brand, ipad_category, ipad_model
                    )
                    
                    compatible_product = {
                        'product_name': product_name,
                        'series': ipad_model,
                        'ipad_model': ipad_model,
                        'category': ipad_category,
                        'subcategory': category.title(),
                        'color': 'Default',
                        'brand': brand,
                        'width': width,
                        'height': height,
                        'depth': depth,
                        'frequency': frequency,
                        'priority_score': priority_score,
                        'core_product': 'iPad',
                        'source': 'mac_accessories'
                    }
                    
                    compatible_products.append(compatible_product)
                    
                except Exception as e:
                    continue
            
            return compatible_products
            
        except Exception as e:
            print(f"Error loading compatible Mac accessories: {e}")
            return []
    
    def classify_products_by_model(self, products: List[Dict]) -> Dict[str, List[Dict]]:
        """Classify products by iPad model with size-based grouping"""
        model_groups = {
            'iPad Mini': [],
            'iPad Base': [],
            'iPad Air': [],
            'iPad Pro': [],
            'iPad Pro 12.9': []
        }
        
        # Group products by classified model
        for product in products:
            model = product['ipad_model']
            if model in model_groups:
                model_groups[model].append(product)
            else:
                # Fallback to iPad Base for unknown models
                model_groups['iPad Base'].append(product)
        
        # Sort each group by priority score (highest first)
        for model in model_groups:
            model_groups[model].sort(key=lambda p: p['priority_score'], reverse=True)
        
        return model_groups
    
    def get_model_compatibility_matrix(self) -> Dict[str, Dict]:
        """Get compatibility matrix showing which accessories work with which iPad models"""
        products = self.load_ipad_data()
        model_groups = self.classify_products_by_model(products)
        
        compatibility_matrix = {}
        
        for model, products_list in model_groups.items():
            if not products_list:
                continue
                
            model_info = self.ipad_models.get(model, {})
            
            # Analyze product categories for this model
            categories = Counter(p['category'] for p in products_list)
            brands = Counter(p['brand'] for p in products_list)
            
            # Calculate average dimensions
            widths = [p['width'] for p in products_list]
            heights = [p['height'] for p in products_list]
            
            compatibility_matrix[model] = {
                'product_count': len(products_list),
                'total_sales': sum(p['frequency'] for p in products_list),
                'avg_sales_per_product': sum(p['frequency'] for p in products_list) / len(products_list),
                'categories': dict(categories.most_common()),
                'top_brands': dict(brands.most_common(3)),
                'dimensions': {
                    'avg_width': sum(widths) / len(widths),
                    'avg_height': sum(heights) / len(heights),
                    'width_range': (min(widths), max(widths)),
                    'height_range': (min(heights), max(heights))
                },
                'display_size': model_info.get('display_size', 'Unknown'),
                'grid_columns': model_info.get('columns', []),
                'priority_multiplier': model_info.get('priority_multiplier', 1.0),
                'top_products': [
                    {
                        'name': p['product_name'][:40] + '...' if len(p['product_name']) > 40 else p['product_name'],
                        'brand': p['brand'],
                        'category': p['category'],
                        'sales': p['frequency']
                    }
                    for p in sorted(products_list, key=lambda x: x['frequency'], reverse=True)[:5]
                ]
            }
        
        return compatibility_matrix
    
    def get_size_based_allocation(self) -> Dict[str, Dict]:
        """Get size-based allocation strategy for grid layout"""
        model_groups = self.classify_products_by_model(self.load_ipad_data())
        
        allocation_strategy = {}
        total_products = sum(len(products) for products in model_groups.values())
        
        for model, products in model_groups.items():
            if not products:
                continue
                
            model_info = self.ipad_models.get(model, {})
            product_count = len(products)
            
            # Calculate allocation percentage
            allocation_percentage = (product_count / total_products) * 100
            
            # Determine grid allocation
            columns = model_info.get('columns', [])
            column_count = len(columns)
            
            allocation_strategy[model] = {
                'product_count': product_count,
                'allocation_percentage': allocation_percentage,
                'grid_columns': columns,
                'column_count': column_count,
                'dimensions': model_info.get('dimensions', (25.0, 17.8, 0.75)),
                'display_size': model_info.get('display_size', 'Unknown'),
                'priority_multiplier': model_info.get('priority_multiplier', 1.0),
                'recommended_positions': self._calculate_recommended_positions(model, product_count, columns),
                'space_requirements': self._calculate_space_requirements(model, product_count)
            }
        
        return allocation_strategy
    
    def _calculate_recommended_positions(self, model: str, product_count: int, columns: List[int]) -> List[Tuple[int, int]]:
        """Calculate recommended grid positions for a model's products"""
        positions = []
        
        if not columns:
            return positions
        
        # Calculate how many products per column
        products_per_column = max(1, product_count // len(columns))
        remaining_products = product_count % len(columns)
        
        for col_idx, col in enumerate(columns):
            # Distribute products across rows for this column
            products_in_this_column = products_per_column
            if col_idx < remaining_products:
                products_in_this_column += 1
            
            for row in range(min(products_in_this_column, 8)):  # Max 8 rows
                positions.append((row, col))
        
        return positions
    
    def _calculate_space_requirements(self, model: str, product_count: int) -> Dict:
        """Calculate space requirements for a model's products"""
        model_info = self.ipad_models.get(model, {})
        dimensions = model_info.get('dimensions', (25.0, 17.8, 0.75))
        
        # Base space per product (including spacing)
        base_width = dimensions[0] + 2.0  # 2cm spacing
        base_height = dimensions[1] + 2.0  # 2cm spacing
        
        # Calculate total space needed
        columns = model_info.get('columns', [1])
        column_count = len(columns)
        
        if column_count > 0:
            products_per_column = max(1, product_count // column_count)
            total_width = base_width * column_count
            total_height = base_height * min(products_per_column, 8)  # Max 8 rows
        else:
            total_width = base_width
            total_height = base_height
        
        return {
            'total_width_cm': total_width,
            'total_height_cm': total_height,
            'products_per_column': products_per_column if column_count > 0 else product_count,
            'column_count': column_count,
            'space_efficiency': min(1.0, product_count / (column_count * 8)) if column_count > 0 else 1.0
        }
    
    def organize_products_by_category(self, products: List[Dict]) -> Dict[str, List[Dict]]:
        """Organize products by category with row-based allocation"""
        category_groups = {
            'cases': [],           # Rows 0-2 (basic protection)
            'folios': [],          # Rows 3-4 (premium protection)
            'keyboard_cases': [],  # Rows 5-6 (productivity)
            'specialty': []        # Row 7 (armor cases, hardshells, accessories)
        }
        
        # Map original categories to planogram categories
        category_mapping = {
            'case': 'cases',
            'folio': 'folios',
            'keyboard case': 'keyboard_cases',
            'armor case': 'specialty',
            'hardshell': 'specialty',
            'accessory': 'specialty'
        }
        
        # Group products by mapped categories
        for product in products:
            original_category = product.get('category', 'case')
            mapped_category = category_mapping.get(original_category, 'cases')
            category_groups[mapped_category].append(product)
        
        # Sort each category by priority score (highest first)
        for category in category_groups:
            category_groups[category].sort(key=lambda p: p['priority_score'], reverse=True)
        
        return category_groups
    
    def get_category_allocation_strategy(self) -> Dict[str, Dict]:
        """Get category-based allocation strategy for row organization"""
        products = self.load_ipad_data()
        category_groups = self.organize_products_by_category(products)
        
        allocation_strategy = {}
        total_products = len(products)
        
        for category, products_list in category_groups.items():
            if not products_list:
                continue
            
            category_info = self.categories.get(category.rstrip('s'), {})  # Remove plural 's'
            if not category_info:
                # Handle special cases
                if category == 'keyboard_cases':
                    category_info = self.categories.get('keyboard case', {})
                elif category == 'specialty':
                    category_info = {'rows': [7], 'priority': 1.0, 'description': 'Specialty Items'}
            
            product_count = len(products_list)
            allocation_percentage = (product_count / total_products) * 100
            
            # Calculate sales performance
            total_sales = sum(p['frequency'] for p in products_list)
            avg_sales = total_sales / product_count if product_count > 0 else 0
            
            # Get top brands in this category
            brand_counts = Counter(p['brand'] for p in products_list)
            
            # Get iPad model distribution
            model_counts = Counter(p['ipad_model'] for p in products_list)
            
            allocation_strategy[category] = {
                'product_count': product_count,
                'allocation_percentage': allocation_percentage,
                'total_sales': total_sales,
                'avg_sales_per_product': avg_sales,
                'assigned_rows': category_info.get('rows', []),
                'row_count': len(category_info.get('rows', [])),
                'priority_multiplier': category_info.get('priority', 1.0),
                'description': category_info.get('description', category.title()),
                'top_brands': dict(brand_counts.most_common(3)),
                'model_distribution': dict(model_counts.most_common()),
                'top_products': [
                    {
                        'name': p['product_name'][:40] + '...' if len(p['product_name']) > 40 else p['product_name'],
                        'brand': p['brand'],
                        'model': p['ipad_model'],
                        'sales': p['frequency']
                    }
                    for p in sorted(products_list, key=lambda x: x['frequency'], reverse=True)[:5]
                ],
                'products_per_row': self._calculate_products_per_row(product_count, len(category_info.get('rows', [1]))),
                'space_requirements': self._calculate_category_space_requirements(category, products_list)
            }
        
        return allocation_strategy
    
    def _calculate_products_per_row(self, total_products: int, row_count: int) -> int:
        """Calculate how many products should be placed per row for a category"""
        if row_count == 0:
            return 0
        
        # Distribute products evenly across available rows
        products_per_row = max(1, total_products // row_count)
        
        # Cap at 6 products per row (grid width)
        return min(products_per_row, 6)
    
    def _calculate_category_space_requirements(self, category: str, products: List[Dict]) -> Dict:
        """Calculate space requirements for a category"""
        if not products:
            return {'total_width_cm': 0, 'total_height_cm': 0, 'rows_needed': 0}
        
        # Get category info
        category_key = category.rstrip('s')  # Remove plural 's'
        if category == 'keyboard_cases':
            category_key = 'keyboard case'
        
        category_info = self.categories.get(category_key, {})
        assigned_rows = category_info.get('rows', [7])
        
        # Calculate average dimensions for this category
        widths = [p['width'] for p in products]
        heights = [p['height'] for p in products]
        depths = [p['depth'] for p in products]
        
        avg_width = sum(widths) / len(widths)
        avg_height = sum(heights) / len(heights)
        avg_depth = sum(depths) / len(depths)
        
        # Calculate space requirements
        products_per_row = min(6, len(products) // len(assigned_rows)) if assigned_rows else 6
        
        # Add spacing (2cm between products)
        total_width = (avg_width + 2.0) * min(6, products_per_row)
        total_height = (avg_height + 2.0) * len(assigned_rows)
        
        return {
            'total_width_cm': total_width,
            'total_height_cm': total_height,
            'rows_needed': len(assigned_rows),
            'products_per_row': products_per_row,
            'avg_product_size': (avg_width, avg_height, avg_depth),
            'space_efficiency': min(1.0, len(products) / (6 * len(assigned_rows)))
        }
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics of loaded iPad data"""
        products = self.load_ipad_data()
        
        if not products:
            return {'error': 'No data loaded'}
        
        # Calculate statistics
        total_products = len(products)
        total_sales = sum(p['frequency'] for p in products)
        
        # Brand distribution
        brand_counts = Counter(p['brand'] for p in products)
        
        # Category distribution
        category_counts = Counter(p['category'] for p in products)
        
        # iPad model distribution
        model_counts = Counter(p['ipad_model'] for p in products)
        
        # Top selling products
        top_products = sorted(products, key=lambda p: p['frequency'], reverse=True)[:10]
        
        # Dimension analysis
        widths = [p['width'] for p in products]
        heights = [p['height'] for p in products]
        
        return {
            'total_products': total_products,
            'total_sales': total_sales,
            'average_sales': total_sales / total_products if total_products > 0 else 0,
            'brand_distribution': dict(brand_counts.most_common()),
            'category_distribution': dict(category_counts.most_common()),
            'model_distribution': dict(model_counts.most_common()),
            'top_products': [
                {
                    'name': p['product_name'][:50] + '...' if len(p['product_name']) > 50 else p['product_name'],
                    'brand': p['brand'],
                    'model': p['ipad_model'],
                    'category': p['category'],
                    'sales': p['frequency']
                }
                for p in top_products
            ],
            'dimensions': {
                'width_range': (min(widths), max(widths)),
                'height_range': (min(heights), max(heights)),
                'average_width': sum(widths) / len(widths),
                'average_height': sum(heights) / len(heights)
            }
        }
    
    def get_category_priority_ranking(self) -> List[Tuple[str, Dict]]:
        """Get categories ranked by priority for planogram placement"""
        allocation = self.get_category_allocation_strategy()
        
        # Calculate composite priority score
        priority_ranking = []
        for category, info in allocation.items():
            # Composite score based on sales performance, product count, and category priority
            sales_score = info['total_sales'] / 1000  # Normalize sales
            count_score = info['product_count'] / 10   # Normalize product count
            priority_score = info['priority_multiplier']
            
            composite_score = (sales_score * 0.4) + (count_score * 0.3) + (priority_score * 0.3)
            
            priority_ranking.append((category, {
                'composite_score': composite_score,
                'sales_contribution': info['total_sales'],
                'product_count': info['product_count'],
                'priority_multiplier': info['priority_multiplier'],
                'assigned_rows': info['assigned_rows'],
                'description': info['description']
            }))
        
        # Sort by composite score (highest first)
        priority_ranking.sort(key=lambda x: x[1]['composite_score'], reverse=True)
        
        return priority_ranking
    
    def optimize_category_placement(self, products: List[Dict]) -> Dict[str, List[Dict]]:
        """Optimize product placement within categories based on sales and brand"""
        category_groups = self.organize_products_by_category(products)
        optimized_groups = {}
        
        for category, products_list in category_groups.items():
            if not products_list:
                optimized_groups[category] = []
                continue
            
            # Sort by multiple criteria for optimal placement
            def placement_score(product):
                score = product['priority_score']
                
                # Boost Apple products for premium positioning
                if product['brand'].lower() == 'apple':
                    score *= 1.3
                
                # Boost high-volume Gripp products
                elif product['brand'].lower() == 'gripp':
                    score *= 1.2
                
                # Boost keyboard cases (productivity premium)
                if category == 'keyboard_cases':
                    score *= 1.5
                
                # Boost folios (premium category)
                elif category == 'folios':
                    score *= 1.2
                
                return score
            
            # Sort by placement score
            optimized_products = sorted(products_list, key=placement_score, reverse=True)
            
            # Apply category-specific organization
            if category == 'cases':
                # For cases: prioritize by iPad model and brand
                optimized_products = self._organize_cases_by_model_and_brand(optimized_products)
            elif category == 'folios':
                # For folios: prioritize Apple products first
                optimized_products = self._organize_folios_by_premium_first(optimized_products)
            elif category == 'keyboard_cases':
                # For keyboards: prioritize by productivity value
                optimized_products = self._organize_keyboards_by_productivity(optimized_products)
            
            optimized_groups[category] = optimized_products
        
        return optimized_groups
    
    def _organize_cases_by_model_and_brand(self, products: List[Dict]) -> List[Dict]:
        """Organize cases by iPad model and brand priority"""
        # Group by iPad model first
        model_groups = defaultdict(list)
        for product in products:
            model_groups[product['ipad_model']].append(product)
        
        # Sort each model group by brand priority (Apple > Gripp > Others)
        organized = []
        model_priority = ['iPad Air', 'iPad Pro', 'iPad Base', 'iPad Pro 12.9', 'iPad Mini']
        
        for model in model_priority:
            if model in model_groups:
                model_products = model_groups[model]
                
                # Sort by brand priority within model
                apple_products = [p for p in model_products if p['brand'].lower() == 'apple']
                gripp_products = [p for p in model_products if p['brand'].lower() == 'gripp']
                other_products = [p for p in model_products if p['brand'].lower() not in ['apple', 'gripp']]
                
                # Sort each brand group by sales
                apple_products.sort(key=lambda p: p['frequency'], reverse=True)
                gripp_products.sort(key=lambda p: p['frequency'], reverse=True)
                other_products.sort(key=lambda p: p['frequency'], reverse=True)
                
                organized.extend(apple_products + gripp_products + other_products)
        
        return organized
    
    def _organize_folios_by_premium_first(self, products: List[Dict]) -> List[Dict]:
        """Organize folios with Apple premium products first"""
        apple_products = [p for p in products if p['brand'].lower() == 'apple']
        other_products = [p for p in products if p['brand'].lower() != 'apple']
        
        # Sort each group by sales
        apple_products.sort(key=lambda p: p['frequency'], reverse=True)
        other_products.sort(key=lambda p: p['frequency'], reverse=True)
        
        return apple_products + other_products
    
    def _organize_keyboards_by_productivity(self, products: List[Dict]) -> List[Dict]:
        """Organize keyboard cases by productivity value (Apple Magic Keyboards first)"""
        magic_keyboards = [p for p in products if 'magic keyboard' in p['product_name'].lower()]
        other_keyboards = [p for p in products if 'magic keyboard' not in p['product_name'].lower()]
        
        # Sort each group by sales
        magic_keyboards.sort(key=lambda p: p['frequency'], reverse=True)
        other_keyboards.sort(key=lambda p: p['frequency'], reverse=True)
        
        return magic_keyboards + other_keyboards
    
    def calculate_product_dimensions(self, product: Dict) -> Tuple[float, float, float]:
        """
        Calculate display dimensions based on actual product size and iPad model
        Returns: (display_width, display_height, spacing_needed)
        """
        # Get base dimensions from product data
        base_width = product.get('width', 25.0)
        base_height = product.get('height', 17.8)
        base_depth = product.get('depth', 0.75)
        
        # Apply iPad model-specific adjustments
        ipad_model = product.get('ipad_model', 'iPad Base')
        
        # iPad Pro 12.9" accessories are 20% larger
        if ipad_model == 'iPad Pro 12.9':
            display_width = base_width * 1.2
            display_height = base_height * 1.2
            spacing_multiplier = 1.2
        # iPad Mini accessories are smaller
        elif ipad_model == 'iPad Mini':
            display_width = base_width * 0.8
            display_height = base_height * 0.8
            spacing_multiplier = 0.9
        else:
            display_width = base_width
            display_height = base_height
            spacing_multiplier = 1.0
        
        # Apply category-specific adjustments
        category = product.get('category', 'case')
        
        # Keyboard cases need 2x depth accommodation
        if category == 'keyboard case':
            depth_multiplier = 2.0
            # Keyboard cases also need more visual space
            display_width *= 1.1
            display_height *= 1.1
            spacing_multiplier *= 1.3  # More spacing for thick products
        else:
            depth_multiplier = 1.0
        
        # Calculate final depth
        final_depth = base_depth * depth_multiplier
        
        # Calculate spacing needed (includes product + buffer space)
        spacing_needed = max(2.0, (display_width + display_height) / 20) * spacing_multiplier
        
        return (display_width, display_height, spacing_needed)
    
    def calculate_grid_layout_dimensions(self, products: List[Dict], grid_size: Tuple[int, int]) -> Dict:
        """
        Calculate realistic grid layout dimensions based on actual product sizes
        Returns comprehensive layout specifications for shelf implementation
        """
        rows, cols = grid_size
        
        # Calculate dimensions for each grid position
        position_dimensions = {}
        row_heights = [0.0] * rows
        col_widths = [0.0] * cols
        
        # Process each product to determine space requirements
        for product in products:
            if 'grid_position' not in product or product['grid_position'] is None:
                continue
                
            row, col = product['grid_position']
            if row >= rows or col >= cols:
                continue
            
            display_width, display_height, spacing = self.calculate_product_dimensions(product)
            
            # Update maximum dimensions for this row/column
            row_heights[row] = max(row_heights[row], display_height + spacing)
            col_widths[col] = max(col_widths[col], display_width + spacing)
            
            position_dimensions[(row, col)] = {
                'width': display_width,
                'height': display_height,
                'spacing': spacing,
                'product': product['product_name'][:30] + '...' if len(product['product_name']) > 30 else product['product_name'],
                'category': product.get('category', 'case'),
                'ipad_model': product.get('ipad_model', 'iPad Base')
            }
        
        # Calculate total grid dimensions
        total_width = sum(col_widths)
        total_height = sum(row_heights)
        
        # Calculate category-specific row allocations
        category_rows = self._calculate_category_row_dimensions(products, row_heights)
        
        # Calculate model-specific column allocations
        model_columns = self._calculate_model_column_dimensions(products, col_widths)
        
        return {
            'grid_size': grid_size,
            'total_dimensions': {
                'width_cm': total_width,
                'height_cm': total_height,
                'width_inches': total_width / 2.54,
                'height_inches': total_height / 2.54
            },
            'row_heights': row_heights,
            'col_widths': col_widths,
            'position_dimensions': position_dimensions,
            'category_allocations': category_rows,
            'model_allocations': model_columns,
            'shelf_specifications': self._generate_shelf_specifications(row_heights, col_widths),
            'spacing_requirements': self._calculate_spacing_requirements(products)
        }
    
    def _calculate_category_row_dimensions(self, products: List[Dict], row_heights: List[float]) -> Dict:
        """Calculate space requirements for each category's assigned rows"""
        category_allocations = {}
        
        for category, info in self.categories.items():
            assigned_rows = info.get('rows', [])
            if not assigned_rows:
                continue
            
            # Calculate total height for this category
            total_height = sum(row_heights[row] for row in assigned_rows if row < len(row_heights))
            
            # Count products in this category
            category_products = [p for p in products if p.get('category') == category]
            
            # Calculate average product dimensions for this category
            if category_products:
                avg_width = sum(self.calculate_product_dimensions(p)[0] for p in category_products) / len(category_products)
                avg_height = sum(self.calculate_product_dimensions(p)[1] for p in category_products) / len(category_products)
                avg_spacing = sum(self.calculate_product_dimensions(p)[2] for p in category_products) / len(category_products)
            else:
                avg_width = avg_height = avg_spacing = 0.0
            
            category_allocations[category] = {
                'assigned_rows': assigned_rows,
                'row_count': len(assigned_rows),
                'total_height_cm': total_height,
                'avg_product_width': avg_width,
                'avg_product_height': avg_height,
                'avg_spacing': avg_spacing,
                'product_count': len(category_products),
                'products_per_row': len(category_products) / len(assigned_rows) if assigned_rows else 0,
                'description': info.get('description', category.title())
            }
        
        return category_allocations
    
    def _calculate_model_column_dimensions(self, products: List[Dict], col_widths: List[float]) -> Dict:
        """Calculate space requirements for each iPad model's assigned columns"""
        model_allocations = {}
        
        for model, info in self.ipad_models.items():
            assigned_columns = info.get('columns', [])
            if not assigned_columns:
                continue
            
            # Calculate total width for this model
            total_width = sum(col_widths[col] for col in assigned_columns if col < len(col_widths))
            
            # Count products for this model
            model_products = [p for p in products if p.get('ipad_model') == model]
            
            # Calculate average product dimensions for this model
            if model_products:
                avg_width = sum(self.calculate_product_dimensions(p)[0] for p in model_products) / len(model_products)
                avg_height = sum(self.calculate_product_dimensions(p)[1] for p in model_products) / len(model_products)
                avg_spacing = sum(self.calculate_product_dimensions(p)[2] for p in model_products) / len(model_products)
            else:
                avg_width = avg_height = avg_spacing = 0.0
            
            model_allocations[model] = {
                'assigned_columns': assigned_columns,
                'column_count': len(assigned_columns),
                'total_width_cm': total_width,
                'avg_product_width': avg_width,
                'avg_product_height': avg_height,
                'avg_spacing': avg_spacing,
                'product_count': len(model_products),
                'products_per_column': len(model_products) / len(assigned_columns) if assigned_columns else 0,
                'display_size': info.get('display_size', 'Unknown'),
                'base_dimensions': info.get('dimensions', (25.0, 17.8, 0.75))
            }
        
        return model_allocations
    
    def _generate_shelf_specifications(self, row_heights: List[float], col_widths: List[float]) -> Dict:
        """Generate detailed shelf specifications for physical implementation"""
        
        # Calculate shelf depths needed for different product types
        standard_depth = 3.0  # cm - standard case depth
        keyboard_depth = 6.0  # cm - keyboard case depth (2x standard)
        folio_depth = 2.5     # cm - folio depth (thinner than cases)
        
        # Calculate weight considerations
        weight_specs = {
            'keyboard_cases': {'max_weight_per_product': 1.5, 'shelf_load_rating': 'heavy_duty'},  # kg
            'cases': {'max_weight_per_product': 0.3, 'shelf_load_rating': 'standard'},
            'folios': {'max_weight_per_product': 0.2, 'shelf_load_rating': 'light'},
            'specialty': {'max_weight_per_product': 0.5, 'shelf_load_rating': 'standard'}
        }
        
        # Generate shelf specifications by row
        shelf_specs = {}
        for row_idx, height in enumerate(row_heights):
            # Determine primary category for this row
            primary_category = self._get_primary_category_for_row(row_idx)
            
            # Set depth based on category
            if primary_category == 'keyboard case':
                shelf_depth = keyboard_depth
                load_rating = 'heavy_duty'
                mounting = 'reinforced'  # Keyboard cases need stronger mounting
            elif primary_category == 'folio':
                shelf_depth = folio_depth
                load_rating = 'light'
                mounting = 'standard'
            else:
                shelf_depth = standard_depth
                load_rating = 'standard'
                mounting = 'standard'
            
            shelf_specs[f'row_{row_idx}'] = {
                'height_cm': height,
                'depth_cm': shelf_depth,
                'width_cm': sum(col_widths),
                'primary_category': primary_category,
                'load_rating': load_rating,
                'mounting_type': mounting,
                'recommended_material': 'tempered_glass' if primary_category == 'folio' else 'metal_mesh',
                'weight_capacity_kg': weight_specs.get(primary_category, {}).get('max_weight_per_product', 0.3) * len(col_widths),
                'accessibility': 'eye_level' if 2 <= row_idx <= 5 else 'standard'
            }
        
        return shelf_specs
    
    def _get_primary_category_for_row(self, row_idx: int) -> str:
        """Determine the primary category assigned to a specific row"""
        for category, info in self.categories.items():
            if row_idx in info.get('rows', []):
                return category
        return 'case'  # Default fallback
    
    def _calculate_spacing_requirements(self, products: List[Dict]) -> Dict:
        """Calculate comprehensive spacing requirements for the layout"""
        
        # Analyze spacing needs by category and model
        spacing_analysis = {
            'horizontal_spacing': {},
            'vertical_spacing': {},
            'category_buffers': {},
            'model_transitions': {}
        }
        
        # Calculate horizontal spacing between columns
        for col in range(6):  # 6 columns in 8x6 grid
            col_products = [p for p in products if p.get('grid_position') is not None and p.get('grid_position')[1] == col]
            if col_products:
                max_width = max(self.calculate_product_dimensions(p)[0] for p in col_products)
                avg_spacing = sum(self.calculate_product_dimensions(p)[2] for p in col_products) / len(col_products)
                
                spacing_analysis['horizontal_spacing'][f'column_{col}'] = {
                    'max_product_width': max_width,
                    'recommended_spacing': avg_spacing,
                    'buffer_space': max_width * 0.1  # 10% buffer
                }
        
        # Calculate vertical spacing between rows
        for row in range(8):  # 8 rows in 8x6 grid
            row_products = [p for p in products if p.get('grid_position') is not None and p.get('grid_position')[0] == row]
            if row_products:
                max_height = max(self.calculate_product_dimensions(p)[1] for p in row_products)
                avg_spacing = sum(self.calculate_product_dimensions(p)[2] for p in row_products) / len(row_products)
                
                spacing_analysis['vertical_spacing'][f'row_{row}'] = {
                    'max_product_height': max_height,
                    'recommended_spacing': avg_spacing,
                    'buffer_space': max_height * 0.1  # 10% buffer
                }
        
        # Calculate category transition buffers
        category_transitions = [
            (2, 3, 'cases_to_folios'),      # Between cases and folios
            (4, 5, 'folios_to_keyboards'),  # Between folios and keyboards
            (6, 7, 'keyboards_to_specialty') # Between keyboards and specialty
        ]
        
        for row1, row2, transition_name in category_transitions:
            spacing_analysis['category_buffers'][transition_name] = {
                'between_rows': (row1, row2),
                'recommended_buffer_cm': 1.5,  # Extra space between categories
                'visual_separator': True,
                'description': f'Buffer between {transition_name.replace("_", " ")}'
            }
        
        # Calculate model transition spacing
        model_transitions = [
            (0, 1, 'mini_to_base'),
            (1, 2, 'base_to_air'),
            (3, 4, 'air_to_pro'),
            (4, 5, 'pro_to_pro_12_9')
        ]
        
        for col1, col2, transition_name in model_transitions:
            spacing_analysis['model_transitions'][transition_name] = {
                'between_columns': (col1, col2),
                'recommended_buffer_cm': 1.0,  # Moderate space between models
                'visual_separator': False,
                'description': f'Transition between {transition_name.replace("_", " ")}'
            }
        
        return spacing_analysis
    
    def apply_dimension_aware_positioning(self, products: List[Dict], grid_size: Tuple[int, int]) -> List[Dict]:
        """
        Apply dimension-aware positioning to products based on their physical characteristics
        Returns products with optimized grid positions considering size constraints
        """
        rows, cols = grid_size
        positioned_products = []
        
        # Create grid availability matrix
        grid_available = [[True for _ in range(cols)] for _ in range(rows)]
        
        # Sort products by priority and size requirements
        sorted_products = sorted(products, key=lambda p: (
            -p.get('priority_score', 0),  # Higher priority first
            -self.calculate_product_dimensions(p)[0],  # Larger products first
            -p.get('frequency', 0)  # Higher sales first
        ))
        
        for product in sorted_products:
            # Calculate product dimensions
            width, height, spacing = self.calculate_product_dimensions(product)
            
            # Determine preferred placement based on category and model
            preferred_positions = self._get_preferred_positions(product, grid_size)
            
            # Find best available position
            best_position = self._find_best_position(
                product, preferred_positions, grid_available, grid_size
            )
            
            if best_position:
                row, col = best_position
                product['grid_position'] = (row, col)
                product['display_width'] = width
                product['display_height'] = height
                product['spacing_needed'] = spacing
                
                # Mark position as occupied
                grid_available[row][col] = False
                
                # Mark adjacent positions if product needs extra space
                if spacing > 2.5:  # Large spacing requirement
                    self._mark_adjacent_positions(grid_available, row, col, rows, cols)
                
                positioned_products.append(product)
            else:
                # Product couldn't be placed - add to overflow
                product['grid_position'] = None
                product['placement_status'] = 'overflow'
                positioned_products.append(product)
        
        return positioned_products
    
    def _get_preferred_positions(self, product: Dict, grid_size: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get preferred grid positions for a product based on its characteristics"""
        rows, cols = grid_size
        preferred = []
        
        # Get category preferences
        category = product.get('category', 'case')
        category_rows = self.categories.get(category, {}).get('rows', [0, 1, 2])
        
        # Get model preferences
        ipad_model = product.get('ipad_model', 'iPad Base')
        model_columns = self.ipad_models.get(ipad_model, {}).get('columns', [1, 2])
        
        # Generate preferred positions (category rows × model columns)
        for row in category_rows:
            for col in model_columns:
                if 0 <= row < rows and 0 <= col < cols:
                    preferred.append((row, col))
        
        # Sort by priority (eye-level positions first for premium products)
        brand = product.get('brand', '').lower()
        frequency = product.get('frequency', 0)
        
        def position_priority(pos):
            row, col = pos
            score = 0
            
            # Eye-level preference (rows 2-5)
            if 2 <= row <= 5:
                score += 10
            
            # Apple products prefer premium positions
            if brand == 'apple' and row <= 4:
                score += 5
            
            # High-sales products prefer visible positions
            if frequency > 50 and row <= 5:
                score += 3
            
            # Keyboard cases prefer lower rows (stability)
            if category == 'keyboard case' and row >= 5:
                score += 8
            
            # Left-to-right preference for better visibility
            score += (cols - col)
            
            return score
        
        preferred.sort(key=position_priority, reverse=True)
        return preferred
    
    def _find_best_position(self, product: Dict, preferred_positions: List[Tuple[int, int]], 
                           grid_available: List[List[bool]], grid_size: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find the best available position for a product"""
        
        # Try preferred positions first
        for pos in preferred_positions:
            row, col = pos
            if grid_available[row][col]:
                # Check if position meets size requirements
                if self._position_meets_size_requirements(product, pos, grid_available, grid_size):
                    return pos
        
        # If no preferred position available, try any available position
        rows, cols = grid_size
        for row in range(rows):
            for col in range(cols):
                if grid_available[row][col]:
                    if self._position_meets_size_requirements(product, (row, col), grid_available, grid_size):
                        return (row, col)
        
        return None  # No suitable position found
    
    def _position_meets_size_requirements(self, product: Dict, position: Tuple[int, int], 
                                        grid_available: List[List[bool]], grid_size: Tuple[int, int]) -> bool:
        """Check if a position meets the size requirements for a product"""
        row, col = position
        rows, cols = grid_size
        
        # Calculate space requirements
        width, height, spacing = self.calculate_product_dimensions(product)
        
        # Check if product needs extra space (large iPad Pro 12.9" or keyboard cases)
        needs_extra_space = (
            product.get('ipad_model') == 'iPad Pro 12.9' or 
            product.get('category') == 'keyboard case' or
            spacing > 2.5
        )
        
        if needs_extra_space:
            # Check adjacent positions are available
            adjacent_positions = [
                (row-1, col), (row+1, col),  # Above and below
                (row, col-1), (row, col+1)   # Left and right
            ]
            
            for adj_row, adj_col in adjacent_positions:
                if 0 <= adj_row < rows and 0 <= adj_col < cols:
                    if not grid_available[adj_row][adj_col]:
                        return False  # Adjacent position occupied
        
        return True
    
    def _mark_adjacent_positions(self, grid_available: List[List[bool]], row: int, col: int, rows: int, cols: int):
        """Mark adjacent positions as occupied for large products"""
        adjacent_positions = [
            (row-1, col), (row+1, col),  # Above and below
            (row, col-1), (row, col+1)   # Left and right
        ]
        
        for adj_row, adj_col in adjacent_positions:
            if 0 <= adj_row < rows and 0 <= adj_col < cols:
                grid_available[adj_row][adj_col] = False
    
    def implement_brand_allocation_strategy(self, products: List[Dict], grid_capacity: int = 48) -> Dict[str, List[Dict]]:
        """
        Implement 40% Apple, 35% Gripp, 25% other brands allocation strategy
        Returns organized products by brand with premium positioning
        """
        # Calculate target allocations
        apple_target = int(grid_capacity * 0.40)  # 40% = ~19 products
        gripp_target = int(grid_capacity * 0.35)  # 35% = ~17 products  
        other_target = grid_capacity - apple_target - gripp_target  # 25% = ~12 products
        
        # Separate products by brand
        apple_products = [p for p in products if p.get('brand', '').lower() == 'apple']
        gripp_products = [p for p in products if p.get('brand', '').lower() == 'gripp']
        other_products = [p for p in products if p.get('brand', '').lower() not in ['apple', 'gripp']]
        
        # Sort each brand group by priority score (highest first)
        apple_products.sort(key=lambda p: p.get('priority_score', 0), reverse=True)
        gripp_products.sort(key=lambda p: p.get('priority_score', 0), reverse=True)
        other_products.sort(key=lambda p: p.get('priority_score', 0), reverse=True)
        
        # Apply brand-specific organization
        organized_apple = self._organize_apple_products_with_colors(apple_products[:apple_target])
        organized_gripp = self._organize_gripp_products_by_series(gripp_products[:gripp_target])
        organized_others = self._organize_other_brands_with_diversity(other_products[:other_target])
        
        # Calculate actual allocations
        actual_apple = len(organized_apple)
        actual_gripp = len(organized_gripp)
        actual_others = len(organized_others)
        
        allocation_result = {
            'apple_products': organized_apple,
            'gripp_products': organized_gripp,
            'other_products': organized_others,
            'allocation_summary': {
                'target_allocation': {
                    'apple': apple_target,
                    'gripp': gripp_target,
                    'others': other_target
                },
                'actual_allocation': {
                    'apple': actual_apple,
                    'gripp': actual_gripp,
                    'others': actual_others
                },
                'allocation_percentages': {
                    'apple': (actual_apple / grid_capacity) * 100,
                    'gripp': (actual_gripp / grid_capacity) * 100,
                    'others': (actual_others / grid_capacity) * 100
                },
                'total_products': actual_apple + actual_gripp + actual_others,
                'grid_utilization': ((actual_apple + actual_gripp + actual_others) / grid_capacity) * 100
            }
        }
        
        return allocation_result
    
    def _organize_apple_products_with_colors(self, apple_products: List[Dict]) -> List[Dict]:
        """
        Organize Apple products with premium positioning and accurate color extraction
        """
        # Extract and enhance Apple product colors
        enhanced_apple_products = []
        
        for product in apple_products:
            enhanced_product = product.copy()
            
            # Extract Apple-specific colors
            apple_color = self._extract_apple_product_colors(product['product_name'], product.get('subcategory', ''))
            enhanced_product['apple_color'] = apple_color
            enhanced_product['premium_positioning'] = True
            
            # Boost priority for premium Apple products
            if apple_color in ['Electric Orange', 'Mallard Green', 'Dark Cherry', 'English Lavender']:
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.2
            
            # Special handling for Magic Keyboard products
            if 'magic keyboard' in product['product_name'].lower():
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.5
                enhanced_product['productivity_premium'] = True
            
            enhanced_apple_products.append(enhanced_product)
        
        # Sort by enhanced priority (premium colors and productivity first)
        enhanced_apple_products.sort(key=lambda p: p.get('priority_score', 0), reverse=True)
        
        # Group by category for premium positioning
        apple_by_category = defaultdict(list)
        for product in enhanced_apple_products:
            category = product.get('category', 'case')
            apple_by_category[category].append(product)
        
        # Prioritize categories: folios (premium) > keyboard cases (productivity) > cases
        category_priority = ['folio', 'keyboard case', 'case', 'armor case', 'hardshell']
        organized_apple = []
        
        for category in category_priority:
            if category in apple_by_category:
                organized_apple.extend(apple_by_category[category])
        
        return organized_apple
    
    def _extract_apple_product_colors(self, product_name: str, subcategory: str) -> str:
        """
        Extract accurate Apple product colors from product names and subcategories
        """
        combined_text = f"{product_name} {subcategory}".lower()
        
        # Apple's official iPad accessory colors (2024)
        apple_colors = {
            'black': 'Black',
            'white': 'White', 
            'electric orange': 'Electric Orange',
            'mallard green': 'Mallard Green',
            'dark cherry': 'Dark Cherry',
            'english lavender': 'English Lavender',
            'denim': 'Denim',
            'charcoal gray': 'Charcoal Gray',
            'charcoal grey': 'Charcoal Gray',
            'light violet': 'Light Violet',
            'sage': 'Sage',
            'marine blue': 'Marine Blue',
            'papaya': 'Papaya',
            'lemon zest': 'Lemon Zest',
            'watermelon': 'Watermelon',
            'cantaloupe': 'Cantaloupe',
            'sky blue': 'Sky Blue',
            'pink': 'Pink',
            'purple': 'Purple',
            'blue': 'Blue',
            'green': 'Green',
            'orange': 'Orange',
            'red': 'Red',
            'yellow': 'Yellow'
        }
        
        # Check for exact color matches (prioritize longer/more specific matches)
        sorted_colors = sorted(apple_colors.keys(), key=len, reverse=True)
        
        for color_key in sorted_colors:
            if color_key in combined_text:
                return apple_colors[color_key]
        
        # Fallback to generic color detection
        if 'zml' in combined_text:  # Apple's internal color codes
            return 'Premium Color'
        
        return 'Standard'
    
    def _organize_gripp_products_by_series(self, gripp_products: List[Dict]) -> List[Dict]:
        """
        Organize Gripp products by series (Ultra, Melon, Styleus) with volume-based prioritization
        """
        # Group Gripp products by series
        gripp_series = {
            'Ultra': [],    # Premium series (150-220 sales)
            'Melon': [],    # Mid-range series (65-151 sales)
            'Styleus': [],  # Fashion series (35-69 sales)
            'Armor': [],    # Heavy-duty series (21-51 sales)
            'Other': []     # Other Gripp products
        }
        
        for product in gripp_products:
            product_name = product['product_name'].lower()
            series_identified = False
            
            # Identify series from product name
            for series_name in ['ultra', 'melon', 'styleus', 'armor']:
                if series_name in product_name:
                    series_key = series_name.title()
                    gripp_series[series_key].append(product)
                    
                    # Add series information to product
                    enhanced_product = product.copy()
                    enhanced_product['gripp_series'] = series_key
                    enhanced_product['volume_leader'] = True
                    
                    # Apply series-specific priority boosts
                    if series_name == 'ultra':
                        enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.3
                    elif series_name == 'melon':
                        enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.2
                    elif series_name == 'styleus':
                        enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.1
                    
                    gripp_series[series_key][-1] = enhanced_product
                    series_identified = True
                    break
            
            if not series_identified:
                gripp_series['Other'].append(product)
        
        # Sort each series by sales frequency
        for series in gripp_series.values():
            series.sort(key=lambda p: p.get('frequency', 0), reverse=True)
        
        # Organize by series priority: Ultra > Melon > Styleus > Armor > Other
        organized_gripp = []
        series_priority = ['Ultra', 'Melon', 'Styleus', 'Armor', 'Other']
        
        for series_name in series_priority:
            organized_gripp.extend(gripp_series[series_name])
        
        return organized_gripp
    
    def _organize_other_brands_with_diversity(self, other_products: List[Dict]) -> List[Dict]:
        """
        Organize other brands (STM, Logitech, Tucano, etc.) with visual diversity
        """
        # Group by brand for diversity
        brands_groups = defaultdict(list)
        for product in other_products:
            brand = product.get('brand', 'Default')
            brands_groups[brand].append(product)
        
        # Sort each brand group by priority
        for brand_products in brands_groups.values():
            brand_products.sort(key=lambda p: p.get('priority_score', 0), reverse=True)
        
        # Apply brand-specific enhancements
        enhanced_other_products = []
        
        for brand, products in brands_groups.items():
            for product in products:
                enhanced_product = product.copy()
                enhanced_product['brand_category'] = self._categorize_other_brand(brand)
                
                # Apply brand-specific priority adjustments
                if brand.lower() in ['stm', 'logitech']:
                    enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.1
                    enhanced_product['professional_brand'] = True
                elif brand.lower() in ['tucano', 'tomtoc']:
                    enhanced_product['fashion_brand'] = True
                
                enhanced_other_products.append(enhanced_product)
        
        # Distribute brands for visual diversity (avoid clustering same brands)
        organized_others = self._distribute_brands_for_diversity(enhanced_other_products)
        
        return organized_others
    
    def _categorize_other_brand(self, brand: str) -> str:
        """Categorize other brands by their market positioning"""
        brand_categories = {
            'stm': 'Professional',
            'logitech': 'Productivity', 
            'tucano': 'Fashion',
            'tomtoc': 'Minimalist',
            'dbramante1928': 'Premium',
            'muvtech': 'Specialty',
            'xtrememac': 'Specialty'
        }
        
        return brand_categories.get(brand.lower(), 'Standard')
    
    def _distribute_brands_for_diversity(self, products: List[Dict]) -> List[Dict]:
        """
        Distribute products to avoid brand clustering and ensure visual diversity
        """
        if len(products) <= 1:
            return products
        
        # Group by brand
        brand_groups = defaultdict(list)
        for product in products:
            brand = product.get('brand', 'Default')
            brand_groups[brand].append(product)
        
        # Create distributed list
        distributed = []
        brand_iterators = {brand: iter(products) for brand, products in brand_groups.items()}
        brands_cycle = cycle(brand_groups.keys())
        
        total_products = len(products)
        placed_products = 0
        
        while placed_products < total_products:
            current_brand = next(brands_cycle)
            
            try:
                next_product = next(brand_iterators[current_brand])
                distributed.append(next_product)
                placed_products += 1
            except StopIteration:
                # This brand is exhausted, remove from cycle
                brand_iterators.pop(current_brand)
                if not brand_iterators:
                    break
                brands_cycle = cycle(brand_iterators.keys())
        
        return distributed
    
    def apply_premium_positioning_strategy(self, allocated_products: Dict[str, List[Dict]], grid_size: Tuple[int, int]) -> List[Dict]:
        """
        Apply premium positioning strategy with Apple products in prime locations
        """
        rows, cols = grid_size
        positioned_products = []
        
        # Create premium position matrix (eye-level and high-visibility positions)
        premium_positions = self._identify_premium_positions(grid_size)
        standard_positions = self._identify_standard_positions(grid_size)
        
        # Track position availability
        position_availability = {pos: True for pos in premium_positions + standard_positions}
        
        # Phase 1: Place Apple products in premium positions
        apple_products = allocated_products.get('apple_products', [])
        for product in apple_products:
            best_position = self._find_premium_position_for_apple(
                product, premium_positions, position_availability, grid_size
            )
            
            if best_position:
                product['grid_position'] = best_position
                product['positioning_tier'] = 'premium'
                position_availability[best_position] = False
                positioned_products.append(product)
        
        # Phase 2: Place Gripp products in high-visibility positions
        gripp_products = allocated_products.get('gripp_products', [])
        available_positions = [pos for pos, available in position_availability.items() if available]
        
        for product in gripp_products:
            best_position = self._find_volume_position_for_gripp(
                product, available_positions, position_availability, grid_size
            )
            
            if best_position:
                product['grid_position'] = best_position
                product['positioning_tier'] = 'volume'
                position_availability[best_position] = False
                positioned_products.append(product)
        
        # Phase 3: Place other brands in remaining positions
        other_products = allocated_products.get('other_products', [])
        available_positions = [pos for pos, available in position_availability.items() if available]
        
        for product in other_products:
            if available_positions:
                # Choose position based on product characteristics
                best_position = self._find_diversity_position_for_others(
                    product, available_positions, position_availability, grid_size
                )
                
                if best_position:
                    product['grid_position'] = best_position
                    product['positioning_tier'] = 'standard'
                    position_availability[best_position] = False
                    positioned_products.append(product)
            else:
                # No positions available - mark as overflow
                product['grid_position'] = None
                product['positioning_tier'] = 'overflow'
                positioned_products.append(product)
        
        return positioned_products
    
    def _identify_premium_positions(self, grid_size: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Identify premium positions for Apple products (eye-level, high visibility)"""
        rows, cols = grid_size
        premium_positions = []
        
        # Eye-level rows (2-5) with left-to-right preference
        eye_level_rows = [2, 3, 4, 5]
        
        for row in eye_level_rows:
            for col in range(cols):
                # Left side gets higher priority (better visibility)
                premium_positions.append((row, col))
        
        # Sort by visibility priority (left columns first, middle rows first)
        premium_positions.sort(key=lambda pos: (abs(pos[0] - 3.5), pos[1]))
        
        return premium_positions
    
    def _identify_standard_positions(self, grid_size: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Identify standard positions for non-premium products"""
        rows, cols = grid_size
        standard_positions = []
        
        # All positions not in premium tier
        premium_positions = set(self._identify_premium_positions(grid_size))
        
        for row in range(rows):
            for col in range(cols):
                if (row, col) not in premium_positions:
                    standard_positions.append((row, col))
        
        return standard_positions
    
    def _find_premium_position_for_apple(self, product: Dict, premium_positions: List[Tuple[int, int]], 
                                       position_availability: Dict, grid_size: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find the best premium position for an Apple product"""
        
        # Get product preferences
        category = product.get('category', 'case')
        ipad_model = product.get('ipad_model', 'iPad Base')
        
        # Filter positions by category and model preferences
        suitable_positions = []
        
        for pos in premium_positions:
            if not position_availability.get(pos, False):
                continue
                
            row, col = pos
            
            # Check category row preferences
            category_rows = self.categories.get(category, {}).get('rows', [])
            if category_rows and row not in category_rows:
                continue
            
            # Check model column preferences
            model_columns = self.ipad_models.get(ipad_model, {}).get('columns', [])
            if model_columns and col not in model_columns:
                continue
            
            suitable_positions.append(pos)
        
        # Return best suitable position (highest priority)
        if suitable_positions:
            return suitable_positions[0]
        
        # Fallback: any available premium position
        for pos in premium_positions:
            if position_availability.get(pos, False):
                return pos
        
        return None
    
    def _find_volume_position_for_gripp(self, product: Dict, available_positions: List[Tuple[int, int]], 
                                      position_availability: Dict, grid_size: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find the best position for Gripp volume products"""
        
        # Gripp products prefer high-visibility positions but not necessarily premium
        category = product.get('category', 'case')
        ipad_model = product.get('ipad_model', 'iPad Base')
        
        # Filter by category and model preferences
        suitable_positions = []
        
        for pos in available_positions:
            if not position_availability.get(pos, False):
                continue
                
            row, col = pos
            
            # Check category row preferences
            category_rows = self.categories.get(category, {}).get('rows', [])
            if category_rows and row not in category_rows:
                continue
            
            # Check model column preferences  
            model_columns = self.ipad_models.get(ipad_model, {}).get('columns', [])
            if model_columns and col not in model_columns:
                continue
            
            suitable_positions.append(pos)
        
        # Prefer positions in rows 1-6 (good visibility)
        visibility_positions = [pos for pos in suitable_positions if 1 <= pos[0] <= 6]
        
        if visibility_positions:
            return visibility_positions[0]
        elif suitable_positions:
            return suitable_positions[0]
        
        # Fallback: any available position
        if available_positions:
            return available_positions[0]
        
        return None
    
    def _find_diversity_position_for_others(self, product: Dict, available_positions: List[Tuple[int, int]], 
                                          position_availability: Dict, grid_size: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find position for other brands ensuring diversity"""
        
        category = product.get('category', 'case')
        ipad_model = product.get('ipad_model', 'iPad Base')
        
        # Filter by category and model preferences
        suitable_positions = []
        
        for pos in available_positions:
            if not position_availability.get(pos, False):
                continue
                
            row, col = pos
            
            # Check category row preferences
            category_rows = self.categories.get(category, {}).get('rows', [])
            if category_rows and row not in category_rows:
                continue
            
            # Check model column preferences
            model_columns = self.ipad_models.get(ipad_model, {}).get('columns', [])
            if model_columns and col not in model_columns:
                continue
            
            suitable_positions.append(pos)
        
        if suitable_positions:
            return suitable_positions[0]
        elif available_positions:
            return available_positions[0]
        
        return None
    
    def build_sales_based_prioritization_system(self, products: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Build comprehensive sales-based prioritization system with tier-based product ranking
        Returns products organized by sales performance tiers
        """
        # Define sales performance tiers
        sales_tiers = {
            'premium': [],      # >100 sales - premium positioning
            'high_volume': [],  # 50-100 sales - high visibility
            'medium_volume': [], # 25-49 sales - standard positioning  
            'low_volume': [],   # 10-24 sales - lower positioning
            'miscellaneous': [] # <10 sales - miscellaneous wall
        }
        
        # Classify products by sales performance
        for product in products:
            frequency = product.get('frequency', 0)
            enhanced_product = product.copy()
            
            # Add sales tier information
            if frequency >= 100:
                enhanced_product['sales_tier'] = 'premium'
                enhanced_product['tier_priority'] = 5
                sales_tiers['premium'].append(enhanced_product)
            elif frequency >= 50:
                enhanced_product['sales_tier'] = 'high_volume'
                enhanced_product['tier_priority'] = 4
                sales_tiers['high_volume'].append(enhanced_product)
            elif frequency >= 25:
                enhanced_product['sales_tier'] = 'medium_volume'
                enhanced_product['tier_priority'] = 3
                sales_tiers['medium_volume'].append(enhanced_product)
            elif frequency >= 10:
                enhanced_product['sales_tier'] = 'low_volume'
                enhanced_product['tier_priority'] = 2
                sales_tiers['low_volume'].append(enhanced_product)
            else:
                enhanced_product['sales_tier'] = 'miscellaneous'
                enhanced_product['tier_priority'] = 1
                sales_tiers['miscellaneous'].append(enhanced_product)
        
        # Sort each tier by sales frequency (highest first)
        for tier_products in sales_tiers.values():
            tier_products.sort(key=lambda p: p.get('frequency', 0), reverse=True)
        
        # Apply tier-specific enhancements
        sales_tiers['premium'] = self._enhance_premium_products(sales_tiers['premium'])
        sales_tiers['high_volume'] = self._enhance_high_volume_products(sales_tiers['high_volume'])
        sales_tiers['medium_volume'] = self._enhance_medium_volume_products(sales_tiers['medium_volume'])
        sales_tiers['low_volume'] = self._enhance_low_volume_products(sales_tiers['low_volume'])
        sales_tiers['miscellaneous'] = self._filter_miscellaneous_products(sales_tiers['miscellaneous'])
        
        return sales_tiers
    
    def _enhance_premium_products(self, premium_products: List[Dict]) -> List[Dict]:
        """
        Enhance premium products (>100 sales) with special positioning and priority boosts
        """
        enhanced_products = []
        
        for product in premium_products:
            enhanced_product = product.copy()
            frequency = product.get('frequency', 0)
            brand = product.get('brand', '').lower()
            category = product.get('category', 'case')
            
            # Premium positioning indicators
            enhanced_product['premium_sales'] = True
            enhanced_product['eye_level_priority'] = True
            
            # Special handling for Magic Keyboard Folios (110+ sales)
            if 'magic keyboard' in product['product_name'].lower() and frequency >= 110:
                enhanced_product['magic_keyboard_premium'] = True
                enhanced_product['productivity_flagship'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 2.0
            
            # Special handling for Gripp Ultra cases (150-220 sales range)
            elif brand == 'gripp' and 'ultra' in product['product_name'].lower() and frequency >= 150:
                enhanced_product['gripp_ultra_premium'] = True
                enhanced_product['eye_level_mandatory'] = True
                enhanced_product['volume_flagship'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.8
            
            # General premium boost for high-sales products
            elif frequency >= 150:
                enhanced_product['super_premium'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.6
            elif frequency >= 120:
                enhanced_product['high_premium'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.4
            else:
                enhanced_product['standard_premium'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.2
            
            # Category-specific premium enhancements
            if category == 'folio' and brand == 'apple':
                enhanced_product['apple_folio_premium'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.3
            elif category == 'keyboard case':
                enhanced_product['productivity_premium'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.5
            
            enhanced_products.append(enhanced_product)
        
        # Sort by enhanced priority score
        enhanced_products.sort(key=lambda p: p.get('priority_score', 0), reverse=True)
        
        return enhanced_products
    
    def _enhance_high_volume_products(self, high_volume_products: List[Dict]) -> List[Dict]:
        """
        Enhance high-volume products (50-100 sales) with good visibility positioning
        """
        enhanced_products = []
        
        for product in high_volume_products:
            enhanced_product = product.copy()
            frequency = product.get('frequency', 0)
            brand = product.get('brand', '').lower()
            
            # High volume indicators
            enhanced_product['high_volume_sales'] = True
            enhanced_product['good_visibility'] = True
            
            # Brand-specific enhancements
            if brand == 'gripp':
                enhanced_product['gripp_volume_leader'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.3
            elif brand == 'apple':
                enhanced_product['apple_strong_seller'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.2
            else:
                enhanced_product['third_party_performer'] = True
                enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.1
            
            enhanced_products.append(enhanced_product)
        
        return enhanced_products
    
    def _enhance_medium_volume_products(self, medium_volume_products: List[Dict]) -> List[Dict]:
        """
        Enhance medium-volume products (25-49 sales) with standard positioning
        """
        enhanced_products = []
        
        for product in medium_volume_products:
            enhanced_product = product.copy()
            
            # Medium volume indicators
            enhanced_product['medium_volume_sales'] = True
            enhanced_product['standard_positioning'] = True
            
            # Slight priority boost for medium performers
            enhanced_product['priority_score'] = enhanced_product.get('priority_score', 0) * 1.05
            
            enhanced_products.append(enhanced_product)
        
        return enhanced_products
    
    def _enhance_low_volume_products(self, low_volume_products: List[Dict]) -> List[Dict]:
        """
        Enhance low-volume products (10-24 sales) with lower positioning
        """
        enhanced_products = []
        
        for product in low_volume_products:
            enhanced_product = product.copy()
            
            # Low volume indicators
            enhanced_product['low_volume_sales'] = True
            enhanced_product['lower_positioning'] = True
            
            # No priority boost for low performers
            enhanced_products.append(enhanced_product)
        
        return enhanced_products
    
    def _filter_miscellaneous_products(self, miscellaneous_products: List[Dict]) -> List[Dict]:
        """
        Filter and categorize miscellaneous products (<10 sales) for miscellaneous wall
        """
        filtered_products = []
        
        for product in miscellaneous_products:
            enhanced_product = product.copy()
            frequency = product.get('frequency', 0)
            
            # Miscellaneous indicators
            enhanced_product['miscellaneous_tier'] = True
            enhanced_product['miscellaneous_wall_candidate'] = True
            
            # Categorize reasons for miscellaneous placement
            reasons = []
            
            if frequency < 5:
                reasons.append('very_low_sales')
                enhanced_product['very_low_sales'] = True
            elif frequency < 10:
                reasons.append('low_sales')
                enhanced_product['low_sales'] = True
            
            # Check for other miscellaneous criteria
            product_name = product['product_name'].lower()
            
            if any(term in product_name for term in ['1st generation', '2nd generation', '3rd generation', '4th generation']):
                reasons.append('outdated_model')
                enhanced_product['outdated_ipad_model'] = True
            
            if any(term in product_name for term in ['sleeve', 'bag', 'pouch']):
                reasons.append('generic_accessory')
                enhanced_product['generic_accessory'] = True
            
            if any(term in product_name for term in ['privacy filter', 'screen protector', 'keyboard skin']):
                reasons.append('specialty_item')
                enhanced_product['specialty_item'] = True
            
            enhanced_product['miscellaneous_reasons'] = reasons
            filtered_products.append(enhanced_product)
        
        return filtered_products
    
    def apply_eye_level_placement_strategy(self, sales_tiers: Dict[str, List[Dict]], grid_size: Tuple[int, int]) -> List[Dict]:
        """
        Apply eye-level placement strategy prioritizing high-sales products and Gripp Ultra cases
        """
        rows, cols = grid_size
        
        # Define eye-level rows (rows 2-5 are optimal for visibility)
        eye_level_rows = [2, 3, 4, 5]
        premium_eye_level_rows = [3, 4]  # Best eye-level positions
        
        # Create position priority matrix
        position_priorities = {}
        
        for row in range(rows):
            for col in range(cols):
                priority_score = 0
                
                # Eye-level bonus
                if row in premium_eye_level_rows:
                    priority_score += 100
                elif row in eye_level_rows:
                    priority_score += 80
                elif row in [1, 6]:  # Adjacent to eye-level
                    priority_score += 60
                else:
                    priority_score += 40
                
                # Left-to-right visibility preference
                priority_score += (cols - col) * 5
                
                position_priorities[(row, col)] = priority_score
        
        # Sort positions by priority
        sorted_positions = sorted(position_priorities.items(), key=lambda x: x[1], reverse=True)
        available_positions = [pos for pos, _ in sorted_positions]
        
        positioned_products = []
        
        # Phase 1: Place premium products (>100 sales) in best positions
        premium_products = sales_tiers.get('premium', [])
        for product in premium_products:
            if available_positions:
                # Special handling for Gripp Ultra cases (150-220 sales)
                if product.get('gripp_ultra_premium'):
                    # Find best eye-level position for Gripp Ultra
                    best_position = self._find_best_eye_level_position(
                        product, available_positions, premium_eye_level_rows
                    )
                elif product.get('magic_keyboard_premium'):
                    # Magic Keyboard gets premium positioning
                    best_position = self._find_best_productivity_position(
                        product, available_positions
                    )
                else:
                    # Other premium products get good positions
                    best_position = available_positions.pop(0)
                
                if best_position:
                    product['grid_position'] = best_position
                    product['positioning_reason'] = 'premium_sales'
                    if best_position in available_positions:
                        available_positions.remove(best_position)
                    positioned_products.append(product)
        
        # Phase 2: Place high-volume products in remaining good positions
        high_volume_products = sales_tiers.get('high_volume', [])
        for product in high_volume_products:
            if available_positions:
                # Prefer eye-level or adjacent positions
                best_position = self._find_good_visibility_position(
                    product, available_positions, eye_level_rows
                )
                
                if best_position:
                    product['grid_position'] = best_position
                    product['positioning_reason'] = 'high_volume_sales'
                    available_positions.remove(best_position)
                    positioned_products.append(product)
        
        # Phase 3: Place medium-volume products in standard positions
        medium_volume_products = sales_tiers.get('medium_volume', [])
        for product in medium_volume_products:
            if available_positions:
                best_position = self._find_standard_position(
                    product, available_positions
                )
                
                if best_position:
                    product['grid_position'] = best_position
                    product['positioning_reason'] = 'medium_volume_sales'
                    available_positions.remove(best_position)
                    positioned_products.append(product)
        
        # Phase 4: Place low-volume products in remaining positions
        low_volume_products = sales_tiers.get('low_volume', [])
        for product in low_volume_products:
            if available_positions:
                best_position = available_positions.pop(0)
                product['grid_position'] = best_position
                product['positioning_reason'] = 'low_volume_sales'
                positioned_products.append(product)
        
        # Phase 5: Mark miscellaneous products for separate wall
        miscellaneous_products = sales_tiers.get('miscellaneous', [])
        for product in miscellaneous_products:
            product['grid_position'] = None
            product['positioning_reason'] = 'miscellaneous_wall'
            positioned_products.append(product)
        
        return positioned_products
    
    def _find_best_eye_level_position(self, product: Dict, available_positions: List[Tuple[int, int]], 
                                    premium_rows: List[int]) -> Optional[Tuple[int, int]]:
        """Find the best eye-level position for premium products like Gripp Ultra cases"""
        
        # Get product preferences
        category = product.get('category', 'case')
        ipad_model = product.get('ipad_model', 'iPad Base')
        
        # Filter positions by category and model preferences
        suitable_positions = []
        
        for pos in available_positions:
            row, col = pos
            
            # Must be in premium eye-level rows
            if row not in premium_rows:
                continue
            
            # Check category row preferences
            category_rows = self.categories.get(category, {}).get('rows', [])
            if category_rows and row not in category_rows:
                continue
            
            # Check model column preferences
            model_columns = self.ipad_models.get(ipad_model, {}).get('columns', [])
            if model_columns and col not in model_columns:
                continue
            
            suitable_positions.append(pos)
        
        # Return best suitable position (leftmost in premium rows)
        if suitable_positions:
            suitable_positions.sort(key=lambda pos: (pos[0], pos[1]))
            return suitable_positions[0]
        
        # Fallback: any premium eye-level position
        for pos in available_positions:
            if pos[0] in premium_rows:
                return pos
        
        return None
    
    def _find_best_productivity_position(self, product: Dict, available_positions: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Find the best position for productivity products like Magic Keyboards"""
        
        # Productivity products prefer keyboard case rows (5-6) but with good visibility
        category = product.get('category', 'keyboard case')
        ipad_model = product.get('ipad_model', 'iPad Base')
        
        # Get category and model preferences
        category_rows = self.categories.get(category, {}).get('rows', [5, 6])
        model_columns = self.ipad_models.get(ipad_model, {}).get('columns', [])
        
        suitable_positions = []
        
        for pos in available_positions:
            row, col = pos
            
            # Check category row preferences
            if category_rows and row in category_rows:
                # Check model column preferences
                if not model_columns or col in model_columns:
                    suitable_positions.append(pos)
        
        if suitable_positions:
            # Sort by visibility (prefer row 5 over 6, left columns over right)
            suitable_positions.sort(key=lambda pos: (pos[0], pos[1]))
            return suitable_positions[0]
        
        # Fallback: any available position
        if available_positions:
            return available_positions[0]
        
        return None
    
    def _find_good_visibility_position(self, product: Dict, available_positions: List[Tuple[int, int]], 
                                     eye_level_rows: List[int]) -> Optional[Tuple[int, int]]:
        """Find a good visibility position for high-volume products"""
        
        category = product.get('category', 'case')
        ipad_model = product.get('ipad_model', 'iPad Base')
        
        # Get preferences
        category_rows = self.categories.get(category, {}).get('rows', [])
        model_columns = self.ipad_models.get(ipad_model, {}).get('columns', [])
        
        # Prefer eye-level or adjacent positions
        preferred_rows = eye_level_rows + [1, 6]  # Eye-level + adjacent
        
        suitable_positions = []
        
        for pos in available_positions:
            row, col = pos
            
            # Check if in preferred visibility rows
            if row in preferred_rows:
                # Check category and model preferences
                if (not category_rows or row in category_rows) and (not model_columns or col in model_columns):
                    suitable_positions.append(pos)
        
        if suitable_positions:
            # Sort by row preference (eye-level first)
            suitable_positions.sort(key=lambda pos: (pos[0] not in eye_level_rows, pos[0], pos[1]))
            return suitable_positions[0]
        
        # Fallback: any position matching category/model
        for pos in available_positions:
            row, col = pos
            if (not category_rows or row in category_rows) and (not model_columns or col in model_columns):
                return pos
        
        # Final fallback: any available position
        if available_positions:
            return available_positions[0]
        
        return None
    
    def _find_standard_position(self, product: Dict, available_positions: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Find a standard position for medium-volume products"""
        
        category = product.get('category', 'case')
        ipad_model = product.get('ipad_model', 'iPad Base')
        
        # Get preferences
        category_rows = self.categories.get(category, {}).get('rows', [])
        model_columns = self.ipad_models.get(ipad_model, {}).get('columns', [])
        
        # Find positions matching category and model preferences
        suitable_positions = []
        
        for pos in available_positions:
            row, col = pos
            if (not category_rows or row in category_rows) and (not model_columns or col in model_columns):
                suitable_positions.append(pos)
        
        if suitable_positions:
            return suitable_positions[0]
        
        # Fallback: any available position
        if available_positions:
            return available_positions[0]
        
        return None
    
    def create_ipad_grid_generation_system(self, products: List[Dict], grid_size: Tuple[int, int] = (5, 4)) -> List[List[Dict]]:
        """
        Create iPad grid with proper Apple/TPA separation - NO BLANK FACINGS
        Rows 0-2: Apple products only (3 rows)
        Rows 3-4: TPA products only (2 rows) - Gripp-focused with other brands
        Column organization: Mini(0), Base(1), Air(2), Pro(3)
        Color diversity: Same colors across series in rows, avoid repetition
        """
        rows, cols = 5, 4  # Proper 5x4 grid (3 Apple + 2 TPA)
        
        # Initialize empty grid
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        
        # Consolidate iPad Pro models for consistency
        processed_products = []
        for product in products:
            product_copy = product.copy()
            if product_copy.get('ipad_model') == 'iPad Pro 12.9':
                product_copy['ipad_model'] = 'iPad Pro'
            processed_products.append(product_copy)
        
        # Define column-to-model mapping
        column_models = {
            0: 'iPad Mini',
            1: 'iPad Base', 
            2: 'iPad Air',
            3: 'iPad Pro'
        }
        
        # Separate Apple and TPA products
        apple_products = [p for p in processed_products if p.get('brand', '').lower() == 'apple']
        tpa_products = [p for p in processed_products if p.get('brand', '').lower() != 'apple']
        
        print(f"📊 Brand Distribution:")
        print(f"   Apple products: {len(apple_products)}")
        print(f"   TPA products: {len(tpa_products)}")
        
        # Group by model and brand
        apple_by_model = self._group_products_by_model_and_color(apple_products)
        tpa_by_model = self._group_products_by_model_and_color(tpa_products)
        
        # Phase 1: Fill Apple rows (0-2) with color diversity - NO BLANKS
        print(f"\n🍎 Filling Apple Section (Rows 0-2) - NO BLANK FACINGS:")
        self._fill_apple_section_no_blanks(grid, apple_by_model, [0, 1, 2], column_models)
        
        # Phase 2: Fill TPA rows (3-4) with color diversity - NO BLANKS
        print(f"\n🔧 Filling TPA Section (Rows 3-4) - NO BLANK FACINGS:")
        self._fill_tpa_section_no_blanks(grid, tpa_by_model, [3, 4], column_models)
        
        # Phase 3: Final cleanup - ensure NO empty spaces
        self._eliminate_all_blank_facings(grid, processed_products)
        
        # Phase 4: Color optimization
        self._optimize_color_distribution(grid)
        
        # Print final grid summary
        self._print_grid_summary(grid)
        
        return grid
    
    def _group_products_by_model_and_color(self, products: List[Dict]) -> Dict[str, Dict[str, List[Dict]]]:
        """Group products by iPad model and then by color for diversity management"""
        grouped = {}
        
        for model in self.ipad_models.keys():
            grouped[model] = {}
            model_products = [p for p in products if p.get('ipad_model') == model]
            
            # Group by color
            for product in model_products:
                color = self._extract_display_color(product.get('product_name', ''))
                if color not in grouped[model]:
                    grouped[model][color] = []
                grouped[model][color].append(product)
            
            # Sort each color group by sales frequency
            for color in grouped[model]:
                grouped[model][color].sort(key=lambda p: p.get('frequency', 0), reverse=True)
        
        return grouped
    
    def _fill_apple_section_no_blanks(self, grid: List[List[Dict]], apple_by_model: Dict, 
                                     apple_rows: List[int], column_models: Dict):
        """Fill Apple section (rows 0-2) with NO BLANK FACINGS"""
        used_colors_per_row = {row: set() for row in apple_rows}
        
        # Create a pool of all Apple products for reuse if needed
        all_apple_products = []
        for model_colors in apple_by_model.values():
            for color_products in model_colors.values():
                all_apple_products.extend(color_products)
        all_apple_products.sort(key=lambda p: p.get('frequency', 0), reverse=True)
        
        for row in apple_rows:
            print(f"   Filling Apple Row {row}:")
            
            for col, model in column_models.items():
                best_product = None
                best_color = None
                
                # Try to find model-specific product first
                if model in apple_by_model:
                    # Prioritize colors not used in previous rows
                    all_used_colors = set()
                    for prev_row in apple_rows:
                        if prev_row < row:
                            all_used_colors.update(used_colors_per_row[prev_row])
                    
                    # Look for unused colors first
                    for color, products in apple_by_model[model].items():
                        if products and color not in all_used_colors:
                            best_product = products[0]
                            best_color = color
                            break
                    
                    # If no unused colors, use any available
                    if not best_product:
                        for color, products in apple_by_model[model].items():
                            if products:
                                best_product = products[0]
                                best_color = color
                                break
                
                # If no model-specific product, use any Apple product to avoid blanks
                if not best_product and all_apple_products:
                    best_product = all_apple_products[0]
                    best_color = self._extract_display_color(best_product.get('product_name', ''))
                    print(f"     WARNING: Using fallback Apple product for {model} at ({row},{col})")
                
                if best_product:
                    product_copy = best_product.copy()
                    product_copy['grid_position'] = (row, col)
                    grid[row][col] = product_copy
                    used_colors_per_row[row].add(best_color)
                    
                    # Remove used product from specific model group
                    if model in apple_by_model and best_color in apple_by_model[model]:
                        if best_product in apple_by_model[model][best_color]:
                            apple_by_model[model][best_color].remove(best_product)
                            if not apple_by_model[model][best_color]:
                                del apple_by_model[model][best_color]
                    
                    # Remove from general pool
                    if best_product in all_apple_products:
                        all_apple_products.remove(best_product)
                    
                    print(f"     ({row},{col}): {model} - {best_color} - {best_product.get('product_name', 'Unknown')[:30]}...")
                else:
                    print(f"     ERROR: No Apple product available for {model} at ({row},{col})")
    
    def _fill_tpa_section_no_blanks(self, grid: List[List[Dict]], tpa_by_model: Dict, 
                                   tpa_rows: List[int], column_models: Dict):
        """Fill TPA section (rows 3-4) with NO BLANK FACINGS - Gripp-focused"""
        used_colors_per_row = {row: set() for row in tpa_rows}
        
        # Create a pool of all TPA products for reuse if needed
        all_tpa_products = []
        for model_colors in tpa_by_model.values():
            for color_products in model_colors.values():
                all_tpa_products.extend(color_products)
        
        # Sort by brand priority (Gripp first) then by sales
        brand_priority = ['gripp', 'tomtoc', 'stm', 'logitech', 'tucano', 'dbramante1928', 'muvtech']
        all_tpa_products.sort(key=lambda p: (
            brand_priority.index(p.get('brand', '').lower()) if p.get('brand', '').lower() in brand_priority else 999,
            -p.get('frequency', 0)
        ))
        
        for row in tpa_rows:
            print(f"   Filling TPA Row {row}:")
            
            for col, model in column_models.items():
                best_product = None
                best_color = None
                
                # Try to find model-specific product first
                if model in tpa_by_model:
                    # Prioritize colors not used in previous TPA rows
                    all_used_colors = set()
                    for prev_row in tpa_rows:
                        if prev_row < row:
                            all_used_colors.update(used_colors_per_row[prev_row])
                    
                    # Try each brand in priority order
                    for brand in brand_priority:
                        for color, products in tpa_by_model[model].items():
                            for product in products:
                                if (product.get('brand', '').lower() == brand and 
                                    color not in all_used_colors):
                                    best_product = product
                                    best_color = color
                                    break
                            if best_product:
                                break
                        if best_product:
                            break
                    
                    # If no unused colors with priority brands, use any available
                    if not best_product:
                        for color, products in tpa_by_model[model].items():
                            if products:
                                best_product = products[0]
                                best_color = color
                                break
                
                # If no model-specific product, use any TPA product to avoid blanks
                if not best_product and all_tpa_products:
                    best_product = all_tpa_products[0]
                    best_color = self._extract_display_color(best_product.get('product_name', ''))
                    print(f"     WARNING: Using fallback TPA product for {model} at ({row},{col})")
                
                if best_product:
                    product_copy = best_product.copy()
                    product_copy['grid_position'] = (row, col)
                    grid[row][col] = product_copy
                    used_colors_per_row[row].add(best_color)
                    
                    # Remove used product from specific model group
                    if model in tpa_by_model and best_color in tpa_by_model[model]:
                        if best_product in tpa_by_model[model][best_color]:
                            tpa_by_model[model][best_color].remove(best_product)
                            if not tpa_by_model[model][best_color]:
                                del tpa_by_model[model][best_color]
                    
                    # Remove from general pool
                    if best_product in all_tpa_products:
                        all_tpa_products.remove(best_product)
                    
                    brand = best_product.get('brand', 'Unknown')
                    print(f"     ({row},{col}): {model} - {brand} - {best_color} - {best_product.get('product_name', 'Unknown')[:30]}...")
                else:
                    print(f"     ERROR: No TPA product available for {model} at ({row},{col})")
    
    def _eliminate_all_blank_facings(self, grid: List[List[Dict]], all_products: List[Dict]):
        """Final pass to eliminate any remaining blank facings"""
        rows, cols = len(grid), len(grid[0])
        
        # Create a pool of unused products
        used_product_names = set()
        for row in range(rows):
            for col in range(cols):
                if grid[row][col]:
                    used_product_names.add(grid[row][col].get('product_name', ''))
        
        unused_products = [p for p in all_products if p.get('product_name', '') not in used_product_names]
        unused_products.sort(key=lambda p: p.get('frequency', 0), reverse=True)
        
        # Fill any remaining empty spaces
        for row in range(rows):
            for col in range(cols):
                if grid[row][col] is None:
                    if unused_products:
                        product = unused_products.pop(0)
                        product_copy = product.copy()
                        product_copy['grid_position'] = (row, col)
                        grid[row][col] = product_copy
                        print(f"   🔧 Filled blank at ({row},{col}) with {product.get('brand', 'Unknown')} - {product.get('product_name', 'Unknown')[:30]}...")
                    else:
                        # Reuse existing products if no unused ones available
                        if all_products:
                            product = all_products[0]
                            product_copy = product.copy()
                            product_copy['grid_position'] = (row, col)
                            grid[row][col] = product_copy
                            print(f"   🔄 Reused product at ({row},{col}) with {product.get('brand', 'Unknown')} - {product.get('product_name', 'Unknown')[:30]}...")
        
        # Verify no blanks remain
        blank_count = sum(1 for row in grid for cell in row if cell is None)
        if blank_count == 0:
            print(f"   ✅ SUCCESS: No blank facings remaining!")
        else:
            print(f"   ⚠️ WARNING: {blank_count} blank facings still remain")
    
    def _optimize_color_distribution(self, grid: List[List[Dict]]):
        """Optimize color distribution to reduce black dominance"""
        rows, cols = len(grid), len(grid[0])
        
        # Count colors per section
        apple_colors = {}
        tpa_colors = {}
        
        for row in range(rows):
            for col in range(cols):
                if grid[row][col]:
                    color = self._extract_display_color(grid[row][col].get('product_name', ''))
                    if row < 3:  # Apple section
                        apple_colors[color] = apple_colors.get(color, 0) + 1
                    else:  # TPA section
                        tpa_colors[color] = tpa_colors.get(color, 0) + 1
        
        print(f"\n🎨 Color Distribution:")
        print(f"   Apple section: {dict(sorted(apple_colors.items(), key=lambda x: x[1], reverse=True))}")
        print(f"   TPA section: {dict(sorted(tpa_colors.items(), key=lambda x: x[1], reverse=True))}")
    
    def _print_grid_summary(self, grid: List[List[Dict]]):
        """Print detailed grid summary with brand and color info - 5 rows (3 Apple + 2 TPA)"""
        rows, cols = len(grid), len(grid[0])
        
        print(f"\n📋 Final Grid Summary ({rows}x{cols}):")
        print(f"   Apple Section (Rows 0-2):")
        for row in range(min(3, rows)):
            row_summary = []
            for col in range(cols):
                if row < len(grid) and col < len(grid[row]) and grid[row][col]:
                    brand = grid[row][col].get('brand', 'Unknown')[:4]
                    color = self._extract_display_color(grid[row][col].get('product_name', ''))[:3]
                    sales = grid[row][col].get('frequency', 0)
                    row_summary.append(f"{brand}-{color}({sales})")
                else:
                    row_summary.append("Empty")
            print(f"     Row {row}: {' | '.join(row_summary)}")
        
        print(f"   TPA Section (Rows 3-4):")
        for row in range(3, min(5, rows)):
            row_summary = []
            for col in range(cols):
                if row < len(grid) and col < len(grid[row]) and grid[row][col]:
                    brand = grid[row][col].get('brand', 'Unknown')[:4]
                    color = self._extract_display_color(grid[row][col].get('product_name', ''))[:3]
                    sales = grid[row][col].get('frequency', 0)
                    row_summary.append(f"{brand}-{color}({sales})")
                else:
                    row_summary.append("Empty")
            print(f"     Row {row}: {' | '.join(row_summary)}")
        
        # Count blanks
        blank_count = sum(1 for row in grid for cell in row if cell is None)
        total_positions = rows * cols
        print(f"\n   📊 Grid Stats: {total_positions - blank_count}/{total_positions} filled ({((total_positions - blank_count)/total_positions)*100:.1f}%)")
        if blank_count > 0:
            print(f"   ⚠️ {blank_count} blank facings detected!")
        else:
            print(f"   ✅ No blank facings - Perfect fill!")
    
    def generate_store_planograms(self, store_name: str, num_walls: int) -> Dict[str, bool]:
        """
        Generate iPad planograms with proper Apple/TPA wall allocation strategy:
        - 1 wall: Half Apple, 2 rows TPA (Gripp), 1 row other TPA brands
        - 2 walls: Wall 1 Apple/TPA split, Wall 2 TPA-focused
        - 3+ walls: 2 walls with Apple/TPA split, rest TPA-focused
        """
        results = {}
        
        try:
            # Load iPad accessories data
            products = self.load_ipad_data()
            
            if num_walls == 1:
                # Single wall strategy: Mixed Apple/TPA with brand diversity
                results.update(self._generate_single_wall_mixed(products, store_name))
                
            elif num_walls == 2:
                # Two wall strategy: Apple/TPA split + TPA-focused
                results.update(self._generate_two_wall_apple_tpa_split(products, store_name))
                
            elif num_walls >= 3:
                # Multi-wall strategy: 2 Apple/TPA walls + TPA-only walls
                results.update(self._generate_multi_wall_apple_tpa_strategy(products, store_name, num_walls))
            
            return results
            
        except Exception as e:
            print(f"Error generating store planograms: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _generate_single_wall_mixed(self, products: List[Dict], store_name: str) -> Dict[str, bool]:
        """Generate single wall with mixed Apple/TPA strategy"""
        results = {}
        
        print(f"🏪 Single Wall Strategy: Half Apple, 2 rows Gripp, 1 row other TPA")
        
        # Use standard Apple/TPA grid generation
        grid = self.create_ipad_grid_generation_system(products)
        
        # Generate visual planogram
        output_path = f"ipad_wall_1_{store_name.lower().replace(' ', '_')}.png"
        visual_success = self.generate_ipad_planogram_visual(
            grid, 
            store_name=f"{store_name} - iPad Mixed Wall",
            wall_number=1,
            output_path=output_path
        )
        
        # Generate report
        report_path = f"ipad_wall_1_{store_name.lower().replace(' ', '_')}_report.txt"
        report_success = self.generate_ipad_planogram_report(grid, report_path)
        
        results['wall_1'] = visual_success and report_success
        return results
    
    def _generate_two_wall_apple_tpa_split(self, products: List[Dict], store_name: str) -> Dict[str, bool]:
        """Generate 2 walls: Wall 1 Apple/TPA split, Wall 2 TPA-focused"""
        results = {}
        
        print(f"🏪 Two Wall Strategy: Wall 1 Apple/TPA split, Wall 2 TPA-focused")
        
        # Wall 1: Standard Apple/TPA split
        grid_1 = self.create_ipad_grid_generation_system(products)
        
        output_path_1 = f"ipad_wall_1_{store_name.lower().replace(' ', '_')}.png"
        visual_success_1 = self.generate_ipad_planogram_visual(
            grid_1,
            store_name=f"{store_name} - iPad Apple/TPA Wall 1",
            wall_number=1,
            output_path=output_path_1
        )
        
        report_path_1 = f"ipad_wall_1_{store_name.lower().replace(' ', '_')}_report.txt"
        report_success_1 = self.generate_ipad_planogram_report(grid_1, report_path_1)
        results['wall_1'] = visual_success_1 and report_success_1
        
        # Wall 2: TPA-focused (Gripp + other brands)
        tpa_products = [p for p in products if p.get('brand', '').lower() != 'apple']
        grid_2 = self.create_tpa_focused_grid(tpa_products)
        
        output_path_2 = f"ipad_wall_2_{store_name.lower().replace(' ', '_')}.png"
        visual_success_2 = self.generate_ipad_planogram_visual(
            grid_2,
            store_name=f"{store_name} - iPad TPA Wall 2",
            wall_number=2,
            output_path=output_path_2
        )
        
        report_path_2 = f"ipad_wall_2_{store_name.lower().replace(' ', '_')}_report.txt"
        report_success_2 = self.generate_ipad_planogram_report(grid_2, report_path_2)
        results['wall_2'] = visual_success_2 and report_success_2
        
        return results
    
    def _generate_multi_wall_apple_tpa_strategy(self, products: List[Dict], store_name: str, num_walls: int) -> Dict[str, bool]:
        """Generate 3+ walls: 2 Apple/TPA walls + TPA-only walls"""
        results = {}
        
        print(f"🏪 Multi-Wall Strategy: 2 Apple/TPA walls + {num_walls-2} TPA-only walls")
        
        # Wall 1: Apple/TPA split
        grid_1 = self.create_ipad_grid_generation_system(products)
        
        output_path_1 = f"ipad_wall_1_{store_name.lower().replace(' ', '_')}.png"
        visual_success_1 = self.generate_ipad_planogram_visual(
            grid_1,
            store_name=f"{store_name} - iPad Apple/TPA Wall 1",
            wall_number=1,
            output_path=output_path_1
        )
        
        report_path_1 = f"ipad_wall_1_{store_name.lower().replace(' ', '_')}_report.txt"
        report_success_1 = self.generate_ipad_planogram_report(grid_1, report_path_1)
        results['wall_1'] = visual_success_1 and report_success_1
        
        # Wall 2: Another Apple/TPA split with different products
        remaining_products = [p for p in products if not self._is_product_in_grid(p, grid_1)]
        grid_2 = self.create_ipad_grid_generation_system(remaining_products)
        
        output_path_2 = f"ipad_wall_2_{store_name.lower().replace(' ', '_')}.png"
        visual_success_2 = self.generate_ipad_planogram_visual(
            grid_2,
            store_name=f"{store_name} - iPad Apple/TPA Wall 2",
            wall_number=2,
            output_path=output_path_2
        )
        
        report_path_2 = f"ipad_wall_2_{store_name.lower().replace(' ', '_')}_report.txt"
        report_success_2 = self.generate_ipad_planogram_report(grid_2, report_path_2)
        results['wall_2'] = visual_success_2 and report_success_2
        
        # Walls 3+: TPA-only walls
        tpa_products = [p for p in products if p.get('brand', '').lower() != 'apple']
        
        for wall_num in range(3, num_walls + 1):
            grid = self.create_tpa_focused_grid(tpa_products)
            
            output_path = f"ipad_wall_{wall_num}_{store_name.lower().replace(' ', '_')}.png"
            visual_success = self.generate_ipad_planogram_visual(
                grid,
                store_name=f"{store_name} - iPad TPA Wall {wall_num}",
                wall_number=wall_num,
                output_path=output_path
            )
            
            report_path = f"ipad_wall_{wall_num}_{store_name.lower().replace(' ', '_')}_report.txt"
            report_success = self.generate_ipad_planogram_report(grid, report_path)
            results[f'wall_{wall_num}'] = visual_success and report_success
        
        return results
    
    def create_tpa_focused_grid(self, tpa_products: List[Dict]) -> List[List[Dict]]:
        """Create TPA-focused grid with Gripp priority and other brand diversity - 5 rows"""
        rows, cols = 5, 4
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        
        # Column models mapping
        column_models = {
            0: 'iPad Mini',
            1: 'iPad Base', 
            2: 'iPad Air',
            3: 'iPad Pro'
        }
        
        # Separate Gripp and other TPA brands
        gripp_products = [p for p in tpa_products if p.get('brand', '').lower() == 'gripp']
        other_tpa_products = [p for p in tpa_products if p.get('brand', '').lower() != 'gripp']
        
        print(f"🔧 TPA-Focused Grid: {len(gripp_products)} Gripp, {len(other_tpa_products)} other TPA")
        
        # Group by model and color
        gripp_by_model = self._group_products_by_model_and_color(gripp_products)
        other_by_model = self._group_products_by_model_and_color(other_tpa_products)
        
        # Fill rows 0-3 with Gripp (4 rows)
        print(f"   Filling rows 0-3 with Gripp products:")
        self._fill_tpa_section_no_blanks(grid, gripp_by_model, [0, 1, 2, 3], column_models)
        
        # Fill rows 4-5 with other TPA brands (1 row for 5-row grid)
        if len(grid) > 4:
            print(f"   Filling row 4 with other TPA brands:")
            self._fill_tpa_section_no_blanks(grid, other_by_model, [4], column_models)
        
        return grid
    
    def _is_product_in_grid(self, product: Dict, grid: List[List[Dict]]) -> bool:
        """Check if a product is already placed in the grid"""
        product_name = product.get('product_name', '')
        
        for row in grid:
            for cell in row:
                if cell and cell.get('product_name', '') == product_name:
                    return True
        return False
    
    def _generate_multi_wall_planograms(self, products: List[Dict], store_name: str, num_walls: int) -> Dict[str, bool]:
        """Generate planograms for 3+ wall iPad setup"""
        results = {}
        
        # Distribute products across walls
        products_per_wall = len(products) // num_walls
        
        for wall_num in range(1, num_walls + 1):
            start_idx = (wall_num - 1) * products_per_wall
            end_idx = start_idx + products_per_wall if wall_num < num_walls else len(products)
            
            wall_products = products[start_idx:end_idx]
            grid = self.create_ipad_grid_generation_system(wall_products)
            
            # Generate visual planogram
            output_path = f"ipad_wall_{wall_num}_{store_name.lower().replace(' ', '_')}.png"
            visual_success = self.generate_ipad_planogram_visual(
                grid,
                store_name=f"{store_name} - iPad Accessories Wall {wall_num}",
                wall_number=wall_num,
                output_path=output_path
            )
            
            # Generate report
            report_path = f"ipad_wall_{wall_num}_{store_name.lower().replace(' ', '_')}_report.txt"
            report_success = self.generate_ipad_planogram_report(grid, report_path)
            
            results[f'wall_{wall_num}'] = visual_success and report_success
        
        return results
    
    def get_ipad_wall_count(self) -> int:
        """Get the number of walls allocated to iPad Accessories from stored config"""
        try:
            config_path = self.project_root / 'data' / 'processed' / 'final_wall_configs.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    configs = json.load(f)
                    
                # Look for any store config with iPad Accessories
                for store_name, config in configs.items():
                    wall_counts = config.get('wall_counts', {})
                    ipad_walls = wall_counts.get('iPad Accessories', 1)
                    if ipad_walls > 0:
                        print(f"Found iPad Accessories wall count: {ipad_walls}")
                        return ipad_walls
            
            # Default to 1 wall for iPad Accessories
            return 1
            
        except Exception as e:
            print(f"Error getting iPad wall count: {e}")
            return 1
    
    def _apply_gripp_color_diversity(self, gripp_products: List[Dict], max_products: int) -> List[Dict]:
        """Apply color diversity specifically for Gripp products with actual case colors"""
        if not gripp_products:
            return []
        
        # Sort by sales first
        gripp_products.sort(key=lambda p: p.get('frequency', 0), reverse=True)
        
        # Group by Gripp series for color diversity
        series_groups = {
            'Ultra': [],
            'Melon': [],
            'Styleus': [],
            'Armor': [],
            'Other': []
        }
        
        for product in gripp_products:
            product_name = product['product_name'].lower()
            series_found = False
            
            for series_name in ['ultra', 'melon', 'styleus', 'armor']:
                if series_name in product_name:
                    series_key = series_name.title()
                    
                    # Extract actual case color from product name
                    case_color = self._extract_gripp_case_color(product['product_name'])
                    product['case_color'] = case_color
                    product['gripp_series'] = series_key
                    
                    series_groups[series_key].append(product)
                    series_found = True
                    break
            
            if not series_found:
                product['case_color'] = 'Black'  # Default
                product['gripp_series'] = 'Other'
                series_groups['Other'].append(product)
        
        # Create diverse selection prioritizing different series and colors
        diverse_products = []
        series_cycle = cycle(['Ultra', 'Melon', 'Styleus', 'Armor', 'Other'])
        
        while len(diverse_products) < max_products and any(series_groups.values()):
            try:
                series = next(series_cycle)
                if series_groups[series]:
                    product = series_groups[series].pop(0)
                    diverse_products.append(product)
                else:
                    # Remove empty series
                    series_groups.pop(series, None)
                    if series_groups:
                        series_cycle = cycle(series_groups.keys())
                    else:
                        break
            except StopIteration:
                break
        
        return diverse_products
    
    def _apply_enhanced_gripp_color_diversity(self, gripp_products: List[Dict], max_products: int) -> List[Dict]:
        """Apply enhanced color diversity for Gripp products prioritizing visual variety"""
        if not gripp_products:
            return []
        
        # Extract colors for all products
        for product in gripp_products:
            product['extracted_color'] = self._extract_gripp_case_color(product['product_name'])
        
        # Group by color first (not just sales)
        color_groups = defaultdict(list)
        for product in gripp_products:
            color = product['extracted_color']
            color_groups[color].append(product)
        
        # Sort each color group by sales
        for color in color_groups:
            color_groups[color].sort(key=lambda p: p.get('frequency', 0), reverse=True)
        
        # Create diverse selection with color rotation
        diverse_products = []
        available_colors = list(color_groups.keys())
        color_cycle = cycle(available_colors) if available_colors else []
        
        # Prioritize non-black colors first
        priority_colors = [c for c in available_colors if c.lower() != 'black']
        if priority_colors:
            color_cycle = cycle(priority_colors + ['Black'])  # Add black at the end
        
        while len(diverse_products) < max_products and any(color_groups.values()):
            try:
                color = next(color_cycle)
                if color_groups[color]:
                    product = color_groups[color].pop(0)
                    diverse_products.append(product)
                else:
                    # Remove empty color group
                    color_groups.pop(color, None)
                    if color_groups:
                        available_colors = list(color_groups.keys())
                        priority_colors = [c for c in available_colors if c.lower() != 'black']
                        if priority_colors:
                            color_cycle = cycle(priority_colors + [c for c in available_colors if c.lower() == 'black'])
                        else:
                            color_cycle = cycle(available_colors)
                    else:
                        break
            except StopIteration:
                break
        
        return diverse_products
    
    def _apply_enhanced_apple_color_diversity(self, apple_products: List[Dict], max_products: int) -> List[Dict]:
        """Apply enhanced color diversity for Apple products"""
        if not apple_products:
            return []
        
        # Extract colors for all Apple products
        for product in apple_products:
            product['extracted_color'] = self._extract_apple_product_colors(product['product_name'], product.get('subcategory', ''))
        
        # Group by color
        color_groups = defaultdict(list)
        for product in apple_products:
            color = product['extracted_color']
            color_groups[color].append(product)
        
        # Sort each color group by sales
        for color in color_groups:
            color_groups[color].sort(key=lambda p: p.get('frequency', 0), reverse=True)
        
        # Create diverse selection with Apple color priorities
        diverse_products = []
        
        # Apple color priority: premium colors first, then standard colors
        apple_color_priority = [
            'Electric Orange', 'Mallard Green', 'Dark Cherry', 'English Lavender',  # Premium colors
            'Blue', 'White', 'Red', 'Purple', 'Green', 'Yellow',  # Standard colors
            'Black', 'Gray', 'Default'  # Basic colors last
        ]
        
        # Reorder colors by priority
        available_colors = []
        for priority_color in apple_color_priority:
            if priority_color in color_groups and color_groups[priority_color]:
                available_colors.append(priority_color)
        
        # Add any remaining colors not in priority list
        for color in color_groups:
            if color not in available_colors and color_groups[color]:
                available_colors.append(color)
        
        color_cycle = cycle(available_colors) if available_colors else []
        
        while len(diverse_products) < max_products and any(color_groups.values()):
            try:
                color = next(color_cycle)
                if color_groups[color]:
                    product = color_groups[color].pop(0)
                    diverse_products.append(product)
                else:
                    # Remove empty color group
                    color_groups.pop(color, None)
                    if color_groups:
                        # Rebuild available colors
                        available_colors = [c for c in apple_color_priority if c in color_groups and color_groups[c]]
                        for color in color_groups:
                            if color not in available_colors and color_groups[color]:
                                available_colors.append(color)
                        color_cycle = cycle(available_colors) if available_colors else []
                    else:
                        break
            except StopIteration:
                break
        
        return diverse_products
    
    def _extract_gripp_case_color(self, product_name: str) -> str:
        """Extract actual Gripp case color from product name"""
        product_lower = product_name.lower()
        
        # Common Gripp case colors - expanded list
        gripp_colors = {
            'black': 'Black',
            'blue': 'Blue', 
            'sky blue': 'Sky Blue',
            'dark blue': 'Dark Blue',
            'green': 'Green',
            'dark green': 'Dark Green',
            'red': 'Red',
            'purple': 'Purple',
            'orange': 'Orange',
            'yellow': 'Yellow',
            'pink': 'Pink',
            'gray': 'Gray',
            'grey': 'Gray',
            'white': 'White',
            'clear': 'Clear',
            'dark': 'Dark',
            'light': 'Light'
        }
        
        # Check for color matches (prioritize longer matches first)
        sorted_colors = sorted(gripp_colors.keys(), key=len, reverse=True)
        for color_key in sorted_colors:
            if color_key in product_lower:
                return gripp_colors[color_key]
        
        return 'Black'  # Default fallback
    
    def _extract_apple_product_colors(self, product_name: str, subcategory: str) -> str:
        """Extract Apple product colors with official Apple color names"""
        # Check subcategory first
        if subcategory and subcategory not in ['Size 7.9-Inch', 'Size 10.2-Inch', 'Size 10.9-Inch', 'Size 11.0-Inch', 'Size 12.9-Inch', 'Size 13.0-Inch']:
            return subcategory
        
        product_lower = product_name.lower()
        
        # Official Apple iPad accessory colors
        apple_colors = {
            'electric orange': 'Electric Orange',
            'mallard green': 'Mallard Green', 
            'dark cherry': 'Dark Cherry',
            'english lavender': 'English Lavender',
            'black': 'Black',
            'white': 'White',
            'blue': 'Blue',
            'red': 'Red',
            'green': 'Green',
            'purple': 'Purple',
            'yellow': 'Yellow',
            'orange': 'Orange',
            'pink': 'Pink',
            'gray': 'Gray',
            'grey': 'Gray',
            'silver': 'Silver',
            'gold': 'Gold'
        }
        
        # Check for color matches (prioritize longer matches first)
        sorted_colors = sorted(apple_colors.keys(), key=len, reverse=True)
        for color_key in sorted_colors:
            if color_key in product_lower:
                return apple_colors[color_key]
        
        return 'Default'
    
    def _fill_brand_rows_with_hard_boundary(self, grid: List[List[Dict]], products_by_model: Dict, 
                                           assigned_rows: List[int], brand: str):
        """Fill brand-specific rows with STRICT boundary enforcement and COLOR DIVERSITY"""
        
        # Get all products for this brand with color diversity applied
        all_brand_products = []
        for model_products in products_by_model.values():
            all_brand_products.extend(model_products)
        
        # Apply color diversity to the brand products
        if brand.lower() == 'gripp':
            diverse_products = self._apply_enhanced_gripp_color_diversity(all_brand_products, len(assigned_rows) * len(grid[0]))
        else:
            diverse_products = self._apply_enhanced_apple_color_diversity(all_brand_products, len(assigned_rows) * len(grid[0]))
        
        # Fill by column priority (model-specific columns) with color diversity
        product_index = 0
        for col, (model, model_info) in enumerate(self.ipad_models.items()):
            if col >= len(grid[0]):  # Don't exceed grid width
                break
                
            # Get model-specific products with color diversity
            model_products = [p for p in diverse_products if p.get('ipad_model') == model]
            if not model_products:
                model_products = diverse_products  # Fallback to any product
            
            # Fill this column's assigned rows with diverse products
            for row in assigned_rows:
                if model_products:
                    product = model_products[product_index % len(model_products)]
                    grid[row][col] = product.copy()  # Use copy to allow reuse
                    grid[row][col]['grid_position'] = (row, col)
                    grid[row][col]['positioning_reason'] = f'{brand}_color_diverse'
                    product_index += 1
    
    def _fill_all_empty_spaces_with_reuse(self, grid: List[List[Dict]], apple_products: List[Dict], 
                                         gripp_products: List[Dict], apple_rows: List[int], gripp_rows: List[int]):
        """Fill ALL empty spaces with product reuse, maintaining hard boundaries when possible"""
        
        # Create reusable product pools
        apple_pool = apple_products * 5 if apple_products else []  # 5x pool for extensive reuse
        gripp_pool = gripp_products * 5 if gripp_products else []  # 5x pool for extensive reuse
        
        # If one brand is missing, use the available brand to fill ALL spaces
        if not apple_pool and gripp_pool:
            # No Apple products - fill entire grid with Gripp (maintaining visual organization)
            self._fill_entire_grid_with_single_brand(grid, gripp_pool, 'gripp')
            return
        elif not gripp_pool and apple_pool:
            # No Gripp products - fill entire grid with Apple (maintaining visual organization)
            self._fill_entire_grid_with_single_brand(grid, apple_pool, 'apple')
            return
        
        # Both brands available - maintain hard boundaries
        apple_index = 0
        gripp_index = 0
        
        # Fill all empty positions with strict boundary enforcement
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] is None:
                    
                    if row in apple_rows and apple_pool:
                        # Apple rows - use Apple products only
                        product = apple_pool[apple_index % len(apple_pool)]
                        grid[row][col] = product.copy()
                        grid[row][col]['grid_position'] = (row, col)
                        grid[row][col]['positioning_reason'] = 'apple_boundary_fill'
                        grid[row][col]['reused'] = apple_index >= len(apple_products)
                        apple_index += 1
                        
                    elif row in gripp_rows and gripp_pool:
                        # Gripp rows - use Gripp products only
                        product = gripp_pool[gripp_index % len(gripp_pool)]
                        grid[row][col] = product.copy()
                        grid[row][col]['grid_position'] = (row, col)
                        grid[row][col]['positioning_reason'] = 'gripp_boundary_fill'
                        grid[row][col]['reused'] = gripp_index >= len(gripp_products)
                        gripp_index += 1
    
    def _fill_entire_grid_with_single_brand(self, grid: List[List[Dict]], product_pool: List[Dict], brand: str):
        """Fill entire grid with single brand when the other brand is unavailable"""
        
        product_index = 0
        
        # Fill all empty positions
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] is None and product_pool:
                    product = product_pool[product_index % len(product_pool)]
                    grid[row][col] = product.copy()
                    grid[row][col]['grid_position'] = (row, col)
                    grid[row][col]['positioning_reason'] = f'{brand}_single_brand_fill'
                    grid[row][col]['reused'] = product_index >= (len(product_pool) // 5)  # Original pool size
                    product_index += 1
    
    def _group_products_by_model(self, products: List[Dict]) -> Dict[str, List[Dict]]:
        """Group products by iPad model for column dedication"""
        grouped = {model: [] for model in self.ipad_models.keys()}
        
        for product in products:
            model = product.get('ipad_model', 'iPad Base')
            if model in grouped:
                grouped[model].append(product)
            else:
                # Fallback for unknown models
                grouped['iPad Base'].append(product)
        
        return grouped
    
    def _apply_color_diversity(self, products: List[Dict], max_products: int) -> List[Dict]:
        """Apply color diversity to third-party products"""
        if not products:
            return []
        
        # Sort by sales first
        products.sort(key=lambda p: p.get('frequency', 0), reverse=True)
        
        # Group by brand for diversity
        brand_groups = defaultdict(list)
        for product in products:
            brand = product.get('brand', 'Unknown')
            brand_groups[brand].append(product)
        
        # Create diverse selection
        diverse_products = []
        brand_cycle = cycle(brand_groups.keys()) if brand_groups else []
        
        # Add color information for visual diversity
        color_palette = [
            '#00C851',  # Green (Gripp)
            '#FF6B35',  # Orange (STM)
            '#8E44AD',  # Purple (Tucano)
            '#E74C3C',  # Red (tomtoc)
            '#0066CC',  # Blue (Logitech)
            '#F39C12',  # Yellow (Muvtech)
            '#2C3E50'   # Dark gray (others)
        ]
        
        color_index = 0
        while len(diverse_products) < max_products and any(brand_groups.values()):
            try:
                brand = next(brand_cycle)
                if brand_groups[brand]:
                    product = brand_groups[brand].pop(0)
                    # Add color diversity
                    product['tpa_color'] = color_palette[color_index % len(color_palette)]
                    diverse_products.append(product)
                    color_index += 1
                else:
                    # Remove empty brand from cycle
                    brand_groups.pop(brand, None)
                    if brand_groups:
                        brand_cycle = cycle(brand_groups.keys())
                    else:
                        break
            except StopIteration:
                break
        
        return diverse_products
    
    def generate_ipad_planogram_visual(self, grid: List[List[Dict]], store_name: str = "iPad Accessories Store", 
                                     wall_number: int = 1, output_path: str = "ipad_planogram.png") -> bool:
        """
        Generate professional iPad accessories planogram with visual rendering
        Fixed version that addresses black PNG issue and ensures proper rendering
        """
        try:
            # Force matplotlib to use Agg backend to prevent display issues
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib.patches import Rectangle, FancyBboxPatch
            
            # Ensure output path is in the main project output directory for web serving
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent.absolute()
            main_output_dir = project_root / 'output'
            main_output_dir.mkdir(exist_ok=True)

            print(f"DEBUG: Original output_path: {output_path}")
            print(f"DEBUG: Project root: {project_root}")
            print(f"DEBUG: Main output dir: {main_output_dir}")

            if not output_path.startswith(str(main_output_dir)):
                output_path = str(main_output_dir / output_path)
                print(f"DEBUG: Updated output_path: {output_path}")
            
            rows = len(grid)
            cols = len(grid[0]) if grid else 0
            
            if rows == 0 or cols == 0:
                print("Error: Empty grid provided")
                return False
            
            print(f"Generating visual for {rows}x{cols} grid with {sum(1 for row in grid for cell in row if cell)} products")
            
            # Calculate figure dimensions for proper aspect ratio
            fig_width = max(12, cols * 2.5)  # Ensure minimum width
            fig_height = max(10, rows * 1.5)  # Ensure minimum height
            
            # Create figure with explicit white background
            fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor='white')
            ax.set_xlim(0, cols)
            ax.set_ylim(0, rows)
            ax.set_aspect('equal')
            
            # Set explicit white background
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            
            # Draw grid and products
            products_drawn = 0
            for row in range(rows):
                for col in range(cols):
                    product = grid[row][col]
                    
                    # Calculate position (flip row for visual display)
                    x = col
                    y = rows - row - 1
                    
                    if product:
                        self._draw_ipad_product_rectangle(ax, product, x, y)
                        products_drawn += 1
                    else:
                        # Draw blank facing with subtle indication
                        rect = Rectangle((x + 0.1, y + 0.1), 0.8, 0.8, 
                                       linewidth=1, 
                                       edgecolor='#E0E0E0',
                                       facecolor='#F8F8F8',
                                       alpha=0.7,
                                       linestyle='--')
                        ax.add_patch(rect)
                        
                        # Add "BLANK FACING" text for empty slots
                        ax.text(x + 0.5, y + 0.5, 'BLANK\nFACING',
                               ha='center', va='center',
                               fontsize=6,
                               color='#999999',
                               alpha=0.8,
                               style='italic')
            
            print(f"Drew {products_drawn} product rectangles")
            
            # Add grid lines with better visibility
            for i in range(rows + 1):
                ax.axhline(i, color='#CCCCCC', linewidth=1, alpha=0.8)
            for i in range(cols + 1):
                ax.axvline(i, color='#CCCCCC', linewidth=1, alpha=0.8)
            
            # Add headers and labels
            self._add_ipad_planogram_headers(ax, store_name, wall_number, rows, cols)
            self._add_ipad_model_column_labels(ax, cols, rows)
            self._add_ipad_category_row_labels(ax, rows)
            
            # Remove axes but keep the plot area visible
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            # Save with explicit settings to prevent black PNG
            plt.tight_layout(pad=1.0)
            
            # Use multiple save attempts with different settings
            try:
                plt.savefig(output_path, 
                           dpi=300, 
                           bbox_inches='tight', 
                           facecolor='white', 
                           edgecolor='none',
                           format='png',
                           transparent=False)
                print(f"iPad planogram saved successfully to: {output_path}")
            except Exception as save_error:
                print(f"First save attempt failed: {save_error}")
                # Try alternative save method
                plt.savefig(output_path, 
                           dpi=150, 
                           bbox_inches='tight', 
                           facecolor='white',
                           format='png')
                print(f"iPad planogram saved with alternative method to: {output_path}")
            
            plt.close(fig)
            
            # Verify file was created and has content
            import os
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                print(f"✅ File verification successful: {os.path.getsize(output_path)} bytes")
                return True
            else:
                print(f"❌ File verification failed: File size {os.path.getsize(output_path) if os.path.exists(output_path) else 0} bytes")
                return False
            
        except Exception as e:
            print(f"Error generating iPad planogram: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _draw_ipad_product_rectangle(self, ax, product: Dict, x: float, y: float):
        """Draw iPad product rectangle with realistic sizing, colors, and proper spacing - Fixed version"""
        
        try:
            # Import required modules
            from matplotlib.patches import Rectangle, FancyBboxPatch
            
            # Get product details with safe defaults
            brand = product.get('brand', 'Default')
            category = product.get('category', 'case')
            ipad_model = product.get('ipad_model', 'iPad Base')
            sales = product.get('frequency', 0)
            product_name = product.get('product_name', 'Unknown Product')
            
            # Calculate realistic product size based on iPad model with proper scaling
            base_width = 0.8
            base_height = 0.85
            
            # Get size scale from model specifications
            model_info = self.ipad_models.get(ipad_model, {'size_scale': 0.8})
            size_scale = model_info.get('size_scale', 0.8)
            
            # Apply size scaling: Mini smallest, Base medium, Air/Pro same (largest)
            width = base_width * size_scale
            height = base_height * size_scale
            
            # Keyboard cases get slight size boost
            if category == 'keyboard case':
                width *= 1.1
                height *= 1.15
            
            # Center the product in the grid cell
            offset_x = (1.0 - width) / 2
            offset_y = (1.0 - height) / 2
            
            # Get brand color with safe fallback
            brand_color = self.brand_colors.get(brand, '#607D8B')
            
            # Extract color from product name for better color representation
            product_color = self._extract_product_color(product_name, brand)
            display_color = self._extract_display_color(product_name)
            
            # Set background color based on brand and product
            if brand.lower() == 'gripp':
                bg_color = product_color
                alpha = 0.85
                edge_width = 1.5
            elif brand.lower() == 'apple':
                bg_color = '#F8F9FA'  # Light background for Apple
                alpha = 0.9
                edge_width = 2.0
            else:
                bg_color = '#FFFFFF'
                alpha = 0.9
                edge_width = 1.0
            
            # Draw main product rectangle with safe parameters
            try:
                rect = Rectangle((x + offset_x, y + offset_y), width, height,
                               facecolor=bg_color,
                               edgecolor=product_color,
                               linewidth=edge_width,
                               alpha=alpha)
                ax.add_patch(rect)
            except Exception as rect_error:
                print(f"Error drawing rectangle: {rect_error}")
                # Fallback to simple rectangle
                rect = Rectangle((x + 0.1, y + 0.1), 0.8, 0.8,
                               facecolor='lightblue',
                               edgecolor='navy',
                               linewidth=1)
                ax.add_patch(rect)
            
            # Determine text color based on background
            if brand.lower() == 'gripp' and any(color in product_name.lower() for color in ['black', 'dark', 'blue', 'purple']):
                text_color = 'white'
            else:
                text_color = '#2C3E50'  # Dark text
            
            # Add color indicator bar at top
            try:
                color_bar_height = height * 0.15
                color_rect = Rectangle((x + offset_x + 0.05, y + offset_y + height - color_bar_height - 0.05), 
                                      width - 0.1, color_bar_height,
                                      facecolor=product_color,
                                      alpha=0.9)
                ax.add_patch(color_rect)
            except Exception as bar_error:
                print(f"Error drawing color bar: {bar_error}")
            
            # Add text information with safe font sizes
            text_scale = min(width, height)
            base_font_size = max(6, 8 * text_scale)  # Ensure minimum readable size
            
            try:
                # Brand name (top, in color bar)
                ax.text(x + 0.5, y + offset_y + height - 0.1, brand, 
                       ha='center', va='center', 
                       fontsize=base_font_size, fontweight='bold', 
                       color='white')
                
                # iPad model (upper middle)
                model_short = ipad_model.replace('iPad ', '')
                ax.text(x + 0.5, y + offset_y + height * 0.65,
                       model_short,
                       ha='center', va='center',
                       fontsize=base_font_size * 0.8, fontweight='bold',
                       color=text_color)
                
                # Color name (middle)
                if display_color and display_color != 'Standard':
                    ax.text(x + 0.5, y + offset_y + height * 0.45,
                           display_color,
                           ha='center', va='center',
                           fontsize=base_font_size * 0.6,
                           color=text_color,
                           fontweight='bold')
                
                # Category (lower middle)
                category_display = category.replace('_', ' ').title()
                ax.text(x + 0.5, y + offset_y + height * 0.25,
                       category_display,
                       ha='center', va='center',
                       fontsize=base_font_size * 0.6,
                       color=text_color)
                
                # Sales number (bottom)
                ax.text(x + 0.5, y + offset_y + 0.15,
                       f"{sales}",
                       ha='center', va='center',
                       fontsize=base_font_size * 0.8, fontweight='bold',
                       color=text_color)
                       
            except Exception as text_error:
                print(f"Error adding text: {text_error}")
                # Fallback text
                ax.text(x + 0.5, y + 0.5, f"{brand}\n{sales}",
                       ha='center', va='center',
                       fontsize=8, color='black')
            
        except Exception as e:
            print(f"Error in _draw_ipad_product_rectangle: {e}")
            # Draw a simple fallback rectangle
            rect = Rectangle((x + 0.1, y + 0.1), 0.8, 0.8,
                           facecolor='lightgray',
                           edgecolor='black',
                           linewidth=1)
            ax.add_patch(rect)
            ax.text(x + 0.5, y + 0.5, f"{product.get('brand', 'Unknown')}\n{product.get('frequency', 0)}",
                   ha='center', va='center', fontsize=8, color='black')
    
    def _extract_product_color(self, product_name: str, brand: str) -> str:
        """Extract product color from name with DATA-BACKED color mapping"""
        product_lower = product_name.lower()
        
        # Universal color mapping based on actual data
        color_mapping = {
            # Apple official colors
            'electric orange': '#FF6B00',
            'mallard green': '#00C851', 
            'dark cherry': '#8B0000',
            'english lavender': '#9370DB',
            'charcoal gray': '#36454F',
            'denim': '#1E3A8A',
            'light violet': '#DDA0DD',
            'marine blue': '#0077BE',
            'sage': '#87CEEB',
            
            # Common colors
            'black': '#1C1C1E',
            'white': '#F8F8FF',
            'blue': '#1976D2',
            'red': '#D32F2F',
            'green': '#388E3C',
            'yellow': '#FBC02D',
            'orange': '#F57C00',
            'purple': '#7B1FA2',
            'pink': '#C2185B',
            'gray': '#616161',
            'grey': '#616161',
            'silver': '#C0C0C0',
            'gold': '#FFD700',
            
            # Extended colors from data
            'cyprus green': '#4A6741',
            'dark blue': '#003366',
            'dark grey': '#2F2F2F',
            'deep navy': '#000080',
            'midnight blue': '#191970',
            'military green': '#4B5320',
            'petroleum': '#1C4E80',
            'rainbow pink': '#FF69B4',
            'sky blue': '#87CEEB',
            'space grey': '#4A4A4A',
            'tile blue': '#6495ED',
            'watermelon': '#FF7F7F',
            'lemonade': '#FFFACD',
            'tan': '#D2B48C',
            'clear': '#E3F2FD'
        }
        
        # Sort by length (longest first) to match more specific colors first
        sorted_colors = sorted(color_mapping.items(), key=lambda x: len(x[0]), reverse=True)
        
        for color_name, color_code in sorted_colors:
            if color_name in product_lower:
                return color_code
        
        # Brand-specific defaults
        if brand.lower() == 'apple':
            return '#007AFF'  # Apple blue
        elif brand.lower() == 'gripp':
            return '#00C851'  # Gripp green
        else:
            return self.brand_colors.get(brand, '#607D8B')
    
    def _extract_display_color(self, product_name: str) -> str:
        """Extract display color name from product - DATA-BACKED from actual product names"""
        
        # First try to extract from " - Color" pattern (most accurate)
        if ' - ' in product_name:
            parts = product_name.split(' - ')
            if len(parts) > 1:
                potential_color = parts[-1].strip()
                # Filter out non-color suffixes
                non_colors = ['11 inch', 'DEMO', 'NEW', 'US English']
                if potential_color not in non_colors and len(potential_color) < 20:
                    return potential_color
        
        # Fallback to searching in product name for known colors
        product_lower = product_name.lower()
        
        # Extended color list based on actual data
        data_colors = [
            'electric orange', 'mallard green', 'dark cherry', 'english lavender',
            'charcoal gray', 'cyprus green', 'dark blue', 'dark grey', 'deep navy',
            'denim', 'light violet', 'marine blue', 'midnight blue', 'military green',
            'petroleum', 'rainbow pink', 'sky blue', 'space grey', 'tile blue',
            'watermelon', 'lemonade', 'sage', 'black', 'white', 'blue', 'red', 
            'green', 'yellow', 'orange', 'purple', 'pink', 'gray', 'grey', 
            'silver', 'gold', 'clear', 'transparent', 'tan'
        ]
        
        # Sort by length (longest first) to match more specific colors first
        data_colors.sort(key=len, reverse=True)
        
        for color in data_colors:
            if color in product_lower:
                return color.title()
        
        return 'Standard'
    
    def _add_category_icon(self, ax, category: str, x: float, y: float, size: float):
        """Add category-specific visual indicators"""
        
        icon_color = self.colors['text_secondary']
        
        if category == 'case':
            # Draw simple rectangle for case
            icon_rect = Rectangle((x, y), size, size * 0.6,
                                facecolor='none',
                                edgecolor=icon_color,
                                linewidth=1.5)
            ax.add_patch(icon_rect)
        
        elif category == 'folio':
            # Draw folded rectangle for folio
            icon_rect1 = Rectangle((x, y), size * 0.6, size * 0.6,
                                 facecolor='none',
                                 edgecolor=icon_color,
                                 linewidth=1.5)
            icon_rect2 = Rectangle((x + size * 0.4, y), size * 0.6, size * 0.6,
                                 facecolor='none',
                                 edgecolor=icon_color,
                                 linewidth=1.5)
            ax.add_patch(icon_rect1)
            ax.add_patch(icon_rect2)
        
        elif category == 'keyboard case':
            # Draw keyboard-like pattern
            for i in range(3):
                for j in range(4):
                    key_rect = Rectangle((x + j * size * 0.2, y + i * size * 0.15), 
                                       size * 0.15, size * 0.1,
                                       facecolor=icon_color,
                                       alpha=0.6)
                    ax.add_patch(key_rect)
        
        elif category in ['armor case', 'hardshell']:
            # Draw reinforced rectangle
            icon_rect = Rectangle((x, y), size, size * 0.6,
                                facecolor='none',
                                edgecolor=icon_color,
                                linewidth=2.5)
            ax.add_patch(icon_rect)
            # Add corner reinforcements
            for corner_x, corner_y in [(x, y), (x + size - size*0.2, y), 
                                     (x, y + size*0.4), (x + size - size*0.2, y + size*0.4)]:
                corner_rect = Rectangle((corner_x, corner_y), size * 0.2, size * 0.2,
                                      facecolor=icon_color,
                                      alpha=0.4)
                ax.add_patch(corner_rect)
    
    def _add_ipad_planogram_headers(self, ax, store_name: str, wall_number: int, rows: int, cols: int):
        """Add headers and title information to iPad planogram"""
        
        # Main title
        title = f"{store_name} - iPad Accessories Wall {wall_number}"
        ax.text(cols/2, rows + 0.5, title,
               ha='center', va='center',
               fontsize=14, fontweight='bold',
               color=self.colors['text_primary'])
        
        # Subtitle with grid info
        subtitle = f"8×6 Grid Layout | {rows * cols} Positions | Optimized for iPad Accessories"
        ax.text(cols/2, rows + 0.2, subtitle,
               ha='center', va='center',
               fontsize=10,
               color=self.colors['text_secondary'])
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        ax.text(cols - 0.1, rows + 0.1, f"Generated: {timestamp}",
               ha='right', va='center',
               fontsize=8,
               color=self.colors['text_secondary'])
    
    def _add_ipad_model_column_labels(self, ax, cols: int, rows: int):
        """Add iPad model labels for dedicated columns"""
        
        model_labels = {
            0: "Mini\n7.9\"",
            1: "Base\n10.2\"/10.9\"", 
            2: "Air\n10.9\"/11\"",
            3: "Pro\n11\"/12.9\""
        }
        
        for col in range(min(cols, 4)):  # Only 4 columns now
            if col in model_labels:
                ax.text(col + 0.5, -0.3, model_labels[col],
                       ha='center', va='center',
                       fontsize=9, fontweight='bold',
                       color=self.colors['text_primary'])
    
    def _add_ipad_category_row_labels(self, ax, rows: int):
        """Add category labels for clean 6-row structure"""
        
        category_labels = {
            0: "Apple\nPremium",
            1: "Apple\nCore", 
            2: "Apple\nValue",
            3: "Gripp\nPremium",
            4: "Gripp\nCore",
            5: "Gripp\nValue"
        }
        
        for row in range(rows):
            visual_row = rows - row - 1  # Flip for display
            if row in category_labels:
                ax.text(-0.3, visual_row + 0.5, category_labels[row],
                       ha='center', va='center',
                       fontsize=8, fontweight='bold',
                       color=self.colors['text_primary'],
                       rotation=90)
    
    def generate_ipad_planogram_report(self, grid: List[List[Dict]], output_path: str = "ipad_planogram_report.txt") -> bool:
        """Generate detailed iPad planogram report"""
        
        try:
            # Ensure output path is in the main project output directory for web serving
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent.absolute()
            main_output_dir = project_root / 'output'
            main_output_dir.mkdir(exist_ok=True)

            if not output_path.startswith(str(main_output_dir)):
                output_path = str(main_output_dir / output_path)
                
            with open(output_path, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("iPad ACCESSORIES PLANOGRAM REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Grid summary
                rows = len(grid)
                cols = len(grid[0]) if grid else 0
                total_positions = rows * cols
                
                # Count filled positions and analyze products
                filled_positions = 0
                brand_counts = defaultdict(int)
                category_counts = defaultdict(int)
                model_counts = defaultdict(int)
                sales_total = 0
                
                products_list = []
                
                for row in range(rows):
                    for col in range(cols):
                        product = grid[row][col]
                        if product:
                            filled_positions += 1
                            brand_counts[product.get('brand', 'Unknown')] += 1
                            category_counts[product.get('category', 'unknown')] += 1
                            model_counts[product.get('ipad_model', 'Unknown')] += 1
                            sales_total += product.get('frequency', 0)
                            products_list.append(product)
                
                # Grid utilization
                utilization = (filled_positions / total_positions) * 100
                
                f.write(f"GRID SUMMARY\n")
                f.write(f"Grid Size: {rows}×{cols} ({total_positions} positions)\n")
                f.write(f"Filled Positions: {filled_positions}\n")
                f.write(f"Utilization: {utilization:.1f}%\n")
                f.write(f"Total Sales Volume: {sales_total}\n")
                f.write(f"Average Sales per Product: {sales_total/filled_positions:.1f}\n\n")
                
                # Brand distribution
                f.write("BRAND DISTRIBUTION\n")
                f.write("-" * 40 + "\n")
                for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / filled_positions) * 100
                    f.write(f"{brand:20} {count:3d} products ({percentage:5.1f}%)\n")
                f.write("\n")
                
                # Category distribution
                f.write("CATEGORY DISTRIBUTION\n")
                f.write("-" * 40 + "\n")
                for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / filled_positions) * 100
                    f.write(f"{category:20} {count:3d} products ({percentage:5.1f}%)\n")
                f.write("\n")
                
                # iPad model distribution
                f.write("IPAD MODEL DISTRIBUTION\n")
                f.write("-" * 40 + "\n")
                for model, count in sorted(model_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / filled_positions) * 100
                    f.write(f"{model:20} {count:3d} products ({percentage:5.1f}%)\n")
                f.write("\n")
                
                # Top products by sales
                f.write("TOP PRODUCTS BY SALES\n")
                f.write("-" * 80 + "\n")
                top_products = sorted(products_list, key=lambda p: p.get('frequency', 0), reverse=True)[:10]
                
                for i, product in enumerate(top_products, 1):
                    name = product['product_name'][:50] + '...' if len(product['product_name']) > 50 else product['product_name']
                    brand = product.get('brand', 'Unknown')
                    model = product.get('ipad_model', 'Unknown')
                    sales = product.get('frequency', 0)
                    position = product.get('grid_position', (0, 0))
                    
                    f.write(f"{i:2d}. {name}\n")
                    f.write(f"    Brand: {brand} | Model: {model} | Sales: {sales} | Position: {position}\n\n")
                
                # Grid layout
                f.write("GRID LAYOUT\n")
                f.write("-" * 80 + "\n")
                f.write("Position format: (Row,Col) Brand - Product Name [Sales]\n\n")
                
                for row in range(rows):
                    f.write(f"Row {row}: ")
                    for col in range(cols):
                        product = grid[row][col]
                        if product:
                            brand = product.get('brand', 'Unknown')[:4]
                            sales = product.get('frequency', 0)
                            f.write(f"({row},{col}){brand}[{sales}] ")
                        else:
                            f.write(f"({row},{col})Empty ")
                    f.write("\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")
            
            print(f"iPad planogram report saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating iPad planogram report: {e}")
            return False

# Test functions
def test_ipad_model_classification():
    """Test the iPad model classification engine"""
    print("=== Testing iPad Model Classification Engine ===")
    
    generator = IPadAccessoriesGenerator('.')
    
    # Test model classification
    products = generator.load_ipad_data()
    model_groups = generator.classify_products_by_model(products)
    
    print(f"Model Classification Results:")
    for model, products_list in model_groups.items():
        if products_list:
            print(f"\n{model}: {len(products_list)} products")
            
            # Show top 3 products for each model
            top_products = sorted(products_list, key=lambda p: p['frequency'], reverse=True)[:3]
            for i, product in enumerate(top_products, 1):
                name = product['product_name'][:50] + '...' if len(product['product_name']) > 50 else product['product_name']
                print(f"  {i}. {product['brand']} - {name} ({product['frequency']} sales)")
    
    # Test compatibility matrix
    print(f"\n=== iPad Model Compatibility Matrix ===")
    compatibility = generator.get_model_compatibility_matrix()
    
    for model, info in compatibility.items():
        print(f"\n{model} ({info['display_size']}):")
        print(f"  Products: {info['product_count']}")
        print(f"  Total Sales: {info['total_sales']}")
        print(f"  Avg Sales/Product: {info['avg_sales_per_product']:.1f}")
        print(f"  Grid Columns: {info['grid_columns']}")
        print(f"  Avg Dimensions: {info['dimensions']['avg_width']:.1f}×{info['dimensions']['avg_height']:.1f} cm")
        print(f"  Top Categories: {list(info['categories'].items())[:3]}")
        print(f"  Top Brands: {list(info['top_brands'].items())}")
    
    # Test size-based allocation
    print(f"\n=== Size-Based Allocation Strategy ===")
    allocation = generator.get_size_based_allocation()
    
    for model, strategy in allocation.items():
        print(f"\n{model}:")
        print(f"  Allocation: {strategy['allocation_percentage']:.1f}% ({strategy['product_count']} products)")
        print(f"  Grid Columns: {strategy['grid_columns']} ({strategy['column_count']} columns)")
        print(f"  Dimensions: {strategy['dimensions'][0]}×{strategy['dimensions'][1]} cm")
        print(f"  Space Requirements: {strategy['space_requirements']['total_width_cm']:.1f}×{strategy['space_requirements']['total_height_cm']:.1f} cm")
        print(f"  Space Efficiency: {strategy['space_requirements']['space_efficiency']:.1%}")
        print(f"  Recommended Positions: {len(strategy['recommended_positions'])} positions")
    
    return len(model_groups) > 0

def test_category_organization():
    """Test the category-based organization system"""
    print("=== Testing Category-Based Organization System ===")
    
    generator = IPadAccessoriesGenerator('.')
    products = generator.load_ipad_data()
    
    # Test category organization
    category_groups = generator.organize_products_by_category(products)
    
    print(f"Category Organization Results:")
    for category, products_list in category_groups.items():
        if products_list:
            print(f"\n{category.upper()}: {len(products_list)} products")
            
            # Show top 3 products for each category
            top_products = sorted(products_list, key=lambda p: p['frequency'], reverse=True)[:3]
            for i, product in enumerate(top_products, 1):
                name = product['product_name'][:45] + '...' if len(product['product_name']) > 45 else product['product_name']
                print(f"  {i}. {product['brand']} - {name} ({product['frequency']} sales)")
    
    # Test category allocation strategy
    print(f"\n=== Category Allocation Strategy ===")
    allocation = generator.get_category_allocation_strategy()
    
    for category, strategy in allocation.items():
        print(f"\n{category.upper()} ({strategy['description']}):")
        print(f"  Products: {strategy['product_count']} ({strategy['allocation_percentage']:.1f}%)")
        print(f"  Total Sales: {strategy['total_sales']} (avg: {strategy['avg_sales_per_product']:.1f})")
        print(f"  Assigned Rows: {strategy['assigned_rows']} ({strategy['row_count']} rows)")
        print(f"  Products per Row: {strategy['products_per_row']}")
        print(f"  Priority Multiplier: {strategy['priority_multiplier']}")
        print(f"  Top Brands: {list(strategy['top_brands'].items())[:3]}")
        print(f"  Space Requirements: {strategy['space_requirements']['total_width_cm']:.1f}×{strategy['space_requirements']['total_height_cm']:.1f} cm")
        print(f"  Space Efficiency: {strategy['space_requirements']['space_efficiency']:.1%}")
    
    # Test category priority ranking
    print(f"\n=== Category Priority Ranking ===")
    priority_ranking = generator.get_category_priority_ranking()
    
    for i, (category, info) in enumerate(priority_ranking, 1):
        print(f"{i}. {category.upper()}: Score {info['composite_score']:.2f}")
        print(f"   Sales: {info['sales_contribution']}, Products: {info['product_count']}")
        print(f"   Rows: {info['assigned_rows']}, Description: {info['description']}")
    
    # Test optimized category placement
    print(f"\n=== Optimized Category Placement ===")
    optimized = generator.optimize_category_placement(products)
    
    for category, products_list in optimized.items():
        if products_list:
            print(f"\n{category.upper()} (Optimized Order):")
            for i, product in enumerate(products_list[:5], 1):  # Show top 5
                name = product['product_name'][:40] + '...' if len(product['product_name']) > 40 else product['product_name']
                print(f"  {i}. {product['brand']} {product['ipad_model']} - {name} ({product['frequency']} sales)")
    
    return len(category_groups) > 0

def test_dimension_aware_layout():
    """Test the dimension-aware layout engine"""
    print("=== Testing Dimension-Aware Layout Engine ===")
    
    generator = IPadAccessoriesGenerator('.')
    products = generator.load_ipad_data()
    
    # Test product dimension calculations
    print(f"Product Dimension Analysis:")
    test_products = products[:10]  # Test with first 10 products
    
    for product in test_products:
        width, height, spacing = generator.calculate_product_dimensions(product)
        name = product['product_name'][:40] + '...' if len(product['product_name']) > 40 else product['product_name']
        print(f"\n{product['brand']} {product['ipad_model']}:")
        print(f"  Product: {name}")
        print(f"  Category: {product['category']}")
        print(f"  Original: {product['width']:.1f}×{product['height']:.1f}×{product['depth']:.1f} cm")
        print(f"  Display: {width:.1f}×{height:.1f} cm (spacing: {spacing:.1f} cm)")
    
    # Test grid layout dimensions
    print(f"\n=== Grid Layout Dimensions ===")
    grid_size = (8, 6)  # 8x6 iPad planogram
    
    # Apply dimension-aware positioning
    positioned_products = generator.apply_dimension_aware_positioning(products[:48], grid_size)
    
    # Calculate grid layout dimensions
    layout_dims = generator.calculate_grid_layout_dimensions(positioned_products, grid_size)
    
    print(f"Grid Layout Analysis:")
    print(f"  Grid Size: {layout_dims['grid_size'][0]}×{layout_dims['grid_size'][1]}")
    print(f"  Total Dimensions: {layout_dims['total_dimensions']['width_cm']:.1f}×{layout_dims['total_dimensions']['height_cm']:.1f} cm")
    print(f"  Total Dimensions: {layout_dims['total_dimensions']['width_inches']:.1f}×{layout_dims['total_dimensions']['height_inches']:.1f} inches")
    
    print(f"\nRow Heights:")
    for i, height in enumerate(layout_dims['row_heights']):
        print(f"  Row {i}: {height:.1f} cm")
    
    print(f"\nColumn Widths:")
    for i, width in enumerate(layout_dims['col_widths']):
        print(f"  Column {i}: {width:.1f} cm")
    
    # Test category allocations
    print(f"\n=== Category Space Allocations ===")
    for category, allocation in layout_dims['category_allocations'].items():
        print(f"\n{category.upper()} ({allocation['description']}):")
        print(f"  Assigned Rows: {allocation['assigned_rows']}")
        print(f"  Total Height: {allocation['total_height_cm']:.1f} cm")
        print(f"  Products: {allocation['product_count']} ({allocation['products_per_row']:.1f} per row)")
        print(f"  Avg Product Size: {allocation['avg_product_width']:.1f}×{allocation['avg_product_height']:.1f} cm")
        print(f"  Avg Spacing: {allocation['avg_spacing']:.1f} cm")
    
    # Test model allocations
    print(f"\n=== iPad Model Space Allocations ===")
    for model, allocation in layout_dims['model_allocations'].items():
        print(f"\n{model} ({allocation['display_size']}):")
        print(f"  Assigned Columns: {allocation['assigned_columns']}")
        print(f"  Total Width: {allocation['total_width_cm']:.1f} cm")
        print(f"  Products: {allocation['product_count']} ({allocation['products_per_column']:.1f} per column)")
        print(f"  Avg Product Size: {allocation['avg_product_width']:.1f}×{allocation['avg_product_height']:.1f} cm")
        print(f"  Base Dimensions: {allocation['base_dimensions'][0]}×{allocation['base_dimensions'][1]} cm")
    
    # Test shelf specifications
    print(f"\n=== Shelf Implementation Specifications ===")
    for shelf_id, specs in layout_dims['shelf_specifications'].items():
        print(f"\n{shelf_id.upper()}:")
        print(f"  Dimensions: {specs['width_cm']:.1f}×{specs['height_cm']:.1f}×{specs['depth_cm']:.1f} cm")
        print(f"  Primary Category: {specs['primary_category']}")
        print(f"  Load Rating: {specs['load_rating']}")
        print(f"  Mounting: {specs['mounting_type']}")
        print(f"  Material: {specs['recommended_material']}")
        print(f"  Weight Capacity: {specs['weight_capacity_kg']:.1f} kg")
        print(f"  Accessibility: {specs['accessibility']}")
    
    # Test spacing requirements
    print(f"\n=== Spacing Requirements Analysis ===")
    spacing_reqs = layout_dims['spacing_requirements']
    
    print(f"Horizontal Spacing (Columns):")
    for col_id, spacing in spacing_reqs['horizontal_spacing'].items():
        print(f"  {col_id}: {spacing['recommended_spacing']:.1f} cm (max width: {spacing['max_product_width']:.1f} cm)")
    
    print(f"\nVertical Spacing (Rows):")
    for row_id, spacing in spacing_reqs['vertical_spacing'].items():
        print(f"  {row_id}: {spacing['recommended_spacing']:.1f} cm (max height: {spacing['max_product_height']:.1f} cm)")
    
    print(f"\nCategory Transition Buffers:")
    for transition, buffer in spacing_reqs['category_buffers'].items():
        print(f"  {transition}: {buffer['recommended_buffer_cm']:.1f} cm between rows {buffer['between_rows']}")
    
    # Test positioning results
    print(f"\n=== Positioning Results ===")
    positioned_count = len([p for p in positioned_products if p.get('grid_position')])
    overflow_count = len([p for p in positioned_products if p.get('placement_status') == 'overflow'])
    
    print(f"Successfully positioned: {positioned_count} products")
    print(f"Overflow products: {overflow_count} products")
    print(f"Positioning efficiency: {positioned_count / len(positioned_products) * 100:.1f}%")
    
    # Show sample positioned products
    print(f"\nSample Positioned Products:")
    sample_positioned = [p for p in positioned_products if p.get('grid_position')][:8]
    for product in sample_positioned:
        row, col = product['grid_position']
        name = product['product_name'][:35] + '...' if len(product['product_name']) > 35 else product['product_name']
        print(f"  ({row},{col}): {product['brand']} {product['ipad_model']} - {name}")
        print(f"         Size: {product['display_width']:.1f}×{product['display_height']:.1f} cm, Spacing: {product['spacing_needed']:.1f} cm")
    
    return positioned_count > 0

def test_brand_allocation_system():
    """Test the Apple vs third-party brand allocation system"""
    print("=== Testing Brand Allocation System ===")
    
    generator = IPadAccessoriesGenerator('.')
    products = generator.load_ipad_data()
    
    # Test brand allocation strategy
    print(f"Brand Allocation Strategy (40% Apple, 35% Gripp, 25% Others):")
    
    grid_capacity = 48  # 8x6 grid
    allocation_result = generator.implement_brand_allocation_strategy(products, grid_capacity)
    
    # Display allocation summary
    summary = allocation_result['allocation_summary']
    print(f"\nAllocation Summary:")
    print(f"  Target: Apple {summary['target_allocation']['apple']}, Gripp {summary['target_allocation']['gripp']}, Others {summary['target_allocation']['others']}")
    print(f"  Actual: Apple {summary['actual_allocation']['apple']}, Gripp {summary['actual_allocation']['gripp']}, Others {summary['actual_allocation']['others']}")
    print(f"  Percentages: Apple {summary['allocation_percentages']['apple']:.1f}%, Gripp {summary['allocation_percentages']['gripp']:.1f}%, Others {summary['allocation_percentages']['others']:.1f}%")
    print(f"  Grid Utilization: {summary['grid_utilization']:.1f}%")
    
    # Test Apple products with color extraction
    print(f"\n=== Apple Products (Premium Positioning) ===")
    apple_products = allocation_result['apple_products']
    print(f"Apple Products Selected: {len(apple_products)}")
    
    for i, product in enumerate(apple_products[:8], 1):  # Show top 8
        name = product['product_name'][:45] + '...' if len(product['product_name']) > 45 else product['product_name']
        apple_color = product.get('apple_color', 'Standard')
        category = product.get('category', 'case')
        model = product.get('ipad_model', 'iPad Base')
        sales = product.get('frequency', 0)
        
        premium_indicators = []
        if product.get('premium_positioning'):
            premium_indicators.append('Premium')
        if product.get('productivity_premium'):
            premium_indicators.append('Productivity')
        
        indicators_str = f" [{', '.join(premium_indicators)}]" if premium_indicators else ""
        
        print(f"  {i}. {name}")
        print(f"     {model} | {category} | Color: {apple_color} | Sales: {sales}{indicators_str}")
    
    # Test Gripp products by series
    print(f"\n=== Gripp Products (Volume Leader) ===")
    gripp_products = allocation_result['gripp_products']
    print(f"Gripp Products Selected: {len(gripp_products)}")
    
    # Group by series for display
    gripp_by_series = defaultdict(list)
    for product in gripp_products:
        series = product.get('gripp_series', 'Other')
        gripp_by_series[series].append(product)
    
    for series, products in gripp_by_series.items():
        if products:
            print(f"\n  {series} Series ({len(products)} products):")
            for i, product in enumerate(products[:3], 1):  # Show top 3 per series
                name = product['product_name'][:40] + '...' if len(product['product_name']) > 40 else product['product_name']
                model = product.get('ipad_model', 'iPad Base')
                sales = product.get('frequency', 0)
                
                volume_indicator = " [Volume Leader]" if product.get('volume_leader') else ""
                
                print(f"    {i}. {name}")
                print(f"       {model} | Sales: {sales}{volume_indicator}")
    
    # Test other brands with diversity
    print(f"\n=== Other Brands (Visual Diversity) ===")
    other_products = allocation_result['other_products']
    print(f"Other Brand Products Selected: {len(other_products)}")
    
    # Group by brand for display
    other_by_brand = defaultdict(list)
    for product in other_products:
        brand = product.get('brand', 'Default')
        other_by_brand[brand].append(product)
    
    for brand, products in other_by_brand.items():
        if products:
            brand_category = products[0].get('brand_category', 'Standard')
            print(f"\n  {brand} ({brand_category}) - {len(products)} products:")
            
            for i, product in enumerate(products[:2], 1):  # Show top 2 per brand
                name = product['product_name'][:40] + '...' if len(product['product_name']) > 40 else product['product_name']
                model = product.get('ipad_model', 'iPad Base')
                sales = product.get('frequency', 0)
                
                brand_indicators = []
                if product.get('professional_brand'):
                    brand_indicators.append('Professional')
                if product.get('fashion_brand'):
                    brand_indicators.append('Fashion')
                
                indicators_str = f" [{', '.join(brand_indicators)}]" if brand_indicators else ""
                
                print(f"    {i}. {name}")
                print(f"       {model} | Sales: {sales}{indicators_str}")
    
    # Test premium positioning strategy
    print(f"\n=== Premium Positioning Strategy ===")
    grid_size = (8, 6)
    positioned_products = generator.apply_premium_positioning_strategy(allocation_result, grid_size)
    
    # Analyze positioning results
    positioning_tiers = defaultdict(list)
    for product in positioned_products:
        tier = product.get('positioning_tier', 'unassigned')
        positioning_tiers[tier].append(product)
    
    print(f"Positioning Results:")
    for tier, products in positioning_tiers.items():
        print(f"  {tier.title()}: {len(products)} products")
    
    # Show sample premium positioned products
    premium_products = positioning_tiers.get('premium', [])
    if premium_products:
        print(f"\nSample Premium Positioned Products (Apple):")
        for i, product in enumerate(premium_products[:6], 1):
            if product.get('grid_position'):
                row, col = product['grid_position']
                name = product['product_name'][:35] + '...' if len(product['product_name']) > 35 else product['product_name']
                color = product.get('apple_color', 'Standard')
                print(f"  {i}. Position ({row},{col}): {name} - {color}")
    
    # Show sample volume positioned products
    volume_products = positioning_tiers.get('volume', [])
    if volume_products:
        print(f"\nSample Volume Positioned Products (Gripp):")
        for i, product in enumerate(volume_products[:6], 1):
            if product.get('grid_position'):
                row, col = product['grid_position']
                name = product['product_name'][:35] + '...' if len(product['product_name']) > 35 else product['product_name']
                series = product.get('gripp_series', 'Other')
                print(f"  {i}. Position ({row},{col}): {name} - {series}")
    
    # Calculate brand distribution across grid
    positioned_with_grid = [p for p in positioned_products if p.get('grid_position')]
    total_positioned = len(positioned_with_grid)
    
    if total_positioned > 0:
        apple_positioned = len([p for p in positioned_with_grid if p.get('brand', '').lower() == 'apple'])
        gripp_positioned = len([p for p in positioned_with_grid if p.get('brand', '').lower() == 'gripp'])
        others_positioned = total_positioned - apple_positioned - gripp_positioned
        
        print(f"\nFinal Grid Distribution:")
        print(f"  Apple: {apple_positioned}/{total_positioned} ({apple_positioned/total_positioned*100:.1f}%)")
        print(f"  Gripp: {gripp_positioned}/{total_positioned} ({gripp_positioned/total_positioned*100:.1f}%)")
        print(f"  Others: {others_positioned}/{total_positioned} ({others_positioned/total_positioned*100:.1f}%)")
        print(f"  Total Positioned: {total_positioned}/48 ({total_positioned/48*100:.1f}% grid utilization)")
    
    return len(positioned_products) > 0

def test_sales_based_prioritization():
    """Test the sales-based prioritization system"""
    print("=== Testing Sales-Based Prioritization System ===")
    
    generator = IPadAccessoriesGenerator('.')
    products = generator.load_ipad_data()
    
    # Test sales-based tier classification
    print(f"Sales-Based Tier Classification:")
    
    sales_tiers = generator.build_sales_based_prioritization_system(products)
    
    # Display tier summary
    print(f"\nSales Tier Summary:")
    for tier, products_list in sales_tiers.items():
        if products_list:
            total_sales = sum(p.get('frequency', 0) for p in products_list)
            avg_sales = total_sales / len(products_list)
            print(f"  {tier.upper()}: {len(products_list)} products (avg: {avg_sales:.1f} sales)")
    
    # Test premium products (>100 sales)
    print(f"\n=== Premium Products (>100 sales) ===")
    premium_products = sales_tiers.get('premium', [])
    print(f"Premium Products: {len(premium_products)}")
    
    for i, product in enumerate(premium_products[:8], 1):  # Show top 8
        name = product['product_name'][:45] + '...' if len(product['product_name']) > 45 else product['product_name']
        brand = product.get('brand', 'Unknown')
        sales = product.get('frequency', 0)
        
        # Collect premium indicators
        premium_indicators = []
        if product.get('magic_keyboard_premium'):
            premium_indicators.append('Magic Keyboard')
        if product.get('gripp_ultra_premium'):
            premium_indicators.append('Gripp Ultra')
        if product.get('super_premium'):
            premium_indicators.append('Super Premium')
        if product.get('apple_folio_premium'):
            premium_indicators.append('Apple Folio')
        if product.get('productivity_premium'):
            premium_indicators.append('Productivity')
        
        indicators_str = f" [{', '.join(premium_indicators)}]" if premium_indicators else ""
        
        print(f"  {i}. {brand} - {name}")
        print(f"     Sales: {sales} | Tier: {product.get('sales_tier', 'unknown')}{indicators_str}")
    
    # Test Gripp Ultra cases specifically (150-220 sales range)
    print(f"\n=== Gripp Ultra Cases (Eye-Level Priority) ===")
    gripp_ultra_products = [p for p in premium_products if p.get('gripp_ultra_premium')]
    print(f"Gripp Ultra Products: {len(gripp_ultra_products)}")
    
    for i, product in enumerate(gripp_ultra_products, 1):
        name = product['product_name'][:40] + '...' if len(product['product_name']) > 40 else product['product_name']
        model = product.get('ipad_model', 'iPad Base')
        sales = product.get('frequency', 0)
        
        eye_level_indicators = []
        if product.get('eye_level_mandatory'):
            eye_level_indicators.append('Eye-Level Mandatory')
        if product.get('volume_flagship'):
            eye_level_indicators.append('Volume Flagship')
        
        indicators_str = f" [{', '.join(eye_level_indicators)}]" if eye_level_indicators else ""
        
        print(f"  {i}. {name}")
        print(f"     {model} | Sales: {sales}{indicators_str}")
    
    # Test Magic Keyboard products (110+ sales priority)
    print(f"\n=== Magic Keyboard Products (110+ sales priority) ===")
    magic_keyboard_products = [p for p in premium_products if p.get('magic_keyboard_premium')]
    print(f"Magic Keyboard Products: {len(magic_keyboard_products)}")
    
    for i, product in enumerate(magic_keyboard_products, 1):
        name = product['product_name'][:40] + '...' if len(product['product_name']) > 40 else product['product_name']
        model = product.get('ipad_model', 'iPad Base')
        sales = product.get('frequency', 0)
        
        productivity_indicators = []
        if product.get('productivity_flagship'):
            productivity_indicators.append('Productivity Flagship')
        if product.get('productivity_premium'):
            productivity_indicators.append('Productivity Premium')
        
        indicators_str = f" [{', '.join(productivity_indicators)}]" if productivity_indicators else ""
        
        print(f"  {i}. {name}")
        print(f"     {model} | Sales: {sales}{indicators_str}")
    
    # Test miscellaneous products (<10 sales)
    print(f"\n=== Miscellaneous Products (<10 sales) ===")
    miscellaneous_products = sales_tiers.get('miscellaneous', [])
    print(f"Miscellaneous Products: {len(miscellaneous_products)}")
    
    # Group by miscellaneous reasons
    misc_by_reason = defaultdict(list)
    for product in miscellaneous_products:
        reasons = product.get('miscellaneous_reasons', ['low_sales'])
        primary_reason = reasons[0] if reasons else 'low_sales'
        misc_by_reason[primary_reason].append(product)
    
    for reason, products_list in misc_by_reason.items():
        if products_list:
            print(f"\n  {reason.replace('_', ' ').title()} ({len(products_list)} products):")
            for i, product in enumerate(products_list[:3], 1):  # Show top 3 per reason
                name = product['product_name'][:40] + '...' if len(product['product_name']) > 40 else product['product_name']
                sales = product.get('frequency', 0)
                
                misc_indicators = []
                if product.get('very_low_sales'):
                    misc_indicators.append('Very Low Sales')
                if product.get('outdated_ipad_model'):
                    misc_indicators.append('Outdated Model')
                if product.get('generic_accessory'):
                    misc_indicators.append('Generic')
                if product.get('specialty_item'):
                    misc_indicators.append('Specialty')
                
                indicators_str = f" [{', '.join(misc_indicators)}]" if misc_indicators else ""
                
                print(f"    {i}. {name}")
                print(f"       Sales: {sales}{indicators_str}")
    
    # Test eye-level placement strategy
    print(f"\n=== Eye-Level Placement Strategy ===")
    grid_size = (8, 6)
    positioned_products = generator.apply_eye_level_placement_strategy(sales_tiers, grid_size)
    
    # Analyze positioning results by tier
    positioning_analysis = defaultdict(list)
    for product in positioned_products:
        tier = product.get('sales_tier', 'unknown')
        positioning_analysis[tier].append(product)
    
    print(f"Positioning Analysis by Sales Tier:")
    for tier, products_list in positioning_analysis.items():
        positioned_count = len([p for p in products_list if p.get('grid_position')])
        total_count = len(products_list)
        print(f"  {tier.upper()}: {positioned_count}/{total_count} positioned")
    
    # Analyze eye-level placement success
    eye_level_rows = [2, 3, 4, 5]
    premium_eye_level_rows = [3, 4]
    
    positioned_with_grid = [p for p in positioned_products if p.get('grid_position')]
    
    eye_level_products = []
    premium_eye_level_products = []
    
    for product in positioned_with_grid:
        row, col = product['grid_position']
        if row in eye_level_rows:
            eye_level_products.append(product)
        if row in premium_eye_level_rows:
            premium_eye_level_products.append(product)
    
    print(f"\nEye-Level Placement Success:")
    print(f"  Products in eye-level rows (2-5): {len(eye_level_products)}")
    print(f"  Products in premium eye-level rows (3-4): {len(premium_eye_level_products)}")
    
    # Show sample eye-level positioned products
    print(f"\nSample Eye-Level Positioned Products:")
    for i, product in enumerate(premium_eye_level_products[:6], 1):
        row, col = product['grid_position']
        name = product['product_name'][:35] + '...' if len(product['product_name']) > 35 else product['product_name']
        sales = product.get('frequency', 0)
        tier = product.get('sales_tier', 'unknown')
        reason = product.get('positioning_reason', 'unknown')
        
        print(f"  {i}. Position ({row},{col}): {name}")
        print(f"     Sales: {sales} | Tier: {tier} | Reason: {reason}")
    
    # Analyze Gripp Ultra eye-level placement specifically
    gripp_ultra_positioned = [p for p in positioned_with_grid if p.get('gripp_ultra_premium')]
    gripp_ultra_eye_level = [p for p in gripp_ultra_positioned if p['grid_position'][0] in premium_eye_level_rows]
    
    print(f"\nGripp Ultra Eye-Level Success:")
    print(f"  Gripp Ultra products positioned: {len(gripp_ultra_positioned)}")
    print(f"  Gripp Ultra in premium eye-level: {len(gripp_ultra_eye_level)}")
    
    if gripp_ultra_eye_level:
        print(f"  Sample Gripp Ultra Eye-Level Placements:")
        for i, product in enumerate(gripp_ultra_eye_level[:3], 1):
            row, col = product['grid_position']
            name = product['product_name'][:30] + '...' if len(product['product_name']) > 30 else product['product_name']
            sales = product.get('frequency', 0)
            print(f"    {i}. Position ({row},{col}): {name} - {sales} sales")
    
    # Calculate overall positioning efficiency
    total_products = len(positioned_products)
    positioned_count = len(positioned_with_grid)
    miscellaneous_count = len([p for p in positioned_products if p.get('positioning_reason') == 'miscellaneous_wall'])
    
    print(f"\nOverall Positioning Results:")
    print(f"  Total products processed: {total_products}")
    print(f"  Products positioned on main wall: {positioned_count}")
    print(f"  Products moved to miscellaneous wall: {miscellaneous_count}")
    print(f"  Main wall utilization: {positioned_count}/48 ({positioned_count/48*100:.1f}%)")
    
    return len(positioned_products) > 0

def test_complete_ipad_planogram_generation():
    """Test complete iPad planogram generation from data to visual output"""
    print("=== Testing Complete iPad Planogram Generation ===")
    
    generator = IPadAccessoriesGenerator('.')
    products = generator.load_ipad_data()
    
    print(f"Loaded {len(products)} iPad accessories for planogram generation")
    
    # Generate grid
    print("\nGenerating iPad-specific 8×6 grid...")
    grid = generator.create_ipad_grid_generation_system(products)
    
    # Analyze grid
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    filled_positions = sum(1 for row in grid for cell in row if cell is not None)
    
    print(f"Grid Analysis:")
    print(f"  Grid Size: {rows}×{cols} ({rows * cols} positions)")
    print(f"  Filled Positions: {filled_positions}")
    print(f"  Utilization: {filled_positions / (rows * cols) * 100:.1f}%")
    
    # Show sample grid contents
    print(f"\nSample Grid Contents (First 3 rows):")
    for row in range(min(3, rows)):
        print(f"  Row {row}: ", end="")
        for col in range(cols):
            product = grid[row][col]
            if product:
                brand = product.get('brand', 'Unknown')[:4]
                sales = product.get('frequency', 0)
                print(f"{brand}[{sales}] ", end="")
            else:
                print("Empty ", end="")
        print()
    
    # Generate visual planogram
    print(f"\nGenerating visual planogram...")
    visual_success = generator.generate_ipad_planogram_visual(
        grid, 
        store_name="iPad Accessories Showcase",
        wall_number=1,
        output_path="ipad_planogram_showcase.png"
    )
    
    # Generate detailed report
    print(f"Generating detailed report...")
    report_success = generator.generate_ipad_planogram_report(
        grid,
        output_path="ipad_planogram_report.txt"
    )
    
    # Analyze brand distribution in final grid
    brand_counts = defaultdict(int)
    category_counts = defaultdict(int)
    sales_total = 0
    
    for row in grid:
        for product in row:
            if product:
                brand_counts[product.get('brand', 'Unknown')] += 1
                category_counts[product.get('category', 'unknown')] += 1
                sales_total += product.get('frequency', 0)
    
    print(f"\nFinal Grid Analysis:")
    print(f"  Total Sales Volume: {sales_total}")
    print(f"  Average Sales per Product: {sales_total/filled_positions:.1f}")
    
    print(f"\nBrand Distribution:")
    for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / filled_positions) * 100
        print(f"  {brand}: {count} products ({percentage:.1f}%)")
    
    print(f"\nCategory Distribution:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / filled_positions) * 100
        print(f"  {category}: {count} products ({percentage:.1f}%)")
    
    success = visual_success and report_success and filled_positions > 0
    
    if success:
        print(f"\n🎉 SUCCESS: Complete iPad planogram generated!")
        print(f"   Visual: ipad_planogram_showcase.png")
        print(f"   Report: ipad_planogram_report.txt")
    else:
        print(f"\n❌ FAILED: Issues with planogram generation")
    
    return success

def test_ipad_data_loading():
    """Test the iPad data loading and processing system"""
    print("=== Testing iPad Data Loading System ===")
    
    generator = IPadAccessoriesGenerator('.')
    
    # Test data loading
    products = generator.load_ipad_data()
    print(f"Loaded {len(products)} products")
    
    # Test data summary
    summary = generator.get_data_summary()
    print(f"\nData Summary:")
    print(f"  Total products: {summary['total_products']}")
    print(f"  Total sales: {summary['total_sales']}")
    print(f"  Average sales per product: {summary['average_sales']:.1f}")
    
    print(f"\nBrand distribution:")
    for brand, count in list(summary['brand_distribution'].items())[:5]:
        print(f"  {brand}: {count} products")
    
    print(f"\nCategory distribution:")
    for category, count in summary['category_distribution'].items():
        print(f"  {category}: {count} products")
    
    print(f"\niPad model distribution:")
    for model, count in summary['model_distribution'].items():
        print(f"  {model}: {count} products")
    
    print(f"\nTop 5 selling products:")
    for product in summary['top_products'][:5]:
        print(f"  {product['brand']} {product['model']}: {product['sales']} sales")
        print(f"    {product['name']}")
    
    print(f"\nDimensions analysis:")
    dims = summary['dimensions']
    print(f"  Width range: {dims['width_range'][0]:.1f} - {dims['width_range'][1]:.1f} cm")
    print(f"  Height range: {dims['height_range'][0]:.1f} - {dims['height_range'][1]:.1f} cm")
    print(f"  Average size: {dims['average_width']:.1f} × {dims['average_height']:.1f} cm")
    
    return len(products) > 0

if __name__ == "__main__":
    print("=== iPad Accessories Generator Test Suite ===\n")
    
    # Test 1: Data loading system
    success1 = test_ipad_data_loading()
    print(f"\n{'✅ SUCCESS' if success1 else '❌ FAILED'}: iPad data loading system test")
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Model classification engine
    success2 = test_ipad_model_classification()
    print(f"\n{'✅ SUCCESS' if success2 else '❌ FAILED'}: iPad model classification engine test")
    
    print("\n" + "="*60 + "\n")
    
    # Test 3: Category organization system
    success3 = test_category_organization()
    print(f"\n{'✅ SUCCESS' if success3 else '❌ FAILED'}: Category organization system test")
    
    print("\n" + "="*60 + "\n")
    
    # Test 4: Dimension-aware layout engine
    success4 = test_dimension_aware_layout()
    print(f"\n{'✅ SUCCESS' if success4 else '❌ FAILED'}: Dimension-aware layout engine test")
    
    print("\n" + "="*60 + "\n")
    
    # Test 5: Brand allocation system
    success5 = test_brand_allocation_system()
    print(f"\n{'✅ SUCCESS' if success5 else '❌ FAILED'}: Brand allocation system test")
    
    print("\n" + "="*60 + "\n")
    
    # Test 6: Sales-based prioritization system
    success6 = test_sales_based_prioritization()
    print(f"\n{'✅ SUCCESS' if success6 else '❌ FAILED'}: Sales-based prioritization system test")
    
    print("\n" + "="*60 + "\n")
    
    # Test 7: Complete iPad planogram generation
    success7 = test_complete_ipad_planogram_generation()
    print(f"\n{'✅ SUCCESS' if success7 else '❌ FAILED'}: Complete iPad planogram generation test")
    
    print("\n" + "="*60)
    print(f"Overall Test Results:")
    print(f"  Data Loading: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"  Model Classification: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"  Category Organization: {'✅ PASS' if success3 else '❌ FAIL'}")
    print(f"  Dimension-Aware Layout: {'✅ PASS' if success4 else '❌ FAIL'}")
    print(f"  Brand Allocation: {'✅ PASS' if success5 else '❌ FAIL'}")
    print(f"  Sales-Based Prioritization: {'✅ PASS' if success6 else '❌ FAIL'}")
    print(f"  Complete Planogram Generation: {'✅ PASS' if success7 else '❌ FAIL'}")
    print(f"  Overall: {'🎉 ALL TESTS PASSED' if all([success1, success2, success3, success4, success5, success6, success7]) else '⚠️ SOME TESTS FAILED'}")