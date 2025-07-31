
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from typing import List, Dict, Tuple
from src.models.product import Product
import textwrap
import os
from datetime import datetime

def extract_product_category(name: str) -> str:
    """Extracts the category (e.g., Clear, Magsafe, Armor) from a product name."""
    name_lower = name.lower()
    if 'clear' in name_lower:
        return 'Clear'
    if 'magsafe' in name_lower:
        return 'MagSafe'
    if 'armor' in name_lower or 'rugged' in name_lower:
        return 'Armor'
    if 'screen' in name_lower or 'glass' in name_lower:
        return 'Screen Protector'
    if 'lens' in name_lower:
        return 'Lens Protector'
    return 'Standard'

def create_advanced_planogram(products: List[Product], store_template: 'Store', wall_config: Dict, output_filename: str):
    """
    Creates a single, advanced planogram wall with detailed product info and aesthetics.
    """
    from src.utils.logger import get_logger
    logger = get_logger()

    fig, ax = plt.subplots(figsize=(20, 14))
    ax.set_facecolor('#F5F5F7')

    # Layout parameters
    cols = wall_config.get('cols', 5)
    rows = wall_config.get('rows', 6)
    product_width = 2.5
    product_height = 4.5
    gap_x, gap_y = 0.6, 0.8

    total_width = cols * product_width + (cols - 1) * gap_x
    total_height = rows * product_height + (rows - 1) * gap_y
    ax.set_xlim(-1, total_width + 1)
    ax.set_ylim(-1, total_height + 1)

    # Draw products
    for i, product_data in enumerate(wall_config['products']):
        if not product_data:
            continue

        row = i // cols
        col = i % cols
        x = col * (product_width + gap_x)
        y = total_height - (row + 1) * product_height - row * gap_y

        product, facings = product_data
        brand = getattr(product, 'brand', 'N/A')
        series = getattr(product, 'series', 'N/A')
        color = extract_color_from_name(getattr(product, 'product_name', ''))
        category = extract_product_category(getattr(product, 'product_name', ''))

        # Product Box
        case_color = get_color_for_product(color)
        box = FancyBboxPatch((x, y), product_width, product_height, boxstyle="round,pad=0.02,rounding_size=0.1",
                             facecolor=case_color, edgecolor='#DDDDDD', linewidth=1, alpha=0.9)
        ax.add_patch(box)

        # Product Info
        text_color = '#FFFFFF' if is_dark(case_color) else '#000000'
        ax.text(x + product_width / 2, y + product_height - 0.5, brand.upper(),
                fontsize=10, color=text_color, ha='center', weight='bold')
        ax.text(x + product_width / 2, y + product_height - 1.1, series,
                fontsize=8, color=text_color, ha='center')
        ax.text(x + product_width / 2, y + 0.8, f"{color} ({category})",
                fontsize=8, color=text_color, ha='center')

    # Title
    ax.set_title(wall_config['title'], fontsize=18, weight='bold', pad=20)
    ax.axis('off')
    fig.tight_layout()

    # Save
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    logger.info(f"Saved planogram to {output_filename}")
    plt.close(fig)

def get_color_for_product(color_name: str) -> str:
    """Returns a hex code for a given color name."""
    color_map = {
        'black': '#202020', 'blue': '#0A3D91', 'green': '#006633',
        'red': '#BF0A30', 'pink': '#FF69B4', 'purple': '#4B0082',
        'yellow': '#FFD700', 'white': '#FFFFFF', 'clear': '#EFEFEF',
        'gray': '#808080', 'silver': '#C0C0C0', 'gold': '#FFD700'
    }
    return color_map.get(color_name.lower(), '#CCCCCC')

def is_dark(hex_color: str) -> bool:
    """Checks if a hex color is dark."""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return luminance < 0.5

def extract_color_from_name(name: str) -> str:
    """Extracts a color from a product name."""
    # This is a simplified version. A more robust implementation would be needed.
    colors = ['Black', 'Blue', 'Green', 'Red', 'Pink', 'Purple', 'Yellow', 'White', 'Clear', 'Gray', 'Silver', 'Gold']
    for color in colors:
        if color.lower() in name.lower():
            return color
    return 'Gray'
