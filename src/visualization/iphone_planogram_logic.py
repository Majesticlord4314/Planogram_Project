
from typing import List, Dict, Tuple
from src.models.product import Product

def arrange_iphone_products(products: List[Product], store_template: 'Store') -> List[Dict]:
    """Determines the wall configuration based on store type and arranges products."""
    store_type = store_template.store_type.lower()

    # 1. Wall Allocation Logic
    if store_type == 'flagship':
        num_walls = 4
    elif store_type == 'standard':
        num_walls = 3
    elif store_type == 'express':
        num_walls = 2
    else:
        num_walls = 1

    # 2. Product Categorization
    apple_cases = [p for p in products if 'apple' in getattr(p, 'brand', '').lower() and 'case' in getattr(p, 'product_name', '').lower()]
    tpa_cases = [p for p in products if 'apple' not in getattr(p, 'brand', '').lower() and 'case' in getattr(p, 'product_name', '').lower()]
    protectors = [p for p in products if any(cat in getattr(p, 'product_name', '').lower() for cat in ['screen', 'glass', 'lens'])]

    # 3. Wall Configuration
    wall_configs = []
    if num_walls == 4:
        series_walls = ['iPhone 16 Pro Max', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16 Base']
        for i, series_name in enumerate(series_walls):
            wall_products = [p for p in apple_cases if series_name.lower() in getattr(p, 'series', '').lower()]
            wall_configs.append({
                'title': f'Wall {i+1}/4: {series_name} Cases',
                'products': _prepare_product_tuples(wall_products)
            })
    elif num_walls == 3:
        pro_models = [p for p in apple_cases if 'pro' in getattr(p, 'series', '').lower()]
        base_plus_models = [p for p in apple_cases if 'base' in getattr(p, 'series', '').lower() or 'plus' in getattr(p, 'series', '').lower()]
        wall_configs.append({'title': 'Wall 1/3: Pro & Pro Max Cases', 'products': _prepare_product_tuples(pro_models)})
        wall_configs.append({'title': 'Wall 2/3: Plus & Base Cases', 'products': _prepare_product_tuples(base_plus_models)})
        wall_configs.append({'title': 'Wall 3/3: Protection & TPA', 'products': _prepare_product_tuples(protectors + tpa_cases)})
    elif num_walls == 2:
        pro_models = [p for p in apple_cases if 'pro' in getattr(p, 'series', '').lower()]
        base_plus_models = [p for p in apple_cases if 'base' in getattr(p, 'series', '').lower() or 'plus' in getattr(p, 'series', '').lower()]
        wall_configs.append({'title': 'Wall 1/2: Pro & Pro Max Cases', 'products': _prepare_product_tuples(pro_models)})
        wall_configs.append({'title': 'Wall 2/2: Plus & Base Cases', 'products': _prepare_product_tuples(base_plus_models)})
    else: # 1 Wall
        bestsellers = sorted(products, key=lambda p: getattr(p, 'total_qty', 0), reverse=True)
        wall_configs.append({'title': 'Bestsellers', 'products': _prepare_product_tuples(bestsellers)})

    # Add layout details to each config
    for config in wall_configs:
        config['rows'] = 6
        config['cols'] = 5

    return wall_configs

def _prepare_product_tuples(products: List[Product]) -> List[Tuple[Product, int]]:
    """Converts a list of products to the (product, facings) format."""
    # Sort products by sales quantity for better placement
    sorted_products = sorted(products, key=lambda p: getattr(p, 'total_qty', 0), reverse=True)
    return [(p, 1) for p in sorted_products] # Assuming 1 facing per product for now
