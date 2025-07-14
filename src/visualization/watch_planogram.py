import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib import patches
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import textwrap
import os

def extract_color_from_watch_name(name):
    """Extract color from watch product name"""
    color_keywords = [
        'Black', 'White', 'Silver', 'Gold', 'Rose Gold', 'Blue', 'Red', 'Green', 'Pink', 'Purple', 
        'Yellow', 'Orange', 'Gray', 'Grey', 'Brown', 'Tan', 'Olive', 'Navy', 'Midnight', 'Starlight',
        'Space Gray', 'Graphite', 'Pacific Blue', 'Sierra Blue', 'Alpine Green', 'Product Red',
        'Deep Purple', 'Dynamic Island', 'Storm Blue', 'Winter Blue', 'Spring Yellow', 'Canary Yellow',
        'Electric Orange', 'Dark Cherry', 'Clover', 'Forest Green', 'Jade', 'Mint', 'Seafoam',
        'Lavender', 'Light Pink', 'Flamingo', 'Coral', 'Grapefruit', 'Pomegranate', 'Plum',
        'Eggplant', 'Grape', 'Violet', 'Indigo', 'Cerulean', 'Capri Blue', 'Azure', 'Sky Blue',
        'Ice Blue', 'Powder Blue', 'Denim', 'Steel Blue', 'Teal', 'Pine Green', 'Moss Green',
        'Lime', 'Chartreuse', 'Lemon', 'Sunshine', 'Amber', 'Honey', 'Butterscotch', 'Caramel',
        'Cognac', 'Saddle Brown', 'Coffee', 'Espresso', 'Chocolate', 'Cocoa', 'Mahogany',
        'Burgundy', 'Wine', 'Crimson', 'Scarlet', 'Cherry', 'Rose', 'Blush', 'Cream', 'Ivory',
        'Pearl', 'Snow', 'Fog', 'Smoke', 'Ash', 'Charcoal', 'Jet', 'Onyx', 'Obsidian',
        'Khaki', 'Sage', 'Cypress', 'Stone', 'Clay', 'Sand', 'Beige', 'Taupe', 'Mushroom',
        'Pride', 'Rainbow', 'Multi', 'Clear', 'Transparent', 'Frosted', 'Matte', 'Glossy',
        'Metallic', 'Satin', 'Brushed', 'Polished', 'Antique', 'Vintage', 'Retro', 'Classic',
        'Modern', 'Sport', 'Casual', 'Formal', 'Luxury', 'Premium', 'Standard', 'Basic',
        'Blue Horizon', 'Magic Ember', 'Midnight Sky', 'Cargo Khaki', 'Desert Stone', 'Bright Green',
        'Spearmint', 'Blue Flame', 'Light Green', 'Mavau Pink', 'Wine Red', 'Camel'
    ]
    
    name_lower = name.lower()
    for color in color_keywords:
        if color.lower() in name_lower:
            return color
    
    # Fallback: try to extract from product name patterns
    if '-' in name:
        parts = name.split('-')
        for part in parts:
            part = part.strip()
            if len(part) > 2 and not part.isdigit():
                return part
    
    return ''

def load_watch_products():
    """Load Apple Watch products from combined_watch.csv"""
    watch_file = Path("data/raw/accessories/combined_watch.csv")
    
    if not watch_file.exists():
        raise FileNotFoundError(f"Watch data file not found: {watch_file}")
    
    df = pd.read_csv(watch_file)
    # Clean column names and values
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # Convert to product-like objects with required attributes
    products = []
    for _, row in df.iterrows():
        product = type('Product', (), {
            'product_name': row['product_name'],
            'brand': row['brand'],
            'category': row['category'],
            'subcategory': row['subcategory'],
            'width': row['width'],
            'height': row['height'],
            'depth': row['depth'],
            'frequency': row['frequency'],  # This is our sales data
            'total_qty': row['frequency'],  # Use frequency as total_qty for compatibility
        })()
        products.append(product)
    
    return products

def create_watch_planogram(store_template: 'Store', figsize: Tuple[int, int] = (20, 14)):
    """Create Apple Watch planograms for different store templates"""
    from src.utils.logger import get_logger
    logger = get_logger()
    logger.info(f"Generating Apple Watch planogram for store '{store_template.store_name}'.")
    
    # Load watch products
    try:
        all_products = load_watch_products()
        logger.info(f"Loaded {len(all_products)} watch products from combined_watch.csv")
    except Exception as e:
        logger.error(f"Failed to load watch products: {e}")
        return None
    
    # Filter Apple and TPA products
    apple_products = [p for p in all_products if 'apple' in p.brand.lower()]
    tpa_products = [p for p in all_products if 'apple' not in p.brand.lower()]
    
    logger.info(f"Found {len(apple_products)} Apple and {len(tpa_products)} TPA watch products.")
    
    if not apple_products and not tpa_products:
        logger.warning("No watch products found.")
        return None
    
    # Store template specific configurations
    store_type = store_template.store_type.lower()
    if store_type == 'flagship':
        cols = 10
        total_rows = 6  # 3 rows Apple + 3 rows TPA
        apple_rows = 3
        tpa_rows = 3
    else:  # standard and express
        cols = 6
        total_rows = 6  # 2 rows Apple + 4 rows TPA
        apple_rows = 2
        tpa_rows = 4
    
    # Sort products by frequency (sales)
    apple_products.sort(key=lambda p: p.frequency, reverse=True)
    tpa_products.sort(key=lambda p: p.frequency, reverse=True)
    
    # Calculate slots
    apple_slots = apple_rows * cols
    tpa_slots = tpa_rows * cols
    total_slots = apple_slots + tpa_slots
    
    # Arrange products
    apple_grid = arrange_apple_watch_products(apple_products, apple_slots, cols, apple_rows)
    tpa_grid = arrange_tpa_watch_products(tpa_products, tpa_slots, cols, tpa_rows)
    
    # Create the planogram
    create_watch_planogram_visual(
        apple_grid, tpa_grid, store_template, 
        apple_rows, tpa_rows, cols, figsize
    )

def arrange_apple_watch_products(apple_products, total_slots, cols, rows):
    """Arrange Apple Watch products with diversity"""
    if not apple_products:
        return [None] * total_slots
    
    # Group by category and subcategory for diversity
    category_groups = {}
    for product in apple_products:
        key = f"{product.category}_{product.subcategory}"
        if key not in category_groups:
            category_groups[key] = []
        category_groups[key].append(product)
    
    # Sort each group by frequency and get diverse selection
    diverse_products = []
    for category, products in category_groups.items():
        products.sort(key=lambda p: p.frequency, reverse=True)
        diverse_products.extend(products[:3])  # Take top 3 from each category
    
    # Sort final selection by frequency
    diverse_products.sort(key=lambda p: p.frequency, reverse=True)
    
    # If we need more products, add from remaining
    if len(diverse_products) < total_slots:
        remaining = [p for p in apple_products if p not in diverse_products]
        diverse_products.extend(remaining[:total_slots - len(diverse_products)])
    
    # Create grid
    grid = []
    for i in range(total_slots):
        if diverse_products:
            grid.append(diverse_products[i % len(diverse_products)])
        else:
            grid.append(None)
    
    return grid[:total_slots]

def arrange_tpa_watch_products(tpa_products, total_slots, cols, rows):
    """Arrange TPA Watch products with brand diversity"""
    if not tpa_products:
        return [None] * total_slots
    
    # Group by brand
    brand_groups = {}
    for product in tpa_products:
        brand = product.brand
        if brand not in brand_groups:
            brand_groups[brand] = []
        brand_groups[brand].append(product)
    
    # Sort each brand group by frequency
    for brand in brand_groups:
        brand_groups[brand].sort(key=lambda p: p.frequency, reverse=True)
    
    # Sort brands by their total frequency
    brand_totals = {}
    for brand, products in brand_groups.items():
        brand_totals[brand] = sum(p.frequency for p in products)
    
    sorted_brands = sorted(brand_groups.keys(), key=lambda b: brand_totals[b], reverse=True)
    
    # Create brand-grouped arrangement
    grid = []
    products_per_brand = max(1, total_slots // len(sorted_brands)) if sorted_brands else total_slots
    
    for brand in sorted_brands:
        brand_products = brand_groups[brand]
        for i in range(min(products_per_brand, total_slots - len(grid))):
            if len(grid) < total_slots and i < len(brand_products):
                grid.append(brand_products[i])
    
    # Fill remaining slots
    if len(grid) < total_slots:
        all_remaining = []
        for brand in sorted_brands:
            all_remaining.extend(brand_groups[brand])
        all_remaining.sort(key=lambda p: p.frequency, reverse=True)
        
        while len(grid) < total_slots and all_remaining:
            grid.append(all_remaining[len(grid) % len(all_remaining)])
    
    return grid[:total_slots]

def create_watch_planogram_visual(apple_grid, tpa_grid, store_template, apple_rows, tpa_rows, cols, figsize):
    """Create the visual planogram for Apple Watch products"""
    from src.utils.logger import get_logger
    logger = get_logger()
    
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    
    # Calculate dimensions
    product_width = 2.0
    product_height = 1.5
    gap_x = 0.3
    gap_y = 0.3
    
    total_width = cols * product_width + (cols - 1) * gap_x
    total_height = (apple_rows + tpa_rows) * product_height + (apple_rows + tpa_rows - 1) * gap_y
    
    ax.set_xlim(0, total_width)
    ax.set_ylim(0, total_height + 2)
    
    # Brand colors for TPA
    brand_colors = {}
    brand_colors_used = set()
    
    # Draw products
    apple_slots = len(apple_grid)
    total_products = apple_grid + tpa_grid
    
    for i, product in enumerate(total_products):
        if product is None:
            continue
            
        row = i // cols
        col = i % cols
        
        x = col * (product_width + gap_x)
        y = total_height - (row + 1) * product_height - row * gap_y
        
        # Determine color and section
        if i < apple_slots:  # Apple section
            color = '#1f77b4'  # Apple blue
        else:  # TPA section
            brand = getattr(product, 'brand', 'Unknown')
            if brand not in brand_colors:
                brand_colors[brand] = plt.cm.tab20(len(brand_colors) % 20)
            color = brand_colors[brand]
            brand_colors_used.add((brand.title(), color))
        
        # Draw product box
        box = FancyBboxPatch(
            (x, y), product_width, product_height,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor='#333333',
            linewidth=1.2,
            alpha=0.8
        )
        ax.add_patch(box)
        
        # Add text labels
        product_name = getattr(product, 'product_name', 'Unknown Product')
        brand_name = getattr(product, 'brand', 'Unknown')
        category = getattr(product, 'category', 'Unknown')
        subcategory = getattr(product, 'subcategory', 'Unknown')
        
        if i < apple_slots:  # Apple section
            # Show category and size/color
            color_name = extract_color_from_watch_name(product_name)
            display_text = category
            if color_name:
                display_text = f"{color_name} {category}"
            elif subcategory:
                display_text = f"{subcategory} {category}"
            
            ax.text(x + product_width / 2, y + product_height * 0.75, 
                   'Apple', fontsize=8, ha='center', va='center', 
                   color='white', weight='bold')
            ax.text(x + product_width / 2, y + product_height * 0.35, 
                   display_text, fontsize=6, ha='center', va='center', 
                   color='white', linespacing=1.1)
        else:  # TPA section
            # Show brand and color/category
            color_name = extract_color_from_watch_name(product_name)
            display_text = category
            if color_name:
                display_text = f"{color_name} {category}"
            
            ax.text(x + product_width / 2, y + product_height * 0.75, 
                   brand_name, fontsize=7, ha='center', va='center', 
                   color='white', weight='bold')
            ax.text(x + product_width / 2, y + product_height * 0.35, 
                   display_text, fontsize=6, ha='center', va='center', 
                   color='white', linespacing=1.1)
    
    # Add section divider line
    divider_y = total_height - apple_rows * product_height - (apple_rows - 0.5) * gap_y
    ax.axhline(y=divider_y, color='#333333', linewidth=2, alpha=0.7)
    
    # Add section labels
    ax.text(total_width / 2, total_height + 0.5, 'Apple Watch Accessories', 
           fontsize=12, ha='center', va='top', weight='bold', color='black')
    ax.text(total_width / 2, divider_y - 0.3, 'TPA Watch Accessories', 
           fontsize=11, ha='center', va='top', weight='bold', color='black')
    
    # Set title
    ax.set_title(f'Apple Watch Planogram - {store_template.store_name}', 
                fontsize=16, weight='bold', pad=20, color='black')
    
    # Add legend for TPA brands
    if brand_colors_used:
        legend_elements = [patches.Patch(facecolor=color, edgecolor='black', label=brand) 
                          for brand, color in sorted(brand_colors_used)]
        fig.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 0.02), 
                  ncol=min(len(legend_elements), 6), frameon=True, title='TPA Brands',
                  fancybox=True, shadow=True)
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    
    fig.tight_layout(rect=[0, 0.12, 1, 0.95])
    
    # Save the plot
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"{output_dir}/Watch_{store_template.store_name.replace(' ', '_')}_planogram.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    logger.info(f"Saved Apple Watch planogram to {filename}")
    plt.close(fig)
