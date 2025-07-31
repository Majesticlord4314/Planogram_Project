#!/usr/bin/env python3
"""
Retail-Style Planogram Generator
Creates planograms that match real Apple Store layouts with proper organization and aesthetics.
"""

import matplotlib
# Set non-interactive backend to prevent GUI issues
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from collections import defaultdict
from datetime import datetime
from pathlib import Path

class RetailPlanogramGenerator:
    def __init__(self):
        """Initialize the retail planogram generator with proper styling"""
        
        # Uniform product dimensions - all products same size like real stores
        self.product_width = 0.85
        self.product_height = 0.85
        self.gap = 0.15  # Gap between products
        
        # Brand colors for organization
        self.brand_colors = {
            'Apple': '#007AFF',      # Apple blue
            'Pulse': '#FF6B6B',      # Red
            'Tekne': '#4ECDC4',      # Teal  
            'Gripp': '#45B7D1',      # Light blue
            'Hyphen': '#FFA07A',     # Orange
            'UAG': '#8B5CF6',        # Purple
            'nmaxn': '#F59E0B',      # Amber
            'Default': '#6B7280'     # Gray
        }
        
        # Screen protector styling
        self.screen_protector_color = '#E5E7EB'  # Light gray
        
    def create_intelligent_cases_planogram(self, products, store_type, store_name, num_walls):
        """Main entry point - creates organized planograms matching real store layouts"""
        
        try:
            # Organize products by series and brand
            organized_products = self.organize_products_by_series(products)
            
            # Allocate walls with proper series grouping
            wall_allocations = self.allocate_walls_properly(organized_products, num_walls)
            
            # Generate planograms for each wall
            generated_planograms = {}
            
            for wall_key, wall_data in wall_allocations.items():
                if wall_data['products']:  # Only generate if there are products
                    wall_num = wall_key.replace('wall', '')
                    
                    result = self.create_wall_planogram(
                        wall_data['products'], 
                        wall_num, 
                        wall_data['focus'],
                        store_name
                    )
                    
                    if result:
                        generated_planograms[wall_key] = result
            
            return {
                'status': 'success',
                'planograms': generated_planograms,
                'summary': {
                    'total_walls': len(generated_planograms),
                    'store_type': store_type,
                    'store_name': store_name
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'planograms': {}
            }
    
    def organize_products_by_series(self, products):
        """Organize products by iPhone series for proper allocation"""
        
        series_products = {
            'pro_max': [],
            'pro': [],
            'plus': [],
            'base': [],
            'screen_protectors': [],
            'lens_protectors': [],
            'other': []
        }
        
        print(f"📊 Organizing {len(products)} products by series...")
        
        for product in products:
            product_name = str(product.product_name).lower()
            
            # Screen protectors
            if any(term in product_name for term in ['screen protector', 'tempered glass', 'tg', 'glass']):
                series_products['screen_protectors'].append(product)
                print(f"  📱 Screen Protector: {product.product_name}")
            # Lens protectors  
            elif any(term in product_name for term in ['lens protector', 'camera lens']):
                series_products['lens_protectors'].append(product)
                print(f"  📸 Lens Protector: {product.product_name}")
            # iPhone series
            elif 'pro max' in product_name:
                series_products['pro_max'].append(product)
                print(f"  📱 Pro Max: {product.product_name}")
            elif 'pro' in product_name and 'pro max' not in product_name:
                series_products['pro'].append(product)
                print(f"  📱 Pro: {product.product_name}")
            elif 'plus' in product_name:
                series_products['plus'].append(product)
                print(f"  📱 Plus: {product.product_name}")
            elif any(term in product_name for term in ['iphone 16', 'iphone 15', 'base']):
                series_products['base'].append(product)
                print(f"  📱 Base: {product.product_name}")
            else:
                series_products['other'].append(product)
                # Only show first few "other" products to avoid spam
                if len(series_products['other']) <= 5:
                    print(f"  ❓ Other: {product.product_name}")
        
        # Print summary
        print(f"📊 Organization Summary:")
        for series, prods in series_products.items():
            print(f"  {series}: {len(prods)} products")
        
        return series_products
    
    def allocate_walls_properly(self, organized_products, num_walls):
        """Allocate walls with correct series pairing: Pro Max + Pro, Plus + Base"""
        
        print(f"🏗️ Allocating {num_walls} walls with products:")
        for series, prods in organized_products.items():
            print(f"  {series}: {len(prods)} products")
        
        wall_allocations = {}
        
        if num_walls >= 4:
            # 4+ walls: Each series gets its own wall
            wall_allocations['wall1'] = {
                'focus': 'iPhone Pro Max',
                'products': organized_products['pro_max'] + organized_products['screen_protectors'][:len(organized_products['screen_protectors'])//4]
            }
            
            wall_allocations['wall2'] = {
                'focus': 'iPhone Pro', 
                'products': organized_products['pro'] + organized_products['screen_protectors'][len(organized_products['screen_protectors'])//4:len(organized_products['screen_protectors'])//2]
            }
            
            wall_allocations['wall3'] = {
                'focus': 'iPhone Plus',
                'products': organized_products['plus'] + organized_products['screen_protectors'][len(organized_products['screen_protectors'])//2:3*len(organized_products['screen_protectors'])//4]
            }
            
            wall_allocations['wall4'] = {
                'focus': 'iPhone Base',
                'products': organized_products['base'] + organized_products['screen_protectors'][3*len(organized_products['screen_protectors'])//4:]
            }
            
        elif num_walls == 3:
            # 3 walls: Pro Max + Pro, Plus + Base, Accessories
            wall_allocations['wall1'] = {
                'focus': 'iPhone Pro Max & Pro',
                'products': organized_products['pro_max'] + organized_products['pro']
            }
            
            wall_allocations['wall2'] = {
                'focus': 'iPhone Plus & Base', 
                'products': organized_products['plus'] + organized_products['base']
            }
            
            wall_allocations['wall3'] = {
                'focus': 'Screen Protectors & Accessories',
                'products': organized_products['screen_protectors'] + organized_products['lens_protectors'] + organized_products['other']
            }
            
        elif num_walls == 2:
            # 2 walls: Premium (Pro Max + Pro) vs Standard (Plus + Base)
            wall_allocations['wall1'] = {
                'focus': 'iPhone Pro Max & Pro',
                'products': organized_products['pro_max'] + organized_products['pro'] + organized_products['screen_protectors'][:len(organized_products['screen_protectors'])//2]
            }
            
            wall_allocations['wall2'] = {
                'focus': 'iPhone Plus & Base + Accessories',
                'products': organized_products['plus'] + organized_products['base'] + organized_products['screen_protectors'][len(organized_products['screen_protectors'])//2:] + organized_products['lens_protectors'] + organized_products['other']
            }
            
        else:  # 1 wall
            # All products on one wall
            all_products = []
            for product_list in organized_products.values():
                all_products.extend(product_list)
            
            wall_allocations['wall1'] = {
                'focus': 'All iPhone Series & Accessories',
                'products': all_products
            }
        
        # Debug: Show final allocation
        print(f"🏗️ Final wall allocation:")
        for wall_key, wall_data in wall_allocations.items():
            print(f"  {wall_key}: {wall_data['focus']} - {len(wall_data['products'])} products")
        
        return wall_allocations
    
    def create_wall_planogram(self, products, wall_num, focus, store_name):
        """Create a single wall planogram with retail-style organization"""
        
        print(f"🎨 Creating wall {wall_num} planogram:")
        print(f"  Focus: {focus}")
        print(f"  Products received: {len(products)}")
        
        if not products:
            print(f"  ❌ No products for wall {wall_num}, skipping...")
            return None
        
        # Fixed grid size for consistency (like real stores)
        rows, cols = 8, 6
        total_slots = rows * cols
        
        # Organize products by brand for column-wise grouping
        brand_groups = self.group_products_by_brand(products)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(cols * 1.2, rows * 1.2))
        ax.set_xlim(0, cols)
        ax.set_ylim(0, rows)
        ax.set_aspect('equal')
        
        # Remove all axes - clean look like real stores
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('off')
        
        # Fill grid with organized layout
        product_grid = self.create_organized_grid(brand_groups, rows, cols)
        
        # Draw products
        placement_details = []
        
        for row in range(rows):
            for col in range(cols):
                product = product_grid[row][col]
                if product:
                    self.draw_uniform_product(ax, row, col, product)
                    
                    placement_details.append({
                        'row': row + 1,
                        'col': col + 1,
                        'product': product.product_name,
                        'brand': str(product.brand).strip(),
                        'series': self.extract_series(product.product_name),
                        'color': self.extract_color(product.product_name)
                    })
        
        # Add legend at bottom (like real stores)
        self.add_legend(ax, rows, cols, brand_groups)
        
        # Save planogram
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"wall{wall_num}_planogram_{timestamp}.png"
        
        # Use absolute path for output directory
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / 'output'
        output_dir.mkdir(exist_ok=True)  # Ensure directory exists
        output_path = output_dir / filename
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"✅ Saved planogram: {output_path}")
        
        # Create details file
        details_path = self.create_details_file(placement_details, wall_num, focus, timestamp)
        
        return {
            'planogram_image': str(output_path),
            'product_details_file': str(details_path),
            'summary': {
                'total_products': len(placement_details),
                'grid_size': f"{rows}x{cols}",
                'utilization': f"{len(placement_details)/total_slots*100:.1f}%"
            }
        }
    
    def group_products_by_brand(self, products):
        """Group products by brand for organized column layout"""
        
        brand_groups = defaultdict(list)
        
        for product in products:
            brand = str(product.brand).strip()
            product_name = str(product.product_name).lower()
            
            # Special handling for screen protectors
            if any(term in product_name for term in ['screen protector', 'tempered glass', 'tg']):
                brand_groups['Screen Protectors'].append(product)
            elif any(term in product_name for term in ['lens protector', 'camera lens']):
                brand_groups['Lens Protectors'].append(product)
            else:
                brand_groups[brand].append(product)
        
        return brand_groups
    
    def create_organized_grid(self, brand_groups, rows, cols):
        """Create organized grid with brands in columns like real stores"""
        
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        
        # Sort brands: Apple first, then others alphabetically
        sorted_brands = []
        if 'Apple' in brand_groups:
            sorted_brands.append('Apple')
        
        other_brands = [brand for brand in self.sorted_brands_by_importance(brand_groups.keys()) if brand != 'Apple']
        sorted_brands.extend(other_brands)
        
        print(f"  🔍 Sorted brands for grid: {sorted_brands}")
        
        # Allocate columns to brands - ensure each brand gets at least 1 column
        if sorted_brands:
            # If we have more brands than columns, give priority brands more space
            if len(sorted_brands) > cols:
                # Take only the top brands that fit
                sorted_brands = sorted_brands[:cols]
                col_per_brand = 1
            else:
                col_per_brand = max(1, cols // len(sorted_brands))
        else:
            col_per_brand = 1
            
        current_col = 0
        
        for brand in sorted_brands:
            products = brand_groups[brand]
            
            # Fill column(s) for this brand
            brand_cols = min(col_per_brand, cols - current_col)
            
            product_idx = 0
            for col in range(current_col, current_col + brand_cols):
                for row in range(rows):
                    if product_idx < len(products):
                        grid[row][col] = products[product_idx]
                        product_idx += 1
            
            current_col += brand_cols
            
            if current_col >= cols:
                break
        
        return grid
    
    def draw_uniform_product(self, ax, row, col, product):
        """Draw product with uniform size and proper spacing"""
        
        # Calculate position with gaps
        x = col * (self.product_width + self.gap) + self.gap/2
        y = (7 - row) * (self.product_height + self.gap) + self.gap/2  # Flip Y axis
        
        # Determine color
        brand = str(product.brand).strip()
        product_name = str(product.product_name).lower()
        
        if any(term in product_name for term in ['screen protector', 'tempered glass', 'tg']):
            color = self.screen_protector_color
            text_color = 'black'
        else:
            color = self.brand_colors.get(brand, self.brand_colors['Default'])
            text_color = 'white'
        
        # Draw rectangle
        rect = FancyBboxPatch(
            (x, y), self.product_width, self.product_height,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor='black',
            linewidth=1,
            alpha=0.9
        )
        ax.add_patch(rect)
        
        # Add text labels
        self.add_product_text(ax, x, y, product, text_color)
    
    def add_product_text(self, ax, x, y, product, text_color):
        """Add properly formatted text to product facing"""
        
        brand = str(product.brand).strip()
        series = self.extract_series(product.product_name)
        color = self.extract_color(product.product_name)
        product_type = self.extract_type(product.product_name)
        
        # Text positions
        center_x = x + self.product_width / 2
        text_positions = [
            y + self.product_height * 0.8,  # Brand
            y + self.product_height * 0.6,  # Series
            y + self.product_height * 0.4,  # Type
            y + self.product_height * 0.2   # Color
        ]
        
        texts = [brand, series, product_type, color]
        font_sizes = [8, 7, 6, 5]
        font_weights = ['bold', 'normal', 'normal', 'normal']
        
        for i, (text, font_size, font_weight) in enumerate(zip(texts, font_sizes, font_weights)):
            if text and text != 'Unknown':
                ax.text(center_x, text_positions[i], text[:12], 
                       ha='center', va='center',
                       fontsize=font_size, fontweight=font_weight,
                       color=text_color)
    
    def add_legend(self, ax, rows, cols, brand_groups):
        """Add legend section at bottom like real stores"""
        
        legend_y = -0.8
        legend_height = 0.4
        
        # Create legend boxes for each brand
        brands = list(brand_groups.keys())
        box_width = cols / len(brands) if brands else 1
        
        for i, brand in enumerate(brands):
            x = i * box_width + 0.1
            
            color = self.brand_colors.get(brand, self.brand_colors['Default'])
            
            # Legend box
            legend_rect = patches.Rectangle(
                (x, legend_y), box_width - 0.2, legend_height,
                facecolor=color, alpha=0.7, edgecolor='black'
            )
            ax.add_patch(legend_rect)
            
            # Legend text
            ax.text(x + (box_width - 0.2)/2, legend_y + legend_height/2, 
                   brand, ha='center', va='center',
                   fontsize=10, fontweight='bold', color='white')
            
            # Product count
            count = len(brand_groups[brand])
            ax.text(x + (box_width - 0.2)/2, legend_y - 0.2, 
                   f"{count} items", ha='center', va='center',
                   fontsize=8, color='black')
    
    def extract_series(self, product_name):
        """Extract iPhone series from product name"""
        product_name = str(product_name).lower()
        
        if 'pro max' in product_name:
            return 'Pro Max'
        elif 'pro' in product_name:
            return 'Pro'
        elif 'plus' in product_name:
            return 'Plus'
        elif any(term in product_name for term in ['iphone 16', 'iphone 15']):
            return 'Base'
        else:
            return 'Universal'
    
    def extract_color(self, product_name):
        """Extract color from product name"""
        product_name = str(product_name).lower()
        
        colors = ['black', 'white', 'clear', 'blue', 'red', 'green', 'purple', 'pink', 'yellow', 'orange']
        
        for color in colors:
            if color in product_name:
                return color.title()
        
        return 'Mixed'
    
    def extract_type(self, product_name):
        """Extract product type from name"""
        product_name = str(product_name).lower()
        
        if 'screen protector' in product_name or 'tempered glass' in product_name:
            return 'Screen Guard'
        elif 'lens protector' in product_name:
            return 'Lens Guard'
        elif 'case' in product_name:
            return 'Case'
        elif 'cover' in product_name:
            return 'Cover'
        else:
            return 'Accessory'
    
    def create_details_file(self, placement_details, wall_num, focus, timestamp):
        """Create detailed product placement file"""
        
        details_filename = f"wall{wall_num}_details_{timestamp}.txt"
        
        # Use absolute path for output directory
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / 'output'
        output_dir.mkdir(exist_ok=True)  # Ensure directory exists
        details_path = output_dir / details_filename
        
        with open(details_path, 'w') as f:
            f.write(f"RETAIL PLANOGRAM - Wall {wall_num}\n")
            f.write(f"Focus: {focus}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n")
            f.write(f"TOTAL PRODUCTS: {len(placement_details)}\n\n")
            
            # Brand summary
            brand_counts = {}
            for detail in placement_details:
                brand = detail['brand']
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            f.write("BRAND DISTRIBUTION:\n")
            for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {brand}: {count}\n")
            
            f.write("\nDETAILED PLACEMENT:\n")
            f.write("-" * 80 + "\n")
            for detail in placement_details:
                f.write(f"Row {detail['row']:2d}, Col {detail['col']:2d}: {detail['product'][:40]:<40} | {detail['brand']:<10} | {detail['series']:<8} | {detail['color']}\n")
        
        print(f"✅ Saved details: {details_path}")
        return details_path
    
    def sorted_brands_by_importance(self, brands):
        """Sort brands by importance for layout"""
        priority_order = ['Apple', 'Pulse', 'Tekne', 'Gripp', 'Hyphen', 'UAG', 'Screen Protectors', 'Lens Protectors']
        
        sorted_brands = []
        
        # Add priority brands first
        for brand in priority_order:
            if brand in brands:
                sorted_brands.append(brand)
        
        # Add remaining brands alphabetically
        remaining_brands = [brand for brand in brands if brand not in sorted_brands]
        sorted_brands.extend(sorted(remaining_brands))
        
        return sorted_brands

# For compatibility with existing code
class EnhancedPlanogramGenerator(RetailPlanogramGenerator):
    """Compatibility wrapper for existing code"""
    pass
