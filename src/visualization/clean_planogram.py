import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from typing import List, Dict, Optional, Tuple
from src.models.product import Product
from src.optimization.base_optimizer import OptimizationResult

def create_clean_planogram(result: OptimizationResult,
                          product_lookup: Dict[str, Product],
                          title: str = "Clean Planogram",
                          save_path: Optional[str] = None,
                          figsize: Tuple[int, int] = (16, 12)) -> plt.Figure:
    """Create a clean, modern planogram visualization"""
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor('#FFFFFF')
    
    # Get all placed products
    all_products = []
    for shelf in result.store.shelves:
        for position in shelf.positions:
            if position.product_id in product_lookup:
                product = product_lookup[position.product_id]
                all_products.append((product, position.facings))
    
    if not all_products:
        ax.text(0.5, 0.5, 'No products placed', ha='center', va='center', 
               transform=ax.transAxes, fontsize=16, color='red')
        ax.axis('off')
        return fig
    
    # Determine layout based on store type
    store_type = getattr(result.store, 'store_type', 'standard')
    
    if store_type == 'flagship':
        rows, cols = 8, 5
    elif store_type == 'express':
        rows, cols = 5, 6
    elif store_type == 'standard':
        rows, cols = 6, 6
    else:
        rows, cols = 4, 6
    
    # Separate Apple and TPA products
    apple_products = [(p, f) for p, f in all_products if getattr(p, 'brand', '').lower() == 'apple']
    tpa_products = [(p, f) for p, f in all_products if getattr(p, 'brand', '').lower() != 'apple']
    
    # Group and diversify products
    def group_and_diversify_products(products, max_per_product=2):
        """Group products by subcategory and create variety"""
        # Group by subcategory AND color/variant for Apple products
        by_variant = {}
        for product, facings in products:
            name = getattr(product, 'product_name', 'Unknown')
            brand = getattr(product, 'brand', '').lower()
            subcategory = getattr(product, 'subcategory', 'other')
            
            # Create variant key for better variety
            if brand == 'apple':
                if 'Clear' in name:
                    variant_key = f"{subcategory}_clear"
                elif 'Silicone' in name:
                    if 'Black' in name:
                        variant_key = f"{subcategory}_black_silicone"
                    elif 'Denim' in name:
                        variant_key = f"{subcategory}_denim_silicone"
                    elif 'Fuchsia' in name:
                        variant_key = f"{subcategory}_fuchsia_silicone"
                    elif 'Lake Green' in name:
                        variant_key = f"{subcategory}_green_silicone"
                    elif 'Plum' in name:
                        variant_key = f"{subcategory}_plum_silicone"
                    elif 'Star Fruit' in name:
                        variant_key = f"{subcategory}_starfruit_silicone"
                    elif 'Stone Gray' in name:
                        variant_key = f"{subcategory}_gray_silicone"
                    elif 'Ultramarine' in name:
                        variant_key = f"{subcategory}_blue_silicone"
                    else:
                        variant_key = f"{subcategory}_silicone"
                else:
                    variant_key = subcategory
            else:
                # For TPA, group by brand and type
                if 'CRYSTAL' in name.upper():
                    variant_key = f"{brand}_crystal"
                elif 'CLEAR' in name.upper():
                    variant_key = f"{brand}_clear"
                elif 'MATT' in name.upper() or 'MATTE' in name.upper():
                    variant_key = f"{brand}_matte"
                elif 'ARMOUR' in name.upper() or 'ARMOR' in name.upper():
                    variant_key = f"{brand}_armor"
                elif 'PRIVACY' in name.upper():
                    variant_key = f"{brand}_privacy"
                else:
                    variant_key = f"{brand}_{subcategory}"
            
            if variant_key not in by_variant:
                by_variant[variant_key] = []
            by_variant[variant_key].append((product, facings))
        
        # Sort each variant by sales velocity
        for variant in by_variant:
            by_variant[variant].sort(key=lambda x: getattr(x[0], 'sales_velocity', 0), reverse=True)
        
        # Create diversified list - take best from each variant
        diversified = []
        
        # First pass: one from each variant
        for variant_key, products_in_variant in by_variant.items():
            if products_in_variant:
                diversified.append(products_in_variant[0])
        
        # Second pass: add more if we have room
        for variant_key, products_in_variant in by_variant.items():
            for i in range(1, min(len(products_in_variant), max_per_product)):
                diversified.append(products_in_variant[i])
        
        return diversified
    
    # Diversify both Apple and TPA products
    apple_products = group_and_diversify_products(apple_products, max_per_product=3)
    tpa_products = group_and_diversify_products(tpa_products, max_per_product=2)
    
    # Arrange products based on store type
    display_products = []
    
    def get_variant_key(product):
        """Helper to get variant key for a product"""
        name = getattr(product, 'product_name', 'Unknown')
        brand = getattr(product, 'brand', '').lower()
        
        if brand == 'apple':
            if 'Clear' in name:
                return 'clear'
            elif 'Silicone' in name:
                return 'silicone'
            else:
                return 'other'
        else:
            if 'CRYSTAL' in name.upper():
                return f"{brand}_crystal"
            elif 'CLEAR' in name.upper():
                return f"{brand}_clear"
            elif 'MATT' in name.upper() or 'MATTE' in name.upper():
                return f"{brand}_matte"
            elif 'ARMOUR' in name.upper() or 'ARMOR' in name.upper():
                return f"{brand}_armor"
            else:
                return f"{brand}_other"

    def arrange_products_symmetrically(products, total_slots, cols, column_wise=True):
        """Arrange products so each column is a type, cycling through colors for that type (column-wise symmetry)."""
        if not products:
            return [None] * total_slots
        
        # Group by (brand, type), then by color
        from collections import defaultdict
        type_color_groups = defaultdict(lambda: defaultdict(list))
        for product, facings in products:
            name = getattr(product, 'product_name', 'Unknown')
            brand = getattr(product, 'brand', '').lower()
            subcategory = getattr(product, 'subcategory', '').lower()
            # Extract type and color
            if brand == 'apple':
                if 'clear' in name.lower():
                    type_group = 'clear'
                    color = 'clear'
                elif 'silicone' in name.lower():
                    type_group = 'silicone'
                    # Color after last hyphen
                    if '-' in name:
                        color = name.split('-')[-1].strip().lower().replace(' ', '_')
                    else:
                        color = 'silicone'
                else:
                    type_group = subcategory
                    color = subcategory
            else:
                # TPA: type by keywords, color after hyphen if present
                n = name.upper()
                if 'CRYSTAL' in n:
                    type_group = 'crystal'
                elif 'CLEAR' in n:
                    type_group = 'clear'
                elif 'MATT' in n or 'MATTE' in n:
                    type_group = 'matte'
                elif 'ARMOUR' in n or 'ARMOR' in n:
                    type_group = 'armor'
                elif 'PRIVACY' in n:
                    type_group = 'privacy'
                else:
                    type_group = subcategory
                # Try to extract color after hyphen, else fallback
                if '-' in name:
                    color = name.split('-')[-1].strip().lower().replace(' ', '_')
                else:
                    color = subcategory
            type_color_groups[type_group][color].append((product, facings))
        
        # Sort types for columns
        type_keys = sorted(type_color_groups.keys())
        arranged = [None] * total_slots
        rows = total_slots // cols
        for col, type_key in enumerate(type_keys):
            color_dict = type_color_groups[type_key]
            color_keys = sorted(color_dict.keys())
            clear_colors = [c for c in color_keys if 'clear' in c]
            other_colors = [c for c in color_keys if 'clear' not in c]
            # Block: fill with all clear SKUs first
            clear_cycle = []
            for clr in clear_colors:
                clear_cycle.extend(color_dict[clr])
            # For other colors: pick the SKU with highest sales for each color, and strictly cycle through all colors/SKUs before any repeat
            color_diverse_cycle = []
            color_sku_map = {}
            for c in other_colors:
                if color_dict[c]:
                    # Sort SKUs for this color by sales, descending
                    sorted_skus = sorted(color_dict[c], key=lambda tup: getattr(tup[0], 'sales_velocity', 0), reverse=True)
                    color_sku_map[c] = sorted_skus
            # Strict color cycling: never repeat a color/SKU until all have been shown
            used_skus = set()
            col_items = list(clear_cycle)
            color_list = list(color_sku_map.keys())
            color_idx = 0
        else:
            # TPA: type by keywords, color after hyphen if present
            n = name.upper()
            if 'CRYSTAL' in n:
                type_group = 'crystal'
            elif 'CLEAR' in n:
                type_group = 'clear'
            elif 'MATT' in n or 'MATTE' in n:
                type_group = 'matte'
            elif 'ARMOUR' in n or 'ARMOR' in n:
                type_group = 'armor'
            elif 'PRIVACY' in n:
                type_group = 'privacy'
            else:
                type_group = subcategory
            # Try to extract color after hyphen, else fallback
            if '-' in name:
                color = name.split('-')[-1].strip().lower().replace(' ', '_')
            else:
                color = subcategory
        type_color_groups[type_group][color].append((product, facings))
    
    arranged = arrange_products_symmetrically(all_products, total_slots=rows*cols, cols=cols, column_wise=True)

    # Calculate layout - more compact dimensions
    product_width = 2.2
    product_height = 3.8
    gap_x = 0.15
    gap_y = 0.25
    
    shelf_width = cols * product_width + (cols - 1) * gap_x
    shelf_height = rows * product_height + (rows - 1) * gap_y
    
    start_x = 0.8
    start_y = 1.5
    
    # Draw shelf background
    shelf_bg = Rectangle(
        (start_x - 0.3, start_y - 0.3),
        shelf_width + 0.6,
        shelf_height + 0.6,
        facecolor='#F8F8F8',
        edgecolor='#888888',
        linewidth=2,
        alpha=0.9
    )
    ax.add_patch(shelf_bg)
    
    # Brand colors
    brand_colors = {
        'apple': '#007AFF',
        'pulse': '#FF3B30',
        'gripp': '#AF52DE',
        'tekne': '#34C759',
        'uag': '#FF9500',
        'default': '#8E8E93'
    }
    
    brand_colors_used = set()
    
    # Draw products
    if not arranged or all(x is None for x in arranged):
        ax.text(0.5, 0.5, 'No products arranged', ha='center', va='center', 
                transform=ax.transAxes, fontsize=16, color='red')
        ax.axis('off')
        return fig
    
    for i, product_data in enumerate(arranged):
        row = i // cols
        col = i % cols
        
        x = start_x + col * (product_width + gap_x)
        y = start_y + (rows - 1 - row) * (product_height + gap_y)
        
        if product_data is None:
            # Empty slot - should not happen with our new logic
            continue
        
        product, facings = product_data
        brand = getattr(product, 'brand', 'Unknown').lower()
        
        # Get color
        if brand == 'apple':
            color = brand_colors['apple']
            brand_colors_used.add(('Apple', color))
        else:
            color = brand_colors.get(brand, brand_colors['default'])
            brand_colors_used.add((brand.title(), color))
        
        # Draw phone case with rounded corners to look more realistic
        case_bg = FancyBboxPatch(
            (x, y), product_width, product_height,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor='#333333',
            linewidth=1.5,
            alpha=0.95
        )
        ax.add_patch(case_bg)
        
        # Add phone outline inside the case
        phone_width = product_width * 0.75
        phone_height = product_height * 0.85
        phone_x = x + (product_width - phone_width) / 2
        phone_y = y + (product_height - phone_height) / 2
        
        phone_outline = FancyBboxPatch(
            (phone_x, phone_y), phone_width, phone_height,
            boxstyle="round,pad=0.01",
            facecolor='none',
            edgecolor='white',
            linewidth=1.2,
            alpha=0.8
        )
        ax.add_patch(phone_outline)
        
        # Add camera bump for realism
        if brand == 'apple':
            camera_size = 0.15
            camera_x = phone_x + phone_width - camera_size - 0.05
            camera_y = phone_y + phone_height - camera_size - 0.05
            
            camera_bump = Rectangle(
                (camera_x, camera_y), camera_size, camera_size,
                facecolor='#DDDDDD',
                edgecolor='white',
                linewidth=0.8,
                alpha=0.9
            )
            ax.add_patch(camera_bump)
        
        # Product label - show actual product details
        name = getattr(product, 'product_name', 'Unknown')
        subcategory = getattr(product, 'subcategory', 'case')
        
        if brand == 'apple':
            # Extract iPhone model and case type from name
            if 'Pro Max' in name:
                main_label = 'iPhone 16'
                sub_label = 'Pro Max'
            elif 'Pro' in name and 'Pro Max' not in name:
                main_label = 'iPhone 16'
                sub_label = 'Pro'
            elif 'Plus' in name:
                main_label = 'iPhone 16'
                sub_label = 'Plus'
            else:
                main_label = 'iPhone 16'
                sub_label = 'Base'
            
            # Extract case type/color from name
            if 'Clear' in name:
                color_label = 'Clear'
            elif 'Silicone' in name:
                if 'Black' in name:
                    color_label = 'Black Silicone'
                elif 'Denim' in name:
                    color_label = 'Denim'
                elif 'Fuchsia' in name:
                    color_label = 'Fuchsia'
                elif 'Lake Green' in name:
                    color_label = 'Lake Green'
                elif 'Plum' in name:
                    color_label = 'Plum'
                elif 'Star Fruit' in name:
                    color_label = 'Star Fruit'
                elif 'Stone Gray' in name:
                    color_label = 'Stone Gray'
                elif 'Ultramarine' in name:
                    color_label = 'Ultramarine'
                else:
                    color_label = 'Silicone'
            else:
                color_label = subcategory.title()
        else:
            # For TPA products, show brand and specific product details
            main_label = brand.title()
            
            # Extract specific product type and features
            name_upper = name.upper()
            if 'CRYSTAL' in name_upper:
                if 'METAL CAMERA' in name_upper:
                    sub_label = 'Crystal Camera'
                elif 'SUPER CRYSTAL' in name_upper:
                    sub_label = 'Super Crystal'
                else:
                    sub_label = 'Crystal'
            elif 'MATT' in name_upper or 'MATTE' in name_upper:
                if 'MAGSAFE' in name_upper:
                    sub_label = 'Matt MagSafe'
                else:
                    sub_label = 'Matte'
            elif 'ARMOUR' in name_upper or 'ARMOR' in name_upper:
                sub_label = 'Armor'
            elif 'CLEAR' in name_upper:
                if 'MAGSAFE' in name_upper:
                    sub_label = 'Clear MagSafe'
                else:
                    sub_label = 'Clear'
            elif 'PRIVACY' in name_upper:
                if 'GLASS' in name_upper:
                    sub_label = 'Privacy Glass'
                else:
                    sub_label = 'Privacy'
            elif 'FOCAL' in name_upper:
                if 'CAMERA LENS' in name_upper:
                    sub_label = 'Camera Lens'
                else:
                    sub_label = 'Focal'
            elif 'TEMPERED GLASS' in name_upper:
                sub_label = 'Tempered Glass'
            elif 'SCREEN PROTECTOR' in name_upper:
                sub_label = 'Screen Guard'
            else:
                sub_label = 'Case'
            
            # Extract color information for TPA products
            if 'BLACK' in name_upper:
                color_label = 'Black'
            elif 'CLEAR' in name_upper:
                color_label = 'Clear'
            elif 'BLUE' in name_upper:
                color_label = 'Blue'
            elif 'GREY' in name_upper or 'GRAY' in name_upper:
                color_label = 'Grey'
            elif 'GOLD' in name_upper:
                color_label = 'Gold'
            elif 'SILVER' in name_upper:
                color_label = 'Silver'
            elif 'DIAMOND' in name_upper:
                color_label = 'Diamond'
            else:
                color_label = ''
        
        # Main label (top)
        ax.text(x + product_width/2, y + product_height*0.7, main_label,
               fontsize=7, ha='center', va='center', 
               color='white', weight='bold')
        
        # Sub label (middle)
        ax.text(x + product_width/2, y + product_height*0.5, sub_label,
               fontsize=8, ha='center', va='center', 
               color='white', weight='bold')
        
        # Color/type label (bottom)
        if color_label:
            ax.text(x + product_width/2, y + product_height*0.3, color_label,
                   fontsize=6, ha='center', va='center', 
                   color='white', weight='normal', alpha=0.9)
        
        # Facings indicator
        if facings > 1:
            ax.text(x + product_width - 0.15, y + product_height - 0.15, 
                   f'{facings}', fontsize=8, ha='right', va='top',
                   color='white', weight='bold',
                   bbox=dict(boxstyle='circle,pad=0.05', facecolor='red', alpha=0.9))
    
    # Title
    ax.text(start_x + shelf_width/2, start_y + shelf_height + 0.8, title,
           fontsize=20, ha='center', va='bottom', weight='bold', color='#333333')
    
    # Legend in bottom right
    if brand_colors_used:
        legend_x = start_x + shelf_width - 6
        legend_y = start_y - 1.5
        
        # Legend background
        legend_bg = Rectangle(
            (legend_x - 0.2, legend_y - len(brand_colors_used) * 0.6 - 0.3),
            5.5, len(brand_colors_used) * 0.6 + 0.8,
            facecolor='white',
            edgecolor='#CCCCCC',
            linewidth=1,
            alpha=0.95
        )
        ax.add_patch(legend_bg)
        
        ax.text(legend_x, legend_y, 'Brands', fontsize=12, weight='bold', color='#333333')
        legend_y -= 0.7
        
        for brand_name, color in sorted(brand_colors_used):
            # Color square
            color_rect = Rectangle(
                (legend_x, legend_y - 0.2), 0.4, 0.4,
                facecolor=color, edgecolor='#333333', linewidth=1, alpha=0.9
            )
            ax.add_patch(color_rect)
            
            # Brand name
            ax.text(legend_x + 0.6, legend_y, brand_name,
                   fontsize=11, va='center', color='#333333')
            legend_y -= 0.6
    
    # Clean axis
    ax.set_xlim(0, start_x + shelf_width + 1)
    ax.set_ylim(start_y - 3, start_y + shelf_height + 2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
    
    return fig
