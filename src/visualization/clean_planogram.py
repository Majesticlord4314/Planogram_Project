import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib import patches
import numpy as np
from typing import List, Dict, Optional, Tuple
from src.models.product import Product
from src.optimization.base_optimizer import OptimizationResult
from src.visualization.arrangement_utils import extract_color_from_name, arrange_section
import textwrap
import os

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

def create_clean_planogram(products: List[Product], store_template: 'Store', lob: str, figsize: Tuple[int, int] = (16, 12), title: str = None, save_path: str = None, products_list: List = None) -> plt.Figure:
    """Create a clean, modern planogram visualization with two separate planograms for iPad/iPhone series split."""
    from src.utils.logger import get_logger
    logger = get_logger()
    logger.info(f"Generating clean planogram for LOB '{lob}' with store '{store_template.store_name}'.")

    # Convert the simple product list to the (product, facings) format
    all_products = [(p, 1) for p in products]

    if not all_products:
        logger.warning("No products provided to create_clean_planogram. Generating empty plot.")
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_facecolor('#FFFFFF')
        ax.text(0.5, 0.5, 'No products to display', ha='center', va='center', transform=ax.transAxes, fontsize=16, color='red')
        ax.axis('off')
        return fig
    
    # Filter products - for Mac, use all products since they're third-party accessories
    if lob.lower() == 'mac':
        apple_products = all_products  # Mac accessories are third-party, use all
    else:
        # Filter only Apple products for other LOBs
        apple_products = [p for p in all_products if 'apple' in getattr(p[0], 'brand', '').lower()]
    
    if not apple_products:
        logger.warning(f"No products found for {lob.upper()} planogram.")
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_facecolor('#FFFFFF')
        ax.text(0.5, 0.5, f'No {lob.upper()} products to display', ha='center', va='center', transform=ax.transAxes, fontsize=16, color='red')
        ax.axis('off')
        return fig

    logger.info(f"Found {len(apple_products)} products for {lob.upper()} planogram generation.")

    # Sort Apple products by sales velocity to get best selling products
    apple_products.sort(key=lambda p: getattr(p[0], 'total_qty', 0), reverse=True)

    # Fixed layout: 3 columns, realistic shelf capacity
    cols = 3
    
    # Determine layout based on store template
    if store_template.store_type.lower() == 'flagship':
        # Flagship stores get more space
        apple_rows = 4
        tpa_rows = 4
    elif store_template.store_type.lower() == 'standard':
        # Standard stores get medium space
        apple_rows = 3
        tpa_rows = 3
    else:  # Express stores
        # Express stores get compact space
        apple_rows = 2
        tpa_rows = 2
    
    # Split Apple products into two groups for two planograms based on LOB
    if lob.lower() == 'ipad':
        # iPad series split: Pro & Air vs Mini & Base
        part1_products = []
        part2_products = []
        
        for prod_tuple in apple_products:
            product = prod_tuple[0]
            series = getattr(product, 'series', '').lower()
            
            if 'pro' in series or 'air' in series:
                part1_products.append(prod_tuple)
            elif 'mini' in series or 'base' in series:
                part2_products.append(prod_tuple)
        
        # Ensure we have products for both parts
        if not part1_products:
            part1_products = apple_products[:apple_rows * cols]
        if not part2_products:
            part2_products = apple_products[:apple_rows * cols]
            
        part1_title = "Pro & Air"
        part2_title = "Mini & Base"
        part1_filter = ["pro", "air"]
        part2_filter = ["mini", "base"]
        
    elif lob.lower() == 'iphone':
        # Use dedicated iPhone planogram system
        from src.visualization.iphone_planogram_logic import arrange_iphone_products
        planogram_data = arrange_iphone_products(products, store_template)
        # Create dummy figure to return
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'iPhone planograms generated successfully', ha='center', va='center', transform=ax.transAxes, fontsize=16)
        ax.axis('off')
        return fig
        
    elif lob.lower() == 'watch':
        # Use dedicated Watch planogram system
        from src.visualization.watch_planogram import create_watch_planogram
        create_watch_planogram(store_template)
        # Create dummy figure to return
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'Apple Watch planograms generated successfully', ha='center', va='center', transform=ax.transAxes, fontsize=16)
        ax.axis('off')
        return fig
        
    elif lob.lower() == 'mac':
        # Use dedicated Mac planogram system with our pre-built planograms
        from src.visualization.mac_planogram import create_mac_planogram
        create_mac_planogram(products, store_template)
        # Create dummy figure to return
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'Mac planograms generated successfully', ha='center', va='center', transform=ax.transAxes, fontsize=16)
        ax.axis('off')
        return fig
        
    else:
        # Default fallback for other LOBs
        mid_point = len(apple_products) // 2
        part1_products = apple_products[:mid_point]
        part2_products = apple_products[mid_point:]
        part1_title = "Series 1"
        part2_title = "Series 2"
        part1_filter = []
        part2_filter = []

    def arrange_products_columnwise(products_list, total_slots, cols, rows):
        """Arrange products column-wise to create symmetrical layout"""
        from itertools import cycle, islice
        
        if not products_list:
            return [None] * total_slots
            
        # If we have fewer products than slots, cycle through them
        if len(products_list) < total_slots:
            expanded_products = list(islice(cycle(products_list), total_slots))
        else:
            expanded_products = products_list[:total_slots]
        
        # Create a grid arranged column-wise for symmetry
        grid = [None] * total_slots
        
        # Fill column by column instead of row by row
        for col in range(cols):
            for row in range(rows):
                source_index = col * rows + row
                target_index = row * cols + col
                
                if source_index < len(expanded_products) and target_index < total_slots:
                    grid[target_index] = expanded_products[source_index]
        
        return grid
    
    # Function to create a single planogram part
    def create_planogram_part(apple_part_products, part_title, part_num, series_filter, apple_rows, tpa_rows):
        """Create a single planogram with adaptive rows based on store template"""
        
        # Layout: adaptive rows based on store template
        total_rows = apple_rows + tpa_rows
        
        # Limit to realistic shelf capacity based on store template
        apple_slots = apple_rows * cols  # slots for specific series
        tpa_slots = tpa_rows * cols      # slots for TPA same series
        
        # Arrange Apple products column-wise for symmetry
        apple_grid = arrange_products_columnwise(apple_part_products, apple_slots, cols, apple_rows)
        
        # For TPA section: use products that match the same series as Apple section
        # Filter all products (including non-Apple) by the same series
        tpa_part_products = []
        for prod_tuple in all_products:
            product = prod_tuple[0]
            series = getattr(product, 'series', '').lower()
            brand = getattr(product, 'brand', '').lower()
            
            # Include both Apple and non-Apple products that match the series
            if any(s in series for s in series_filter):
                tpa_part_products.append(prod_tuple)
        
        # Sort TPA products by sales velocity to get best ones
        tpa_part_products.sort(key=lambda p: getattr(p[0], 'total_qty', 0), reverse=True)
        
        # Arrange TPA products column-wise to match Apple section symmetry
        tpa_grid = arrange_products_columnwise(tpa_part_products, tpa_slots, cols, tpa_rows)
        
        # Combine grids
        combined_products = apple_grid + tpa_grid
        
        # Create figure for this part
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_facecolor('#FFFFFF')
        
        # Layout parameters
        product_width = 2.2
        product_height = 4.0
        gap_x, gap_y = 0.8, 1.0
        
        total_width = cols * product_width + (cols - 1) * gap_x
        total_height = total_rows * product_height + (total_rows - 1) * gap_y
        
        ax.set_xlim(0, total_width)
        ax.set_ylim(0, total_height)
        
        # Brand colors
        brand_colors = {'apple': '#d6d6d6', 'default': '#a9a9a9'}
        
        # Draw products
        for i, product_data in enumerate(combined_products):
            if not product_data:
                continue
                
            row = i // cols
            col = i % cols
            x = col * (product_width + gap_x)
            y = total_height - (row + 1) * product_height - row * gap_y
            
            product, facings = product_data
            brand = getattr(product, 'brand', 'Unknown').lower()
            
            # Use different shades for Apple main vs TPA sections
            if i < apple_slots:  # Main Apple section
                color = '#4a90e2'  # Blue for main series
            else:  # TPA section (same series)
                color = '#7fb069'  # Green for TPA same series
            
            # Draw product box
            box = FancyBboxPatch(
                (x, y), product_width, product_height,
                boxstyle="round,pad=0.02",
                facecolor=color,
                edgecolor='#333333',
                linewidth=1.5,
                alpha=0.95
            )
            ax.add_patch(box)
            
            # Add text labels
            series_label = getattr(product, 'series', 'Unknown')
            name_label = getattr(product, 'product_name', 'Unknown Product')
            wrapped_name = '\n'.join(textwrap.wrap(name_label, width=20))
            
            ax.text(x + product_width / 2, y + product_height * 0.75, 
                   series_label, fontsize=8, ha='center', va='center', 
                   color='white', weight='bold')
            ax.text(x + product_width / 2, y + product_height * 0.45, 
                   wrapped_name, fontsize=6, ha='center', va='center', 
                   color='white', style='italic', linespacing=1.2)
        
        # Add section divider line
        divider_y = total_height - apple_rows * product_height - (apple_rows - 0.5) * gap_y
        ax.axhline(y=divider_y, color='#333333', linewidth=2, alpha=0.7)
        
        # Add section labels
        ax.text(total_width / 2, total_height - 0.5, f'Apple {part_title} Series', 
               fontsize=10, ha='center', va='top', weight='bold')
        ax.text(total_width / 2, divider_y - 0.5, f'TPA {part_title} Series', 
               fontsize=10, ha='center', va='top', weight='bold')
        
        # Set title and clean up
        ax.set_title(f'{lob.title()} Planogram - {store_template.store_name} (Part {part_num})', 
                    fontsize=16, weight='bold', pad=20)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('off')
        
        fig.tight_layout(rect=[0, 0.1, 1, 0.95])
        
        # Save the plot
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filename = f"{output_dir}/{lob.replace(' ', '_')}_{store_template.store_name.replace(' ', '_')}_planogram_part{part_num}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        logger.info(f"Saved planogram part {part_num} to {filename}")
        plt.close(fig)
        
        return fig
    
    # Create Part 1
    logger.info(f"Creating Part 1: {lob.title()} {part1_title} series")
    create_planogram_part(part1_products, part1_title, 1, part1_filter, apple_rows, tpa_rows)
    
    # Create Part 2
    logger.info(f"Creating Part 2: {lob.title()} {part2_title} series")
    fig = create_planogram_part(part2_products, part2_title, 2, part2_filter, apple_rows, tpa_rows)
    
    return fig

