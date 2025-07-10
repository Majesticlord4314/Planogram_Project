from collections import defaultdict
from itertools import cycle

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

def arrange_section(products, slots, cols, group_clear_columnwise=True, group_by_brand=False, color_columnwise=False, color_rowwise=False, priority_brands=None, brand_columnwise=False):
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
    # If no products passed, return empty placeholders to keep slot count consistent
    if not products:
        return [None] * slots

    # Prepare grid
    rows = slots // cols
    grid = [[None for _ in range(cols)] for _ in range(rows)]
    # Assign clear cases to leftmost columns
    # Apple requirement: at most one clear-case column
    clear_cols = 1 if (group_clear_columnwise and len(clear_cases) > 0) else 0
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

    if len(color_keys) == 0:
        # No coloured products (all clear or empty) – just cycle clear cases / placeholders
        arranged_flat = []
        all_items = clear_cases if clear_cases else [None]
        for i in range(slots):
            arranged_flat.append(all_items[i % len(all_items)])
        return arranged_flat

    if group_by_brand:
        # Column-wise grouping for TPA if requested
        if brand_columnwise:
            # --- Proportional column allocation by brand sales ---
            if priority_brands is None:
                priority_brands = []
            brand_groups = defaultdict(list)
            for p in products:
                brand_groups[getattr(p[0], 'brand', 'Unknown')].append(p)

            # Keep only brands in priority list for display
            ordered_brands = [b for b in priority_brands if b in brand_groups]
            if not ordered_brands:
                ordered_brands = list(brand_groups.keys())  # fallback

            # Compute total sales and per-brand share
            brand_sales = {b: sum(item[0].sales_velocity for item in brand_groups[b]) for b in ordered_brands}
            total_sales = sum(brand_sales.values()) or 1  # avoid div-by-zero
            raw_shares = {b: (brand_sales[b] / total_sales) * cols for b in ordered_brands}
            # Initial integer allocation (at least 1 col each)
            col_alloc = {b: max(1, int(round(raw_shares[b]))) for b in ordered_brands}
            # Adjust allocation to exactly cols total
            while sum(col_alloc.values()) > cols:
                # reduce from smallest share brand >1 col
                b_reduce = min((b for b in col_alloc if col_alloc[b]>1), key=lambda x: col_alloc[x], default=None)
                if b_reduce is None:
                    break
                col_alloc[b_reduce] -= 1
            while sum(col_alloc.values()) < cols:
                # add to largest share brand
                b_add = max(col_alloc, key=lambda x: col_alloc[x])
                col_alloc[b_add] += 1

            rows = slots // cols
            arranged_columns = []
            for brand in ordered_brands:
                n_cols = col_alloc.get(brand, 0)
                if n_cols == 0:
                    continue
                prods = sorted(brand_groups[brand], key=lambda p: p[0].sales_velocity, reverse=True)
                clear_prods = [p for p in prods if is_clear_case(p[0])]
                color_prods = [p for p in prods if not is_clear_case(p[0])]
                clear_iter = cycle(clear_prods) if clear_prods else None
                color_iter = cycle(color_prods) if color_prods else None
                for _ in range(n_cols):
                    col_items = []
                    # First row – clear if available else top colour
                    if clear_iter is not None:
                        col_items.append(next(clear_iter))
                    elif color_iter is not None:
                        col_items.append(next(color_iter))
                    else:
                        col_items.append(None)
                    # Remaining rows – top colours
                    for _ in range(1, rows):
                        if color_iter is not None:
                            col_items.append(next(color_iter))
                        elif clear_iter is not None:
                            col_items.append(next(clear_iter))
                        else:
                            col_items.append(None)
                    arranged_columns.append(col_items)
            # Flatten column-major order back to arranged_flat
            arranged_flat = []
            for r in range(rows):
                for col in arranged_columns:
                    arranged_flat.append(col[r])
            # Fill any leftover slots with None
            arranged_flat.extend([None]*(slots-len(arranged_flat)))
            return arranged_flat
            arranged_flat = []
            if priority_brands is None:
                priority_brands = []
            priority_lower = [b.lower() for b in priority_brands]
            brand_groups = defaultdict(list)
            for p in products:
                brand_groups[getattr(p[0], 'brand', 'Unknown')].append(p)
            # Build ordered brand list – priority first then others by sales
            remaining_brands = [b for b in brand_groups if b.lower() not in priority_lower]
            remaining_brands.sort(key=lambda b: sum(p[0].sales_velocity for p in brand_groups[b]), reverse=True)
            ordered_brands = priority_brands + remaining_brands
            rows = slots // cols
            col_idx = 0
            for brand in ordered_brands:
                if brand not in brand_groups:
                    continue
                brand_products = sorted(brand_groups[brand], key=lambda p: p[0].sales_velocity, reverse=True)
                if not brand_products:
                    continue
                prod_iter = cycle(brand_products)
                while col_idx < cols and len(arranged_flat) < slots:
                    # Fill one entire column for this brand
                    for _ in range(rows):
                        arranged_flat.append(next(prod_iter))
                    col_idx += 1
                if col_idx >= cols or len(arranged_flat) >= slots:
                    break
            # If slots remain (fewer brands than columns), cycle priority brands again
            while len(arranged_flat) < slots:
                for brand in ordered_brands:
                    if brand in brand_groups and brand_groups[brand]:
                        prod_iter = cycle(brand_groups[brand])
                        for _ in range(rows):
                            if len(arranged_flat) < slots:
                                arranged_flat.append(next(prod_iter))
                if not ordered_brands:
                    arranged_flat.extend([None]*(slots-len(arranged_flat)))
            return arranged_flat
            arranged_flat = []
            # Prepare brand order cycling priority first
            if priority_brands is None:
                priority_brands = []
            priority_lower = [b.lower() for b in priority_brands]
            brand_groups = defaultdict(list)
            for p in products:
                brand_groups[getattr(p[0], 'brand', 'Unknown')].append(p)
            # Sort remaining brands by sales velocity
            remaining_brands = [b for b in brand_groups if b.lower() not in priority_lower]
            remaining_brands.sort(key=lambda b: sum(p[0].sales_velocity for p in brand_groups[b]), reverse=True)
            ordered_brands = priority_brands + remaining_brands
            # Build iterators per brand
            brand_iters = {b: cycle(sorted(brand_groups[b], key=lambda p: p[0].sales_velocity, reverse=True)) for b in ordered_brands if b in brand_groups}
            rows = slots // cols
            for col_idx in range(cols):
                brand = ordered_brands[col_idx % len(ordered_brands)] if ordered_brands else None
                if brand is None:
                    # fallback none placeholders
                    for _ in range(rows):
                        arranged_flat.append(None)
                    continue
                for _ in range(rows):
                    arranged_flat.append(next(brand_iters[brand]))
            return arranged_flat
        if priority_brands is None:
            priority_brands = []
        priority_lower = [b.lower() for b in priority_brands]
        brand_groups = defaultdict(list)
        for p in products:
            brand_groups[getattr(p[0], 'brand', 'Unknown')].append(p)

        # Sort brands: priority brands first (in given order), then by total sales velocity
        # Initial sort by sales velocity
        sorted_brands = sorted(brand_groups.keys(), key=lambda b: sum(p[0].sales_velocity for p in brand_groups[b]), reverse=True)
        # Move priority brands to the front while preserving their specified order
        sorted_brands = [b for b in priority_brands if b.lower() in [s.lower() for s in sorted_brands]] + [b for b in sorted_brands if b.lower() not in priority_lower]
        
        # Create iterators for each brand's products, sorted by sales velocity
        brand_product_iterators = {}
        for brand in sorted_brands:
            brand_products = sorted(brand_groups[brand], key=lambda p: p[0].sales_velocity, reverse=True)
            brand_product_iterators[brand] = cycle(brand_products)

        # Interleave products from top brands to ensure diversity
        sorted_products = []
        product_count = len(products)
        while len(sorted_products) < product_count:
            for brand in sorted_brands:
                if len(sorted_products) < product_count:
                    product = next(brand_product_iterators[brand])
                    if product not in sorted_products:
                        sorted_products.append(product)
                else:
                    break
        all_brand_products = sorted_products
        # Fill grid with brand-grouped products
        for i in range(slots):
            if i < len(all_brand_products):
                grid[i // cols][i % cols] = all_brand_products[i]
            else: # Cycle if not enough products
                grid[i // cols][i % cols] = all_brand_products[i % len(all_brand_products)]
    else:
        # --- Color Grouped Arrangement for Apple ---
        if color_columnwise:
            # Fill each column with a dominant colour group for symmetry
            color_iters = {k: iter(color_groups[k]) for k in color_keys}
            for col_idx in range(clear_cols, cols):
                color_key = color_keys[(col_idx - clear_cols) % len(color_keys)]
                for row_idx in range(rows):
                    try:
                        grid[row_idx][col_idx] = next(color_iters[color_key])
                    except StopIteration:
                        # If a colour group is exhausted, rotate to next available
                        for k in color_keys:
                            if color_groups[k]:
                                grid[row_idx][col_idx] = color_groups[k].pop()
                                break
            # Any remaining None slots filled with top-selling products
            flat = [prod for group in color_groups.values() for prod in group]
            idx = 0
            for r in range(rows):
                for c in range(clear_cols, cols):
                    if grid[r][c] is None and idx < len(flat):
                        grid[r][c] = flat[idx]
                        idx += 1
        elif color_rowwise:
            # --- Row-wise dominant colour grouping ---
            color_iters = {k: cycle(color_groups[k]) for k in color_keys}
            row_ptr = 0
            for r in range(rows):
                color_key = color_keys[row_ptr % len(color_keys)]
                row_ptr += 1
                for c in range(clear_cols, cols):
                    try:
                        grid[r][c] = next(color_iters[color_key])
                    except StopIteration:
                        grid[r][c] = None
        else:
            # --- Original colour-alternating logic (fall-back) ---
            color_iters = {k: iter(color_groups[k]) for k in color_keys}
            color_cycle = color_keys[:]
            color_ptr = 0
            for r in range(rows):
                for c in range(clear_cols, cols):
                    placed = False
                    # Alternate colours for diversity
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
                    if not placed:
                        # Fallback cycle through any products
                        unique_products = color_cases + clear_cases
                        if unique_products:
                            idx_local = ((r * cols + c) - clear_cols * rows) % len(unique_products)
                            grid[r][c] = unique_products[idx_local]
                        else:
                            grid[r][c] = None
        # --- Mirror columns for central symmetry ---
        for r in range(rows):
            for c in range(cols // 2):
                left = grid[r][c]
                right = grid[r][cols - 1 - c]
                if left and right and get_color_name(left[0]) != get_color_name(right[0]):
                    grid[r][c], grid[r][cols - 1 - c] = right, left

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
