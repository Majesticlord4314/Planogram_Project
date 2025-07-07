#!/usr/bin/env python3
"""Test the optimization loop specifically"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.data_processing.data_loader import DataLoader
from src.optimization.product_optimizer import ProductOptimizer

def test_optimization_loop():
    print("OPTIMIZATION LOOP TEST")
    print("=" * 40)
    
    loader = DataLoader()
    products = loader.load_products_by_category("cases")[:5]  # Just 5 products
    store = loader.load_store_template("standard")
    
    print(f"Testing with {len(products)} products")
    
    # Create optimizer
    optimizer = ProductOptimizer(store, gap_size=1.0, strategy="balanced")
    optimizer.products_placed = []
    optimizer.warnings = []
    optimizer.metrics = {'category_distribution': {}}
    
    print("\nTesting the actual _optimize_balanced method...")
    
    # Call the method directly
    result = optimizer._optimize_balanced(products)
    
    print(f"Result success: {result.success}")
    print(f"Products placed: {len(result.products_placed)}")
    print(f"Products rejected: {len(result.products_rejected)}")
    print(f"Warnings: {len(result.warnings)}")
    
    # Check shelves
    print("\nShelf status:")
    total_positions = 0
    for shelf in result.store.shelves:
        positions = len(shelf.positions)
        total_positions += positions
        facings = sum(pos.facings for pos in shelf.positions)
        print(f"  {shelf.shelf_name}: {positions} products, {facings} facings")
    
    print(f"\nTotal shelf positions: {total_positions}")
    
    # If placements were made, show details
    if result.products_placed and total_positions > 0:
        print("\nPlacement details:")
        for shelf in result.store.shelves:
            if shelf.positions:
                for pos in shelf.positions:
                    product = next((p for p in result.products_placed if p.product_id == pos.product_id), None)
                    product_name = product.product_name[:30] if product else "Unknown"
                    print(f"  {shelf.shelf_name}: {product_name} - {pos.facings} facings")

if __name__ == "__main__":
    test_optimization_loop()
