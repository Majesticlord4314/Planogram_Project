from collections import defaultdict

def extract_color_from_name(name):
    # Looks for color after last hyphen or common Apple color names
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

def arrange_section(products, slots, cols, group_clear_columnwise=True, group_by_brand=False):
    def get_color_name(product):
        name = getattr(product, 'product_name', '')
        return extract_color_from_name(name)

    def is_clear_case(product):
        name = getattr(product, 'product_name', '').lower()
        subcat = getattr(product, 'subcategory', '').lower()
        return 'clear' in name or 'clear' in subcat

    # Sort products by sales_velocity (descending)
    sorted_products = sorted(products, key=lambda p: getattr(p[0], 'sales_velocity', 0), reverse=True)
    # Group clear and non-clear
    clear_cases = [p for p in sorted_products if is_clear_case(p[0])]
    color_cases = [p for p in sorted_products if not is_clear_case(p[0])]
    # Further group by color
    color_groups = defaultdict(list)
    for p in color_cases:
        color = get_color_name(p[0])
        color_groups[color].append(p)
    # For clear cases, group by color as well (some clear cases have tints)
    clear_color_groups = defaultdict(list)
    for p in clear_cases:
        color = get_color_name(p[0])
        clear_color_groups[color].append(p)
    import random
    import logging
    logger = logging.getLogger("arrangement_utils")
    # Prepare grid
    rows = slots // cols
    grid = [[None for _ in range(cols)] for _ in range(rows)]
    # Assign clear cases to leftmost columns
    clear_cols = min(len(clear_cases), cols // 2) if group_clear_columnwise else 0
    clear_idx = 0
    # Fill clear cases column-wise
    for c in range(clear_cols):
        for r in range(rows):
            if clear_idx < len(clear_cases):
                grid[r][c] = clear_cases[clear_idx]
                clear_idx += 1
    # Fill remaining slots with color cases, maximizing color diversity and symmetry
    # --- Main Arrangement Logic ---
    # Sort color groups by total sales velocity, not just size
    color_sales = {k: sum(p[0].sales_velocity for p in color_groups[k]) for k in color_groups}
    logger.debug(f"Color sales velocity: {color_sales}")
    color_keys = sorted(color_groups, key=lambda k: color_sales[k], reverse=True)

    if group_by_brand:
        brand_groups = defaultdict(list)
        for p in products:
            brand_groups[getattr(p[0], 'brand', 'Unknown')].append(p)

        sorted_brands = sorted(brand_groups.keys(), key=lambda b: sum(p[0].sales_velocity for p in brand_groups[b]), reverse=True)
        
        all_brand_products = [] 
        for brand in sorted_brands:
            all_brand_products.extend(sorted(brand_groups[brand], key=lambda p: p[0].sales_velocity, reverse=True))

        # Fill grid with brand-grouped products
        for i in range(slots):
            if i < len(all_brand_products):
                grid[i // cols][i % cols] = all_brand_products[i]
            else: # Cycle if not enough products
                grid[i // cols][i % cols] = all_brand_products[i % len(all_brand_products)]
    else:
        # --- Original Color-First Arrangement Logic (for Apple) ---
        color_iters = {k: iter(color_groups[k]) for k in color_keys}
        color_cycle = color_keys[:]
        color_ptr = 0
        for r in range(rows):
            for c in range(clear_cols, cols):
                placed = False
                # Try to alternate colors for diversity
                for _ in range(len(color_cycle)):
                    color = color_cycle[color_ptr % len(color_cycle)]
                    color_ptr += 1
                    try:
                        prod = next(color_iters[color])
                        grid[r][c] = prod
                        placed = True
                        break
                    except StopIteration:
                        continue
                if not placed:
                    # If all groups exhausted, fill with top sellers
                    for k in color_keys:
                        if color_groups[k]:
                            grid[r][c] = color_groups[k].pop()
                            placed = True
                            break
                # If still not placed, fill with any available product (cycle through all products)
                if not placed:
                    unique_products = [p for p in color_cases] + clear_cases
                    if unique_products:
                        idx = ((r * cols + c) - clear_cols * rows) % len(unique_products)
                        grid[r][c] = unique_products[idx]
                    else:
                        grid[r][c] = None
        # Central symmetry: swap columns if needed to mirror left/right
        for r in range(rows):
            for c in range(cols // 2):
                left = grid[r][c]
                right = grid[r][cols-1-c]
                if left and right and get_color_name(left[0]) != get_color_name(right[0]):
                    # Swap to match colors if possible
                    grid[r][c], grid[r][cols-1-c] = right, left
    # Flatten grid row-wise
    arranged = [grid[r][c] for r in range(rows) for c in range(cols)]
    # Fill any remaining None with cycling products (as last resort)
    if any(x is None for x in arranged):
        unique_products = [p for p in color_cases] + clear_cases
        if unique_products:
            for i in range(len(arranged)):
                if arranged[i] is None:
                    arranged[i] = unique_products[i % len(unique_products)]
        else:
            logger.warning("No products available to fill planogram section!")
    # Warn if unique products < slots
    if len(set(id(p[0]) for p in color_cases + clear_cases)) < slots:
        logger.warning(f"Not enough unique products to fill all slots ({len(set(id(p[0]) for p in color_cases + clear_cases))} unique, {slots} slots). Some products will repeat.")
    return arranged
