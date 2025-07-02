#!/usr/bin/env python3
"""
Main entry point for the planogram system
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt

# Setup paths
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Create necessary directories
for dir_name in ['logs', 'debug', 'output']:
    (project_root / dir_name).mkdir(exist_ok=True)

def run_custom_planogram():
    """Run planogram with custom accessories data"""
    print("Running Planogram System with Custom Accessories")
    print("=" * 60)
    
    # Import after path setup
    from src.data_processing.data_loader import DataLoader
    from src.data_processing.data_transformer import DataTransformer
    from src.data_processing.data_validator import DataValidator
    from src.optimization.product_optimizer import ProductOptimizer
    from src.visualization.planogram_visualizer import PlanogramVisualizer
    from src.visualization.export_handler import ExportHandler
    from src.utils.logger import get_logger
    
    logger = get_logger()
    
    try:
        # Step 1: Create DataLoader with custom path
        logger.info("Loading data...")
        loader = DataLoader()
        
        # Load store template
        store = loader.load_store_template('standard')
        logger.info(f"Loaded store with {len(store.shelves)} shelves")
        
        # Step 2: Load custom accessories
        # First, let's load from the custom file
        import pandas as pd
        from src.models.product import Product, ProductCategory, ProductStatus
        
        df = pd.read_csv('data/raw/accessories/custom_accessories.csv')
        products = []
        
        for _, row in df.iterrows():
            # Map category
            category_map = {
                'case': ProductCategory.CASE,
                'screen_protector': ProductCategory.SCREEN_PROTECTOR,
                'cable': ProductCategory.CABLE,
                'adapter': ProductCategory.ADAPTER,
                'charger': ProductCategory.CHARGER,
                'audio': ProductCategory.AUDIO,
                'other': ProductCategory.OTHER
            }
            
            product = Product(
                product_id=str(row['product_id']),
                product_name=str(row['product_name']),
                series=str(row['series']),
                category=category_map.get(row['category'], ProductCategory.OTHER),
                subcategory=str(row['subcategory']),
                brand=str(row['brand']),
                width=float(row['width']),
                height=float(row['height']),
                depth=float(row['depth']),
                weight=float(row['weight']),
                qty_sold_last_week=int(row['qty_sold_last_week']),
                qty_sold_last_month=int(row['qty_sold_last_month']),
                avg_weekly_sales=float(row['avg_weekly_sales']),
                current_stock=int(row['current_stock']),
                min_stock=int(row['min_stock']),
                min_facings=int(row['min_facings']),
                max_facings=int(row['max_facings']),
                color=str(row['color']),
                price=float(row['price']),
                core_product=str(row['core_product']),
                launch_date=str(row['launch_date']),
                status=ProductStatus.ACTIVE
            )
            products.append(product)
        
        logger.info(f"Loaded {len(products)} custom products")
        # After loading products, before validation
        for product in products:
            if not hasattr(product, 'attach_rate') or product.attach_rate is None:
                product.attach_rate = 0.0
            if not hasattr(product, 'bundle_frequency') or product.bundle_frequency is None:
                product.bundle_frequency = 0
        # Step 3: Validate data
        logger.info("Validating data...")
        validator = DataValidator()
        is_valid, issues = validator.validate_products(products)
        if issues:
            logger.warning(f"Validation issues: {len(issues)}")
            for issue in issues[:3]:  # Show first 3 issues
                logger.warning(f"  - {issue}")
        
        # Step 4: Transform data
        logger.info("Transforming data...")
        transformer = DataTransformer()
        products = transformer.prepare_products_for_store(products, store, strategy="balanced")
        
        # Step 5: Run optimization
        logger.info("Running optimization...")
        optimizer = ProductOptimizer(store, gap_size=2.0, strategy="balanced")
        
        # Initialize required attributes
        optimizer.products_placed = []
        
        result = optimizer.create_planogram(products)
        
        logger.info(f"Optimization complete!")
        logger.info(f"  - Products placed: {len(result.products_placed)}")
        logger.info(f"  - Products rejected: {len(result.products_rejected)}")
        logger.info(f"  - Average utilization: {result.metrics.get('average_utilization', 0):.1f}%")
        
        # Step 6: Create product lookup
        product_lookup = {p.product_id: p for p in products}
        
        # Step 7: Visualize results
        logger.info("Creating visualization...")
        visualizer = PlanogramVisualizer()
        
        # Create the visualization
        fig = visualizer.visualize_planogram(
            result,
            product_lookup,
            title="Custom Apple Accessories Planogram",
            save_path="output/custom_planogram.png",
            show_metrics=True
        )
        
        # Step 8: Export results
        logger.info("Exporting results...")
        exporter = ExportHandler()
        
        # Export to JSON
        json_file = exporter.export_to_json(result, product_lookup, "custom_planogram.json")
        logger.info(f"Exported to: {json_file}")
        
        # Export to Excel
        excel_file = exporter.export_to_excel(result, product_lookup, "custom_planogram.xlsx")
        logger.info(f"Exported to: {excel_file}")
        
        # Step 9: Print summary
        print("\n" + "="*60)
        print("PLANOGRAM SUMMARY")
        print("="*60)
        
        # Group by category
        category_summary = {}
        for product in result.products_placed:
            cat = product.category.value
            if cat not in category_summary:
                category_summary[cat] = []
            category_summary[cat].append(product)
        
        print("\nProducts by Category:")
        for cat, prods in category_summary.items():
            print(f"  {cat.upper()}: {len(prods)} products")
            for prod in prods[:3]:  # Show first 3
                print(f"    - {prod.product_name}")
        
        print(f"\nShelf Utilization:")
        for shelf_util in result.metrics.get('shelf_utilization', []):
            print(f"  {shelf_util['shelf_name']}: {shelf_util['utilization']:.1f}%")
        
        print(f"\n✅ Success! Check the 'output' folder for:")
        print(f"  - custom_planogram.png (visual)")
        print(f"  - custom_planogram.json (data)")
        print(f"  - custom_planogram.xlsx (spreadsheet)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("Check logs folder for details")

def test_with_minimal_data():
    """Test with minimal data to ensure system works"""
    print("Testing with minimal data...")
    
    from src.models.product import Product, ProductCategory, ProductStatus
    from src.models.shelf import Shelf
    from src.models.store import Store
    from src.optimization.product_optimizer import ProductOptimizer
    from src.visualization.planogram_visualizer import PlanogramVisualizer
    from src.utils.logger import get_logger
    
    logger = get_logger()
    
    # Create minimal test data
    products = [
        Product(
            product_id="TEST_01",
            product_name="Test iPhone Case",
            series="iPhone 16",
            category=ProductCategory.CASE,
            subcategory="test",
            brand="Test",
            width=8.0,
            height=12.0,
            depth=1.0,
            weight=50.0,
            qty_sold_last_week=50,
            qty_sold_last_month=200,
            avg_weekly_sales=50.0,
            current_stock=100,
            min_stock=20,
            min_facings=2,
            max_facings=5,
            color="Black",
            price=39.99,
            core_product="iPhone 16",
            launch_date="2024-01-01",
            status=ProductStatus.ACTIVE
        ),
        Product(
            product_id="TEST_02",
            product_name="Test Screen Protector",
            series="iPhone 16",
            category=ProductCategory.SCREEN_PROTECTOR,
            subcategory="test",
            brand="Test",
            width=7.0,
            height=11.0,
            depth=0.5,
            weight=20.0,
            qty_sold_last_week=80,
            qty_sold_last_month=320,
            avg_weekly_sales=80.0,
            current_stock=200,
            min_stock=40,
            min_facings=3,
            max_facings=8,
            color="Clear",
            price=29.99,
            core_product="iPhone 16",
            launch_date="2024-01-01",
            status=ProductStatus.ACTIVE
        )
    ]
    
    # Create minimal store
    shelves = [
        Shelf(0, "Test Shelf", 100.0, 30.0, 40.0, 50.0, "standard", 0.8)
    ]
    
    store = Store(
        store_type="test",
        store_name="Test Store",
        total_area_sqm=10,
        accessory_area_sqm=5,
        customer_flow="medium",
        restock_frequency_days=3,
        shelves=shelves
    )
    
    # Run optimization
    optimizer = ProductOptimizer(store, gap_size=2.0, strategy="balanced")
    optimizer.products_placed = []
    result = optimizer.create_planogram(products)
    
    print(f"Test result: {len(result.products_placed)} products placed")
    
    if result.success:
        print("✅ Basic test passed!")
    else:
        print("❌ Basic test failed!")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Planogram Optimization System')
    parser.add_argument('--custom', action='store_true', help='Run with custom accessories')
    parser.add_argument('--test', action='store_true', help='Run minimal test')
    parser.add_argument('--create-sample-data', action='store_true', help='Create sample data files')
    
    args = parser.parse_args()
    
    if args.test:
        test_with_minimal_data()
    elif args.custom:
        run_custom_planogram()
    else:
        # Default: run with custom accessories
        run_custom_planogram()

if __name__ == "__main__":
    main()