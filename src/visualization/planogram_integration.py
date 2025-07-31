import os
import sys
from pathlib import Path
from datetime import datetime
from src.visualization.web_planogram_generator import generate_web_planogram, generate_product_details

def generate_store_planograms(products, store_type='flagship'):
    """Generate planograms for a store based on store type"""
    from src.utils.logger import get_logger
    logger = get_logger()
    
    # Determine wall allocation based on store type
    if store_type == 'flagship':
        num_walls = 3
        wall_allocation = [
            {'name': 'Wall 1/3', 'series': ['iPhone 16 Pro Max', 'iPhone 16 Pro'], 'focus': 'iPhone 16 Pro Models'},
            {'name': 'Wall 2/3', 'series': ['iPhone 16 Plus', 'iPhone 16 Base'], 'focus': 'iPhone 16 Standard Models'},
            {'name': 'Wall 3/3', 'series': ['iPhone 16 Pro Max', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16 Base'], 'focus': 'Top TPA Brands (Third Party)'}
        ]
    elif store_type == 'standard':
        num_walls = 2
        wall_allocation = [
            {'name': 'Wall 1/2', 'series': ['iPhone 16 Pro Max', 'iPhone 16 Pro'], 'focus': 'iPhone 16 Pro Models'},
            {'name': 'Wall 2/2', 'series': ['iPhone 16 Plus', 'iPhone 16 Base'], 'focus': 'iPhone 16 Standard Models'}
        ]
    else:  # express
        num_walls = 1
        wall_allocation = [
            {'name': 'Wall 1/1', 'series': ['iPhone 16 Pro Max', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16 Base'], 'focus': 'All iPhone 16 Models'}
        ]
    
    # Filter to only include iPhone 16 products
    iphone16_products = [p for p in products if 'iPhone 16' in getattr(p, 'series', '')]
    
    # Group products by series
    series_groups = {
        'iPhone 16 Pro Max': [],
        'iPhone 16 Pro': [],
        'iPhone 16 Plus': [],
        'iPhone 16 Base': []
    }
    
    # Group products by series
    for product in iphone16_products:
        series = getattr(product, 'series', '')
        for series_key in series_groups.keys():
            if series_key.lower() in series.lower():
                series_groups[series_key].append(product)
                break
    
    results = []
    
    # Create planogram for each wall
    for wall in wall_allocation:
        wall_products = []
        for series in wall['series']:
            wall_products.extend(series_groups.get(series, []))
        
        # Generate planogram
        planogram_file = generate_web_planogram(wall_products, store_type, wall['name'], wall['series'])
        
        # Generate product details
        details_file = generate_product_details(wall_products, planogram_file, store_type, wall['name'], wall['series'])
        
        # Add to results
        results.append({
            'wall_name': wall['name'],
            'focus': wall['focus'],
            'products_count': len(wall_products),
            'planogram_image': planogram_file,
            'details_file': details_file
        })
        
        logger.info(f"Generated planogram for {wall['name']} - {wall['focus']}")
        logger.info(f"  - Products: {len(wall_products)}")
        logger.info(f"  - Planogram: {planogram_file}")
        logger.info(f"  - Details: {details_file}")
    
    return {
        'store_type': store_type,
        'num_walls': num_walls,
        'total_products': len(iphone16_products),
        'results': {wall['name']: result for wall, result in zip(wall_allocation, results)}
    }