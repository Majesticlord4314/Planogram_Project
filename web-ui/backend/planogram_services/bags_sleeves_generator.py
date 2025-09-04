"""
Enhanced Bags & Sleeves Planogram Generator
Improved system for generating Mac bags and sleeves planograms with better brand grouping,
size-based arrangement, and visual enhancements.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

# Configure matplotlib for server environments
import matplotlib
matplotlib.use('Agg')

# Resolve repository root regardless of working directory
REPO_ROOT = Path(__file__).resolve().parents[3]

@dataclass
class BagSleeveProduct:
    """Bag/Sleeve product with enhanced attributes"""
    product_name: str
    series: str
    category: str  # 'bag' or 'sleeve'
    subcategory: str  # Color/style
    brand: str
    width: float
    height: float
    depth: float
    frequency: int
    shelf: int = 0
    position: int = 0
    
    @property
    def volume(self) -> float:
        """Calculate product volume"""
        return self.width * self.height * self.depth
    
    @property
    def is_premium_brand(self) -> bool:
        """Check if product is from premium brand"""
        premium_brands = {'Gripp', 'Native Union', 'tomtoc'}
        return self.brand in premium_brands
    
    @property
    def size_category(self) -> str:
        """Determine size category based on dimensions"""
        if self.width <= 30:
            return "13-inch"
        elif self.width <= 35:
            return "14-inch"
        elif self.width <= 40:
            return "15-inch"
        else:
            return "16-inch"

class BagsSleevesGenerator:
    """Enhanced bags and sleeves planogram generator"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.approved_brands = {'Gripp', 'Pulse', 'Tekne', 'Native Union', 'tomtoc', 'Tucano', 'Rivacase'}

        # Brand priority for placement
        self.brand_priority = {
            'Gripp': 1,
            'Native Union': 2,
            'tomtoc': 3,
            'Tucano': 4,
            'Pulse': 5,
            'Tekne': 6,
            'Rivacase': 7
        }

        # Realistic wall layout (can be tuned per store):
        # - Sleeves use top 3 rows, 5 columns per row (max 15 sleeves)
        # - Bags use bottom 1 row, 3 columns (max 3 bags)
        self.layout = {
            # Sleeves horizontal: 4 rows x 3 columns (max 12)
            'sleeves': {
                'rows': 4,
                'cols_per_row': 3,
                'row_spacing': 40,
                'col_spacing': 20,
                'item_width': 60,
                'item_height': 30
            },
            # Bottom row for bags, vertical: 1 row x 4 columns (max 4)
            'bags': {
                'rows': 1,
                'cols_per_row': 4,
                'row_spacing': 70,
                'col_spacing': 20,
                'item_width': 50,
                'item_height': 70
            }
        }

    def load_bags_sleeves_data(self) -> List[BagSleeveProduct]:
        """Load bags and sleeves data from processed CSV"""
        data_file = REPO_ROOT / "data/processed/planogram_sleeves_bags.csv"
        
        if not data_file.exists():
            raise FileNotFoundError(f"Bags & sleeves data file not found: {data_file}")
        
        df = pd.read_csv(data_file)
        df.columns = df.columns.str.strip()
        
        products = []
        for _, row in df.iterrows():
            product = BagSleeveProduct(
                product_name=row['product_name'],
                series=row['series'],
                category=row['category'],
                subcategory=row['subcategory'],
                brand=row['brand'],
                width=float(row['width']),
                height=float(row['height']),
                depth=float(row['depth']),
                frequency=int(row['frequency']),
                shelf=int(row['shelf']),
                position=int(row['position'])
            )
            products.append(product)
        
        self.logger.info(f"Loaded {len(products)} bags & sleeves products")
        return products

    def filter_approved_brands(self, products: List[BagSleeveProduct]) -> List[BagSleeveProduct]:
        """Filter to approved brands only"""
        filtered = [p for p in products if p.brand in self.approved_brands]
        self.logger.info(f"Filtered to {len(filtered)} products with approved brands")
        return filtered

    def generate_enhanced_bags_sleeves_planogram(self, store_name: str) -> str:
        """Generate enhanced bags & sleeves planogram"""
        self.logger.info(f"Generating enhanced bags & sleeves planogram for {store_name}")
        
        try:
            # Load data
            products = self.load_bags_sleeves_data()
            
            # Filter to approved brands
            products = self.filter_approved_brands(products)
            
            # Separate bags and sleeves
            sleeves = [p for p in products if p.category == 'sleeve']
            bags = [p for p in products if p.category == 'bag']
            
            # Sort by brand priority and frequency
            sleeves = self._sort_by_priority(sleeves)
            bags = self._sort_by_priority(bags)
            
            # Generate visual
            output_path = self._create_bags_sleeves_visual(sleeves, bags, store_name)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating bags & sleeves planogram: {e}")
            raise

    def _sort_by_priority(self, products: List[BagSleeveProduct]) -> List[BagSleeveProduct]:
        """Sort products by brand priority and sales frequency"""
        def priority_key(product):
            brand_score = self.brand_priority.get(product.brand, 10)
            return (brand_score, -product.frequency)  # Lower brand score = higher priority
        
        return sorted(products, key=priority_key)

    def _create_bags_sleeves_visual(self, sleeves: List[BagSleeveProduct],
                                  bags: List[BagSleeveProduct], store_name: str) -> str:
        """Create enhanced visual for bags & sleeves"""
        # Create figure
        fig, ax = plt.subplots(figsize=(20, 16))
        ax.set_facecolor('#F8F9FA')
        ax.set_xlim(0, 400)
        ax.set_ylim(0, 320)
        ax.axis('off')

        # Title
        title_text = f"Mac Bags & Sleeves\n{store_name.replace('_', ' ').title()}"
        ax.text(200, 300, title_text, fontsize=20, fontweight='bold',
               ha='center', va='center', color='#1D1D1F')

        # Draw sleeves section (top area) and capture displayed items
        sleeves_y_start = 270
        displayed_sleeves = self._draw_enhanced_sleeves_section(ax, sleeves, sleeves_y_start)

        # Draw bags section (bottom row) and capture displayed items, add more vertical gap
        bags_y_start = 60
        displayed_bags = self._draw_enhanced_bags_section(ax, bags, bags_y_start)

        # Add section labels with styling placed above item rectangles to avoid overlap
        ax.text(30, 305, "SLEEVES", fontsize=16, fontweight='bold',
               color='#1D1D1F', bbox=dict(boxstyle="round,pad=5", facecolor='#E3F2FD', alpha=0.7))
        ax.text(30, bags_y_start + self.layout['bags']['item_height'] + 15, "BAGS", fontsize=16, fontweight='bold',
               color='#1D1D1F', bbox=dict(boxstyle="round,pad=5", facecolor='#FFF3E0', alpha=0.7))

        # Add enhanced summary with brand breakdown
        self._add_enhanced_summary(ax, displayed_sleeves, displayed_bags)

        # Add legend
        self._add_enhanced_legend(ax)

        # Save planogram image
        filename = f"enhanced_bags_sleeves_{store_name.lower().replace(' ', '_')}.png"
        output_path = REPO_ROOT / "output" / filename

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()

        # Create accompanying display list (descending importance)
        def importance_key(p: BagSleeveProduct):
            # Lower brand score = higher priority; higher frequency = higher priority
            brand_score = self.brand_priority.get(p.brand, 10)
            return (brand_score, -p.frequency)
        displayed_all = displayed_sleeves + displayed_bags
        ordered = sorted(displayed_all, key=importance_key)
        list_filename = f"enhanced_bags_sleeves_{store_name.lower().replace(' ', '_')}_list.txt"
        list_path = REPO_ROOT / "output" / list_filename
        with open(list_path, 'w') as f:
            f.write(f"Bags & Sleeves Display List for {store_name}\n")
            f.write("(Descending importance: brand priority, then sales frequency)\n\n")
            for idx, p in enumerate(ordered, 1):
                f.write(f"{idx}. {p.category.upper()} | {p.brand} | {p.product_name} | {p.series} | {p.size_category} | freq={p.frequency}\n")
        self.logger.info(f"Generated display list: {list_path}")

        return str(output_path)

    def _draw_enhanced_sleeves_section(self, ax, sleeves: List[BagSleeveProduct], y_start: float) -> List[BagSleeveProduct]:
        """Draw sleeves with enhanced brand grouping and size arrangement (horizontal). Returns displayed items."""
        cfg = self.layout['sleeves']
        sleeve_width = cfg['item_width']
        sleeve_height = cfg['item_height']
        cols_per_row = cfg['cols_per_row']
        row_spacing = cfg['row_spacing']
        col_spacing = cfg['col_spacing']
        max_rows = cfg['rows']
        max_items = max_rows * cols_per_row

        # Group sleeves by size category for better arrangement
        size_groups = {}
        for sleeve in sleeves:
            size_cat = sleeve.size_category
            if size_cat not in size_groups:
                size_groups[size_cat] = []
            size_groups[size_cat].append(sleeve)

        # Calculate starting position for centering
        total_width = cols_per_row * sleeve_width + (cols_per_row - 1) * col_spacing
        start_x = (400 - total_width) / 2

        displayed: List[BagSleeveProduct] = []
        drawn = 0
        current_row = 0
        current_col = 0

        # Draw sleeves grouped by size, then by brand, respecting capacity
        for size_cat in sorted(size_groups.keys()):
            if drawn >= max_items:
                break
            for sleeve in size_groups[size_cat]:
                if drawn >= max_items or current_row >= max_rows:
                    break
                x_pos = start_x + current_col * (sleeve_width + col_spacing)
                y_pos = y_start - current_row * row_spacing
                self._draw_enhanced_sleeve(ax, x_pos, y_pos, sleeve_width, sleeve_height, sleeve)
                displayed.append(sleeve)
                drawn += 1
                current_col += 1
                if current_col >= cols_per_row:
                    current_col = 0
                    current_row += 1
        return displayed

    def _draw_enhanced_bags_section(self, ax, bags: List[BagSleeveProduct], y_start: float) -> List[BagSleeveProduct]:
        """Draw bags with enhanced styling and brand grouping (vertical). Returns displayed items."""
        cfg = self.layout['bags']
        bag_width = cfg['item_width']
        bag_height = cfg['item_height']
        cols_per_row = cfg['cols_per_row']
        row_spacing = cfg['row_spacing']
        col_spacing = cfg['col_spacing']
        max_rows = cfg['rows']
        max_items = max_rows * cols_per_row

        # Calculate starting position for centering
        total_width = cols_per_row * bag_width + (cols_per_row - 1) * col_spacing
        start_x = (400 - total_width) / 2

        displayed: List[BagSleeveProduct] = []
        for i, bag in enumerate(bags[:max_items]):
            row = i // cols_per_row
            if row >= max_rows:
                break
            col = i % cols_per_row
            x_pos = start_x + col * (bag_width + col_spacing)
            y_pos = y_start - row * row_spacing
            self._draw_enhanced_bag(ax, x_pos, y_pos, bag_width, bag_height, bag)
            displayed.append(bag)
        return displayed

    def _draw_enhanced_sleeve(self, ax, x: float, y: float, width: float, height: float,
                            sleeve: BagSleeveProduct):
        """Draw individual sleeve (horizontal) with product name and size"""
        color = self._get_brand_color(sleeve.brand)
        sleeve_rect = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=3",
            facecolor=color,
            edgecolor='#86868B',
            linewidth=1.5,
            alpha=0.9
        )
        ax.add_patch(sleeve_rect)

        text_color = 'white' if self._is_dark_color(color) else 'black'

        # Centered product name (wrap to fit width)
        display_name = self._format_product_name(sleeve.product_name, width)
        ax.text(x + width/2, y + height/2 + 2, display_name,
               fontsize=8, ha='center', va='center', color=text_color,
               weight='medium', wrap=True)

        # Small size label at top-left, full size name (e.g., 13-inch)
        size_text = sleeve.size_category
        ax.text(x + 3, y + height - 5, size_text, fontsize=7, ha='left', va='top',
               color=text_color, weight='bold')

    def _draw_enhanced_bag(self, ax, x: float, y: float, width: float, height: float,
                         bag: BagSleeveProduct):
        """Draw individual bag (vertical) with product name and size"""
        color = self._get_brand_color(bag.brand)
        bag_rect = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=4",
            facecolor=color,
            edgecolor='#86868B',
            linewidth=2,
            alpha=0.9
        )
        ax.add_patch(bag_rect)

        text_color = 'white' if self._is_dark_color(color) else 'black'

        # Centered product name (wrap to fit width)
        display_name = self._format_product_name(bag.product_name, width)
        ax.text(x + width/2, y + height/2 + 3, display_name,
               fontsize=9, ha='center', va='center', color=text_color,
               weight='medium', wrap=True)

        # Small size label at bottom-right, full size name (e.g., 16-inch)
        size_text = bag.size_category
        ax.text(x + width - 3, y + 3, size_text, fontsize=7, ha='right', va='bottom',
               color=text_color, weight='bold')

    def _get_brand_color(self, brand: str) -> str:
        """Get brand-specific color"""
        brand_colors = {
            'Gripp': '#4A90E2',
            'Native Union': '#7ED321',
            'tomtoc': '#F5A623',
            'Tucano': '#9013FE',
            'Pulse': '#50E3C2',
            'Tekne': '#FF6B6B',
            'Rivacase': '#4ECDC4'
        }
        return brand_colors.get(brand, '#E5E5EA')

    def _is_dark_color(self, color_hex: str) -> bool:
        """Determine if color is dark"""
        color_hex = color_hex.lstrip('#')
        try:
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness < 128
        except:
            return False

    def _format_product_name(self, name: str, max_width: float) -> str:
        """Format product name for display"""
        max_chars = int(max_width / 6)
        
        # Extract brand and key descriptors
        words = name.split()
        brand = words[0] if words else ""
        
        # Find key descriptors
        key_words = []
        for word in words[1:]:
            if any(desc in word.lower() for desc in ['sleeve', 'bag', 'case', 'slim']):
                key_words.append(word)
                break
        
        # Add size/color
        for word in words:
            if word in ['13', '14', '15', '16', 'Black', 'Blue', 'Grey']:
                key_words.append(word)
                break
        
        result = brand
        for word in key_words:
            if len(result + " " + word) <= max_chars:
                result += " " + word
        
        return result if len(result) > 3 else name[:max_chars]

    def _add_enhanced_summary(self, ax, sleeves: List[BagSleeveProduct], bags: List[BagSleeveProduct]):
        """Add enhanced summary with brand breakdown"""
        summary_y = 50
        
        # Basic stats
        total_sleeves = len(sleeves)
        total_bags = len(bags)
        total_sales = sum(p.frequency for p in sleeves + bags)
        
        ax.text(50, summary_y, f"Sleeves: {total_sleeves} | Bags: {total_bags}", 
               fontsize=12, color='#1D1D1F', weight='medium')
        ax.text(250, summary_y, f"Total Sales: {total_sales:,}", 
               fontsize=12, color='#1D1D1F', weight='medium')
        
        # Brand breakdown
        brand_counts = {}
        for product in sleeves + bags:
            brand_counts[product.brand] = brand_counts.get(product.brand, 0) + 1
        
        brand_text = " | ".join([f"{brand}: {count}" for brand, count in 
                                sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:3]])
        ax.text(50, summary_y - 15, f"Top Brands: {brand_text}", 
               fontsize=10, color='#86868B')

    def _add_enhanced_legend(self, ax):
        """Add enhanced legend"""
        legend_y = 25
        
        # Premium brand indicator
        premium_circle = patches.Circle((50, legend_y), 3, color='gold', alpha=0.9)
        ax.add_patch(premium_circle)
        ax.text(60, legend_y, "Premium Brand", fontsize=10, va='center', color='#1D1D1F')
        
        # High sales indicator
        sales_star = patches.Circle((150, legend_y), 3, color='#FF3B30', alpha=0.9)
        ax.add_patch(sales_star)
        ax.text(160, legend_y, "High Sales (>50)", fontsize=10, va='center', color='#1D1D1F')
        
        # Size categories
        ax.text(250, legend_y, "Sizes: 13\" | 14\" | 15\" | 16\"", 
               fontsize=10, va='center', color='#86868B')
