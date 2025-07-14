import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib import patches
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from pathlib import Path
from src.models.product import Product
from src.utils.logger import get_logger

def load_mac_products():
    """Load Mac accessories from mac-accessories-transformed.csv"""
    mac_file = Path("data/raw/accessories/mac-accessories-transformed.csv")
    
    if not mac_file.exists():
        raise FileNotFoundError(f"Mac data file not found: {mac_file}")
    
    df = pd.read_csv(mac_file)
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
            'frequency': row['frequency'],
            'total_qty': row['frequency'],
        })()
        products.append(product)
    
    return products

def create_mac_planogram(products: List[Product], store_template: 'Store') -> None:
    """Create Mac accessories planograms like iPhone/Watch structure"""
    logger = get_logger()
    logger.info(f"Creating Mac accessories planograms for {store_template.store_type} store...")
    
    try:
        # Load Mac products
        all_products = load_mac_products()
        logger.info(f"Loaded {len(all_products)} Mac products")
        
        # Create planogram 1: Sleeves & Bags
        create_mac_sleeves_bags_planogram(all_products, store_template)
        
        # Create planogram 2: Accessories by category  
        create_mac_accessories_planogram(all_products, store_template)
        
        logger.info(f"Successfully created Mac planograms for {store_template.store_type} store")
        print(f"Mac planograms generated for {store_template.store_type} store:")
        print(f"  mac_sleeves_bags_{store_template.store_type}.png")
        print(f"  mac_accessories_{store_template.store_type}.png")
        
    except Exception as e:
        logger.error(f"Error creating Mac planograms: {e}")
        print(f"Error creating Mac planograms: {e}")

def create_mac_sleeves_bags_planogram(all_products, store_template, figsize: Tuple[int, int] = (20, 16)):
    """Create sleeves & bags planogram: 4 rows sleeves + 1 row bags"""
    logger = get_logger()
    
    # Filter sleeves and bags
    sleeves = [p for p in all_products if p.category == 'sleeve']
    bags = [p for p in all_products if p.category == 'bag']
    
    # Sort by frequency
    sleeves.sort(key=lambda p: p.frequency, reverse=True)
    bags.sort(key=lambda p: p.frequency, reverse=True)
    
    logger.info(f"Found {len(sleeves)} sleeves and {len(bags)} bags")
    
    # Fixed layout: 4 rows sleeves (3 per row) + 1 row bags (4 per row)
    sleeve_cols = 3
    bag_cols = 4
    sleeve_rows = 4
    bag_rows = 1
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor('#F8F9FA')
    ax.set_xlim(0, 280)
    ax.set_ylim(0, 240)
    ax.axis('off')
    
    # Title
    title_color = '#1D1D1F'
    ax.text(140, 225, f"Mac Sleeves & Bags - {store_template.store_type.title()} Store", 
            fontsize=20, fontweight='bold', ha='center', va='center', color=title_color)
    
    # Draw sleeves section (4 rows, 3 per row)
    sleeves_y_start = 180
    draw_sleeves_section_proper(ax, sleeves, y_start=sleeves_y_start, rows=sleeve_rows, cols=sleeve_cols)
    
    # Calculate bags position to avoid overlap
    # Sleeves: 4 rows * (22 height + 8 spacing) = 120 pixels
    # So bags should start at least 120 pixels below sleeves start
    bags_y_start = sleeves_y_start - (sleeve_rows * (22 + 8)) - 15  # Extra 15px gap
    draw_bags_section_proper(ax, bags, y_start=bags_y_start, rows=bag_rows, cols=bag_cols)
    
    # Add section labels
    ax.text(25, sleeves_y_start + 15, "SLEEVES", fontsize=16, fontweight='bold', color=title_color)
    ax.text(25, bags_y_start + 15, "BAGS", fontsize=16, fontweight='bold', color=title_color)
    
    # Add summary
    total_sleeves = len(sleeves)
    total_bags = len(bags)
    total_sales = sum(p.frequency for p in sleeves) + sum(p.frequency for p in bags)
    
    ax.text(200, 35, f"Sleeves: {total_sleeves} | Bags: {total_bags}", fontsize=12, 
           ha='left', va='center', color=title_color, weight='medium')
    ax.text(200, 25, f"Total Sales: {total_sales:,}", fontsize=12, 
           ha='left', va='center', color=title_color, weight='medium')
    
    # Add legend
    star_legend = patches.Circle((200, 15), 2.5, color='gold', alpha=0.9)
    ax.add_patch(star_legend)
    ax.text(210, 15, "High Sales", fontsize=10, ha='left', va='center', color=title_color)
    
    # Save planogram
    output_path = Path("output") / f"mac_sleeves_bags_{store_template.store_type}.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info(f"Saved sleeves & bags planogram: {output_path}")

def create_mac_accessories_planogram(all_products, store_template, figsize: Tuple[int, int] = (20, 16)):
    """Create accessories planogram with proper grouping and spacing"""
    logger = get_logger()
    
    # Filter accessories (exclude sleeves and bags)
    accessories = [p for p in all_products if p.category not in ['sleeve', 'bag']]
    
    # Group by category
    category_groups = {
        'privacy filter': [],
        'cleaning': [],
        'hardshell case': [],
        'hub': [],
        'cable': [],
        'charger': [],
        'storage': [],
        'stand': [],
        'peripheral': [],
        'keyboard skin': [],
        'accessory': []
    }
    
    # Group products
    for product in accessories:
        if product.category in category_groups:
            category_groups[product.category].append(product)
    
    # Remove empty groups and sort by frequency within groups
    category_groups = {k: sorted(v, key=lambda p: p.frequency, reverse=True) 
                      for k, v in category_groups.items() if v}
    
    logger.info(f"Found accessories in {len(category_groups)} categories")
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor('#F8F9FA')
    ax.set_xlim(0, 280)
    ax.set_ylim(0, 240)
    ax.axis('off')
    
    # Title
    title_color = '#1D1D1F'
    ax.text(140, 225, f"Mac Accessories - {store_template.store_type.title()} Store", 
            fontsize=20, fontweight='bold', ha='center', va='center', color=title_color)
    
    # Draw category sections with proper spacing
    draw_accessories_sections(ax, category_groups, store_template)
    
    # Add summary
    total_accessories = sum(len(group) for group in category_groups.values())
    total_sales = sum(p.frequency for group in category_groups.values() for p in group)
    
    ax.text(200, 35, f"Products: {total_accessories}", fontsize=12, 
           ha='left', va='center', color=title_color, weight='medium')
    ax.text(200, 25, f"Total Sales: {total_sales:,}", fontsize=12, 
           ha='left', va='center', color=title_color, weight='medium')
    
    # Add legend
    star_legend = patches.Circle((200, 15), 2.5, color='gold', alpha=0.9)
    ax.add_patch(star_legend)
    ax.text(210, 15, "High Sales", fontsize=10, ha='left', va='center', color=title_color)
    
    # Save planogram
    output_path = Path("output") / f"mac_accessories_{store_template.store_type}.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info(f"Saved accessories planogram: {output_path}")

def draw_sleeves_section_proper(ax, sleeves, y_start, rows, cols):
    """Draw sleeves with proper spacing: 3 per row"""
    sleeve_width = 55  # Smaller than bags (realistic sizing)
    sleeve_height = 22
    x_spacing = 15
    y_spacing = 8
    
    # Calculate total width needed and center the row
    total_width = cols * sleeve_width + (cols - 1) * x_spacing
    available_width = 280 - 100  # Total width minus margins
    x_start = 50 + (available_width - total_width) / 2  # Center the row
    
    for i, sleeve in enumerate(sleeves[:rows * cols]):
        row = i // cols
        col = i % cols
        
        x_pos = x_start + col * (sleeve_width + x_spacing)
        y_pos = y_start - row * (sleeve_height + y_spacing)
        
        # Get color
        color = get_product_color_proper(sleeve)
        
        # Draw sleeve
        sleeve_rect = FancyBboxPatch(
            (x_pos, y_pos), sleeve_width, sleeve_height,
            boxstyle="round,pad=3",
            facecolor=color,
            edgecolor='#86868B',
            linewidth=1.5,
            alpha=0.9
        )
        ax.add_patch(sleeve_rect)
        
        # Add readable text with better formatting
        name = format_product_name_better(sleeve.product_name, sleeve_width, sleeve_height)
        text_color = 'white' if is_dark_color(color) else 'black'
        ax.text(x_pos + sleeve_width/2, y_pos + sleeve_height/2, 
               name, fontsize=9, ha='center', va='center',
               color=text_color, weight='medium', wrap=True)
        
        # Add frequency indicator for high sales
        if sleeve.frequency > 50:
            star = patches.Circle((x_pos + sleeve_width - 5, y_pos + sleeve_height - 4), 
                                3, color='gold', alpha=0.9)
            ax.add_patch(star)

def draw_bags_section_proper(ax, bags, y_start, rows, cols):
    """Draw bags with proper spacing: 4 per row"""
    bag_width = 60  # Slightly smaller to fit 4 per row
    bag_height = 35
    x_spacing = 10
    y_spacing = 8
    
    # Calculate total width needed and center the row
    total_width = cols * bag_width + (cols - 1) * x_spacing
    available_width = 280 - 100  # Total width minus margins
    x_start = 50 + (available_width - total_width) / 2  # Center the row
    
    for i, bag in enumerate(bags[:rows * cols]):
        row = i // cols
        col = i % cols
        
        x_pos = x_start + col * (bag_width + x_spacing)
        y_pos = y_start - row * (bag_height + y_spacing)
        
        # Get color
        color = get_product_color_proper(bag)
        
        # Draw bag
        bag_rect = FancyBboxPatch(
            (x_pos, y_pos), bag_width, bag_height,
            boxstyle="round,pad=3",
            facecolor=color,
            edgecolor='#86868B',
            linewidth=1.5,
            alpha=0.9
        )
        ax.add_patch(bag_rect)
        
        # Add readable text with better formatting
        name = format_product_name_better(bag.product_name, bag_width, bag_height)
        text_color = 'white' if is_dark_color(color) else 'black'
        ax.text(x_pos + bag_width/2, y_pos + bag_height/2, 
               name, fontsize=9, ha='center', va='center',
               color=text_color, weight='medium', wrap=True)
        
        # Add frequency indicator for high sales
        if bag.frequency > 30:
            star = patches.Circle((x_pos + bag_width - 4, y_pos + bag_height - 4), 
                                2.5, color='gold', alpha=0.9)
            ax.add_patch(star)

def draw_accessories_sections(ax, category_groups, store_template):
    """Draw accessories with proper grouping and spacing"""
    
    # Determine layout based on store type
    if store_template.store_type.lower() == 'flagship':
        max_products_per_category = 6
        max_rows = 8
    elif store_template.store_type.lower() == 'standard':
        max_products_per_category = 5
        max_rows = 6
    else:  # express
        max_products_per_category = 4
        max_rows = 5
    
    y_start = 190
    row_height = 22
    row_spacing = 8
    current_y = y_start
    
    # Category display names
    category_names = {
        'privacy filter': 'Privacy Filters',
        'cleaning': 'Cleaners',
        'hardshell case': 'Hardshell Cases',
        'hub': 'Hubs & Adapters',
        'cable': 'Cables',
        'charger': 'Chargers & Power',
        'storage': 'Storage',
        'stand': 'Stands',
        'peripheral': 'Peripherals',
        'keyboard skin': 'Keyboard Skins',
        'accessory': 'General Accessories'
    }
    
    rows_drawn = 0
    for category, products in category_groups.items():
        if rows_drawn >= max_rows or current_y < 50:
            break
            
        if not products:
            continue
            
        # Draw category label
        display_name = category_names.get(category, category.title())
        ax.text(30, current_y + 5, display_name, fontsize=12, fontweight='bold', 
               color='#1D1D1F', va='center')
        
        # Draw products in this category
        draw_category_products(ax, products[:max_products_per_category], current_y, category)
        
        current_y -= (row_height + row_spacing)
        rows_drawn += 1

def draw_category_products(ax, products, y_pos, category):
    """Draw products in a category with proper spacing and centering"""
    x_spacing = 12
    
    # Size based on category
    if category in ['privacy filter', 'hardshell case']:
        width, height = 40, 18
    elif category in ['cleaning', 'charger']:
        width, height = 30, 15
    else:
        width, height = 35, 16
    
    # Determine how many products we can fit (max 6)
    max_products = min(len(products), 6)
    
    # Calculate total width needed for centering
    total_products_width = max_products * width + (max_products - 1) * x_spacing
    available_width = 280 - 100  # Total width minus margins
    x_start = 50 + (available_width - total_products_width) / 2  # Center the row
    
    for i, product in enumerate(products):
        if i >= max_products:
            break
            
        x_pos = x_start + i * (width + x_spacing)
        
        # Get color
        color = get_product_color_proper(product)
        
        # Draw product
        product_rect = FancyBboxPatch(
            (x_pos, y_pos), width, height,
            boxstyle="round,pad=2",
            facecolor=color,
            edgecolor='#86868B',
            linewidth=1,
            alpha=0.9
        )
        ax.add_patch(product_rect)
        
        # Add readable text with better formatting
        if width < 35:
            # For narrow products, use shorter names and rotate
            name = format_product_name_better(product.product_name, width, height, rotation=90)
            font_size = 7
            rotation = 90
        else:
            # For wider products, use longer names
            name = format_product_name_better(product.product_name, width, height)
            font_size = 8
            rotation = 0
            
        text_color = 'white' if is_dark_color(color) else 'black'
        
        ax.text(x_pos + width/2, y_pos + height/2, 
               name, fontsize=font_size, ha='center', va='center',
               color=text_color, weight='medium', rotation=rotation, wrap=True)
        
        # Add frequency indicator for high sales
        if product.frequency > 100:
            star = patches.Circle((x_pos + width - 3, y_pos + height - 3), 
                                2, color='gold', alpha=0.9)
            ax.add_patch(star)

def get_product_color_proper(product):
    """Get product color from subcategory with better color mapping"""
    subcategory = str(getattr(product, 'subcategory', 'Default'))
    
    # Enhanced color mapping
    color_map = {
        'Black': '#2C2C2E',
        'Blue': '#007AFF', 
        'Red': '#FF3B30',
        'Green': '#34C759',
        'Yellow': '#FFCC00',
        'Purple': '#AF52DE',
        'Pink': '#FF2D92',
        'Orange': '#FF9500',
        'Grey': '#8E8E93',
        'Gray': '#8E8E93',
        'White': '#F2F2F7',
        'Brown': '#A2845E',
        'Beige': '#F5DEB3',
        'Frost': '#E8F4FD',
        'Smoke': '#696969',
        'Cognac': '#A0522D',
        'Gold': '#FFD700',
        'Silver': '#C0C0C0',
        'Clear': '#F0F0F0',
        'Default': '#E5E5EA'
    }
    
    # Try to match subcategory to color
    for color_name, color_code in color_map.items():
        if color_name.lower() in subcategory.lower():
            return color_code
    
    # Fallback to category-based colors
    category_colors = {
        'sleeve': '#E3F2FD',
        'bag': '#FFF3E0',
        'cleaning': '#E8F5E8',
        'privacy filter': '#F3E5F5',
        'hub': '#FFF8E1',
        'cable': '#FFEBEE',
        'charger': '#F1F8E9',
        'hardshell case': '#E0F2F1',
        'storage': '#FCE4EC',
        'peripheral': '#F9FBE7',
        'stand': '#EDE7F6',
        'accessory': '#FFF9C4',
        'keyboard skin': '#F3E5F5'
    }
    
    return category_colors.get(product.category, '#E5E5EA')

def is_dark_color(color_hex):
    """Determine if a color is dark (for text color selection)"""
    # Remove # if present
    color_hex = color_hex.lstrip('#')
    
    # Convert to RGB
    try:
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        
        # Calculate brightness
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 128
    except:
        return False

def format_product_name_better(name, width, height, rotation=0):
    """Format product name to fit within box dimensions with proper wrapping"""
    # Calculate approximate characters that fit based on box dimensions
    # For font size 8-9, approximately 1 char per 6-7 pixels width
    char_width = 6.5
    
    if rotation == 90:
        # For rotated text, width and height are swapped
        max_chars_per_line = max(1, int(height / char_width))
        max_lines = max(1, int(width / 12))  # 12px per line height
    else:
        max_chars_per_line = max(1, int(width / char_width))
        max_lines = max(1, int(height / 12))  # 12px per line height
    
    # Extract meaningful parts from the product name
    formatted_name = extract_meaningful_product_info(name, max_chars_per_line, max_lines)
    
    # Split into words for intelligent wrapping
    words = formatted_name.split()
    
    # Try to fit in multiple lines if needed
    lines = []
    current_line = ""
    
    for word in words:
        # Check if adding this word would exceed line length
        test_line = current_line + (" " if current_line else "") + word
        
        if len(test_line) <= max_chars_per_line:
            current_line = test_line
        else:
            # Start new line if we haven't exceeded max lines
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Word is too long, truncate it
                current_line = word[:max_chars_per_line]
            
            # Check if we've reached max lines
            if len(lines) >= max_lines:
                break
    
    # Add the last line if it exists and we have space
    if current_line and len(lines) < max_lines:
        lines.append(current_line)
    
    # Join lines with newlines
    result = "\n".join(lines[:max_lines])
    
    # If we still have nothing meaningful, use the original name truncated
    if not result or len(result.replace('\n', '').strip()) < 3:
        if rotation == 90:
            # For rotated text, use fewer characters
            return name[:max(3, max_chars_per_line)]
        else:
            return name[:max(3, max_chars_per_line * max_lines)]
    
    return result

def extract_meaningful_product_info(name, max_chars_per_line, max_lines):
    """Extract brand + key product information from long product names"""
    # Calculate total available characters
    total_chars = max_chars_per_line * max_lines
    
    # Clean common noise
    name = name.replace('13.3', '13').replace('15.6', '15').replace('14.2', '14')
    name = name.replace(' inch', '"').replace('-inch', '"')
    
    # Split into words
    words = name.split()
    
    # Identify brand (usually first word or common brands)
    common_brands = ['Tucano', 'Gripp', 'RIVACASE', 'tomtoc', 'Belkin', 'ALOGIC', 'Pulse', 'Native', 'AmazingThing', 'AT']
    brand = ""
    remaining_words = []
    
    # Find brand in the name
    for i, word in enumerate(words):
        if word in common_brands or (i == 0 and len(word) > 2):
            brand = word
            remaining_words = words[i+1:]
            break
    
    if not brand:
        brand = words[0] if words else ""
        remaining_words = words[1:]
    
    # Identify key product descriptors
    key_descriptors = ['Sleeve', 'Bag', 'Case', 'Hub', 'Cable', 'Charger', 'Filter', 'Stand', 'Storage', 
                      'Adapter', 'Dock', 'Pro', 'Air', 'Max', 'Mini', 'USB-C', 'HDMI', 'Wireless',
                      'Hardshell', 'Cleaning', 'Privacy', 'Multi', 'Power', 'Magnetic', 'Folding']
    
    # Find the most important descriptors
    important_words = []
    for word in remaining_words:
        word_clean = word.replace('(', '').replace(')', '').replace('-', '').replace(':', '')
        if any(desc.lower() in word_clean.lower() for desc in key_descriptors):
            important_words.append(word_clean)
        elif word_clean in ['13', '14', '15', '16', '13"', '14"', '15"', '16"']:
            important_words.append(word_clean)
        elif word_clean in ['Black', 'Blue', 'Red', 'Green', 'Brown', 'Grey', 'White', 'Silver', 'Gold', 'Space']:
            important_words.append(word_clean)
    
    # Build the result
    result_parts = [brand]
    
    # Add important descriptors that fit
    current_length = len(brand)
    for word in important_words:
        if current_length + len(word) + 1 <= total_chars - 2:  # Leave some buffer
            result_parts.append(word)
            current_length += len(word) + 1
        else:
            break
    
    # If we only have brand, try to add at least one more meaningful word
    if len(result_parts) == 1 and remaining_words:
        for word in remaining_words:
            if len(word) > 2 and current_length + len(word) + 1 <= total_chars:
                result_parts.append(word)
                break
    
    return " ".join(result_parts)

def format_product_name(name, max_chars=20):
    """Format product name to be more readable with intelligent line breaks"""
    # Remove common prefixes/suffixes that add clutter
    name = name.replace('Laptop ', '').replace(' Laptop', '')
    name = name.replace('MacBook ', '').replace(' MacBook', '')
    name = name.replace('Apple ', '').replace(' Apple', '')
    name = name.replace('13.3', '13').replace('15.6', '15').replace('14.2', '14')
    name = name.replace(' inch', '"').replace('-inch', '"')
    
    # If name is short enough, return as is
    if len(name) <= max_chars:
        return name
    
    # Try to create a meaningful short version
    words = name.split()
    
    # Keep brand and main product type
    if len(words) >= 2:
        brand = words[0]
        
        # Try to find the main product descriptor
        descriptors = ['Sleeve', 'Bag', 'Case', 'Hub', 'Cable', 'Charger', 'Filter', 'Stand', 'Storage']
        main_descriptor = ""
        
        for word in words[1:]:
            for desc in descriptors:
                if desc.lower() in word.lower():
                    main_descriptor = desc
                    break
            if main_descriptor:
                break
        
        # Create short version
        if main_descriptor:
            short_name = f"{brand} {main_descriptor}"
            
            # Add color or size if there's room
            remaining_chars = max_chars - len(short_name) - 1
            if remaining_chars > 3:
                for word in words:
                    if word in ['Black', 'Blue', 'Red', 'Green', 'Brown', 'Grey', 'White', 'Silver', 'Gold']:
                        if len(word) <= remaining_chars:
                            short_name += f" {word}"
                            break
                    elif word in ['13', '14', '15', '16', '13"', '14"', '15"', '16"']:
                        if len(word) <= remaining_chars:
                            short_name += f" {word}"
                            break
            
            return short_name
    
    # Fallback: intelligent truncation
    if len(name) > max_chars:
        # Try to break at word boundary
        words = name.split()
        result = ""
        for word in words:
            if len(result + " " + word) <= max_chars - 2:
                if result:
                    result += " " + word
                else:
                    result = word
            else:
                break
        
        if result and len(result) > 8:  # Make sure we have something meaningful
            return result + ".."
        else:
            return name[:max_chars-2] + ".."
    
    return name

def truncate_name_proper(name, max_length):
    """Legacy function for backwards compatibility"""
    return format_product_name(name, max_length)
