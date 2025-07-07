#!/usr/bin/env python3
"""Debug script to test optimization and visualization"""

import os
import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.data_processing.data_loader import DataLoader
from src.optimization.product_optimizer import ProductOptimizer
from src.utils.logger import get_logger

def debug_optimization():
    """Debug the optimization process step by step"""
    print("="*60)
    print("DEBUG: PLANOGRAM OPTIMIZATION")
    print("="*60)
    
    logger = get_logger()
    loader = DataLoader()
    
    # Step 1: Load products
    print("\n1. Loading products...")
    try:
        products = loader.load_products_by_category("cases")
        print(f"   Loaded {len(products)} products")
        
        # Show first few products
        for i, p in enumerate(products[:3]):
            print(f"   Product {i+1}: {p.product_name[:50]} | W:{p.width} H:{p.height} | Qty:{p.total_qty}")
            
    except Exception as e:
        print(f"   ERROR loading products: {e}")
        return
    
    # Step 2: Load store
    print("\n2. Loading store...")
    try:
        store = loader.load_store_template("standard")
        print(f"   Store type: {store.store_type}")
        print(f"   Number of shelves: {len(store.shelves)}")
        for shelf in store.shelves:
            print(f"   - {shelf.shelf_name}: {shelf.width}cm x {shelf.height}cm")
        print(f"   Placement rules: {store.placement_rules}")
        print(f"   Category grouping: {store.placement_rules.get('category_grouping', False)}")
    except Exception as e:
        print(f"   ERROR loading store: {e}")
        return
    
    # Step 3: Filter products
    print("\n3. Filtering products for store...")
    # Just take first 10 products for debugging
    test_products = products[:10]
    print(f"   Using {len(test_products)} test products")
    
    # Step 4: Create optimizer
    print("\n4. Creating optimizer...")
    optimizer = ProductOptimizer(store, gap_size=1.0, strategy="balanced")
    optimizer.products_placed = []
    
    # Enable debug logging
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Step 5: Run optimization
    print("\n5. Running optimization...")
    try:
        result = optimizer.create_planogram(test_products)
        print(f"   Success: {result.success}")
        print(f"   Products placed: {len(result.products_placed)}")
        print(f"   Products rejected: {len(result.products_rejected)}")
        
        # Check shelf positions
        print("\n6. Checking shelf positions...")
        total_facings = 0
        for shelf in result.store.shelves:
            shelf_facings = sum(pos.facings for pos in shelf.positions)
            total_facings += shelf_facings
            print(f"   {shelf.shelf_name}: {len(shelf.positions)} products, {shelf_facings} facings")
            
            # Show first few positions
            for i, pos in enumerate(shelf.positions[:2]):
                print(f"     Position {i+1}: Product {pos.product_id}, {pos.facings} facings, {pos.x_start:.1f}-{pos.x_end:.1f}cm")
        
        print(f"\n   TOTAL FACINGS: {total_facings}")
        
        # Debug: Check products_placed list
        print("\n   DEBUG: Products in result.products_placed:")
        for i, product in enumerate(result.products_placed[:5]):
            print(f"     {i+1}. {product.product_name[:40]} (ID: {product.product_id})")
            
        # Debug: Check if products are in optimizer's products_placed
        print(f"\n   DEBUG: Optimizer products_placed: {len(optimizer.products_placed)}")
        for i, product in enumerate(optimizer.products_placed[:5]):
            print(f"     {i+1}. {product.product_name[:40]} (ID: {product.product_id})")
        
        # Check metrics
        print("\n7. Checking metrics...")
        metrics = result.metrics
        print(f"   Total facings in metrics: {metrics.get('total_facings', 0)}")
        print(f"   Category distribution: {metrics.get('category_distribution', {})}")
        
        # Test visualization
        print("\n8. Testing visualization...")
        try:
            from src.visualization.clean_planogram import create_clean_planogram
            
            # Create product lookup
            product_lookup = {p.product_id: p for p in test_products}
            
            # Try to create visualization
            fig = create_clean_planogram(result, product_lookup, "Debug Test", "debug_test.png")
            print("   Visualization created successfully!")
            
            # Check if file was actually saved
            if os.path.exists("debug_test.png"):
                print("   File saved successfully!")
            else:
                print("   WARNING: File not saved!")
                
        except Exception as e:
            print(f"   ERROR in visualization: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"   ERROR in optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_optimization()
