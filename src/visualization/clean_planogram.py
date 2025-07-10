import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from typing import List, Dict, Optional, Tuple
from src.models.product import Product
from src.optimization.base_optimizer import OptimizationResult
from src.visualization.arrangement_utils import extract_color_from_name, arrange_section

def extract_color_from_name(name):
    # Looks for color after last hyphen or common Apple color names
    import re
    color_keywords = [
        'Black', 'Denim', 'Fuchsia', 'Lake Green', 'Plum', 'Star Fruit', 'Stone Gray', 'Ultramarine',
        'Red', 'Blue', 'Green', 'Pink', 'Purple', 'Yellow', 'White', 'Orange', 'Silver', 'Gold', 'Clear', 'Grey', 'Gray', 'Brown', 'Beige', 'Coral', 'Midnight', 'Starlight', 'Lavender', 'Mint', 'Deep Navy', 'Cypress', 'Storm Blue', 'Sunshine', 'Violet', 'Forest', 'Indigo', 'Sky', 'Sand', 'Crimson', 'Teal', 'Turquoise', 'Graphite', 'Magenta', 'Rose', 'Champagne', 'Charcoal', 'Smoke', 'Pearl', 'Aqua', 'Peach', 'Cobalt', 'Emerald', 'Ruby', 'Amber', 'Bronze', 'Copper', 'Ivory', 'Mustard', 'Olive', 'Sage', 'Slate', 'Taupe', 'Wine', 'Zinc', 'Maroon', 'Cyan', 'Lime', 'Mint', 'Berry', 'Lilac', 'Cream', 'Espresso', 'Mocha', 'Onyx', 'Blush', 'Ice', 'Cement', 'Graphite', 'Shadow', 'Ocean', 'Sunset', 'Dusk', 'Dawn', 'Twilight', 'Mist', 'Fog', 'Frost', 'Snow', 'Steel', 'Ash', 'Jet', 'Obsidian', 'Sapphire', 'Topaz', 'Jade', 'Opal', 'Quartz', 'Ruby', 'Amber', 'Pearl', 'Diamond', 'Crystal', 'Matte', 'Matt', 'Armor', 'Armour', 'Privacy'
    ]
    for color in color_keywords:
        if color.lower() in name.lower():
            return color
    # Fallback: after last hyphen
    if '-' in name:
        return name.split('-')[-1].strip()
    return ''

def create_clean_planogram(result: OptimizationResult,
                          product_lookup: Dict[str, Product],
                          title: str = "Clean Planogram",
                          save_path: Optional[str] = None,
                          figsize: Tuple[int, int] = (16, 12),
                          products_list: Optional[List[Product]] = None) -> plt.Figure:
    """Create a clean, modern planogram visualization"""
    from src.utils.logger import get_logger
    logger = get_logger()
    logger.debug(f"create_clean_planogram called with save_path={save_path}")
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor('#FFFFFF')
    
    # Get products to visualize
    if products_list is not None and len(products_list) > 0:
        # Use provided list directly (default 1 facing each)
        all_products = [(p, 1) for p in products_list]
    else:
        # Fallback to products actually placed on shelves
        all_products = []
        for shelf in result.store.shelves:
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    all_products.append((product, position.facings))
    
    if not all_products:
        logger.debug("No products found, returning early")
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
    
    # Split products by brand
    apple_products = [p for p in all_products if getattr(p[0], 'brand', '').lower() == 'apple']
    tpa_products = [p for p in all_products if getattr(p[0], 'brand', '').lower() != 'apple']

    logger.debug(f"Apple products count: {len(apple_products)}")
    logger.debug(f"Apple product names: {[getattr(p[0], 'product_name', 'Unknown') for p in apple_products]}")
    logger.debug(f"TPA products count: {len(tpa_products)}")
    logger.debug(f"TPA product names: {[getattr(p[0], 'product_name', 'Unknown') for p in tpa_products]}")

    # Enforce: first 4 rows for Apple, remaining for TPA
    apple_rows = 4
    apple_slots = apple_rows * cols
    tpa_rows = rows - apple_rows
    tpa_slots = tpa_rows * cols


    
    # Arrange Apple and TPA sections with new logic
    arranged = []
    # For iPad cases we skip clear-case priority; detect by checking any product series contains 'ipad'
    apple_series_lower = [getattr(p[0], 'series', '').lower() for p in apple_products]
    is_ipad_context = any('ipad' in s for s in apple_series_lower)
    arranged_apple = arrange_section(
        apple_products,
        apple_slots,
        cols,
        group_clear_columnwise=not is_ipad_context,
        color_rowwise=True
    )
    priority_brands = ['Pulse', 'Tekne', 'Gripp']
    priority_lower = [b.lower() for b in priority_brands]
    tpa_products_priority = [p for p in tpa_products if getattr(p[0], 'brand', '').lower() in priority_lower]
    arranged_tpa = arrange_section(tpa_products_priority, tpa_slots, cols, group_clear_columnwise=False, group_by_brand=True, priority_brands=priority_brands, brand_columnwise=True)
    arranged += arranged_apple
    arranged += arranged_tpa

    logger.debug(f"Arranged Apple section product names: {[getattr(p[0], 'product_name', 'None') if p else 'None' for p in arranged_apple]}")
    logger.debug(f"Arranged TPA section product names: {[getattr(p[0], 'product_name', 'None') if p else 'None' for p in arranged_tpa]}")

    # Calculate layout dimensions
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
    for i, product_data in enumerate(arranged):
        if product_data is None:
            continue
            
        row = i // cols
        col = i % cols
        
        x = start_x + col * (product_width + gap_x)
        y = start_y + (rows - 1 - row) * (product_height + gap_y)
        
        product, facings = product_data
        brand = getattr(product, 'brand', 'Unknown').lower()
        
        # Get color
        if brand == 'apple':
            color = brand_colors['apple']
            brand_colors_used.add(('Apple', color))
        else:
            color = brand_colors.get(brand, brand_colors['default'])
            brand_colors_used.add((brand.title(), color))
        
        # Draw phone case with rounded corners
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
        
        # Product label
        name = getattr(product, 'product_name', 'Unknown')
        
        # Extract main info from product name
        def extract_color_from_name(name):
            # Looks for color after last hyphen or common Apple color names
            import re
            color_keywords = [
                'Black', 'Denim', 'Fuchsia', 'Lake Green', 'Plum', 'Star Fruit', 'Stone Gray', 'Ultramarine',
                'Red', 'Blue', 'Green', 'Pink', 'Purple', 'Yellow', 'White', 'Orange', 'Silver', 'Gold', 'Clear', 'Grey', 'Gray', 'Brown', 'Beige', 'Coral', 'Midnight', 'Starlight', 'Lavender', 'Mint', 'Deep Navy', 'Cypress', 'Storm Blue', 'Sunshine', 'Violet', 'Forest', 'Indigo', 'Sky', 'Sand', 'Crimson', 'Teal', 'Turquoise', 'Graphite', 'Magenta', 'Rose', 'Champagne', 'Charcoal', 'Smoke', 'Pearl', 'Aqua', 'Peach', 'Cobalt', 'Emerald', 'Ruby', 'Amber', 'Bronze', 'Copper', 'Ivory', 'Mustard', 'Olive', 'Sage', 'Slate', 'Taupe', 'Wine', 'Zinc', 'Maroon', 'Cyan', 'Lime', 'Mint', 'Berry', 'Lilac', 'Cream', 'Espresso', 'Mocha', 'Onyx', 'Blush', 'Ice', 'Cement', 'Graphite', 'Shadow', 'Ocean', 'Sunset', 'Dusk', 'Dawn', 'Twilight', 'Mist', 'Fog', 'Frost', 'Snow', 'Steel', 'Ash', 'Jet', 'Obsidian', 'Sapphire', 'Topaz', 'Jade', 'Opal', 'Quartz', 'Ruby', 'Amber', 'Pearl', 'Diamond', 'Crystal', 'Matte', 'Matt', 'Armor', 'Armour', 'Privacy'
            ]
            for color in color_keywords:
                if color.lower() in name.lower():
                    return color
            # Fallback: after last hyphen
            if '-' in name:
                return name.split('-')[-1].strip()
            return ''

        if brand == 'apple':
            if 'Pro Max' in name:
                main_label = 'iPhone 16 Pro Max'
            elif 'Pro' in name:
                main_label = 'iPhone 16 Pro'
            elif 'Plus' in name:
                main_label = 'iPhone 16 Plus'
            else:
                main_label = 'iPhone 16'
            color = extract_color_from_name(name)
            if 'Clear' in name:
                sub_label = f'{color} Clear Case' if color and color != 'Clear' else 'Clear Case'
            elif 'Silicone' in name:
                sub_label = f'{color} Silicone Case' if color and color != 'Silicone' else 'Silicone Case'
            else:
                sub_label = color + ' Case' if color else 'Case'
        else:
            main_label = brand.title()
            color = extract_color_from_name(name)
            if color:
                sub_label = f'{color} Case'
            else:
                sub_label = 'Case'
        
        # Main label
        ax.text(x + product_width/2, y + product_height*0.7, main_label,
               fontsize=8, ha='center', va='center', 
               color='white', weight='bold')
        
        # Sub label
        ax.text(x + product_width/2, y + product_height*0.5, sub_label,
               fontsize=7, ha='center', va='center', 
               color='white', weight='normal')
        
        # Facings indicator
        if facings > 1:
            ax.text(x + product_width - 0.15, y + product_height - 0.15, 
                   f'{facings}', fontsize=8, ha='right', va='top',
                   color='white', weight='bold',
                   bbox=dict(boxstyle='circle,pad=0.05', facecolor='red', alpha=0.9))
    
    # Title
    ax.text(start_x + shelf_width/2, start_y + shelf_height + 0.8, title,
           fontsize=20, ha='center', va='bottom', weight='bold', color='#333333')
    
    # Legend
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
    
    logger.debug("About to call plt.tight_layout()")
    plt.tight_layout()
    logger.debug("plt.tight_layout() completed")
    
    logger.debug(f"save_path = {save_path}")
    if save_path:
        logger.debug("About to save planogram...")
        try:
            plt.savefig(save_path, dpi=300, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            logger.debug(f"Successfully saved planogram to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save planogram to {save_path}: {e}")
            import traceback
            traceback.print_exc()
    else:
        logger.debug("No save_path provided, skipping save")
    
    return fig
