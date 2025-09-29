"""
Mac Accessories Planogram with Real Product Images
Creates planograms exactly like the example using actual product images
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image
import numpy as np
from pathlib import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

class MacPlanogramWithImages:
    def __init__(self):
        self.image_databank_path = "pdf_databank/output/images/combined"
        self.output_path = "output"
        
        # Product mapping with actual images from databank
        self.products = {
            'top_row': [
                {'file': 'pulse mac privacy filter.jpg', 'name': 'Magnetic privacy filter for MacBook', 'brand': 'PULSE'},
                {'file': 'pulse mac privacy filter.jpg', 'name': 'Magnetic privacy filter for MacBook', 'brand': 'PULSE'},
                {'file': 'pulse mac privacy filter.jpg', 'name': 'Magnetic privacy filter for MacBook', 'brand': 'PULSE'}
            ],
            'middle_small': [
                {'file': 'tekne 20W adapter.jpg', 'name': 'TEKNE Speed', 'brand': 'TEKNE'},
                {'file': 'pulse 20W adapter.jpg', 'name': 'PULSE', 'brand': 'PULSE'},
                {'file': 'alogic usb hub.jpg', 'name': 'ALOGIC USB', 'brand': 'ALOGIC'},
                {'file': 'alogic usb-c cable.jpg', 'name': 'ALOGIC USB', 'brand': 'ALOGIC'},
                {'file': 'alogic usb-c dock 3in1.jpg', 'name': 'ALOGIC USB', 'brand': 'ALOGIC'},
                {'file': 'powerup usb hub.jpg', 'name': 'ALOGIC USB', 'brand': 'ALOGIC'},
                {'file': 'usb-c 20W adapter.jpg', 'name': 'ALOGIC USB', 'brand': 'ALOGIC'},
                {'file': 'usb-c 30W adapter.jpg', 'name': 'ALOGIC USB', 'brand': 'ALOGIC'}
            ],
            'middle_small_2': [
                {'file': 'alogic usb hub.jpg', 'name': 'ALOGIC USB', 'brand': 'ALOGIC'},
                {'file': 'alogic usb-c dock 3in1.jpg', 'name': 'ALOGIC USB', 'brand': 'ALOGIC'},
                {'file': 'tekne multiport hub.jpg', 'name': 'BELKIN MagSafe', 'brand': 'BELKIN'},
                {'file': 'tekne 36W adapter.jpg', 'name': 'TEKNE Speed', 'brand': 'TEKNE'},
                {'file': 'tekne macbook 3in1 kit.jpg', 'name': 'TEKNE macbook', 'brand': 'TEKNE'},
                {'file': 'tekne usb-c lightning cable.jpg', 'name': 'TEKNE macbook', 'brand': 'TEKNE'},
                {'file': 'Tekne 45W adapter.jpg', 'name': 'TEKNE macbook', 'brand': 'TEKNE'},
                {'file': 'tekne 60W cable.jpg', 'name': 'TEKNE macbook', 'brand': 'TEKNE'}
            ],
            'bottom_row': [
                {'file': 'Gripp keyboard cover.png', 'name': 'Keyboard Skin for Apple Macbook Pro 16"', 'brand': 'GRIPP'},
                {'file': 'Gripp keyboard cover.png', 'name': 'Keyboard Skin for Macbook Air 13 (2024)', 'brand': 'GRIPP'},
                {'file': 'Gripp keyboard cover.png', 'name': 'Keyboard Skin for Apple Macbook Pro 14"', 'brand': 'GRIPP'}
            ]
        }
        
        # Brand colors matching the example
        self.brand_colors = {
            'PULSE': '#1E90FF',
            'TEKNE': '#FF1493', 
            'ALOGIC': '#E6E6FA',
            'GRIPP': '#2C3E50',
            'BELKIN': '#FF6B35'
        }
    
    def load_product_image(self, image_filename, target_size=(100, 100)):
        """Load and process product image"""
        try:
            image_path = os.path.join(self.image_databank_path, image_filename)
            if os.path.exists(image_path):
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize maintaining aspect ratio
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Create a white background
                background = Image.new('RGB', target_size, 'white')
                
                # Center the image on the background
                x_offset = (target_size[0] - img.width) // 2
                y_offset = (target_size[1] - img.height) // 2
                background.paste(img, (x_offset, y_offset))
                
                return np.array(background)
            else:
                print(f"Image not found: {image_path}")
                return None
        except Exception as e:
            print(f"Error loading image {image_filename}: {e}")
            return None
    
    def add_product_with_image(self, ax, product, x_pos, y_pos, width, height):
        """Add product with package outline and image"""
        
        # Add black package outline representing actual product package size
        package_rect = Rectangle(
            (x_pos, y_pos), width, height,
            facecolor='white',
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(package_rect)
        
        # Load and add product image inside the package
        target_size = (int(width*8), int(height*8))  # Slightly smaller than package
        img_array = self.load_product_image(product['file'], target_size)
        
        if img_array is not None:
            # Add product image centered within the package outline
            imagebox = OffsetImage(img_array, zoom=0.7)
            ab = AnnotationBbox(imagebox, (x_pos + width/2, y_pos + height/2), 
                              frameon=False, boxcoords="data")
            ax.add_artist(ab)
        
        # Add product name below package
        ax.text(x_pos + width/2, y_pos - 1, product['name'], 
               ha='center', va='center', fontsize=8, 
               fontweight='bold', color='#2C3E50')
        
        # Add brand name below product name
        ax.text(x_pos + width/2, y_pos - 3, product['brand'], 
               ha='center', va='center', fontsize=10, 
               fontweight='bold', color=self.brand_colors.get(product['brand'], '#2C3E50'))
    
    def add_shelf_background(self, ax, y_pos, height, shelf_color='#F5F5F5'):
        """Add shelf background"""
        shelf_rect = Rectangle((5, y_pos - 1), 90, height + 2, 
                              facecolor=shelf_color, edgecolor='#D3D3D3', 
                              linewidth=1, alpha=0.3)
        ax.add_patch(shelf_rect)

    def create_image_planogram(self, store_name="IMAGINE KORAMANGALA", wall_number=1):
        """Create planogram with product images matching the example style"""
        
        # Create figure
        fig, ax = plt.subplots(figsize=(20, 14))
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_aspect('equal')
        fig.patch.set_facecolor('white')
        
        # Title
        title = f"{store_name.upper()} - MAC ACCESSORIES WALL {wall_number}"
        subtitle = "Professional Shelf Layout | 22 Products | Dimension-Optimized"
        
        ax.text(50, 95, title, ha='center', va='center', 
                fontsize=18, fontweight='bold', color='#2C3E50')
        ax.text(50, 91, subtitle, ha='center', va='center', 
                fontsize=12, color='#7F8C8D')
        
        # Define constant shelf parameters - realistic shelf dimensions
        shelf_start_x = 8
        shelf_end_x = 92
        shelf_width = shelf_end_x - shelf_start_x  # 84 units total width for all shelves
        
        # Add shelf backgrounds with constant width and reduced gaps between shelves
        self.add_shelf_background(ax, 72, 18)  # Top shelf - moved up, reduced height
        self.add_shelf_background(ax, 52, 14)  # Middle shelf 1 - moved up, closer to top shelf
        self.add_shelf_background(ax, 34, 14)  # Middle shelf 2 - moved up, closer to middle shelf 1
        self.add_shelf_background(ax, 14, 16)  # Bottom shelf - moved up, closer to middle shelf 2
        
        # Top row - 3 large privacy filter products (Target total: ~82 units)
        top_products = self.products['top_row']
        top_widths = [25, 26, 25]  # Total: 76 units
        top_gaps = [3, 3]  # Total gaps: 6 units = 82 total
        
        x_pos = shelf_start_x
        for i, (product, width) in enumerate(zip(top_products, top_widths)):
            y_pos = 74  # Adjusted for new shelf position
            self.add_product_with_image(ax, product, x_pos, y_pos, width, 16)
            x_pos += width + (top_gaps[i] if i < len(top_gaps) else 0)
        
        # Middle row 1 - 8 smaller products (Target total: ~82 units) - MADE SMALLER
        middle1_products = self.products['middle_small']
        middle1_widths = [8.5, 9, 9.5, 9, 8.5, 9.5, 9, 8.5]  # Total: 71.5 units (reduced)
        middle1_gaps = [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]  # Total gaps: 10.5 units = 82 total
        
        x_pos = shelf_start_x
        for i, (product, width) in enumerate(zip(middle1_products, middle1_widths)):
            y_pos = 54  # Adjusted for new shelf position, reduced gap from top row
            self.add_product_with_image(ax, product, x_pos, y_pos, width, 10)  # Reduced height from 12 to 10
            x_pos += width + (middle1_gaps[i] if i < len(middle1_gaps) else 0)
        
        # Middle row 2 - 8 smaller products (Target total: ~82 units) - MADE SMALLER
        middle2_products = self.products['middle_small_2']
        middle2_widths = [9, 8.5, 9.5, 9, 9, 8.5, 9.5, 8.5]  # Total: 71.5 units (reduced)
        middle2_gaps = [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]  # Total gaps: 10.5 units = 82 total
        
        x_pos = shelf_start_x
        for i, (product, width) in enumerate(zip(middle2_products, middle2_widths)):
            y_pos = 36  # Adjusted for new shelf position, reduced gap from middle row 1
            self.add_product_with_image(ax, product, x_pos, y_pos, width, 10)  # Reduced height from 12 to 10
            x_pos += width + (middle2_gaps[i] if i < len(middle2_gaps) else 0)
        
        # Bottom row - 3 keyboard products (Target total: ~82 units) - MORE RECTANGULAR
        bottom_products = self.products['bottom_row']
        bottom_widths = [26, 26, 26]  # Total: 78 units - keeping width for rectangular shape
        bottom_gaps = [2, 2]  # Total gaps: 4 units = 82 total
        
        x_pos = shelf_start_x
        for i, (product, width) in enumerate(zip(bottom_products, bottom_widths)):
            y_pos = 16  # Adjusted for new shelf position, reduced gap from middle row 2
            self.add_product_with_image(ax, product, x_pos, y_pos, width, 10)  # Reduced height from 15 to 10 for more rectangular shape
            x_pos += width + (bottom_gaps[i] if i < len(bottom_gaps) else 0)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Save planogram
        store_clean = store_name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        output_filename = f"{store_clean}_wall{wall_number}_mac_accessories_with_images.png"
        output_path = os.path.join(self.output_path, output_filename)
        
        os.makedirs(self.output_path, exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        return {
            'output_file': output_path,
            'product_count': 19,  # 3 + 8 + 8 = 19 products total
            'store_name': store_name,
            'wall_number': wall_number
        }

def main():
    """Generate Mac accessories planogram with product images"""
    generator = MacPlanogramWithImages()
    
    print("🖼️  Creating Mac Accessories Planogram with Product Images...")
    
    result = generator.create_image_planogram(
        store_name="IMAGINE KORAMANGALA BENGALURU (BANGALORE)",
        wall_number=1
    )
    
    print(f"✅ Generated image-based planogram: {result['output_file']}")
    print(f"📦 Products: {result['product_count']}")
    print(f"🏪 Store: {result['store_name']}")
    print(f"🧱 Wall: {result['wall_number']}")
    
    return result

if __name__ == "__main__":
    main()