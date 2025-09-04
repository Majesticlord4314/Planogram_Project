#!/usr/bin/env python3
"""
Image-Based Cases & Covers Planogram Generator
Replicates the existing logic but uses actual product images instead of plots
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

# Import existing Cases generator to reuse business logic
try:
    from planogram_services.cases_covers_generator import CasesCoversGenerator
except ImportError:
    # Fallback: create a minimal base class
    class CasesCoversGenerator:
        def __init__(self, project_root_path):
            self.project_root = Path(project_root_path)
            self.output_path = self.project_root / "output"
            self.colors = {
                'apple': '#FFD700',
                'gripp': '#4169E1',
                'tekne': '#800080',
                'pulse': '#800080',
                'hyphen': '#FF69B4'
            }

        def load_real_cases_data(self):
            # Simple mock data for testing
            return [
                {'brand': 'Apple', 'series': 'iPhone 15', 'color': 'Black'},
                {'brand': 'Gripp', 'series': 'iPhone 15', 'color': 'Blue'},
                {'brand': 'Tekne', 'series': 'iPhone 15', 'color': 'Purple'},
            ] * 16  # 48 products for 6x8 grid

        def calculate_grid_size(self, total_store_walls, wall_number):
            return (8, 6)  # 8 rows, 6 columns = 48 products

        def create_dense_product_grid(self, products, grid_size, wall_number, total_walls):
            rows, cols = grid_size  # 8 rows, 6 cols = 48 products
            grid = []

            # Create structured product data with iPhone series and colors
            iphone_series = ['iPhone 15', 'iPhone 14', 'iPhone 13', 'iPhone 12']
            colors = ['Black', 'Blue', 'Purple', 'White', 'Red', 'Green', 'Pink', 'Yellow']

            # First 4 rows (24 products) - Apple only
            apple_products = []
            for i in range(24):
                series = iphone_series[i % len(iphone_series)]
                color = colors[i % len(colors)]
                apple_products.append({
                    'brand': 'Apple',
                    'series': series,
                    'color': color,
                    'name': f'{series} Case'
                })

            # Last 4 rows (24 products) - Tekne and Gripp
            other_products = []
            other_brands = ['Tekne', 'Gripp']
            for i in range(24):
                brand = other_brands[i % 2]  # Alternate between Tekne and Gripp
                series = iphone_series[i % len(iphone_series)]
                color = colors[i % len(colors)]
                other_products.append({
                    'brand': brand,
                    'series': series,
                    'color': color,
                    'name': f'{series} Case'
                })

            # Build grid: First 4 rows Apple, last 4 rows Tekne/Gripp
            product_idx = 0
            for r in range(rows):
                row = []
                for c in range(cols):
                    if r < 4:  # First 4 rows - Apple
                        if product_idx < len(apple_products):
                            row.append(apple_products[product_idx])
                        else:
                            row.append(None)
                    else:  # Last 4 rows - Tekne/Gripp
                        other_idx = product_idx - 24  # Offset for other brands
                        if other_idx < len(other_products):
                            row.append(other_products[other_idx])
                        else:
                            row.append(None)
                    product_idx += 1
                grid.append(row)
            return grid

class ImageBasedCasesGenerator(CasesCoversGenerator):
    """Image-based Cases generator that reuses all existing business logic"""
    
    def __init__(self, project_root_path: str):
        super().__init__(project_root_path)
        
        # Image settings
        self.image_dir = Path("/Users/shivansh420/Desktop/Planogram/Phone case photo")
        self.product_image_size = (140, 140)  # Standard size for each product
        self.spacing = 10
        self.margin = 40
        
        # Brand image mapping
        self.brand_images = {
            'apple': 'Apple.png',
            'gripp': 'Gripp.png', 
            'tekne': 'Tekne:Pulse.png',
            'pulse': 'Tekne:Pulse.png',  # Same image for Tekne and Pulse
            'hyphen': 'Tekne:Pulse.png'  # Fallback to Tekne image
        }
        
    def load_brand_image(self, brand: str) -> Image.Image:
        """Load and resize brand image"""
        brand_lower = brand.lower()
        image_filename = self.brand_images.get(brand_lower, 'Apple.png')  # Default to Apple
        
        try:
            image_path = self.image_dir / image_filename
            img = Image.open(image_path)
            # Resize to standard product size
            img = img.resize(self.product_image_size, Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            print(f"Error loading image for brand {brand}: {e}")
            # Create a colored rectangle as fallback
            return self.create_fallback_image(brand)
    
    def create_fallback_image(self, brand: str) -> Image.Image:
        """Create colored rectangle fallback if image not found"""
        # Use existing brand colors from parent class
        brand_color = self.colors.get(brand.lower(), self.colors['apple'])
        
        img = Image.new('RGB', self.product_image_size, brand_color)
        draw = ImageDraw.Draw(img)
        
        # Add brand text
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
            
        text = brand.upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.product_image_size[0] - text_width) // 2
        y = (self.product_image_size[1] - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        return img
    
    def generate_planogram(self, products: List[Dict], capacity: int, output_path: str, 
                          details_path: str, wall_number: int, store_name: str, 
                          total_walls: int = 2, total_store_walls: int = 11) -> bool:
        """Generate image-based planogram using existing business logic"""
        try:
            # Load real data (reuse parent logic)
            real_products = self.load_real_cases_data()
            if not real_products:
                print("No real Cases & Covers data found, using provided products")
                real_products = products
            
            # Get grid size (reuse parent logic)
            grid_size = self.calculate_grid_size(total_store_walls, wall_number)
            rows, cols = grid_size
            
            print(f"Generating IMAGE-BASED Cases & Covers planogram:")
            print(f"  Wall {wall_number} of {total_walls} Cases & Covers walls")
            print(f"  Grid: {rows}x{cols} = {rows*cols} products (8x6 layout)")
            print(f"  Using brand images: Apple, Gripp, Tekne/Pulse")
            
            # Create product grid (reuse parent logic)
            product_grid = self.create_dense_product_grid(real_products, grid_size, wall_number, total_walls)
            
            # Create image-based planogram
            canvas = self.create_image_planogram(product_grid, grid_size, store_name, wall_number, total_walls)
            
            # Save image
            canvas.save(output_path, 'PNG', dpi=(300, 300))
            
            # Generate details file (simple version)
            self.generate_details_file(details_path, wall_number, store_name, real_products, grid_size, total_walls)
            
            print(f"Image-based Cases & Covers planogram saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating image-based planogram: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_image_planogram(self, product_grid: List[List], grid_size: Tuple[int, int], 
                              store_name: str, wall_number: int, total_walls: int) -> Image.Image:
        """Create the actual image-based planogram"""
        rows, cols = grid_size
        
        # Calculate canvas size
        canvas_width = cols * (self.product_image_size[0] + self.spacing) + self.margin * 2
        canvas_height = rows * (self.product_image_size[1] + self.spacing) + self.margin * 2 + 100  # +100 for header
        
        # Create canvas
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        draw = ImageDraw.Draw(canvas)
        
        # Add header
        self.add_header(draw, canvas_width, store_name, wall_number, total_walls)
        
        # Place products in grid
        y_offset = self.margin + 80  # Start below header
        
        for row_idx, row in enumerate(product_grid):
            x_offset = self.margin
            
            for col_idx, product in enumerate(row):
                if product:  # Check if cell has a product
                    # Get brand from product
                    brand = product.get('brand', 'Apple')
                    
                    # Load brand image
                    product_img = self.load_brand_image(brand)
                    
                    # Paste product image
                    canvas.paste(product_img, (x_offset, y_offset))
                    
                    # Add product label
                    self.add_product_label(draw, product, x_offset, y_offset)
                
                x_offset += self.product_image_size[0] + self.spacing
            
            y_offset += self.product_image_size[1] + self.spacing
        
        return canvas
    
    def add_header(self, draw: ImageDraw.Draw, canvas_width: int, store_name: str, 
                   wall_number: int, total_walls: int):
        """Add header to planogram"""
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            subtitle_font = ImageFont.truetype("arial.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Main title
        title = f"{store_name.upper()} - CASES & COVERS WALL {wall_number}"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (canvas_width - title_width) // 2
        
        draw.text((title_x, 20), title, fill='black', font=title_font)
        
        # Subtitle
        subtitle = f"Wall {wall_number} of {total_walls} | Professional Layout with Brand Images"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (canvas_width - subtitle_width) // 2
        
        draw.text((subtitle_x, 50), subtitle, fill='gray', font=subtitle_font)
    
    def add_product_label(self, draw: ImageDraw.Draw, product: Dict, x: int, y: int):
        """Add detailed product label with series and color"""
        try:
            font = ImageFont.truetype("arial.ttf", 9)
        except:
            font = ImageFont.load_default()

        # Get product info
        brand = product.get('brand', 'Unknown')
        series = product.get('series', '')
        color = product.get('color', '')

        # Create multi-line label text like in reference planogram
        lines = []
        lines.append(brand.upper())
        if series:
            lines.append(series)
        if color:
            lines.append(color)

        # Position labels below image
        label_y = y + self.product_image_size[1] + 2
        line_height = 12

        for i, line in enumerate(lines):
            draw.text((x, label_y + i * line_height), line, fill='black', font=font)

    def generate_details_file(self, details_path: str, wall_number: int, store_name: str,
                             products: List[Dict], grid_size: Tuple[int, int], total_walls: int):
        """Generate simple details file"""
        rows, cols = grid_size

        with open(details_path, 'w') as f:
            f.write(f"Cases & Covers Planogram Details\n")
            f.write(f"Store: {store_name}\n")
            f.write(f"Wall: {wall_number} of {total_walls}\n")
            f.write(f"Grid Size: {rows}x{cols} = {rows*cols} products\n")
            f.write(f"Total Products Available: {len(products)}\n")
            f.write(f"Generated with: Image-Based Generator\n")
            f.write(f"Brand Images: Apple, Gripp, Tekne/Pulse\n")


if __name__ == "__main__":
    # Quick test
    generator = ImageBasedCasesGenerator(str(project_root))
    
    # Test with a sample store
    store_name = "imagine- koramangala bengaluru"
    output_path = str(project_root / "output" / f"{store_name}_wall1_cases_image_test.png")
    details_path = str(project_root / "output" / f"{store_name}_wall1_cases_image_details.txt")
    
    success = generator.generate_planogram(
        products=[],  # Will load real data internally
        capacity=48,
        output_path=output_path,
        details_path=details_path,
        wall_number=1,
        store_name=store_name,
        total_walls=3,
        total_store_walls=11
    )
    
    if success:
        print(f"✅ Test planogram created: {output_path}")
    else:
        print("❌ Test failed")
