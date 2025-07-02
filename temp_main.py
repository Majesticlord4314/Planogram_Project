import os
import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Create necessary directories
for dir_name in ['logs', 'debug', 'output']:
    (project_root / dir_name).mkdir(exist_ok=True)

def test_system():
    """Test the complete planogram system"""
    print("Testing Planogram System")
    print("=" * 60)
    
    # Import after path setup
    from src.data_processing.data_loader import DataLoader
    from src.data_processing.data_transformer import DataTransformer
    from src.data_processing.data_validator import DataValidator
    from src.optimization.product_optimizer import ProductOptimizer
    from src.optimization.bundle_optimizer import BundleOptimizer
    from src.visualization.planogram_visualizer import PlanogramVisualizer
    from src.visualization.export_handler import ExportHandler
    from src.utils.logger import get_logger
    from src.utils.debugger import PlanogramDebugger
    
    logger = get_logger()
    debugger = PlanogramDebugger()
    
    try:
        # Step 1: Load data
        logger.info("Step 1: Loading data...")
        loader = DataLoader()
        
        # Check available stores
        available_stores = loader.get_available_stores()
        logger.info(f"Available stores: {available_stores}")
        
        if not available_stores:
            logger.error("No store templates found! Please check data/raw/store_templates/")
            return
        
        # Load a store
        store_type = available_stores[0] if available_stores else 'standard'
        store = loader.load_store_template(store_type)
        logger.info(f"Loaded {store_type} store with {len(store.shelves)} shelves")
        
        # Step 2: Load products
        logger.info("\nStep 2: Loading products...")
        try:
            products = loader.load_products_by_category('cases')
            logger.info(f"Loaded {len(products)} products")
        except Exception as e:
            logger.warning(f"Could not load cases, trying to load all products: {e}")
            products = loader.load_all_products()
            logger.info(f"Loaded {len(products)} total products")
        
        if not products:
            logger.error("No products loaded! Please check data/raw/accessories/")
            return
        
        # Step 3: Validate data
        logger.info("\nStep 3: Validating data...")
        validator = DataValidator()
        is_valid, issues = validator.validate_products(products)
        logger.info(f"Validation: {'PASSED' if is_valid else 'FAILED'}")
        if issues:
            for issue in issues[:5]:
                logger.warning(f"  - {issue}")
        
        # Step 4: Transform data
        logger.info("\nStep 4: Transforming data...")
        transformer = DataTransformer()
        products = transformer.prepare_products_for_store(products, store)
        logger.info(f"Prepared {len(products)} products for optimization")
        
        # Step 5: Run optimization
        logger.info("\nStep 5: Running optimization...")
        optimizer = ProductOptimizer(store, strategy="balanced")
        result = optimizer.create_planogram(products)
        
        logger.info(f"Optimization complete!")
        logger.info(f"  - Products placed: {len(result.products_placed)}")
        logger.info(f"  - Products rejected: {len(result.products_rejected)}")
        logger.info(f"  - Average utilization: {result.metrics.get('average_utilization', 0):.1f}%")
        
        # Step 6: Visualize results
        logger.info("\nStep 6: Creating visualization...")
        product_lookup = {p.product_id: p for p in products}
        
        visualizer = PlanogramVisualizer()
        fig = visualizer.visualize_planogram(
            result, 
            product_lookup,
            title=f"{store_type.title()} Store Planogram",
            save_path="output/planogram.png"
        )
        
        # Step 7: Export results
        logger.info("\nStep 7: Exporting results...")
        exporter = ExportHandler()
        json_file = exporter.export_to_json(result, product_lookup)
        excel_file = exporter.export_to_excel(result, product_lookup)
        
        logger.info(f"Results exported to:")
        logger.info(f"  - {json_file}")
        logger.info(f"  - {excel_file}")
        
        # Generate debug report
        debug_report = debugger.generate_debug_report()
        logger.info("\nDebug report generated")
        
        print("\n✅ Test completed successfully!")
        print(f"Check the 'output' folder for results")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        print("Check logs/errors.log for details")

def create_sample_data():
    """Create sample data files if they don't exist"""
    print("Creating sample data files...")
    
    # Sample cases data
    cases_data = """product_id,product_name,series,category,subcategory,brand,width,height,depth,weight,color,price,qty_sold_last_week,qty_sold_last_month,avg_weekly_sales,current_stock,min_stock,min_facings,max_facings,core_product,launch_date,status
IP16_CLR_01,Clear Case for iPhone 16,iPhone 16,case,clear_case,Generic,8.0,12.0,1.0,50,Clear,39.0,45,180,45,100,20,2,5,iPhone 16,2024-01-15,active
IP16_SIL_01,Silicone Case for iPhone 16,iPhone 16,case,silicone_case,Apple,8.0,12.0,1.0,55,Blue,49.0,38,152,38,80,15,1,4,iPhone 16,2024-01-15,active
IP15_CLR_01,Clear Case for iPhone 15,iPhone 15,case,clear_case,Generic,8.0,12.0,1.0,50,Clear,35.0,32,128,32,120,20,2,5,iPhone 15,2023-09-15,active"""
    
    # Sample store template
    standard_store = {
        "store_info": {
            "store_type": "standard",
            "store_name": "Standard Store Template",
            "total_area_sqm": 30,
            "accessory_area_sqm": 8,
            "customer_flow": "medium",
            "restock_frequency_days": 3
        },
        "shelves": [
            {
                "shelf_id": 0,
                "shelf_name": "Bottom Shelf",
                "width": 150,
                "height": 35,
                "depth": 40,
                "y_position": 20,
                "shelf_type": "standard",
                "eye_level_score": 0.2
            },
            {
                "shelf_id": 1,
                "shelf_name": "Middle Shelf",
                "width": 150,
                "height": 30,
                "depth": 40,
                "y_position": 60,
                "shelf_type": "standard",
                "eye_level_score": 0.5
            },
            {
                "shelf_id": 2,
                "shelf_name": "Eye Level Shelf",
                "width": 150,
                "height": 30,
                "depth": 35,
                "y_position": 95,
                "shelf_type": "premium",
                "eye_level_score": 0.9
            }
        ],
        "placement_rules": {
            "category_grouping": True,
            "min_facings_multiplier": 1.0
        },
        "product_mix_rules": {
            "min_skus_per_category": 2,
            "max_skus_total": 50
        },
        "optimization_weights": {
            "sales_velocity": 0.4,
            "attach_rate": 0.3,
            "new_product_priority": 0.3
        }
    }
    
    # Create directories
    data_dirs = [
        'data/raw/accessories',
        'data/raw/store_templates',
        'data/raw/cohorts'
    ]
    
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Write sample files
    cases_file = Path('data/raw/accessories/cases_sales.csv')
    if not cases_file.exists():
        with open(cases_file, 'w') as f:
            f.write(cases_data)
        print(f"Created sample file: {cases_file}")
    
    store_file = Path('data/raw/store_templates/standard_store.json')
    if not store_file.exists():
        import json
        with open(store_file, 'w') as f:
            json.dump(standard_store, f, indent=2)
        print(f"Created sample file: {store_file}")
    
    print("Sample data files created!")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Planogram Optimization System')
    parser.add_argument('--test', action='store_true', help='Run system test')
    parser.add_argument('--create-sample-data', action='store_true', 
                       help='Create sample data files')
    parser.add_argument('--store-type', default='standard', 
                       help='Store type (flagship, standard, express)')
    parser.add_argument('--category', default='cases', 
                       help='Product category to optimize')
    parser.add_argument('--strategy', default='balanced',
                       help='Optimization strategy (balanced, sales_velocity, category_grouped, value_density)')
    
    args = parser.parse_args()
    
    if args.create_sample_data:
        create_sample_data()
    elif args.test:
        test_system()
    else:
        # Run optimization with specified parameters
        run_optimization(
            store_type=args.store_type,
            category=args.category,
            strategy=args.strategy
        )

def run_optimization(store_type='standard', category='cases', strategy='balanced'):
    """Run optimization with specified parameters"""
    from src.data_processing.data_loader import DataLoader
    from src.data_processing.data_transformer import DataTransformer
    from src.optimization.product_optimizer import ProductOptimizer
    from src.visualization.planogram_visualizer import PlanogramVisualizer
    from src.visualization.export_handler import ExportHandler
    from src.utils.logger import get_logger
    
    logger = get_logger()
    
    try:
        logger.info(f"Running optimization for {store_type} store, {category} category, {strategy} strategy")
        
        # Load data
        loader = DataLoader()
        store = loader.load_store_template(store_type)
        products = loader.load_products_by_category(category)
        
        # Transform data
        transformer = DataTransformer()
        products = transformer.prepare_products_for_store(products, store, strategy)
        
        # Optimize
        optimizer = ProductOptimizer(store, strategy=strategy)
        result = optimizer.create_planogram(products)
        
        # Visualize
        product_lookup = {p.product_id: p for p in products}
        visualizer = PlanogramVisualizer()
        visualizer.visualize_planogram(
            result,
            product_lookup,
            title=f"{store_type.title()} Store - {category.title()} - {strategy.title()} Strategy",
            save_path=f"output/planogram_{store_type}_{category}_{strategy}.png"
        )
        
        # Export
        exporter = ExportHandler()
        exporter.export_to_json(result, product_lookup, 
                               f"planogram_{store_type}_{category}_{strategy}.json")
        
        logger.info("Optimization complete! Check output folder for results.")
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()