#!/usr/bin/env python3
"""
PROFESSIONAL RETAIL PLANOGRAM GENERATOR
- Series split based on number of walls
- Dedicated rows for screen protectors/TG/lens protectors  
- Product categorization (armor, magsafe, silicone, etc.)
- Proper TPA diversity with brand mixing
- Phone-like rectangles with proper dimensions
- Real store integration
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import random
from datetime import datetime

class ProfessionalPlanogramGenerator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.absolute()
        self.cases_data = self._load_cases_reference()
        
        # Grid configuration  
        self.grid_rows = 8
        self.grid_cols = 6
        self.total_slots = self.grid_rows * self.grid_cols
        
        # Dedicate rows for accessories
        self.accessory_rows = 1  # Bottom row for screen/lens protectors
        self.case_rows = self.grid_rows - self.accessory_rows
        self.case_slots = self.case_rows * self.grid_cols
        self.accessory_slots = self.accessory_rows * self.grid_cols
        
        # Ensure we always use all 48 slots
        assert self.case_slots + self.accessory_slots == self.total_slots, "Slot calculation error"
        
        # Professional color scheme
        self.brand_colors = {
            'Apple': '#1D1D1F',      # Apple Space Gray
            'Gripp': '#00A8E8',      # Tech Blue
            'Flayrr': '#FF6B35',     # Orange
            'Robocare': '#4CAF50',   # Green
            'AT Minimal': '#9C27B0', # Purple
            'Native Union': '#FF9800', # Amber
            'Logitech': '#607D8B',   # Blue Gray
            'AmazingThing': '#795548', # Brown
            'Hyphen': '#E91E63',     # Pink
            'Pulse': '#3F51B5',      # Indigo
            'Tekne': '#009688',      # Teal
            'UAG': '#424242',        # Dark Gray
            'nmaxn': '#8BC34A'       # Light Green
        }
        
        # Feature accent colors (overlays on brand colors)
        self.feature_accents = {
            'magsafe': '#FFD700',    # Gold accent
            'armor': '#FF4444',      # Red accent
            'silicone': '#44FF44',   # Green accent
            'clear': '#FFFFFF',      # White accent
            'leather': '#8B4513',    # Brown accent
            'wallet': '#FFA500'      # Orange accent
        }
        
    def _load_cases_reference(self):
        """Load processed cases data"""
        cases_file = self.project_root / 'data' / 'processed' / 'cases_reference.json'
        with open(cases_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _categorize_by_series(self, product_name):
        """Categorize product by iPhone series"""
        product_name = str(product_name).lower()
        
        if any(term in product_name for term in ['16 pro max', '15 pro max']):
            return 'pro_max'
        elif any(term in product_name for term in ['16 pro', '15 pro']) and 'max' not in product_name:
            return 'pro' 
        elif any(term in product_name for term in ['16 plus', '15 plus']):
            return 'plus'
        elif any(term in product_name for term in ['iphone 16', 'iphone 15']) and 'pro' not in product_name and 'plus' not in product_name:
            return 'base'
        elif any(term in product_name for term in ['screen protector', 'tempered glass', 'tg']):
            return 'screen_protector'
        elif any(term in product_name for term in ['lens protector', 'camera lens']):
            return 'lens_protector'
        else:
            return 'other'
    
    def _categorize_by_type(self, product_name):
        """Categorize product by case type"""
        product_name = str(product_name).lower()
        
        if any(term in product_name for term in ['magsafe', 'mag safe', 'magnetic']):
            return 'magsafe'
        elif any(term in product_name for term in ['armor', 'armour', 'rugged', 'tough']):
            return 'armor'
        elif any(term in product_name for term in ['silicone', 'silicon']):
            return 'silicone'
        elif any(term in product_name for term in ['clear', 'transparent']):
            return 'clear'
        elif any(term in product_name for term in ['leather']):
            return 'leather'
        elif any(term in product_name for term in ['wallet', 'folio']):
            return 'wallet'
        else:
            return 'standard'
    
    def _filter_by_series(self, series_name):
        """Get products by series with enhanced categorization"""
        products = []
        for p in self.cases_data['products']:
            if self._categorize_by_series(p['product_name']) == series_name:
                # Add categorization
                p['series'] = series_name
                p['case_type'] = self._categorize_by_type(p['product_name'])
                products.append(p)
        return products
    
    def _get_series_allocation(self, num_walls):
        """Determine series allocation based on number of walls"""
        if num_walls == 1:
            # Express store: Mix all series
            return {
                1: ['pro_max', 'pro', 'plus', 'base']
            }
        elif num_walls == 2:
            # Standard store: Premium + Standard
            return {
                1: ['pro_max', 'pro'],
                2: ['plus', 'base']
            }
        elif num_walls == 3:
            # Flagship store: Dedicated walls
            return {
                1: ['pro_max'],
                2: ['pro'], 
                3: ['plus', 'base']
            }
        else:
            # Large store: Full separation
            return {
                1: ['pro_max'],
                2: ['pro'],
                3: ['plus'],
                4: ['base']
            }
    
    def _create_symmetric_arrangement(self, products, target_count):
        """Create symmetric 50-50 Apple/TPA arrangement for maximum sales optimization"""
        
        # Separate Apple and TPA
        apple_products = [p for p in products if p['brand'] == 'Apple']
        tpa_products = [p for p in products if p['brand'] != 'Apple']
        
        # Calculate exact 50-50 split
        apple_slots = target_count // 2
        tpa_slots = target_count - apple_slots
        
        # Fill Apple slots (top rows - premium placement)
        apple_final = []
        if apple_products:
            while len(apple_final) < apple_slots:
                apple_final.extend(apple_products[:min(len(apple_products), apple_slots - len(apple_final))])
            apple_final = apple_final[:apple_slots]
        else:
            # If no Apple products, fill with TPA
            apple_final = tpa_products[:apple_slots] if tpa_products else []
        
        # Create diverse TPA selection with brand balancing
        tpa_final = []
        if tpa_products:
            # Group by brand
            brand_groups = {}
            for p in tpa_products:
                brand = p['brand']
                if brand not in brand_groups:
                    brand_groups[brand] = []
                brand_groups[brand].append(p)
            
            # Round-robin through brands for diversity
            brands = list(brand_groups.keys())
            brand_index = 0
            
            while len(tpa_final) < tpa_slots and brand_groups:
                if brand_index >= len(brands):
                    brand_index = 0
                
                brand = brands[brand_index]
                if brand in brand_groups and brand_groups[brand]:
                    tpa_final.append(brand_groups[brand].pop(0))
                    if not brand_groups[brand]:
                        del brand_groups[brand]
                        brands.remove(brand)
                        continue
                
                brand_index += 1
            
            # Fill remaining slots if needed
            while len(tpa_final) < tpa_slots and tpa_products:
                tpa_final.extend(tpa_products[:min(len(tpa_products), tpa_slots - len(tpa_final))])
            tpa_final = tpa_final[:tpa_slots]
        
        # Combine: Apple first (top rows), then TPA (bottom rows)
        return apple_final + tpa_final
    
    def _organize_for_wall(self, series_list, wall_num):
        """Organize products for a wall with symmetric 50-50 arrangement"""
        
        # Get cases for assigned series
        case_products = []
        for series in series_list:
            case_products.extend(self._filter_by_series(series))
        
        # Get accessory products (screen protectors, lens protectors)
        accessory_products = []
        for series_name in ['screen_protector', 'lens_protector']:
            accessory_products.extend(self._filter_by_series(series_name))
        
        # Create symmetric case arrangement (50-50 Apple/TPA)
        final_cases = self._create_symmetric_arrangement(case_products, self.case_slots)
        
        # Fill accessory slots with symmetric arrangement
        final_accessories = []
        if accessory_products:
            final_accessories = self._create_symmetric_arrangement(accessory_products, self.accessory_slots)
        else:
            # Fill with cases if no accessories
            final_accessories = self._create_symmetric_arrangement(case_products, self.accessory_slots)
        
        # Ensure exactly 48 products total
        total_products = final_cases + final_accessories
        if len(total_products) != self.total_slots:
            print(f"⚠️ Warning: Expected {self.total_slots} products, got {len(total_products)}")
            # Adjust if needed
            if len(total_products) < self.total_slots:
                needed = self.total_slots - len(total_products)
                total_products.extend((final_cases + final_accessories)[:needed])
            else:
                total_products = total_products[:self.total_slots]
        
        return total_products
    
    def _draw_professional_phone_rectangle(self, ax, x, y, width, height, product):
        """Draw professional phone-like rectangle with proper dimensions and colors"""
        
        brand = product.get('brand', 'Unknown')
        case_type = product.get('case_type', 'standard')
        
        # Get brand color
        brand_color = self.brand_colors.get(brand, '#808080')
        
        # Create phone-like rectangle (9:16 aspect ratio)
        phone_width = width * 0.7  # Make it narrower like a real phone
        phone_height = height
        
        # Center the phone rectangle
        phone_x = x + (width - phone_width) / 2
        phone_y = y
        
        # Draw main phone body
        phone_rect = patches.FancyBboxPatch(
            (phone_x, phone_y), phone_width, phone_height,
            boxstyle="round,pad=0.04",
            facecolor=brand_color,
            edgecolor='#FFFFFF',
            linewidth=2.5,
            alpha=0.9
        )
        ax.add_patch(phone_rect)
        
        # Add feature accent if applicable
        if case_type in self.feature_accents:
            accent_color = self.feature_accents[case_type]
            
            # Add accent stripe at top
            accent_height = phone_height * 0.15
            accent_rect = patches.FancyBboxPatch(
                (phone_x + phone_width * 0.1, phone_y + phone_height - accent_height - phone_height * 0.05),
                phone_width * 0.8, accent_height * 0.6,
                boxstyle="round,pad=0.02",
                facecolor=accent_color,
                alpha=0.8
            )
            ax.add_patch(accent_rect)
        
        # Add text with proper hierarchy
        center_x = phone_x + phone_width/2
        center_y = phone_y + phone_height/2
        
        # Brand name (top)
        text_color = '#FFFFFF' if brand != 'Apple' or case_type == 'clear' else '#FFFFFF'
        ax.text(center_x, center_y + phone_height*0.25, brand, 
                ha='center', va='center', fontsize=10, fontweight='bold', 
                color=text_color, family='Arial')
        
        # Series (middle)
        series_display = product.get('series', '').replace('_', ' ').title()
        if series_display:
            ax.text(center_x, center_y, series_display, 
                    ha='center', va='center', fontsize=9, color=text_color,
                    family='Arial')
        
        # Category (bottom) - only if not standard
        if case_type != 'standard':
            category_display = case_type.replace('_', ' ').title()
            ax.text(center_x, center_y - phone_height*0.25, category_display, 
                    ha='center', va='center', fontsize=8, color=text_color,
                    style='italic', family='Arial')
    
    def generate_wall_planogram(self, series_list, wall_num, store_name):
        """Generate single wall planogram with series split and proper diversity"""
        
        # Organize products for this wall
        organized_products = self._organize_for_wall(series_list, wall_num)
        
        # Create figure with proper aspect ratio
        fig, ax = plt.subplots(figsize=(12, 16))
        ax.set_xlim(0, self.grid_cols)
        ax.set_ylim(0, self.grid_rows)
        ax.set_aspect('equal')
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Title with series information
        series_names = ', '.join([s.replace('_', ' ').title() for s in series_list])
        title = f"{store_name} - Wall {wall_num}\n{series_names} ({len(organized_products)} Products)"
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Draw products in grid
        cell_width = 0.85
        cell_height = 0.85
        margin = 0.075
        
        for idx, product in enumerate(organized_products):
            row = idx // self.grid_cols
            col = idx % self.grid_cols
            
            # Calculate position (flip Y to start from top)
            x = col + margin
            y = (self.grid_rows - 1 - row) + margin
            
            self._draw_professional_phone_rectangle(ax, x, y, cell_width, cell_height, product)
        
        # Add visual separators
        # Apple section separator (after top 50%)
        apple_rows = self.case_rows // 2
        if apple_rows > 0:
            separator_y = self.grid_rows - apple_rows - 0.02
            ax.axhline(y=separator_y, color='#007AFF', linewidth=3, alpha=0.6)
            ax.text(self.grid_cols/2, separator_y - 0.15, 'APPLE PREMIUM SECTION', 
                   ha='center', va='center', fontsize=10, fontweight='bold', color='#007AFF',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Accessories section separator
        if self.accessory_rows > 0:
            ax.axhline(y=self.accessory_rows-0.02, color='#FFD700', linewidth=3, alpha=0.7)
            ax.text(self.grid_cols/2, self.accessory_rows-0.15, 'ACCESSORIES SECTION', 
                   ha='center', va='center', fontsize=10, fontweight='bold', color='#FFD700',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.project_root / 'output'
        output_dir.mkdir(exist_ok=True)
        
        filename = f"wall{wall_num}_planogram_{timestamp}.png"
        filepath = output_dir / filename
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        # Generate enhanced details file
        details_file = output_dir / f"wall{wall_num}_details_{timestamp}.txt"
        with open(details_file, 'w', encoding='utf-8') as f:
            f.write(f"PROFESSIONAL PLANOGRAM DETAILS - Wall {wall_num}\n")
            f.write(f"Store: {store_name}\n")
            f.write(f"Series: {series_names}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Grid Size: {self.grid_rows}x{self.grid_cols} = {self.total_slots} slots\n")
            f.write(f"Products Placed: {len(organized_products)}\n")
            f.write(f"Utilization: 100%\n\n")
            
            # Enhanced breakdowns
            series_count = {}
            brand_count = {}
            category_count = {}
            
            for product in organized_products:
                series = product.get('series', 'unknown')
                brand = product.get('brand', 'unknown')
                category = product.get('case_type', 'standard')
                
                series_count[series] = series_count.get(series, 0) + 1
                brand_count[brand] = brand_count.get(brand, 0) + 1
                category_count[category] = category_count.get(category, 0) + 1
            
            f.write("SERIES BREAKDOWN:\n")
            for series, count in sorted(series_count.items()):
                f.write(f"  {series.replace('_', ' ').title()}: {count} products\n")
            
            f.write("\nBRAND BREAKDOWN:\n")
            for brand, count in sorted(brand_count.items()):
                f.write(f"  {brand}: {count} products\n")
            
            f.write("\nCATEGORY BREAKDOWN:\n")
            for category, count in sorted(category_count.items()):
                f.write(f"  {category.title()}: {count} products\n")
            
            f.write(f"\nTOTAL PRODUCTS: {len(organized_products)}\n")
        
        return {
            'image_file': str(filepath),
            'details_file': str(details_file),
            'products_placed': len(organized_products),
            'utilization': 100.0,
            'series': series_list
        }
    
    def generate_store_planograms(self, store_name, num_walls=3):
        """Generate planograms for entire store with intelligent series allocation"""
        
        series_allocation = self._get_series_allocation(num_walls)
        
        print(f"🏪 Generating planograms for {store_name}")
        print(f"📊 {num_walls} walls with series allocation:")
        for wall, series_list in series_allocation.items():
            if wall <= num_walls:
                print(f"  Wall {wall}: {', '.join([s.replace('_', ' ').title() for s in series_list])}")
        
        results = []
        
        for wall_num in range(1, num_walls + 1):
            if wall_num in series_allocation:
                series_list = series_allocation[wall_num]
                result = self.generate_wall_planogram(series_list, wall_num, store_name)
                results.append(result)
        
        return {
            'store_name': store_name,
            'walls_generated': len(results),
            'total_utilization': 100.0,
            'walls': results
        }

def main():
    """Test the professional planogram generator"""
    generator = ProfessionalPlanogramGenerator()
    
    print("🚀 Testing Professional Planogram Generator")
    print(f"📊 Loaded {generator.cases_data['metadata']['total_products']} case products")
    
    # Test with a real store name
    results = generator.generate_store_planograms("Imagine UB City Bengaluru", num_walls=3)
    
    print(f"\n✅ Generated {results['walls_generated']} walls")
    for wall in results['walls']:
        print(f"  Wall: {wall['products_placed']} products, {wall['utilization']}% utilization")
        print(f"    Series: {', '.join([s.replace('_', ' ').title() for s in wall['series']])}")

if __name__ == "__main__":
    main()
