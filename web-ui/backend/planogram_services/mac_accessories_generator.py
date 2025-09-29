"""
Enhanced Mac Accessories Planogram Generator with Historical Sales Data Integration
- Uses real product images from databank
- Integrates historical sales data for optimal product placement
- Creates realistic shelf layouts with proper package sizing
- Supports constant shelf dimensions with varied product sizes
"""
from __future__ import annotations

import os
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import numpy as np

# Repo root (Planogram)
REPO_ROOT = Path(__file__).resolve().parents[3]
HISTORICAL_DATA = REPO_ROOT / "data/historical_sales_mac_accessories.json"
IMAGE_DATABANK = REPO_ROOT / "pdf_databank/output/images/combined"
OUTPUT_DIR = REPO_ROOT / "web-ui/backend/output"

logger = logging.getLogger(__name__)


@dataclass
class MacProduct:
    """Enhanced Mac product with sales data"""
    name: str
    brand: str
    category: str
    image_file: str
    units_sold: int
    revenue: float
    market_share: float
    width: float
    height: float
    priority: int


class MacAccessoriesGenerator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.image_databank_path = IMAGE_DATABANK
        self.output_path = OUTPUT_DIR
        
        # Brand colors matching the example
        self.brand_colors = {
            'PULSE': '#1E90FF',
            'TEKNE': '#FF1493', 
            'ALOGIC': '#E6E6FA',
            'GRIPP': '#2C3E50',
            'BELKIN': '#FF6B35'
        }
        
        # Load historical sales data
        self.sales_data = self.load_historical_data()
        
    def load_historical_data(self) -> Dict:
        """Load historical sales data from JSON file"""
        try:
            if HISTORICAL_DATA.exists():
                with open(HISTORICAL_DATA, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Historical data file not found: {HISTORICAL_DATA}")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            return {}
    
    def load_product_image(self, image_filename: str, target_size: Tuple[int, int] = (100, 100)) -> Optional[np.ndarray]:
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
                self.logger.warning(f"Image not found: {image_path}")
                return None
        except Exception as e:
            self.logger.error(f"Error loading image {image_filename}: {e}")
            return None
    
    def get_products_from_sales_data(self) -> List[MacProduct]:
        """Extract products from historical sales data with proper mapping to image files"""
        products = []
        
        if not self.sales_data or 'sales_performance' not in self.sales_data:
            self.logger.warning("No sales data available, using fallback products")
            return self.get_fallback_products()
        
        # Image file mapping based on actual databank files
        image_mapping = {
            # Privacy Filters
            'Magnetic Privacy Filter for MacBook Pro 16"': 'pulse mac privacy filter.jpg',
            'Magnetic Privacy Filter for MacBook Air 13"': 'pulse mac privacy filter.jpg', 
            'Magnetic Privacy Filter for MacBook Pro 14"': 'pulse mac privacy filter.jpg',
            
            # Hubs & Docks
            'ALOGIC USB-C Hub 7-in-1': 'alogic usb hub.jpg',
            'TEKNE Multiport Hub USB-C': 'tekne multiport hub.jpg',
            'ALOGIC USB-C Dock 3-in-1': 'alogic usb-c dock 3in1.jpg',
            'PowerUp USB Hub': 'powerup usb hub.jpg',
            'BELKIN MagSafe 3-in-1': 'tekne multiport hub.jpg',
            'TEKNE USB-C Lightning Cable': 'tekne usb-c lightning cable.jpg',
            
            # Cables & Adapters
            'TEKNE 20W USB-C Adapter': 'tekne 20W adapter.jpg',
            'PULSE 20W USB-C Adapter': 'pulse 20W adapter.jpg',
            'ALOGIC USB-C Cable 2m': 'alogic usb-c cable.jpg',
            'TEKNE 36W USB-C Adapter': 'tekne 36W adapter.jpg',
            'ALOGIC USB-C to Lightning Cable': 'alogic usb-c cable.jpg',
            'TEKNE 45W USB-C Adapter': 'Tekne 45W adapter.jpg',
            'USB-C 30W Adapter': 'usb-c 30W adapter.jpg',
            
            # Keyboard Accessories
            'Keyboard Skin for Apple MacBook Pro 16"': 'Gripp keyboard cover.png',
            'Keyboard Skin for MacBook Air 13 (2024)': 'Gripp keyboard cover.png',
            'Keyboard Skin for Apple MacBook Pro 14"': 'Gripp keyboard cover.png',
            
            # Charging Accessories
            'TEKNE MacBook 3-in-1 Kit': 'tekne macbook 3in1 kit.jpg',
            'TEKNE 60W USB-C Cable': 'tekne 60W cable.jpg',
            'PULSE 30W Adapter': 'pulse 30W adapter.jpg',
            'USB-C 20W Adapter': 'usb-c 20W adapter.jpg'
        }
        
        # Category priorities for shelf placement
        category_priorities = {
            'privacy_filters': 1,
            'hubs_docks': 2, 
            'cables_adapters': 3,
            'keyboard_accessories': 4,
            'charging_accessories': 3
        }
        
        # Extract products from sales data
        for category, data in self.sales_data['sales_performance'].items():
            priority = category_priorities.get(category, 5)
            
            for product_data in data.get('top_products', []):
                name = product_data['name']
                brand = product_data['brand']
                image_file = image_mapping.get(name, 'pulse mac privacy filter.jpg')  # fallback
                
                # Determine dimensions based on category - realistic product sizes
                if category == 'privacy_filters':
                    width, height = 28, 18  # Screen-sized rectangles
                elif category == 'keyboard_accessories':
                    width, height = 30, 8   # Wide rectangles for keyboard covers
                else:
                    width, height = 9, 9    # Small squares for hubs/cables
                
                products.append(MacProduct(
                    name=name,
                    brand=brand,
                    category=category,
                    image_file=image_file,
                    units_sold=product_data['units_sold'],
                    revenue=product_data['revenue'],
                    market_share=product_data['market_share'],
                    width=width,
                    height=height,
                    priority=priority
                ))
        
        # Sort by priority then by units sold
        products.sort(key=lambda p: (p.priority, -p.units_sold))
        return products
    
    def get_fallback_products(self) -> List[MacProduct]:
        """Fallback products if sales data is not available"""
        return [
            MacProduct("Magnetic Privacy Filter for MacBook", "PULSE", "privacy_filters", 
                      "pulse mac privacy filter.jpg", 15000, 1349850, 0.33, 26, 16, 1),
            MacProduct("ALOGIC USB Hub", "ALOGIC", "hubs_docks", 
                      "alogic usb hub.jpg", 12000, 1559880, 0.15, 10, 10, 2),
            MacProduct("TEKNE 20W Adapter", "TEKNE", "cables_adapters", 
                      "tekne 20W adapter.jpg", 28000, 1399720, 0.22, 10, 10, 3),
            MacProduct("Keyboard Skin for MacBook Pro 16\"", "GRIPP", "keyboard_accessories", 
                      "Gripp keyboard cover.png", 15000, 599850, 0.43, 25, 15, 4)
        ]
    
    def add_product_with_image(self, ax, product: MacProduct, x_pos: float, y_pos: float, width: float, height: float):
        """Add clean product image with black border and labels"""
        
        # Add black package outline representing actual product package size
        package_rect = Rectangle(
            (x_pos, y_pos), width, height,
            facecolor='white',
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(package_rect)
        
        # Load and add product image inside the package
        target_size = (int(width*10), int(height*10))  # Proper sizing for clean images
        img_array = self.load_product_image(product.image_file, target_size)
        
        if img_array is not None:
            # Add clean image with proper zoom
            imagebox = OffsetImage(img_array, zoom=0.8)
            ab = AnnotationBbox(imagebox, (x_pos + width/2, y_pos + height/2 + 2), 
                              frameon=True, boxcoords="data")
            ab.patch.set_facecolor('white')
            ab.patch.set_edgecolor('black')
            ab.patch.set_linewidth(2)
            ax.add_artist(ab)
        
        # Add product name below package
        ax.text(x_pos + width/2, y_pos - 1, product.name, 
               ha='center', va='center', fontsize=8, 
               fontweight='bold', color='#2C3E50')
        
        # Add brand name below product name
        ax.text(x_pos + width/2, y_pos - 3, product.brand, 
               ha='center', va='center', fontsize=10, 
               fontweight='bold', color=self.brand_colors.get(product.brand, '#2C3E50'))
    
    def add_shelf_background(self, ax, y_pos: float, height: float, shelf_color: str = '#F5F5F5'):
        """Add shelf background - centered and properly sized"""
        shelf_rect = Rectangle((5, y_pos - 1), 90, height + 2, 
                              facecolor=shelf_color, edgecolor='#D3D3D3', 
                              linewidth=1, alpha=0.3)
        ax.add_patch(shelf_rect)
    
    def create_planogram(self, store_name: str = "IMAGINE KORAMANGALA", wall_number: int = 1) -> str:
        """Create enhanced planogram with improved layout and sizing"""
        
        # Get products from sales data
        all_products = self.get_products_from_sales_data()
        
        # Organize products by category
        products_by_category = {}
        for product in all_products:
            if product.category not in products_by_category:
                products_by_category[product.category] = []
            products_by_category[product.category].append(product)
        
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
        
        # Add shelf backgrounds with adjusted sizes for larger boxes
        self.add_shelf_background(ax, 68, 20)  # Top shelf - increased height for larger boxes
        self.add_shelf_background(ax, 48, 15)  # Middle shelf 1 - increased height for larger boxes
        self.add_shelf_background(ax, 30, 15)  # Middle shelf 2 - increased height for larger boxes
        self.add_shelf_background(ax, 10, 15)  # Bottom shelf - keeping constant size
        
        # Prepare product data with fallback
        privacy_products = products_by_category.get('privacy_filters', [])[:3]
        if len(privacy_products) < 3:
            # Create fallback privacy filter products
            fallback_privacy = MacProduct("Magnetic privacy filter for MacBook", "PULSE", "privacy_filters", 
                                        "pulse mac privacy filter.jpg", 15000, 1349850, 0.33, 25, 16, 1)
            while len(privacy_products) < 3:
                privacy_products.append(fallback_privacy)
        
        # Get middle row products
        hub_products = products_by_category.get('hubs_docks', [])
        cable_products = products_by_category.get('cables_adapters', [])
        charging_products = products_by_category.get('charging_accessories', [])
        
        # Combine and prepare middle row products
        middle_products_1 = (hub_products + cable_products)[:8]
        middle_products_2 = (cable_products + charging_products)[:8]
        
        # Fill with fallbacks if needed
        fallback_middle = MacProduct("ALOGIC USB", "ALOGIC", "hubs_docks", 
                                   "alogic usb hub.jpg", 12000, 1559880, 0.15, 10, 10, 2)
        while len(middle_products_1) < 8:
            middle_products_1.append(fallback_middle)
        while len(middle_products_2) < 8:
            middle_products_2.append(fallback_middle)
        
        # Keyboard products
        keyboard_products = products_by_category.get('keyboard_accessories', [])[:3]
        if len(keyboard_products) < 3:
            fallback_keyboard = MacProduct("Keyboard Skin for Apple Macbook Pro 16\"", "GRIPP", "keyboard_accessories", 
                                         "Gripp keyboard cover.png", 15000, 599850, 0.43, 26, 10, 4)
            while len(keyboard_products) < 3:
                keyboard_products.append(fallback_keyboard)
        
        # Top row - 3 large privacy filter products (Target total: ~82 units)
        top_widths = [25, 26, 25]  # Total: 76 units
        top_gaps = [3, 3]  # Total gaps: 6 units = 82 total
        
        x_pos = shelf_start_x
        for i, (product, width) in enumerate(zip(privacy_products, top_widths)):
            y_pos = 74  # Adjusted for new shelf position
            self.add_product_with_image(ax, product, x_pos, y_pos, width, 16)
            x_pos += width + (top_gaps[i] if i < len(top_gaps) else 0)
        
        # Middle row 1 - 8 smaller products (Target total: ~82 units) - MADE SMALLER
        middle1_widths = [8.5, 9, 9.5, 9, 8.5, 9.5, 9, 8.5]  # Total: 71.5 units (reduced)
        middle1_gaps = [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]  # Total gaps: 10.5 units = 82 total
        
        x_pos = shelf_start_x
        for i, (product, width) in enumerate(zip(middle_products_1, middle1_widths)):
            y_pos = 54  # Adjusted for new shelf position, reduced gap from top row
            self.add_product_with_image(ax, product, x_pos, y_pos, width, 10)  # Reduced height from 12 to 10
            x_pos += width + (middle1_gaps[i] if i < len(middle1_gaps) else 0)
        
        # Middle row 2 - 8 smaller products (Target total: ~82 units) - MADE SMALLER
        middle2_widths = [9, 8.5, 9.5, 9, 9, 8.5, 9.5, 8.5]  # Total: 71.5 units (reduced)
        middle2_gaps = [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]  # Total gaps: 10.5 units = 82 total
        
        x_pos = shelf_start_x
        for i, (product, width) in enumerate(zip(middle_products_2, middle2_widths)):
            y_pos = 36  # Adjusted for new shelf position, reduced gap from middle row 1
            self.add_product_with_image(ax, product, x_pos, y_pos, width, 10)  # Reduced height from 12 to 10
            x_pos += width + (middle2_gaps[i] if i < len(middle2_gaps) else 0)
        
        # Bottom row - 3 keyboard products (Target total: ~82 units) - MORE RECTANGULAR
        bottom_widths = [26, 26, 26]  # Total: 78 units - keeping width for rectangular shape
        bottom_gaps = [2, 2]  # Total gaps: 4 units = 82 total
        
        x_pos = shelf_start_x
        for i, (product, width) in enumerate(zip(keyboard_products, bottom_widths)):
            y_pos = 16  # Adjusted for new shelf position, reduced gap from middle row 2
            self.add_product_with_image(ax, product, x_pos, y_pos, width, 10)  # Reduced height from 15 to 10 for more rectangular shape
            x_pos += width + (bottom_gaps[i] if i < len(bottom_gaps) else 0)
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Save planogram
        os.makedirs(self.output_path, exist_ok=True)
        store_clean = store_name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
        output_filename = f"{store_clean}_wall{wall_number}_mac_accessories_enhanced.png"
        output_path = os.path.join(self.output_path, output_filename)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        return output_path
    
    def generate_store_planograms(self, store_name: str, num_walls: int) -> Dict[str, str]:
        """Generate planograms for the specified store and number of walls"""
        results = {}
        
        for wall_num in range(1, min(num_walls + 1, 2)):  # Max 1 wall for Mac accessories
            output_path = self.create_planogram(store_name, wall_num)
            results[f"wall_{wall_num}"] = output_path
            self.logger.info(f"Generated Mac accessories planogram: {output_path}")
        
        return results