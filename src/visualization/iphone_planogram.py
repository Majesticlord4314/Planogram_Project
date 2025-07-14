import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib import patches
import numpy as np
from typing import List, Dict, Optional, Tuple
from src.models.product import Product
import textwrap
import os

def extract_color_from_name(name):
    """Extract color from product name"""
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

def calculate_products_per_row(shelf_width_cm, avg_product_width_cm, gap_cm=2.0):
    """Calculate how many products fit per row based on dimensions"""
    if avg_product_width_cm <= 0:
        return 3  # Default fallback
    
    # Calculate with gaps between products
    products_per_row = int((shelf_width_cm + gap_cm) / (avg_product_width_cm + gap_cm))
    
    # Ensure reasonable bounds
    return max(2, min(products_per_row, 6))

def create_iphone_planogram(products: List[Product], store_template: 'Store', figsize: Tuple[int, int] = (16, 12)):
    """Create comprehensive iPhone planograms with proper store template adaptation"""
    from src.utils.logger import get_logger
    logger = get_logger()
    logger.info(f"Generating iPhone planogram for store '{store_template.store_name}'.")

    # Convert to (product, facings) format
    all_products = [(p, 1) for p in products]

    if not all_products:
        logger.warning("No products provided for iPhone planogram.")
        return None

    # Filter Apple and TPA products
    apple_products = [p for p in all_products if 'apple' in getattr(p[0], 'brand', '').lower()]
    tpa_products = [p for p in all_products if 'apple' not in getattr(p[0], 'brand', '').lower()]

    if not apple_products:
        logger.warning("No Apple products found for iPhone planogram.")
        return None

    logger.info(f"Found {len(apple_products)} Apple and {len(tpa_products)} TPA products.")

    # Calculate dimensions based on actual product sizes
    valid_widths = [p[0].width for p in all_products if p[0].width > 0]
    avg_product_width_cm = np.mean(valid_widths) if valid_widths else 11.0  # iPhone case typical width
    shelf_width_cm = store_template.shelves[0].width
    
    # Calculate products per row based on actual dimensions
    cols = calculate_products_per_row(shelf_width_cm, avg_product_width_cm)
    logger.info(f"Calculated {cols} products per row (shelf: {shelf_width_cm}cm, avg product: {avg_product_width_cm:.1f}cm)")

    # Store template specific row configurations
    if store_template.store_type.lower() == 'flagship':
        apple_rows = 4
        tpa_rows = 4
        # Create 4 individual series planograms for flagship
        create_flagship_series_planograms(apple_products, tpa_products, store_template, cols, figsize)
    elif store_template.store_type.lower() == 'standard':
        apple_rows = 1
        tpa_rows = 5
        # Include screen protectors for standard
        screen_protector_products = [p for p in all_products if 'screen_protector' in str(getattr(p[0], 'category', '')).lower()]
        if screen_protector_products:
            # Add screen protectors to TPA products
            tpa_products.extend(screen_protector_products)
            logger.info(f"Added {len(screen_protector_products)} screen protector products for standard store")
    else:  # Express
        apple_rows = 3
        tpa_rows = 2

    # Create main planograms
    create_main_planogram(apple_products, tpa_products, store_template, apple_rows, tpa_rows, cols, figsize)

def create_flagship_series_planograms(apple_products, tpa_products, store_template, cols, figsize):
    """Create 4 individual series planograms for flagship stores"""
    from src.utils.logger import get_logger
    logger = get_logger()
    
    # Define iPhone 16 series
    series_list = [
        ("iPhone 16 Base", "iPhone16_Base"),
        ("iPhone 16 Plus", "iPhone16_Plus"), 
        ("iPhone 16 Pro", "iPhone16_Pro"),
        ("iPhone 16 Pro Max", "iPhone16_ProMax")
    ]
    
    for series_name, file_suffix in series_list:
        logger.info(f"Creating flagship planogram for {series_name}")
        
        # Filter Apple products for this series
        series_apple = [p for p in apple_products if series_name.lower() in getattr(p[0], 'series', '').lower()]
        
        if not series_apple:
            logger.warning(f"No Apple products found for {series_name}")
            continue
            
        # Filter TPA products for this series
        series_tpa = [p for p in tpa_products if series_name.lower().replace("iphone ", "") in getattr(p[0], 'series', '').lower()]
        
        create_single_series_planogram(series_apple, series_tpa, store_template, series_name, file_suffix, 4, 4, cols, figsize)

def create_main_planogram(apple_products, tpa_products, store_template, apple_rows, tpa_rows, cols, figsize):
    """Create the main planogram with Pro & Pro Max vs Plus & Base split"""
    from src.utils.logger import get_logger
    logger = get_logger()
    
    # Split into two planograms
    # Part 1: Pro & Pro Max
    pro_products = []
    # Part 2: Plus & Base  
    plus_base_products = []
    
    for prod_tuple in apple_products:
        product = prod_tuple[0]
        series = getattr(product, 'series', '').lower()
        
        if 'pro max' in series or ('pro' in series and 'pro max' not in series):
            pro_products.append(prod_tuple)
        elif 'plus' in series or 'base' in series:
            plus_base_products.append(prod_tuple)
    
    # Create Part 1: Pro & Pro Max
    logger.info("Creating Part 1: iPhone Pro & Pro Max series")
    create_single_series_planogram(pro_products, tpa_products, store_template, "Pro & Pro Max", "part1", apple_rows, tpa_rows, cols, figsize)
    
    # Create Part 2: Plus & Base
    logger.info("Creating Part 2: iPhone Plus & Base series")
    create_single_series_planogram(plus_base_products, tpa_products, store_template, "Plus & Base", "part2", apple_rows, tpa_rows, cols, figsize)

def create_single_series_planogram(apple_part_products, tpa_products, store_template, series_title, file_suffix, apple_rows, tpa_rows, cols, figsize):
    """Create a single planogram with clear case logic and proper visualization"""
    from src.utils.logger import get_logger
    logger = get_logger()
    
    # Calculate slots
    apple_slots = apple_rows * cols
    tpa_slots = tpa_rows * cols
    total_rows = apple_rows + tpa_rows
    
    # Arrange Apple products with clear case logic (first column clear, rest high-selling colors)
    apple_grid = arrange_apple_products_with_clear_logic(apple_part_products, apple_slots, cols, apple_rows)
    
    # Arrange TPA products with brand diversity
    tpa_grid = arrange_tpa_products_with_diversity(tpa_products, tpa_slots, cols, tpa_rows)
    
    # Combine grids
    combined_products = apple_grid + tpa_grid
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor('#FFFFFF')
    
    # Layout parameters
    product_width = 2.5
    product_height = 3.5
    gap_x, gap_y = 0.3, 0.4
    
    total_width = cols * product_width + (cols - 1) * gap_x
    total_height = total_rows * product_height + (total_rows - 1) * gap_y
    
    ax.set_xlim(0, total_width)
    ax.set_ylim(0, total_height)
    
    # Brand colors for legend
    brand_colors = {}
    brand_colors_used = set()
    
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
        
        # Color logic
        if i < apple_slots:  # Apple section
            if col == 0:  # First column - clear cases
                color = '#e6f3ff'  # Light blue for clear
            else:  # Other columns - colored cases
                color = '#4a90e2'  # Blue for Apple colored
        else:  # TPA section
            # Brand-specific colors
            if brand not in brand_colors:
                brand_colors[brand] = plt.cm.tab10(len(brand_colors) % 10)
            color = brand_colors[brand]
            brand_colors_used.add((brand.title(), color))
        
        # Draw product box
        box = FancyBboxPatch(
            (x, y), product_width, product_height,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor='#333333',
            linewidth=1.2,
            alpha=0.9
        )
        ax.add_patch(box)
        
        # Add text labels with BLACK text for better readability
        series_label = getattr(product, 'series', 'Unknown')
        name_label = getattr(product, 'product_name', 'Unknown Product')
        brand_name = getattr(product, 'brand', 'Unknown')
        
        if i < apple_slots:  # Apple section
            # Extract color for colored cases
            if col == 0:  # First column - show "Clear Case"
                display_name = "Clear Case"
            else:  # Other columns - show color
                color_name = extract_color_from_name(name_label)
                display_name = color_name if color_name else "Colored Case"
            
            ax.text(x + product_width / 2, y + product_height * 0.75, 
                   series_label, fontsize=7, ha='center', va='center', 
                   color='black', weight='bold')
            ax.text(x + product_width / 2, y + product_height * 0.35, 
                   display_name, fontsize=6, ha='center', va='center', 
                   color='black', linespacing=1.1)
        else:  # TPA section - show brand and product type with color
            # Show brand prominently and product type with color
            product_type = "Case"
            if "screen" in name_label.lower():
                product_type = "Screen Protector"
            elif "lens" in name_label.lower():
                product_type = "Lens Protector"
            elif "cable" in name_label.lower():
                product_type = "Cable"
            
            # Extract color for TPA products
            color_name = extract_color_from_name(name_label)
            display_text = f"{product_type}"
            if color_name:
                display_text = f"{color_name} {product_type}"
            
            ax.text(x + product_width / 2, y + product_height * 0.75, 
                   brand_name, fontsize=7, ha='center', va='center', 
                   color='black', weight='bold')
            ax.text(x + product_width / 2, y + product_height * 0.35, 
                   display_text, fontsize=6, ha='center', va='center', 
                   color='black', linespacing=1.1)
    
    # Add section divider line
    divider_y = total_height - apple_rows * product_height - (apple_rows - 0.5) * gap_y
    ax.axhline(y=divider_y, color='#333333', linewidth=2, alpha=0.7)
    
    # Add section labels
    ax.text(total_width / 2, total_height - 0.3, f'Apple {series_title} Series', 
           fontsize=11, ha='center', va='top', weight='bold', color='black')
    ax.text(total_width / 2, divider_y - 0.3, f'TPA {series_title} Compatible', 
           fontsize=11, ha='center', va='top', weight='bold', color='black')
    
    # Set title
    ax.set_title(f'iPhone Planogram - {store_template.store_name} ({series_title})', 
                fontsize=14, weight='bold', pad=20, color='black')
    
    # Add legend for TPA brands
    if brand_colors_used:
        legend_elements = [patches.Patch(facecolor=color, edgecolor='black', label=brand) 
                          for brand, color in sorted(brand_colors_used)]
        fig.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 0.02), 
                  ncol=min(len(legend_elements), 4), frameon=True, title='TPA Brands',
                  fancybox=True, shadow=True)
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    
    fig.tight_layout(rect=[0, 0.15, 1, 0.95])
    
    # Save the plot
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"{output_dir}/iPhone_{store_template.store_name.replace(' ', '_')}_planogram_{file_suffix}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    logger.info(f"Saved iPhone planogram to {filename}")
    plt.close(fig)

def arrange_apple_products_with_clear_logic(apple_products, total_slots, cols, rows):
    """Arrange Apple products with first column clear, rest diverse high-selling colors"""
    from itertools import cycle, islice
    
    if not apple_products:
        return [None] * total_slots
    
    # Separate clear and colored products
    clear_products = [p for p in apple_products if 'clear' in getattr(p[0], 'product_name', '').lower() or 'clear' in getattr(p[0], 'subcategory', '').lower()]
    colored_products = [p for p in apple_products if p not in clear_products]
    
    # Sort colored by sales (total_qty) - best sellers first
    colored_products.sort(key=lambda p: getattr(p[0], 'total_qty', 0), reverse=True)
    
    # Ensure we have products for both categories
    if not clear_products:
        clear_products = apple_products[:len(apple_products)//2] if len(apple_products) > 1 else apple_products
    if not colored_products:
        colored_products = apple_products[len(apple_products)//2:] if len(apple_products) > 1 else apple_products
    
    # Group colored products by unique colors to maximize diversity
    color_groups = {}
    for prod_tuple in colored_products:
        color = extract_color_from_name(getattr(prod_tuple[0], 'product_name', ''))
        if color not in color_groups:
            color_groups[color] = []
        color_groups[color].append(prod_tuple)
    
    # Sort each color group by sales and take the best seller for each color
    diverse_colored_products = []
    for color, products in color_groups.items():
        # Sort by sales and take the best seller for this color
        products.sort(key=lambda p: getattr(p[0], 'total_qty', 0), reverse=True)
        diverse_colored_products.append(products[0])
    
    # Sort diverse colors by their best product's sales
    diverse_colored_products.sort(key=lambda p: getattr(p[0], 'total_qty', 0), reverse=True)
    
    # If we need more products, add more from top selling colors
    if len(diverse_colored_products) < cols - 1:  # -1 for clear column
        remaining_needed = (cols - 1) - len(diverse_colored_products)
        # Add more products from top selling colors
        for _ in range(remaining_needed):
            if colored_products:
                diverse_colored_products.append(colored_products[len(diverse_colored_products) % len(colored_products)])
    
    grid = []
    clear_idx = 0
    colored_idx = 0
    
    # Fill row by row with clear first column logic
    for row in range(rows):
        for col in range(cols):
            if col == 0:  # First column - clear products
                if clear_products:
                    grid.append(clear_products[clear_idx % len(clear_products)])
                    clear_idx += 1
                else:
                    grid.append(apple_products[0] if apple_products else None)
            else:  # Other columns - diverse colored products
                if diverse_colored_products:
                    grid.append(diverse_colored_products[colored_idx % len(diverse_colored_products)])
                    colored_idx += 1
                else:
                    grid.append(colored_products[0] if colored_products else apple_products[0] if apple_products else None)
    
    # Ensure exact slot count and no None values
    while len(grid) < total_slots:
        if apple_products:
            grid.append(apple_products[len(grid) % len(apple_products)])
        else:
            grid.append(None)
    
    return grid[:total_slots]

def arrange_tpa_products_with_diversity(tpa_products, total_slots, cols, rows):
    """Arrange TPA products with proper brand grouping and no blank spots"""
    from itertools import cycle, islice
    
    if not tpa_products:
        return [None] * total_slots
    
    # Group by brand and sort by sales within each brand
    brand_groups = {}
    for prod_tuple in tpa_products:
        brand = getattr(prod_tuple[0], 'brand', 'Unknown')
        if brand not in brand_groups:
            brand_groups[brand] = []
        brand_groups[brand].append(prod_tuple)
    
    # Sort each brand group by sales (best sellers first)
    for brand in brand_groups:
        brand_groups[brand].sort(key=lambda p: getattr(p[0], 'total_qty', 0), reverse=True)
    
    # Sort brands by their total sales (best brands first)
    brand_totals = {}
    for brand, products in brand_groups.items():
        brand_totals[brand] = sum(getattr(p[0], 'total_qty', 0) for p in products)
    
    sorted_brands = sorted(brand_groups.keys(), key=lambda b: brand_totals[b], reverse=True)
    
    # Create brand-grouped arrangement (fill by brand blocks)
    grid = []
    products_per_brand = max(1, total_slots // len(sorted_brands)) if sorted_brands else total_slots
    
    for brand in sorted_brands:
        brand_products = brand_groups[brand]
        # Add products from this brand (cycling if needed)
        brand_cycle = cycle(brand_products)
        for _ in range(min(products_per_brand, total_slots - len(grid))):
            if len(grid) < total_slots:
                grid.append(next(brand_cycle))
    
    # Fill remaining slots with best sellers from any brand
    if len(grid) < total_slots:
        all_remaining = []
        for brand in sorted_brands:
            all_remaining.extend(brand_groups[brand])
        # Sort all remaining by sales
        all_remaining.sort(key=lambda p: getattr(p[0], 'total_qty', 0), reverse=True)
        remaining_cycle = cycle(all_remaining)
        
        while len(grid) < total_slots:
            grid.append(next(remaining_cycle))
    
    # Ensure no None values
    if len(grid) < total_slots:
        # Fill with cycling through all products
        all_tpa_cycle = cycle(tpa_products)
        while len(grid) < total_slots:
            grid.append(next(all_tpa_cycle))
    
    return grid[:total_slots]  # Ensure exact slot count
