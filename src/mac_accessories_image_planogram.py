"""
Mac Accessories Image-Based Planogram Generator
Creates planograms using actual product images from the databank
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path

class MacAccessoriesImagePlanogram:
    def __init__(self):
        self.image_databank_path = "pdf_databank/output/images/combined"
        self.output_path = "output"
        
        # Mac accessories from the image databank
        self.mac_products = {
            'privacy_filters': [
                'pulse mac privacy filter.jpg'
            ],
            'hubs_docks': [
                'alogic usb hub.jpg',
                'alogic usb-c dock 3in1.jpg',
                'powerup usb hub.jpg',
                'tekne multiport hub.jpg'
            ],
            'cables_adapters': [
                'alogic usb-c cable.jpg',
                'tekne 60W cable.jpg',
                'tekne usb-c lightning cable.jpg',
                'usb-c 240W cable.jpg',
                'usb-c 60w cable.jpg',
                'usb-c to lightning 1m cable.jpg',
                'usb-c apple pencil adapter.jpg'
            ],
            'chargers_power': [
                'pulse 20W adapter.jpg',
                'pulse 30W adapter.jpg',
                'tekne 20W adapter.jpg',
                'tekne 36W adapter.jpg',
                'Tekne 45W adapter.jpg',
                'usb-c 20W adapter.jpg',
                'usb-c 30W adapter.jpg',
                'pulse powerbank 30W.jpg',
                'pulse powerbank.jpg'
            ],
            'keyboard_accessories': [
                'Gripp keyboard cover.png',
                'tekne macbook 3in1 kit.jpg'
            ],
            'charging_stands': [
                'pulse 3in1 charging stand.jpg',
                'pusle 2in1 watch charger.jpg',
                'pusle 3in1 wireless charger.jpg',
                'watch charger.jpg'
            ]
        }
        
        # Brand colors
        self.brand_colors = {
            'pulse': '#1E90FF',    # Blue
            'tekne': '#FF6B35',    # Orange  
            'alogic': '#E6E6FA',   # Light gray
            'gripp': '#32CD32',    # Green
            'usb-c': '#4169E1',    # Royal blue
            'default': '#F0F0F0'   # Light gray
        }
        
        # Product sizes for layout
        self.product_sizes = {
            'large': {'width': 200, 'height': 100},
            'medium': {'width': 150, 'height': 80},
            'small': {'width': 100, 'height': 50}
        }
    
    def get_brand_from_filename(self, filename):
        """Extract brand from filename"""
        filename_lower = filename.lower()
        for brand in self.brand_colors.keys():
            if brand in filename_lower and brand != 'default':
                return brand
        return 'default'
    
    def get_product_size_category(self, category):
        """Determine size category for product type"""
        size_mapping = {
            'privacy_filters': 'large',
            'hubs_docks': 'medium', 
            'cables_adapters': 'small',
            'chargers_power': 'medium',
            'keyboard_accessories': 'large',
            'charging_stands': 'medium'
        }
        return size_mapping.get(category, 'medium')
    
    def load_product_image(self, image_filename):
        """Load and resize product image"""
        try:
            image_path = os.path.join(self.image_databank_path, image_filename)
            if os.path.exists(image_path):
                img = Image.open(image_path)
                # Resize to standard dimensions
                img = img.resize((120, 120), Image.Resampling.LANCZOS)
                return img
            else:
                print(f"Image not found: {image_path}")
                return None
        except Exception as e:
            print(f"Error loading image {image_filename}: {e}")
            return None
    
    def create_product_display_name(self, filename):
        """Create clean display name from filename"""
        # Remove file extension
        name = filename.replace('.jpg', '').replace('.png', '')
        
        # Clean up common patterns
        name = name.replace('_', ' ')
        name = name.replace('-', ' ')
        
        # Capitalize words
        words = name.split()
        cleaned_words = []
        
        for word in words:
            # Handle special cases
            if word.lower() in ['usb', 'usb-c', '20w', '30w', '36w', '45w', '60w', '240w', '3in1', '2in1']:
                cleaned_words.append(word.upper())
            elif word.lower() in ['pulse', 'tekne', 'alogic', 'gripp']:
                cleaned_words.append(word.upper())
            else:
                cleaned_words.append(word.title())
        
        return ' '.join(cleaned_words)
    
    def generate_mac_accessories_planogram(self, store_name="IMAGINE KORAMANGALA", wall_number=1):
        """Generate Mac accessories planogram with actual product images"""
        
        # Create figure
        fig, ax = plt.subplots(figsize=(20, 14))
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_aspect('equal')
        
        # Title
        title = f"{store_name.upper()} - MAC ACCESSORIES WALL {wall_number}"
        subtitle = "Professional Shelf Layout | 22 Products | Dimension-Optimized"
        
        ax.text(50, 95, title, ha='center', va='center', 
                fontsize=18, fontweight='bold', color='#2C3E50')
        ax.text(50, 92, subtitle, ha='center', va='center', 
                fontsize=12, color='#7F8C8D')
        
        # Create layout sections
        sections = [
            {
                'name': 'Privacy Filters & Keyboard Accessories',
                'y_start': 75,
                'height': 12,
                'products': self.mac_products['privacy_filters'] + self.mac_products['keyboard_accessories'],
                'color': '#E8F4FD'
            },
            {
                'name': 'Hubs & Docks',
                'y_start': 55,
                'height': 15,
                'products': self.mac_products['hubs_docks'],
                'color': '#F0F8FF'
            },
            {
                'name': 'Cables & Adapters',
                'y_start': 35,
                'height': 15,
                'products': self.mac_products['cables_adapters'],
                'color': '#F5F5F5'
            },
            {
                'name': 'Chargers & Power',
                'y_start': 15,
                'height': 15,
                'products': self.mac_products['chargers_power'],
                'color': '#FFF8DC'
            }
        ]
        
        product_count = 0
        
        for section in sections:
            # Section background
            section_rect = FancyBboxPatch(
                (5, section['y_start'] - section['height']), 90, section['height'],
                boxstyle="round,pad=0.5",
                facecolor=section['color'],
                edgecolor='#BDC3C7',
                linewidth=1,
                alpha=0.3
            )
            ax.add_patch(section_rect)
            
            # Section title
            ax.text(7, section['y_start'] - 2, section['name'], 
                   fontsize=11, fontweight='bold', color='#34495E')
            
            # Arrange products in this section
            products_per_row = min(len(section['products']), 6)
            if len(section['products']) > 6:
                rows = 2
                products_per_row = 3
            else:
                rows = 1
            
            x_spacing = 85 / products_per_row if products_per_row > 0 else 0
            
            for i, product_file in enumerate(section['products']):
                if i >= 12:  # Limit products per section
                    break
                    
                row = i // products_per_row
                col = i % products_per_row
                
                x_pos = 10 + col * x_spacing
                y_pos = section['y_start'] - 4 - (row * 6)
                
                # Get brand and color
                brand = self.get_brand_from_filename(product_file)
                brand_color = self.brand_colors.get(brand, self.brand_colors['default'])
                
                # Product rectangle
                product_rect = FancyBboxPatch(
                    (x_pos, y_pos - 4), 12, 4,
                    boxstyle="round,pad=0.2",
                    facecolor=brand_color,
                    edgecolor='#2C3E50',
                    linewidth=1.5,
                    alpha=0.8
                )
                ax.add_patch(product_rect)
                
                # Product name
                display_name = self.create_product_display_name(product_file)
                # Truncate long names
                if len(display_name) > 20:
                    display_name = display_name[:17] + "..."
                
                ax.text(x_pos + 6, y_pos - 2, display_name, 
                       ha='center', va='center', fontsize=8, 
                       fontweight='bold', color='white' if brand != 'default' else 'black')
                
                # Brand label
                ax.text(x_pos + 6, y_pos - 3.2, brand.upper(), 
                       ha='center', va='center', fontsize=6, 
                       color='white' if brand != 'default' else 'gray',
                       style='italic')
                
                product_count += 1
        
        # Add bottom section for charging stands
        if self.mac_products['charging_stands']:
            # Charging stands section
            charging_rect = FancyBboxPatch(
                (5, 2), 90, 10,
                boxstyle="round,pad=0.5",
                facecolor='#2C3E50',
                edgecolor='#34495E',
                linewidth=2,
                alpha=0.9
            )
            ax.add_patch(charging_rect)
            
            ax.text(50, 10, "CHARGING STATIONS & WIRELESS CHARGERS", 
                   ha='center', va='center', fontsize=12, 
                   fontweight='bold', color='white')
            
            # Add charging products
            charging_products = self.mac_products['charging_stands']
            x_spacing = 80 / len(charging_products) if charging_products else 0
            
            for i, product_file in enumerate(charging_products):
                x_pos = 10 + i * x_spacing
                
                # Product rectangle
                charge_rect = FancyBboxPatch(
                    (x_pos, 4), 15, 4,
                    boxstyle="round,pad=0.3",
                    facecolor='#3498DB',
                    edgecolor='white',
                    linewidth=2,
                    alpha=0.9
                )
                ax.add_patch(charge_rect)
                
                display_name = self.create_product_display_name(product_file)
                if len(display_name) > 15:
                    display_name = display_name[:12] + "..."
                
                ax.text(x_pos + 7.5, 6, display_name, 
                       ha='center', va='center', fontsize=8, 
                       fontweight='bold', color='white')
                
                product_count += 1
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        # Save planogram
        store_clean = store_name.lower().replace(' ', '_').replace('-', '_')
        output_filename = f"{store_clean}_wall{wall_number}_mac_accessories_images.png"
        output_path = os.path.join(self.output_path, output_filename)
        
        os.makedirs(self.output_path, exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        return {
            'output_file': output_path,
            'product_count': product_count,
            'store_name': store_name,
            'wall_number': wall_number,
            'categories': list(self.mac_products.keys())
        }
    
    def generate_multiple_walls(self, store_name="IMAGINE KORAMANGALA", wall_count=3):
        """Generate multiple Mac accessories walls"""
        results = []
        
        for wall_num in range(1, wall_count + 1):
            result = self.generate_mac_accessories_planogram(store_name, wall_num)
            results.append(result)
            print(f"Generated Mac accessories planogram for Wall {wall_num}: {result['output_file']}")
        
        return results

def main():
    """Test the Mac accessories image planogram generator"""
    generator = MacAccessoriesImagePlanogram()
    
    # Generate planogram for Koramangala store
    print("Generating Mac Accessories Planogram with Product Images...")
    
    result = generator.generate_mac_accessories_planogram(
        store_name="IMAGINE KORAMANGALA BENGALURU (BANGALORE)",
        wall_number=1
    )
    
    print(f"✅ Generated planogram: {result['output_file']}")
    print(f"📦 Products included: {result['product_count']}")
    print(f"🏪 Store: {result['store_name']}")
    print(f"🧱 Wall: {result['wall_number']}")
    print(f"📂 Categories: {', '.join(result['categories'])}")
    
    return result

if __name__ == "__main__":
    main()