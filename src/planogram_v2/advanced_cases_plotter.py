#!/usr/bin/env python3
"""
Advanced Cases Planogram Plotter - Professional Retail Layout
Creates planograms that match the aesthetic of existing retail layouts with proper Apple/TPA segregation
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
import pandas as pd

class AdvancedCasesPlanogramPlotter:
    """Generate professional retail-style planograms for cases & covers"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.color_scheme = self._init_color_scheme()
        self.layout_configs = self._init_layout_configs()
        
    def _init_color_scheme(self) -> Dict:
        """Initialize professional color scheme matching retail standards"""
        return {
            # Apple brand colors
            'apple_bg': '#F8F9FA',
            'apple_border': '#007AFF',
            'apple_text': '#1D1D1F',
            
            # TPA brand colors
            'gripp_bg': '#FFF5F0',
            'gripp_border': '#FF6B35',
            'pulse_bg': '#F5F0FF',
            'pulse_border': '#8E44AD',
            'hyphen_bg': '#F0FFF5',
            'hyphen_border': '#2ECC71',
            'tekne_bg': '#FFF0F0',
            'tekne_border': '#E74C3C',
            'uag_bg': '#F0F0F0',
            'uag_border': '#34495E',
            'other_bg': '#FAFAFA',
            'other_border': '#95A5A6',
            
            # Case category colors
            'clear': '#E8F4FD',
            'silicone': '#F0F8E8',
            'magsafe': '#FFF2E8',
            'leather': '#F5E6D3',
            'armor': '#FFE8E8',
            'crystal': '#F0F8FF',
            
            # Screen protector colors
            'screen_protector': '#E6F3FF',
            'lens_protector': '#F0E6FF',
            
            # General colors
            'wall_bg': '#FFFFFF',
            'section_divider': '#D1D1D6',
            'text_primary': '#1D1D1F',
            'text_secondary': '#6D6D70',
            'text_light': '#8E8E93'
        }
    
    def _init_layout_configs(self) -> Dict:
        """Initialize layout configurations for different store sizes"""
        return {
            'large': {  # 4+ walls
                'grid_size': (8, 6),  # 8 rows x 6 columns
                'case_width': 2.8,
                'case_height': 4.2,
                'gap_x': 0.2,
                'gap_y': 0.3,
                'wall_width': 20,
                'wall_height': 28,
                'title_height': 2.0,
                'apple_ratio': 0.5  # 50% Apple, 50% TPA
            },
            'medium': {  # 3 walls
                'grid_size': (6, 5),  # 6 rows x 5 columns
                'case_width': 3.0,
                'case_height': 4.0,
                'gap_x': 0.25,
                'gap_y': 0.35,
                'wall_width': 18,
                'wall_height': 26,
                'title_height': 2.0,
                'apple_ratio': 0.6  # 60% Apple, 40% TPA
            },
            'small': {  # 2 walls
                'grid_size': (5, 4),  # 5 rows x 4 columns
                'case_width': 3.2,
                'case_height': 3.8,
                'gap_x': 0.3,
                'gap_y': 0.4,
                'wall_width': 16,
                'wall_height': 22,
                'title_height': 1.8,
                'apple_ratio': 0.7  # 70% Apple, 30% TPA
            }
        }
    
    def determine_store_size(self, total_walls: int) -> str:
        """Determine store size category based on wall count"""
        if total_walls >= 4:
            return 'large'
        elif total_walls == 3:
            return 'medium'
        else:
            return 'small'
    
    def organize_products_by_strategy(self, products: List[Dict], wall_num: int, total_walls: int, store_size: str) -> Dict:
        """Organize products according to the specified strategy"""
        
        # Separate Apple and TPA products
        apple_products = [p for p in products if p.get('brand', '').lower() == 'apple']
        tpa_products = [p for p in products if p.get('brand', '').lower() != 'apple']
        
        # Get layout config
        config = self.layout_configs[store_size]
        total_slots = config['grid_size'][0] * config['grid_size'][1]
        apple_slots = int(total_slots * config['apple_ratio'])
        tpa_slots = total_slots - apple_slots
        
        # Strategy based on store size and wall count
        if store_size == 'large' and total_walls >= 4:
            return self._organize_large_store(apple_products, tpa_products, wall_num, total_walls, apple_slots, tpa_slots)
        elif store_size == 'medium' and total_walls == 3:
            return self._organize_medium_store(apple_products, tpa_products, wall_num, total_walls, apple_slots, tpa_slots)
        else:
            return self._organize_small_store(apple_products, tpa_products, wall_num, total_walls, apple_slots, tpa_slots)
    
    def _organize_large_store(self, apple_products: List[Dict], tpa_products: List[Dict], 
                            wall_num: int, total_walls: int, apple_slots: int, tpa_slots: int) -> Dict:
        """Organize products for large stores (4+ walls)"""
        
        # For 4 walls: dedicate each wall to each iPhone series
        series_mapping = {
            1: ['iPhone 16 Base'],
            2: ['iPhone 16 Plus'], 
            3: ['iPhone 16 Pro'],
            4: ['iPhone 16 Pro Max']
        }
        
        if wall_num <= 4:
            target_series = series_mapping.get(wall_num, [])
            # Filter products for this series
            apple_filtered = [p for p in apple_products if p.get('series', '') in target_series]
            tpa_filtered = [p for p in tpa_products if p.get('series', '') in target_series]
        else:
            # Additional walls get mixed products
            apple_filtered = apple_products
            tpa_filtered = tpa_products
        
        # Organize Apple products by color diversity
        apple_organized = self._maximize_color_diversity(apple_filtered[:apple_slots])
        
        # Organize TPA products by brand grouping
        tpa_organized = self._group_by_brand(tpa_filtered[:tpa_slots])
        
        # Add screen protectors if this is a TPA-heavy wall
        if wall_num > 4 or len(tpa_organized) < tpa_slots * 0.8:
            screen_protectors = self._get_screen_protectors(tpa_slots - len(tpa_organized))
            tpa_organized.extend(screen_protectors)
        
        return {
            'apple_section': apple_organized,
            'tpa_section': tpa_organized,
            'layout_strategy': f'Large Store - Wall {wall_num}: {target_series if wall_num <= 4 else "Mixed Series"}'
        }
    
    def _organize_medium_store(self, apple_products: List[Dict], tpa_products: List[Dict], 
                             wall_num: int, total_walls: int, apple_slots: int, tpa_slots: int) -> Dict:
        """Organize products for medium stores (3 walls)"""
        
        # For 3 walls: split series across walls
        series_mapping = {
            1: ['iPhone 16 Base', 'iPhone 16 Plus'],
            2: ['iPhone 16 Pro', 'iPhone 16 Pro Max'],
            3: ['iPhone 15 Base', 'iPhone 15 Plus', 'iPhone 15 Pro', 'iPhone 15 Pro Max']  # TPA + Screen protectors
        }
        
        target_series = series_mapping.get(wall_num, [])
        
        if wall_num == 3:
            # Wall 3 is TPA-focused with screen protectors
            apple_filtered = [p for p in apple_products if p.get('series', '') in target_series][:apple_slots//2]
            tpa_filtered = tpa_products[:tpa_slots//2]
            screen_protectors = self._get_screen_protectors(tpa_slots//2)
            tpa_organized = self._group_by_brand(tpa_filtered + screen_protectors)
        else:
            apple_filtered = [p for p in apple_products if p.get('series', '') in target_series]
            tpa_filtered = [p for p in tpa_products if p.get('series', '') in target_series]
            tpa_organized = self._group_by_brand(tpa_filtered[:tpa_slots])
        
        apple_organized = self._maximize_color_diversity(apple_filtered[:apple_slots])
        
        return {
            'apple_section': apple_organized,
            'tpa_section': tpa_organized,
            'layout_strategy': f'Medium Store - Wall {wall_num}: {target_series}'
        }
    
    def _organize_small_store(self, apple_products: List[Dict], tpa_products: List[Dict], 
                            wall_num: int, total_walls: int, apple_slots: int, tpa_slots: int) -> Dict:
        """Organize products for small stores (2 walls)"""
        
        # For 2 walls: split all 4 series across both walls, maximize diversity
        if wall_num == 1:
            target_series = ['iPhone 16 Base', 'iPhone 16 Pro']
        else:
            target_series = ['iPhone 16 Plus', 'iPhone 16 Pro Max']
        
        apple_filtered = [p for p in apple_products if p.get('series', '') in target_series]
        tpa_filtered = [p for p in tpa_products if p.get('series', '') in target_series]
        
        # Maximize diversity in small stores
        apple_organized = self._maximize_color_diversity(apple_filtered[:apple_slots])
        tpa_organized = self._group_by_brand(tpa_filtered[:tpa_slots])
        
        return {
            'apple_section': apple_organized,
            'tpa_section': tpa_organized,
            'layout_strategy': f'Small Store - Wall {wall_num}: {target_series}'
        }
    
    def _maximize_color_diversity(self, products: List[Dict]) -> List[Dict]:
        """Maximize color diversity in Apple products"""
        if not products:
            return []
        
        # Group by color
        color_groups = {}
        for product in products:
            color = self._extract_color_from_name(product.get('product_name', ''))
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append(product)
        
        # Distribute colors evenly
        organized = []
        max_per_color = max(1, len(products) // len(color_groups))
        
        for color, color_products in color_groups.items():
            # Sort by sales within color group
            color_products.sort(key=lambda x: x.get('total_sales', 0), reverse=True)
            organized.extend(color_products[:max_per_color])
        
        # Fill remaining slots with highest sales
        remaining_slots = len(products) - len(organized)
        if remaining_slots > 0:
            remaining_products = [p for p in products if p not in organized]
            remaining_products.sort(key=lambda x: x.get('total_sales', 0), reverse=True)
            organized.extend(remaining_products[:remaining_slots])
        
        return organized[:len(products)]
    
    def _group_by_brand(self, products: List[Dict]) -> List[Dict]:
        """Group TPA products by brand"""
        if not products:
            return []
        
        # Group by brand
        brand_groups = {}
        for product in products:
            brand = product.get('brand', 'Other')
            if brand not in brand_groups:
                brand_groups[brand] = []
            brand_groups[brand].append(product)
        
        # Organize by brand priority (Gripp, Pulse, Hyphen, etc.)
        brand_priority = ['Gripp', 'Pulse', 'Hyphen', 'Tekne', 'UAG', 'Other']
        organized = []
        
        for brand in brand_priority:
            if brand in brand_groups:
                # Sort by sales within brand
                brand_products = brand_groups[brand]
                brand_products.sort(key=lambda x: x.get('total_sales', 0), reverse=True)
                organized.extend(brand_products)
        
        return organized[:len(products)]
    
    def _get_screen_protectors(self, count: int) -> List[Dict]:
        """Generate screen protector products for TPA section"""
        screen_protectors = []
        
        protector_types = [
            {'name': 'Tempered Glass Screen Protector', 'category': 'screen_protector', 'brand': 'Gripp'},
            {'name': 'Privacy Glass Screen Protector', 'category': 'screen_protector', 'brand': 'Gripp'},
            {'name': 'Camera Lens Protector', 'category': 'lens_protector', 'brand': 'Gripp'},
            {'name': 'Anti-Glare Screen Protector', 'category': 'screen_protector', 'brand': 'Pulse'},
            {'name': 'Blue Light Filter Glass', 'category': 'screen_protector', 'brand': 'Tekne'},
        ]
        
        for i in range(min(count, len(protector_types))):
            protector = protector_types[i % len(protector_types)].copy()
            protector.update({
                'series': 'iPhone 16 Pro Max',  # Most popular series
                'total_sales': 100 + i * 10,
                'priority_score': 50 + i * 5
            })
            screen_protectors.append(protector)
        
        return screen_protectors
    
    def _extract_color_from_name(self, name: str) -> str:
        """Extract color from product name"""
        colors = ['Black', 'White', 'Clear', 'Blue', 'Green', 'Red', 'Pink', 'Purple', 
                 'Yellow', 'Orange', 'Gray', 'Silver', 'Gold', 'Rose Gold', 'Denim', 
                 'Fuchsia', 'Lake Green', 'Plum', 'Star Fruit', 'Stone Gray', 'Ultramarine']
        
        name_lower = name.lower()
        for color in colors:
            if color.lower() in name_lower:
                return color
        return 'Clear'
    
    def create_professional_planogram(self, wall_data: Dict, wall_name: str, store_name: str, 
                                    total_walls: int, output_path: str = None) -> Tuple[str, str]:
        """Create a professional planogram matching retail standards"""
        
        store_size = self.determine_store_size(total_walls)
        config = self.layout_configs[store_size]
        
        # Organize products according to strategy
        wall_num = int(wall_name.split('_')[1])
        organized_data = self.organize_products_by_strategy(
            wall_data['products'], wall_num, total_walls, store_size
        )
        
        # Setup figure
        fig, ax = plt.subplots(figsize=(config['wall_width'], config['wall_height']))
        ax.set_facecolor(self.color_scheme['wall_bg'])
        
        # Draw title and header
        self._draw_professional_header(ax, wall_name, store_name, organized_data['layout_strategy'], config)
        
        # Calculate layout
        rows, cols = config['grid_size']
        apple_slots = int(rows * cols * config['apple_ratio'])
        
        # Draw Apple section (first half)
        apple_y_start = config['wall_height'] - config['title_height'] - 1
        self._draw_product_section(ax, organized_data['apple_section'], 'Apple', 
                                 0, apple_y_start, rows, cols//2, config, True)
        
        # Draw TPA section (second half)
        tpa_x_start = (cols//2) * (config['case_width'] + config['gap_x'])
        self._draw_product_section(ax, organized_data['tpa_section'], 'TPA', 
                                 tpa_x_start, apple_y_start, rows, cols//2, config, False)
        
        # Draw section divider
        divider_x = tpa_x_start - config['gap_x']/2
        ax.axvline(x=divider_x, color=self.color_scheme['section_divider'], 
                  linewidth=2, linestyle='--', alpha=0.7)
        
        # Add section labels
        self._add_section_labels(ax, config, divider_x)
        
        # Finalize plot
        ax.set_xlim(0, config['wall_width'])
        ax.set_ylim(0, config['wall_height'])
        ax.axis('off')
        
        # Save planogram
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.data_path / 'output' / 'planograms_v2' / f"{store_name}_{wall_name}_{timestamp}.png"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Generate corresponding text file with facing details
        text_file = self._generate_facing_details(organized_data, wall_name, store_name, config, output_path)
        
        print(f"Professional planogram saved: {output_path}")
        print(f"Facing details saved: {text_file}")
        
        return str(output_path), str(text_file)
    
    def _draw_professional_header(self, ax, wall_name: str, store_name: str, strategy: str, config: Dict):
        """Draw professional header with store branding"""
        header_y = config['wall_height'] - 0.5
        
        # Main title
        ax.text(config['wall_width']/2, header_y, 
                f"Cases & Covers - {wall_name}",
                fontsize=20, fontweight='bold', ha='center',
                color=self.color_scheme['text_primary'])
        
        # Store name
        ax.text(config['wall_width']/2, header_y - 0.6,
                store_name,
                fontsize=14, ha='center',
                color=self.color_scheme['text_secondary'])
        
        # Strategy
        ax.text(config['wall_width']/2, header_y - 1.0,
                strategy,
                fontsize=10, ha='center', style='italic',
                color=self.color_scheme['text_light'])
        
        # Date
        ax.text(config['wall_width'] - 0.5, header_y,
                datetime.now().strftime('%Y-%m-%d'),
                fontsize=10, ha='right',
                color=self.color_scheme['text_light'])
    
    def _draw_product_section(self, ax, products: List[Dict], section_type: str,
                            start_x: float, start_y: float, rows: int, cols: int, 
                            config: Dict, is_apple: bool):
        """Draw a section of products (Apple or TPA)"""
        
        case_width = config['case_width']
        case_height = config['case_height']
        gap_x = config['gap_x']
        gap_y = config['gap_y']
        
        for i, product in enumerate(products[:rows * cols]):
            row = i // cols
            col = i % cols
            
            x = start_x + col * (case_width + gap_x)
            y = start_y - row * (case_height + gap_y) - case_height
            
            self._draw_hanging_case(ax, product, x, y, case_width, case_height, is_apple)
    
    def _draw_hanging_case(self, ax, product: Dict, x: float, y: float, 
                          width: float, height: float, is_apple: bool):
        """Draw individual case as hanging rectangle with professional styling"""
        
        brand = product.get('brand', 'Other')
        category = product.get('category', 'case')
        
        # Determine colors based on brand and type
        if is_apple:
            bg_color = self.color_scheme['apple_bg']
            border_color = self.color_scheme['apple_border']
        else:
            bg_color = self.color_scheme.get(f'{brand.lower()}_bg', self.color_scheme['other_bg'])
            border_color = self.color_scheme.get(f'{brand.lower()}_border', self.color_scheme['other_border'])
        
        # Special handling for screen protectors
        if 'protector' in category:
            bg_color = self.color_scheme.get(category, self.color_scheme['screen_protector'])
            # Cardboard-like accent for screen protectors
            cardboard_rect = FancyBboxPatch(
                (x-0.1, y-0.1), width+0.2, height+0.2,
                boxstyle="round,pad=0.05",
                facecolor='#D2B48C',  # Cardboard color
                edgecolor='#8B7355',
                linewidth=1,
                alpha=0.3
            )
            ax.add_patch(cardboard_rect)
        
        # Main case rectangle
        case_rect = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.08",
            facecolor=bg_color,
            edgecolor=border_color,
            linewidth=2,
            alpha=0.9
        )
        ax.add_patch(case_rect)
        
        # Brand strip at top
        brand_height = 0.4
        brand_rect = Rectangle(
            (x, y + height - brand_height), width, brand_height,
            facecolor=border_color,
            alpha=0.8
        )
        ax.add_patch(brand_rect)
        
        # Add text content
        self._add_case_text(ax, product, x, y, width, height, is_apple)
        
        # Add hanging hook effect
        hook_y = y + height + 0.1
        hook_rect = Rectangle((x + width/2 - 0.1, hook_y), 0.2, 0.15, 
                            facecolor='#666666', alpha=0.7)
        ax.add_patch(hook_rect)
    
    def _add_case_text(self, ax, product: Dict, x: float, y: float, 
                      width: float, height: float, is_apple: bool):
        """Add text to case rectangle"""
        
        brand = product.get('brand', 'N/A')
        category = product.get('category', 'case').title()
        color = self._extract_color_from_name(product.get('product_name', ''))
        series = product.get('series', '').replace('iPhone ', '')
        
        # Brand name (in brand strip)
        ax.text(x + width/2, y + height - 0.2, brand,
                fontsize=9, fontweight='bold', ha='center', va='center',
                color='white')
        
        # Series (upper middle)
        ax.text(x + width/2, y + height - 0.8, series,
                fontsize=8, ha='center', va='center',
                color=self.color_scheme['text_primary'],
                fontweight='bold')
        
        # Category (middle)
        ax.text(x + width/2, y + height/2, category,
                fontsize=7, ha='center', va='center',
                color=self.color_scheme['text_secondary'])
        
        # Color (lower middle)
        ax.text(x + width/2, y + height/2 - 0.6, color,
                fontsize=8, ha='center', va='center',
                color=self.color_scheme['text_primary'],
                fontweight='bold')
        
        # Sales indicator (bottom)
        sales = product.get('total_sales', 0)
        if sales > 0:
            ax.text(x + width/2, y + 0.3, f"{sales}",
                    fontsize=6, ha='center', va='center',
                    color=self.color_scheme['text_light'])
    
    def _add_section_labels(self, ax, config: Dict, divider_x: float):
        """Add section labels for Apple and TPA"""
        label_y = config['wall_height'] - config['title_height'] - 0.3
        
        # Apple section label
        ax.text(divider_x/2, label_y, "APPLE",
                fontsize=12, fontweight='bold', ha='center',
                color=self.color_scheme['apple_border'])
        
        # TPA section label
        ax.text(divider_x + (config['wall_width'] - divider_x)/2, label_y, "THIRD PARTY",
                fontsize=12, fontweight='bold', ha='center',
                color=self.color_scheme['text_secondary'])
    
    def _generate_facing_details(self, organized_data: Dict, wall_name: str, store_name: str, 
                               config: Dict, planogram_path: Path) -> str:
        """Generate detailed facing allocation text file"""
        
        text_file = planogram_path.with_suffix('.txt')
        
        rows, cols = config['grid_size']
        apple_cols = cols // 2
        tpa_cols = cols - apple_cols
        
        content = []
        content.append(f"FACING DETAILS - {wall_name}")
        content.append(f"Store: {store_name}")
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("=" * 60)
        content.append("")
        
        # Apple section details
        content.append("APPLE SECTION (Left Half)")
        content.append("-" * 30)
        apple_products = organized_data['apple_section']
        
        for row in range(rows):
            for col in range(apple_cols):
                facing_num = row * apple_cols + col + 1
                product_idx = row * apple_cols + col
                
                if product_idx < len(apple_products):
                    product = apple_products[product_idx]
                    content.append(f"Row {row+1}, Col {col+1} (Facing A{facing_num:02d}):")
                    content.append(f"  Product: {product.get('product_name', 'N/A')}")
                    content.append(f"  Brand: {product.get('brand', 'N/A')}")
                    content.append(f"  Series: {product.get('series', 'N/A')}")
                    content.append(f"  Category: {product.get('category', 'N/A')}")
                    content.append(f"  Sales: {product.get('total_sales', 0)}")
                    content.append(f"  Quantity: 1 unit per facing")
                    content.append("")
                else:
                    content.append(f"Row {row+1}, Col {col+1} (Facing A{facing_num:02d}): EMPTY")
                    content.append("")
        
        # TPA section details
        content.append("TPA SECTION (Right Half)")
        content.append("-" * 30)
        tpa_products = organized_data['tpa_section']
        
        for row in range(rows):
            for col in range(tpa_cols):
                facing_num = row * tpa_cols + col + 1
                product_idx = row * tpa_cols + col
                
                if product_idx < len(tpa_products):
                    product = tpa_products[product_idx]
                    content.append(f"Row {row+1}, Col {col+1} (Facing T{facing_num:02d}):")
                    content.append(f"  Product: {product.get('name', product.get('product_name', 'N/A'))}")
                    content.append(f"  Brand: {product.get('brand', 'N/A')}")
                    content.append(f"  Series: {product.get('series', 'N/A')}")
                    content.append(f"  Category: {product.get('category', 'N/A')}")
                    content.append(f"  Sales: {product.get('total_sales', 0)}")
                    content.append(f"  Quantity: 1 unit per facing")
                    content.append("")
                else:
                    content.append(f"Row {row+1}, Col {col+1} (Facing T{facing_num:02d}): EMPTY")
                    content.append("")
        
        # Summary
        content.append("SUMMARY")
        content.append("-" * 20)
        content.append(f"Total Apple facings: {len(apple_products)}")
        content.append(f"Total TPA facings: {len(tpa_products)}")
        content.append(f"Total facings used: {len(apple_products) + len(tpa_products)}")
        content.append(f"Total capacity: {rows * cols}")
        content.append(f"Utilization: {((len(apple_products) + len(tpa_products)) / (rows * cols) * 100):.1f}%")
        
        # Write to file
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        return str(text_file)

# Example usage and testing
if __name__ == "__main__":
    plotter = AdvancedCasesPlanogramPlotter("c:/Users/Shivansh Pal/Desktop/Planogram_Project")
    
    # Test with sample data
    sample_wall_data = {
        'products': [
            {'product_name': 'iPhone 16 Clear Case with MagSafe', 'brand': 'Apple', 'series': 'iPhone 16 Base', 'category': 'clear', 'total_sales': 500},
            {'product_name': 'iPhone 16 Silicone Case - Black', 'brand': 'Apple', 'series': 'iPhone 16 Base', 'category': 'silicone', 'total_sales': 400},
            {'product_name': 'Gripp Clear Case', 'brand': 'Gripp', 'series': 'iPhone 16 Base', 'category': 'clear', 'total_sales': 300},
            {'product_name': 'Pulse Armor Case', 'brand': 'Pulse', 'series': 'iPhone 16 Base', 'category': 'armor', 'total_sales': 250},
        ] * 10  # Multiply to have enough products
    }
    
    try:
        planogram_file, text_file = plotter.create_professional_planogram(
            sample_wall_data, "Wall_1", "IMAGINE- KORAMANGALA BENGALURU", 4
        )
        print(f"Test planogram created: {planogram_file}")
        print(f"Test facing details: {text_file}")
    except Exception as e:
        print(f"Error creating test planogram: {e}")
        import traceback
        traceback.print_exc()