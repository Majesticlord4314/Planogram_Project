"""
Mac Accessories Planogram Generator
Comprehensive system for generating Mac accessories planograms with dimensional awareness,
cohort-based allocation, and multi-wall strategies.
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

@dataclass
class MacProduct:
    """Mac product with dimensional and sales data"""
    product_name: str
    series: str
    category: str
    subcategory: str
    brand: str
    width: float
    height: float
    depth: float
    frequency: int
    attach_rate: float = 0.0
    recommended_facings: int = 1
    
    @property
    def volume(self) -> float:
        """Calculate product volume for shelf allocation"""
        return self.width * self.height * self.depth
    
    @property
    def is_thin_product(self) -> bool:
        """Determine if product is thin (suitable for top shelves)"""
        return self.height <= 1.0  # Privacy filters, keyboard skins
    
    @property
    def is_bulky_product(self) -> bool:
        """Determine if product is bulky (needs lower shelves)"""
        return self.volume > 500  # Large hubs, chargers, bags

class MacAccessoriesGenerator:
    """Enhanced Mac accessories planogram generator"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.approved_tpa_brands = {'Gripp', 'Pulse', 'Tekne'}
        
        # Dimensional constraints for shelf allocation
        self.shelf_constraints = {
            'top_shelf': {'max_height': 1.0, 'max_depth': 25.0},      # Thin items
            'mid_shelf': {'max_height': 5.0, 'max_depth': 20.0},      # Medium items  
            'low_shelf': {'max_height': 15.0, 'max_depth': 35.0},     # Bulky items
            'bottom_shelf': {'max_height': 50.0, 'max_depth': 50.0}   # Bags, large items
        }
        
        # Category priorities for placement
        self.category_priorities = {
            'hardshell case': 1,      # High priority - protection
            'privacy filter': 2,      # High priority - privacy
            'hub': 3,                 # Medium priority - connectivity
            'charger': 4,             # Medium priority - power
            'cable': 5,               # Medium priority - connectivity
            'cleaning': 6,            # Lower priority - maintenance
            'stand': 7,               # Lower priority - ergonomics
            'peripheral': 8,          # Lower priority - extras
            'keyboard skin': 9,       # Lower priority - protection
            'accessory': 10           # Lowest priority - general
        }

    def load_mac_data(self) -> Tuple[List[MacProduct], pd.DataFrame]:
        """Load Mac accessories and cohort data"""
        # Load accessories data
        accessories_file = Path("data/raw/accessories/mac-accessories-transformed.csv")
        cohorts_file = Path("data/raw/cohorts/mac_planogram_cohorts.csv")
        
        if not accessories_file.exists():
            raise FileNotFoundError(f"Mac accessories file not found: {accessories_file}")
        if not cohorts_file.exists():
            raise FileNotFoundError(f"Mac cohorts file not found: {cohorts_file}")
        
        # Load accessories
        accessories_df = pd.read_csv(accessories_file)
        accessories_df.columns = accessories_df.columns.str.strip()
        accessories_df = accessories_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        # Load cohorts for attach rates
        cohorts_df = pd.read_csv(cohorts_file)
        cohorts_df.columns = cohorts_df.columns.str.strip()
        
        # Create product lookup for attach rates
        attach_rates = {}
        for _, row in cohorts_df.iterrows():
            product_name = row['accessory_product']
            attach_rate = float(row['attach_rate'])
            attach_rates[product_name] = attach_rate
        
        # Convert to MacProduct objects
        products = []
        for _, row in accessories_df.iterrows():
            # Get attach rate from cohorts data
            attach_rate = attach_rates.get(row['product_name'], 0.0)
            
            product = MacProduct(
                product_name=row['product_name'],
                series=row['series'],
                category=row['category'],
                subcategory=row['subcategory'],
                brand=row['brand'],
                width=float(row['width']),
                height=float(row['height']),
                depth=float(row['depth']),
                frequency=int(row['frequency']),
                attach_rate=attach_rate,
                recommended_facings=1
            )
            products.append(product)
        
        self.logger.info(f"Loaded {len(products)} Mac products with cohort data")
        return products, cohorts_df

    def filter_tpa_brands(self, products: List[MacProduct]) -> List[MacProduct]:
        """Filter products to approved TPA brands only"""
        # For Mac, we include Apple products (if any) plus approved TPA brands
        filtered = []
        for product in products:
            if (product.brand == 'Apple' or 
                product.brand in self.approved_tpa_brands):
                filtered.append(product)
        
        self.logger.info(f"Filtered to {len(filtered)} products with approved brands")
        return filtered

    def categorize_by_dimensions(self, products: List[MacProduct]) -> Dict[str, List[MacProduct]]:
        """Categorize products by dimensional constraints for shelf allocation"""
        categories = {
            'thin_items': [],      # Privacy filters, keyboard skins
            'medium_items': [],    # Hubs, small chargers, cables
            'bulky_items': [],     # Large chargers, stands
            'large_items': []      # Bags, large accessories
        }
        
        for product in products:
            if product.height <= 1.0:  # Very thin items
                categories['thin_items'].append(product)
            elif product.volume <= 200:  # Small to medium items
                categories['medium_items'].append(product)
            elif product.volume <= 1000:  # Bulky but manageable
                categories['bulky_items'].append(product)
            else:  # Large items
                categories['large_items'].append(product)
        
        return categories

    def generate_store_planograms(self, store_name: str, num_walls: int) -> Dict[str, str]:
        """Generate Mac planograms for a store based on wall count"""
        self.logger.info(f"Generating Mac planograms for {store_name} with {num_walls} walls")
        
        try:
            # Load data
            products, cohorts_df = self.load_mac_data()
            
            # Filter to approved brands
            products = self.filter_tpa_brands(products)
            
            # Sort by priority: attach rate * frequency
            products.sort(key=lambda p: p.attach_rate * p.frequency, reverse=True)
            
            # Generate planograms based on wall count
            if num_walls == 1:
                return self._generate_single_wall_mac(products, store_name)
            elif num_walls == 2:
                return self._generate_two_wall_mac(products, store_name)
            elif num_walls == 3:
                return self._generate_three_wall_mac(products, store_name)
            else:
                return self._generate_multi_wall_mac(products, store_name, num_walls)
                
        except Exception as e:
            self.logger.error(f"Error generating Mac planograms: {e}")
            raise

    def _generate_single_wall_mac(self, products: List[MacProduct], store_name: str) -> Dict[str, str]:
        """Single wall: Mixed categories with dimensional optimization"""
        # Categorize by dimensions
        dim_categories = self.categorize_by_dimensions(products)
        
        # Create mixed selection prioritizing high-attach rate items
        selected_products = []
        
        # Top shelf: Thin items (privacy filters, keyboard skins)
        selected_products.extend(dim_categories['thin_items'][:6])
        
        # Middle shelves: Medium items (hubs, cables, chargers)
        selected_products.extend(dim_categories['medium_items'][:12])
        
        # Bottom shelf: Bulky items
        selected_products.extend(dim_categories['bulky_items'][:6])
        
        # Generate visual
        output_path = self._create_mac_planogram_visual(
            selected_products, store_name, 1, "Mixed Mac Accessories"
        )
        
        return {"wall_1": output_path}

    def _generate_two_wall_mac(self, products: List[MacProduct], store_name: str) -> Dict[str, str]:
        """Two walls: Wall 1 (Protection & Privacy), Wall 2 (Connectivity & Power)"""
        results = {}

        # Wall 1: Protection & Privacy
        protection_categories = ['hardshell case', 'privacy filter', 'keyboard skin', 'cleaning']
        wall1_products = [p for p in products if p.category in protection_categories][:20]

        results["wall_1"] = self._create_mac_planogram_visual(
            wall1_products, store_name, 1, "Mac Protection & Privacy"
        )

        # Wall 2: Connectivity & Power
        connectivity_categories = ['hub', 'charger', 'cable', 'stand', 'accessory']
        wall2_products = [p for p in products if p.category in connectivity_categories][:20]

        results["wall_2"] = self._create_mac_planogram_visual(
            wall2_products, store_name, 2, "Mac Connectivity & Power"
        )

        return results

    def _generate_three_wall_mac(self, products: List[MacProduct], store_name: str) -> Dict[str, str]:
        """Three walls: Protection, Connectivity, Bags & Peripherals"""
        results = {}

        # Wall 1: Protection & Privacy
        protection_products = [p for p in products if p.category in ['hardshell case', 'privacy filter', 'keyboard skin', 'cleaning']][:20]
        results["wall_1"] = self._create_mac_planogram_visual(
            protection_products, store_name, 1, "Mac Protection & Privacy"
        )

        # Wall 2: Connectivity & Power
        connectivity_products = [p for p in products if p.category in ['hub', 'charger', 'cable']][:20]
        results["wall_2"] = self._create_mac_planogram_visual(
            connectivity_products, store_name, 2, "Mac Connectivity & Power"
        )

        # Wall 3: Bags, Sleeves & Peripherals
        bags_products = [p for p in products if p.category in ['stand', 'peripheral', 'accessory']][:20]
        results["wall_3"] = self._create_mac_planogram_visual(
            bags_products, store_name, 3, "Mac Bags & Peripherals"
        )

        return results

    def _generate_multi_wall_mac(self, products: List[MacProduct], store_name: str, num_walls: int) -> Dict[str, str]:
        """Multi-wall strategy: Dedicated walls per category"""
        results = {}

        # Define wall allocation strategy
        wall_strategies = [
            ("Mac Protection & Privacy", ['hardshell case', 'privacy filter', 'keyboard skin', 'cleaning']),
            ("Mac Connectivity", ['hub', 'cable']),
            ("Mac Power & Charging", ['charger', 'accessory']),
            ("Mac Peripherals & Stands", ['stand', 'peripheral']),
        ]

        for i, (wall_title, categories) in enumerate(wall_strategies[:num_walls]):
            wall_products = [p for p in products if p.category in categories][:20]
            results[f"wall_{i+1}"] = self._create_mac_planogram_visual(
                wall_products, store_name, i+1, wall_title
            )

        return results

    def _create_mac_planogram_visual(self, products: List[MacProduct], store_name: str,
                                   wall_number: int, wall_title: str) -> str:
        """Create visual Mac planogram with dimensional awareness"""
        # Create 5-row grid similar to iPad system
        grid_rows = 5
        grid_cols = 4

        # Sort products by dimensional constraints and priority
        sorted_products = self._sort_products_by_shelf_suitability(products)

        # Create grid allocation
        grid = self._allocate_products_to_grid(sorted_products, grid_rows, grid_cols)

        # Generate visual
        output_path = self._generate_mac_planogram_visual(
            grid, store_name, wall_number, wall_title
        )

        return output_path

    def _sort_products_by_shelf_suitability(self, products: List[MacProduct]) -> List[MacProduct]:
        """Sort products by shelf suitability and priority"""
        def shelf_priority(product):
            # Combine category priority with dimensional suitability
            cat_priority = self.category_priorities.get(product.category, 10)
            sales_score = product.attach_rate * product.frequency

            # Thin items get top shelf priority
            if product.is_thin_product:
                shelf_score = 1
            elif product.is_bulky_product:
                shelf_score = 4
            else:
                shelf_score = 2

            # Lower score = higher priority
            return (shelf_score, cat_priority, -sales_score)

        return sorted(products, key=shelf_priority)

    def _allocate_products_to_grid(self, products: List[MacProduct], rows: int, cols: int) -> List[List[Optional[MacProduct]]]:
        """Allocate products to grid with dimensional constraints"""
        grid = [[None for _ in range(cols)] for _ in range(rows)]

        # Separate products by shelf suitability
        thin_products = [p for p in products if p.is_thin_product]
        medium_products = [p for p in products if not p.is_thin_product and not p.is_bulky_product]
        bulky_products = [p for p in products if p.is_bulky_product]

        product_index = 0

        # Row 1: Thin products (privacy filters, keyboard skins)
        for col in range(cols):
            if product_index < len(thin_products):
                grid[0][col] = thin_products[product_index]
                product_index += 1

        # Rows 2-3: Medium products (hubs, cables, small chargers)
        product_index = 0
        for row in range(1, 3):
            for col in range(cols):
                if product_index < len(medium_products):
                    grid[row][col] = medium_products[product_index]
                    product_index += 1

        # Rows 4-5: Bulky products (large chargers, stands)
        product_index = 0
        for row in range(3, 5):
            for col in range(cols):
                if product_index < len(bulky_products):
                    grid[row][col] = bulky_products[product_index]
                    product_index += 1

        return grid

    def _generate_mac_planogram_visual(self, grid: List[List[Optional[MacProduct]]],
                                     store_name: str, wall_number: int, wall_title: str) -> str:
        """Generate visual planogram with proper Mac styling"""
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_facecolor('#F8F9FA')
        ax.set_xlim(0, 400)
        ax.set_ylim(0, 300)
        ax.axis('off')

        # Title
        title_text = f"{wall_title}\n{store_name.replace('_', ' ').title()}"
        ax.text(200, 280, title_text, fontsize=18, fontweight='bold',
               ha='center', va='center', color='#1D1D1F')

        # Grid parameters
        rows = len(grid)
        cols = len(grid[0]) if grid else 0

        # Calculate cell dimensions
        grid_width = 320
        grid_height = 200
        cell_width = grid_width / cols
        cell_height = grid_height / rows

        # Starting position (centered)
        start_x = (400 - grid_width) / 2
        start_y = 220

        # Draw grid and products
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * cell_width
                y = start_y - row * cell_height

                product = grid[row][col]

                if product:
                    self._draw_mac_product_rectangle(ax, x, y, cell_width, cell_height, product)
                else:
                    # Draw empty cell
                    empty_rect = FancyBboxPatch(
                        (x + 5, y - cell_height + 5), cell_width - 10, cell_height - 10,
                        boxstyle="round,pad=3",
                        facecolor='#F0F0F0',
                        edgecolor='#D1D1D6',
                        linewidth=1,
                        alpha=0.3
                    )
                    ax.add_patch(empty_rect)

        # Add shelf labels
        shelf_labels = ["Top Shelf (Thin Items)", "Mid Shelf (Cables & Hubs)",
                       "Mid Shelf (Chargers)", "Low Shelf (Stands)", "Bottom Shelf (Large Items)"]

        for i, label in enumerate(shelf_labels[:rows]):
            y_pos = start_y - i * cell_height - cell_height/2
            ax.text(start_x - 10, y_pos, label, fontsize=10, ha='right', va='center',
                   color='#86868B', rotation=90)

        # Add summary statistics
        total_products = sum(1 for row in grid for cell in row if cell is not None)
        total_sales = sum(p.frequency for row in grid for p in row if p is not None)
        avg_attach_rate = np.mean([p.attach_rate for row in grid for p in row if p is not None and p.attach_rate > 0])

        summary_y = 40
        ax.text(50, summary_y, f"Products: {total_products}", fontsize=12, color='#1D1D1F')
        ax.text(150, summary_y, f"Total Sales: {total_sales:,}", fontsize=12, color='#1D1D1F')
        if not np.isnan(avg_attach_rate):
            ax.text(280, summary_y, f"Avg Attach Rate: {avg_attach_rate:.1%}", fontsize=12, color='#1D1D1F')

        # Add legend
        legend_y = 20
        # High sales indicator
        star = patches.Circle((50, legend_y), 3, color='gold', alpha=0.9)
        ax.add_patch(star)
        ax.text(60, legend_y, "High Sales (>100)", fontsize=10, va='center', color='#1D1D1F')

        # High attach rate indicator
        diamond = patches.RegularPolygon((150, legend_y), 4, radius=4, color='#007AFF', alpha=0.9)
        ax.add_patch(diamond)
        ax.text(160, legend_y, "High Attach Rate (>5%)", fontsize=10, va='center', color='#1D1D1F')

        # Save planogram
        filename = f"mac_wall_{wall_number}_{store_name.lower().replace(' ', '_')}.png"
        output_path = Path("output") / filename

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()

        self.logger.info(f"Generated Mac planogram: {output_path}")
        return str(output_path)

    def _draw_mac_product_rectangle(self, ax, x: float, y: float, width: float, height: float,
                                  product: MacProduct):
        """Draw individual Mac product rectangle with proper styling"""
        # Adjust for padding
        rect_x = x + 3
        rect_y = y - height + 3
        rect_width = width - 6
        rect_height = height - 6

        # Get product color based on category and subcategory
        color = self._get_mac_product_color(product)

        # Draw main rectangle
        product_rect = FancyBboxPatch(
            (rect_x, rect_y), rect_width, rect_height,
            boxstyle="round,pad=2",
            facecolor=color,
            edgecolor='#86868B',
            linewidth=1.5,
            alpha=0.9
        )
        ax.add_patch(product_rect)

        # Format product name for display
        display_name = self._format_mac_product_name(product.product_name, rect_width)

        # Determine text color
        text_color = 'white' if self._is_dark_color(color) else 'black'

        # Add product text
        ax.text(rect_x + rect_width/2, rect_y + rect_height/2, display_name,
               fontsize=8, ha='center', va='center', color=text_color,
               weight='medium', wrap=True)

        # Add indicators for high-performing products
        if product.frequency > 100:  # High sales
            star = patches.Circle((rect_x + rect_width - 8, rect_y + rect_height - 8),
                                3, color='gold', alpha=0.9)
            ax.add_patch(star)

        if product.attach_rate > 0.05:  # High attach rate (>5%)
            diamond = patches.RegularPolygon((rect_x + 8, rect_y + rect_height - 8),
                                           4, radius=3, color='#007AFF', alpha=0.9)
            ax.add_patch(diamond)

    def _get_mac_product_color(self, product: MacProduct) -> str:
        """Get color for Mac product based on category and subcategory"""
        # Brand-based colors for TPA brands
        brand_colors = {
            'Gripp': '#4A90E2',      # Blue
            'Pulse': '#7ED321',      # Green
            'Tekne': '#F5A623',      # Orange
            'Apple': '#1D1D1F',      # Dark gray
        }

        if product.brand in brand_colors:
            return brand_colors[product.brand]

        # Category-based colors
        category_colors = {
            'hardshell case': '#E3F2FD',
            'privacy filter': '#F3E5F5',
            'hub': '#FFF8E1',
            'cable': '#FFEBEE',
            'charger': '#F1F8E9',
            'cleaning': '#E8F5E8',
            'stand': '#EDE7F6',
            'peripheral': '#F9FBE7',
            'keyboard skin': '#FCE4EC',
            'accessory': '#FFF9C4'
        }

        return category_colors.get(product.category, '#E5E5EA')

    def _is_dark_color(self, color_hex: str) -> bool:
        """Determine if color is dark for text contrast"""
        color_hex = color_hex.lstrip('#')
        try:
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness < 128
        except:
            return False

    def _format_mac_product_name(self, name: str, max_width: float) -> str:
        """Format Mac product name for display"""
        # Estimate characters that fit (approximately 6 pixels per character)
        max_chars = int(max_width / 6)

        # Extract key information
        words = name.split()

        # Get brand (first word usually)
        brand = words[0] if words else ""

        # Find key descriptors
        key_words = []
        for word in words[1:]:
            if any(desc in word.lower() for desc in
                  ['case', 'hub', 'cable', 'charger', 'filter', 'stand', 'skin', 'clean']):
                key_words.append(word)
                break

        # Add size if present
        for word in words:
            if any(size in word for size in ['13', '14', '15', '16']):
                key_words.append(word)
                break

        # Build result
        result = brand
        for word in key_words:
            if len(result + " " + word) <= max_chars:
                result += " " + word
            else:
                break

        return result if len(result) > 3 else name[:max_chars]
