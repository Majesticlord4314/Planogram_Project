#!/usr/bin/env python3
"""Simple test to debug product placement"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.data_processing.data_loader import DataLoader
from src.optimization.product_optimizer import ProductOptimizer

def simple_test():
    print("SIMPLE PLACEMENT TEST")
    print("=" * 40)
    
    # Load one product and place it manually
    loader = DataLoader()
    products = loader.load_products_by_category("cases")
    store = loader.load_store_template("standard")
    
    # Take just one product
    product = products[0]
    print(f"Testing product: {product.product_name}")
    print(f"Dimensions: {product.width}x{product.height}x{product.depth}cm")
    print(f"Facings: min={product.min_facings}, max={product.max_facings}")
    
    # Get first shelf
    shelf = store.shelves[0]
    print(f"Testing shelf: {shelf.shelf_name}")
    print(f"Shelf dimensions: {shelf.width}x{shelf.height}cm")
    print(f"Initial positions: {len(shelf.positions)}")
    
    # Create optimizer
    optimizer = ProductOptimizer(store, gap_size=1.0, strategy="balanced")
    
    # Try to place product manually
    print("\nTrying manual placement...")
    facings = 2
    
    # Check if product can fit
    can_fit = shelf.can_fit_product(product, facings)
    print(f"Can fit {facings} facings: {can_fit}")
    
    if can_fit:
        # Try actual placement
        success = optimizer._place_product_on_shelf(shelf, product, facings)
        print(f"Placement success: {success}")
        
        # Check shelf state after placement
        print(f"Positions after placement: {len(shelf.positions)}")
        if shelf.positions:
            pos = shelf.positions[0]
            print(f"Position details: {pos.product_id}, {pos.facings} facings, {pos.x_start}-{pos.x_end}cm")
    else:
        print("Cannot fit - checking constraints...")
        required_width = product.width * facings + 2.0  # with gaps
        print(f"Required width: {required_width}cm")
        print(f"Available width: {shelf.width}cm")
        print(f"Product height: {product.height}cm vs shelf height: {shelf.height}cm")

if __name__ == "__main__":
    simple_test()
