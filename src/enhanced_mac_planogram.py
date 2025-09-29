"""
Enhanced Mac Accessories Planogram with Real Product Images
Creates professional planograms using actual product images from the databank
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from PIL import Image
import numpy as np
from pathlib import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

class EnhancedMacPlanogram:
    def __init__(self):
        self.image_databank_path = "pdf_databank/output/images/combined"
        self.output_path = "output"
        
        # Organized product categories with actual filenames from databank
        self.product_layout = {
            'top_row': {
                'title': 'MAGNETIC PRIVACY FILTERS & KEYBOARD PROTECTION',
                'products': [
                    {'file': 'pulse mac privacy filter.jpg', 'name': 'Magnetic Privacy Filter for MacBook', 'brand': 'PULSE'},
                    {'file': 'pulse mac privacy filter.jpg', 'name': 'Magnetic Privacy Filter for MacBook', 'brand': 'PULSE'}, 
                    {'file': 'pulse mac privacy filter.jpg', 'name': 'Magnetic Privacy Filter for MacBook', 'brand': 'PULSE'}
                ],
                'color': '#1E90FF'
            },
            'middle_row': {
                'title': 'CONNECTIVITY HUBS & ADAPTERS',
                'products': [
                    {'file': 'tekne multiport hub.jpg', 'name': 'TEKNE Multiport Hub', 'brand': 'TEKNE'},
                    {'file': 'alogic usb hub.jpg', 'name': 'ALOGIC USB Hub', 'brand': 'ALOGIC'},
                    {'file': 'alogic usb-c dock 3in1.jpg', 'name': 'ALOGIC USB-C Dock 3-in-1', 'brand': 'ALOGIC'},
                    {'file': 'powerup usb hub.jpg', 'name': 'PowerUp USB Hub', 'brand': 'ALOGIC'},
                    {'file': 'alogic usb-c cable.jpg', 'name': 'ALOGIC USB-C Cable', 'brand': 'ALOGIC'},
                    {'file': 'tekne usb-c lightning cable.jpg', 'name': 'TEKNE USB-C to Lightning', 'brand': 'TEKNE'}
                ],
                'color': '#E6E6FA'
            },
            'bottom_row': {
                'title': 'CHARGING SOLUTIONS & POWER ACCESSORIES',
                'products': [
                    {'file': 'Gripp keyboard cover.png', 'name': 'GRIPP Keyboard Skin for Apple MacBook Pro 16"', 'brand': 'GRIPP'},
                    {'file': 'Gripp keyboard cover.png', 'name': 'GRIPP Keyboard Skin for MacBook Air 13 (2024)', 'brand': 'GRIPP'},
                    {'file': 'Gripp keyboard cover.png', 'name': 'GRIPP Keyboard Skin for Apple MacBook Pro 14"', 'brand': 'GRIPP'}
                ],
                'color': '#2C3E50'
            }
        }
        
        # Brand colors matching the example
        self.brand_colors = {
            'PULSE': '#1E90FF',
            'TEKNE': '#FF1493', 
            'ALOGIC': '#E6E6FA',
            'GRIPP': '#2C3E50',
            'BELKIN': '#FF6B35'
        }
    
    def load_and_resize_image(self, image_filename, target_width, target_height):
        """Load and resize product image"""
        try:
            image_path = os.path.join(self.image_databank_path, image_filename)
            if os.path.exists(image_path):
                img = Image.open(image_path)
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # Resize maintaining aspect ratio
                img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                return np.array(img)
            else:
                print(f"Image not found: {image_path}")
                return None
        except Exception as e:
            print(f"Error loading image {image_filename}: {e}")
            return None

    def add_product_image(self, ax, image_filename, x_pos, y_pos, width, height, product_name, brand_name):
        """Add product image to the planogram"""
        # Load image
        img_array = self.load_and_resize_image(image_filename, int(width*10), int(height*10))
        
        if img_array is not None:
            # Add image to plot
            imagebox = OffsetImage(img_array, zoom=0.8)
            ab = AnnotationBbox(imagebox, (x_pos + width/2, y_pos + height/2), 
                              frameon=True, boxcoords="data")
            ab.patch.set_facecolor('white')
            ab.patch.set_edgecolor('#2C3E50')
            ab.patch.set_linewidth(2)
            ax.add_artist(ab)
            
            # Add product label below image
            ax.text(x_pos + width/2, y_pos - 2, product_name, 
                   ha='center', va='center', fontsize=8, 
                   fontweight='bold', color='#2C3E50')
            ax.text(x_pos + width/2, y_pos - 4, brand_name, 
                   ha='center', va='center', fontsize=10, 
                   fontweight='bold', color=self.brand_colors.get(brand_name, '#2C3E50'))
        else:
            # Fallback to colored rectangle if image not found
            brand_color = self.brand_colors.get(brand_name, '#E6E6FA')
            rect = FancyBboxPatch(
                (x_pos, y_pos), width, height,
                boxstyle="round,pad=0.5",
                facecolor=brand_color,
                edgecolor='white',
                linewidth=2
            )
            ax.add_patch(rect)
            
            text_color = 'white' if brand_color != '#E6E6FA' else 'black'
            ax.text(x_pos + width/2, y_pos + height/2 + 1, product_name, 
                   ha='center', va='center', fontsize=9, 
                   fontweight='bold', color=text_color, wrap=True)
            ax.text(x_pos + width/2, y_pos + height/2 - 1, brand_name, 
                   ha='center', va='center', fontsize=11, 
                   fontweight='bold', color=text_color)

    def create_professional_planogram(self, store_name="IMAGINE KORAMANGALA", wall_number=1):
        """Create a professional planogram matching the example style"""
        
        # Create figure with white background
        fig, ax = plt.subplots(figsize=(20, 14))
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_aspect('equal')
        fig.patch.set_facecolor('white')
        
        # Title section
        title = f"{store_name.upper()} - MAC ACCESSORIES WALL {wall_number}"
        subtitle = "Professional Shelf Layout | 22 Products | Dimension-Optimized"
        
        ax.text(50, 95, title, ha='center', va='center', 
                fontsize=20, fontweight='bold', color='#2C3E50')
        ax.text(50, 91, subtitle, ha='center', va='center', 
                fontsize=12, color='#7F8C8D')
        
        # Top row - Privacy Filters (Large images)
        top_products = self.product_layout['top_row']['products']
        for i, product in enumerate(top_products):
            x_pos = 12 + i * 30
            y_pos = 75
            
            self.add_product_image(ax, product['file'], x_pos, y_pos, 25, 12, 
                                 product['name'], product['brand'])
        
        # Middle section - Small product images
        middle_y = 55
        small_products = [
            {'name': 'TEKNE Speed', 'brand': 'TEKNE', 'file': 'tekne 20W adapter.jpg'},
            {'name': 'PULSE', 'brand': 'PULSE', 'file': 'pulse 20W adapter.jpg'},
            {'name': 'ALOGIC USB', 'brand': 'ALOGIC', 'file': 'alogic usb hub.jpg'},
            {'name': 'ALOGIC USB', 'brand': 'ALOGIC', 'file': 'alogic usb-c cable.jpg'},
            {'name': 'ALOGIC USB', 'brand': 'ALOGIC', 'file': 'alogic usb-c dock 3in1.jpg'},
            {'name': 'ALOGIC USB', 'brand': 'ALOGIC', 'file': 'powerup usb hub.jpg'},
            {'name': 'ALOGIC USB', 'brand': 'ALOGIC', 'file': 'alogic usb hub.jpg'},
            {'name': 'ALOGIC USB', 'brand': 'ALOGIC', 'file': 'alogic usb-c cable.jpg'}
        ]
        
        # First row of small products
        for i in range(8):
            x_pos = 8 + i * 10.5
            product = small_products[i] if i < len(small_products) else small_products[0]
            
            self.add_product_image(ax, product['file'], x_pos, middle_y, 9, 6, 
                                 product['name'], product['brand'])
        
        # Second row of small products
        second_row_y = middle_y - 12
        second_row_products = [
            {'name': 'ALOGIC USB', 'brand': 'ALOGIC', 'file': 'alogic usb hub.jpg'},
            {'name': 'ALOGIC USB', 'brand': 'ALOGIC', 'file': 'alogic usb-c dock 3in1.jpg'},
            {'name': 'BELKIN MagSafe', 'brand': 'BELKIN', 'file': 'tekne multiport hub.jpg'},
            {'name': 'TEKNE Speed', 'brand': 'TEKNE', 'file': 'tekne 36W adapter.jpg'},
            {'name': 'TEKNE macbook', 'brand': 'TEKNE', 'file': 'tekne macbook 3in1 kit.jpg'},
            {'name': 'TEKNE macbook', 'brand': 'TEKNE', 'file': 'tekne usb-c lightning cable.jpg'},
            {'name': 'TEKNE macbook', 'brand': 'TEKNE', 'file': 'Tekne 45W adapter.jpg'},
            {'name': 'TEKNE macbook', 'brand': 'TEKNE', 'file': 'tekne 60W cable.jpg'}
        ]
        
        for i in range(8):
            x_pos = 8 + i * 10.5
            product = second_row_products[i]
            
            self.add_product_image(ax, product['file'], x_pos, second_row_y, 9, 6, 
                                 product['name'], product['brand'])
        
        # Bottom section - GRIPP keyboard products with images
        bottom_y = 15
        gripp_products = [
            {"name": "Keyboard Skin for Apple Macbook Pro 16\"", "file": "Gripp keyboard cover.png"},
            {"name": "Keyboard Skin for Macbook Air 13 (2024)", "file": "Gripp keyboard cover.png"}, 
            {"name": "Keyboard Skin for Apple Macbook Pro 14\"", "file": "Gripp keyboard cover.png"}
        ]
        
        for i, product in enumerate(gripp_products):
            x_pos = 12 + i * 30
            
            self.add_product_image(ax, product['file'], x_pos, bottom_y, 25, 12, 
                                 product['name'], 'GRIPP')
        
        # Remove axes and spines
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Save the planogram
        store_clean = store_name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        output_filename = f"{store_clean}_wall{wall_number}_mac_accessories_professional.png"
        output_path = os.path.join(self.output_path, output_filename)
        
        os.makedirs(self.output_path, exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        return {
            'output_file': output_path,
            'product_count': 22,
            'store_name': store_name,
            'wall_number': wall_number
        }

def main():
    """Generate the enhanced Mac accessories planogram"""
    generator = EnhancedMacPlanogram()
    
    print("🎨 Creating Enhanced Mac Accessories Planogram...")
    
    result = generator.create_professional_planogram(
        store_name="IMAGINE KORAMANGALA BENGALURU (BANGALORE)",
        wall_number=1
    )
    
    print(f"✅ Generated professional planogram: {result['output_file']}")
    print(f"📦 Products: {result['product_count']}")
    print(f"🏪 Store: {result['store_name']}")
    print(f"🧱 Wall: {result['wall_number']}")
    
    return result

if __name__ == "__main__":
    main()