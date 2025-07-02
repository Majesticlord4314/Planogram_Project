#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import argparse
from typing import List, Optional

# Setup paths
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Create necessary directories
for dir_name in ['logs', 'debug', 'output']:
    (project_root / dir_name).mkdir(exist_ok=True)

def interactive_mode():
    """Run the system in interactive mode"""
    print("\n" + "="*60)
    print("APPLE PLANOGRAM OPTIMIZATION SYSTEM")
    print("="*60)
    
    # Import modules
    from src.data_processing.data_loader import DataLoader
    from src.data_processing.data_transformer import DataTransformer
    from src.data_processing.data_validator import DataValidator
    from src.optimization.product_optimizer import ProductOptimizer
    from src.optimization.bundle_optimizer import BundleOptimizer
    from src.visualization.planogram_visualizer import PlanogramVisualizer
    from src.visualization.export_handler import ExportHandler
    from src.utils.logger import get_logger
    
    logger = get_logger()
    loader = DataLoader()
    
    try:
        # Step 1: Choose optimization type
        print("\nSelect optimization type:")
        print("1. Product Category (Cases, Cables, etc.)")
        print("2. Line of Business (iPhone, iPad, Mac, etc.)")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            run_product_category_optimization(loader, logger)
        elif choice == "2":
            run_lob_optimization(loader, logger)
        else:
            print("Invalid choice. Exiting.")
            return
            
    except Exception as e:
        logger.error(f"Error in interactive mode: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")

def run_product_category_optimization(loader, logger):
    """Run optimization for a specific product category"""
    from src.data_processing.data_transformer import DataTransformer
    from src.optimization.product_optimizer import ProductOptimizer
    from src.visualization.planogram_visualizer import PlanogramVisualizer
    from src.visualization.export_handler import ExportHandler
    
    # Step 1: Select category
    print("\nAvailable product categories:")
    categories = {
        '1': ('cases', 'Phone Cases'),
        '2': ('cables', 'Cables & Adapters'),
        '3': ('screen_protectors', 'Screen Protectors'),
        '4': ('others', 'Mounts & Other Accessories')
    }
    
    for key, (_, name) in categories.items():
        print(f"{key}. {name}")
    
    cat_choice = input("\nSelect category (1-4): ").strip()
    if cat_choice not in categories:
        print("Invalid choice.")
        return
    
    category_key, category_name = categories[cat_choice]
    
    # Step 2: Select store type
    store_type = select_store_type(loader)
    if not store_type:
        return
    
    # Step 3: Select optimization strategy
    strategy = select_optimization_strategy()
    
    # Step 4: Load data
    logger.info(f"Loading {category_name} for {store_type} store...")
    
    # Load products
    try:
        products = loader.load_products_by_category(category_key)
        logger.info(f"Loaded {len(products)} products in {category_name}")
    except Exception as e:
        logger.error(f"Could not load category {category_key}: {e}")
        # Try loading all products instead
        products = loader.load_all_products()
        # Filter by category
        from src.models.product import ProductCategory
        cat_map = {
            'cases': ProductCategory.CASE,
            'cables': ProductCategory.CABLE,
            'screen_protectors': ProductCategory.SCREEN_PROTECTOR
        }
        if category_key in cat_map:
            products = [p for p in products if p.category == cat_map[category_key]]
        logger.info(f"Filtered to {len(products)} products in {category_name}")
    
    if not products:
        print(f"No products found for category {category_name}")
        return
    
    # Load store
    store = loader.load_store_template(store_type)
    
    # Step 5: Transform and optimize
    transformer = DataTransformer()
    products = transformer.prepare_products_for_store(products, store, strategy)
    
    # Set default attributes if missing
    for product in products:
        if not hasattr(product, 'attach_rate'):
            product.attach_rate = 0.0
        if not hasattr(product, 'bundle_frequency'):
            product.bundle_frequency = 0
    
    logger.info(f"Running {strategy} optimization...")
    optimizer = ProductOptimizer(store, gap_size=2.0, strategy=strategy)
    optimizer.products_placed = []
    
    result = optimizer.create_planogram(products)
    
    # Step 6: Visualize and export
    output_name = f"{category_key}_{store_type}_{strategy}"
    visualize_and_export_results(result, products, output_name, 
                               f"{category_name} - {store_type.title()} Store - {strategy.title()}")

def run_lob_optimization(loader, logger):
    """Run optimization for a Line of Business using cohort data"""
    from src.data_processing.data_transformer import DataTransformer
    from src.optimization.bundle_optimizer import BundleOptimizer
    from src.visualization.planogram_visualizer import PlanogramVisualizer
    from src.visualization.export_handler import ExportHandler
    
    # Step 1: Select LOB
    print("\nAvailable Lines of Business:")
    lobs = {
        '1': ('iPhone', 'iPhone Accessories'),
        '2': ('iPad', 'iPad Accessories'),
        '3': ('Mac', 'Mac Accessories'),
        '4': ('Watch', 'Apple Watch Accessories'),
        '5': ('AirPods', 'AirPods Accessories')
    }
    
    for key, (_, name) in lobs.items():
        print(f"{key}. {name}")
    
    lob_choice = input("\nSelect LOB (1-5): ").strip()
    if lob_choice not in lobs:
        print("Invalid choice.")
        return
    
    lob_key, lob_name = lobs[lob_choice]
    
    # Step 2: For iPhone, ask for specific model
    model_filter = None
    if lob_key == 'iPhone':
        print("\nSelect iPhone model (optional):")
        print("1. All iPhone models")
        print("2. iPhone 16 Pro Max")
        print("3. iPhone 16 Pro")
        print("4. iPhone 16")
        print("5. iPhone 15 Series")
        
        model_choice = input("\nEnter choice (1-5): ").strip()
        model_map = {
            '2': 'iPhone 16 Pro Max',
            '3': 'iPhone 16 Pro',
            '4': 'iPhone 16',
            '5': 'iPhone 15'
        }
        model_filter = model_map.get(model_choice)
    
    # Step 3: Select store type
    store_type = select_store_type(loader)
    if not store_type:
        return
    
    # Step 4: Load data
    logger.info(f"Loading {lob_name}...")
    
    # Load products for LOB
    if model_filter:
        products = loader.load_products_by_lob(lob_key, model_filter)
        logger.info(f"Loaded {len(products)} products for {model_filter}")
    else:
        products = loader.load_products_by_lob(lob_key)
        logger.info(f"Loaded {len(products)} products for {lob_name}")
    
    if not products:
        print(f"No products found for {lob_name}")
        return
    
    # Load cohort data
    cohort_df = loader.load_cohort_data(lob_key, model_filter)
    if not cohort_df.empty:
        products = loader.enrich_products_with_cohorts(products, cohort_df)
        logger.info("Enriched products with cohort data")
    
    # Load bundle recommendations
    bundle_df = loader.load_bundle_recommendations()
    if not bundle_df.empty:
        # Filter bundles for this LOB
        bundle_df = bundle_df[bundle_df['lob'] == lob_key]
        logger.info(f"Loaded {len(bundle_df)} bundle recommendations")
    
    # Load store
    store = loader.load_store_template(store_type)
    
    # Step 5: Transform and optimize
    transformer = DataTransformer()
    products = transformer.prepare_products_for_store(products, store, "cohort_based")
    
    # Set default attributes if missing
    for product in products:
        if not hasattr(product, 'attach_rate'):
            product.attach_rate = 0.0
        if not hasattr(product, 'bundle_frequency'):
            product.bundle_frequency = 0
    
    logger.info("Running bundle-based optimization...")
    
    if not bundle_df.empty:
        optimizer = BundleOptimizer(store, gap_size=3.0, bundle_data=bundle_df)
    else:
        # Fall back to product optimizer if no bundle data
        logger.info("No bundle data found, using standard optimization")
        optimizer = ProductOptimizer(store, gap_size=2.0, strategy="balanced")
    
    optimizer.products_placed = []
    result = optimizer.create_planogram(products)
    
    # Step 6: Visualize and export
    model_suffix = f"_{model_filter.replace(' ', '_')}" if model_filter else ""
    output_name = f"{lob_key}{model_suffix}_{store_type}_cohort"
    title = f"{lob_name}"
    if model_filter:
        title += f" ({model_filter})"
    title += f" - {store_type.title()} Store - Cohort-Based"
    
    visualize_and_export_results(result, products, output_name, title)

def select_store_type(loader) -> Optional[str]:
    """Select store type from available templates"""
    available_stores = loader.get_available_stores()
    
    if not available_stores:
        print("No store templates found!")
        return None
    
    print("\nAvailable store types:")
    store_map = {}
    for i, store in enumerate(available_stores, 1):
        store_map[str(i)] = store
        print(f"{i}. {store.title()} Store")
    
    store_choice = input(f"\nSelect store type (1-{len(available_stores)}): ").strip()
    return store_map.get(store_choice)

def select_optimization_strategy() -> str:
    """Select optimization strategy"""
    print("\nOptimization strategies:")
    strategies = {
        '1': ('balanced', 'Balanced (considers multiple factors)'),
        '2': ('sales_velocity', 'Sales Velocity (prioritize fast-moving items)'),
        '3': ('category_grouped', 'Category Grouped (group similar products)'),
        '4': ('value_density', 'Value Density (maximize revenue per cm)')
    }
    
    for key, (_, desc) in strategies.items():
        print(f"{key}. {desc}")
    
    strat_choice = input("\nSelect strategy (1-4): ").strip()
    if strat_choice in strategies:
        return strategies[strat_choice][0]
    return 'balanced'  # Default

def visualize_and_export_results(result, products, output_name, title):
    """Common function to visualize and export results"""
    from src.visualization.planogram_visualizer import PlanogramVisualizer
    from src.visualization.export_handler import ExportHandler
    from src.utils.logger import get_logger
    
    logger = get_logger()
    
    # Create product lookup
    product_lookup = {p.product_id: p for p in products}
    
    # Visualize
    logger.info("Creating visualization...")
    visualizer = PlanogramVisualizer()
    fig = visualizer.visualize_planogram(
        result,
        product_lookup,
        title=title,
        save_path=f"output/{output_name}.png",
        show_metrics=True
    )
    
    # Export
    logger.info("Exporting results...")
    exporter = ExportHandler()
    json_file = exporter.export_to_json(result, product_lookup, f"{output_name}.json")
    excel_file = exporter.export_to_excel(result, product_lookup, f"{output_name}.xlsx")
    
    # Print summary
    print("\n" + "="*60)
    print("OPTIMIZATION COMPLETE")
    print("="*60)
    print(f"Products placed: {len(result.products_placed)}")
    print(f"Products rejected: {len(result.products_rejected)}")
    print(f"Average shelf utilization: {result.metrics.get('average_utilization', 0):.1f}%")
    print(f"\nFiles generated:")
    print(f"  📊 {output_name}.png (visual planogram)")
    print(f"  📄 {output_name}.json (data export)")
    print(f"  📑 {output_name}.xlsx (Excel report)")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Apple Planogram Optimization System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Interactive mode
  python main.py --category cases --store standard
  python main.py --lob iPhone --store flagship
  python main.py --lob iPhone --model "iPhone 16 Pro Max" --store express
        """
    )
    
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Run in interactive mode (default)')
    parser.add_argument('--category', '-c', choices=['cases', 'cables', 'screen_protectors', 'others'],
                       help='Optimize specific product category')
    parser.add_argument('--lob', '-l', choices=['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods'],
                       help='Optimize by Line of Business')
    parser.add_argument('--model', '-m', help='Specific model for LOB (e.g., "iPhone 16 Pro Max")')
    parser.add_argument('--store', '-s', choices=['flagship', 'standard', 'express'],
                       default='standard', help='Store type')
    parser.add_argument('--strategy', choices=['balanced', 'sales_velocity', 'category_grouped', 'value_density'],
                       default='balanced', help='Optimization strategy')
    
    args = parser.parse_args()
    
    # If no specific mode selected, run interactive
    if not args.category and not args.lob:
        interactive_mode()
    else:
        # Run with command line arguments
        from src.data_processing.data_loader import DataLoader
        from src.utils.logger import get_logger
        
        loader = DataLoader()
        logger = get_logger()
        
        if args.category:
            # Quick category mode
            logger.info(f"Running category optimization: {args.category}")
            run_product_category_optimization(loader, logger)
        elif args.lob:
            # Quick LOB mode
            logger.info(f"Running LOB optimization: {args.lob}")
            run_lob_optimization(loader, logger)

if __name__ == "__main__":
    main()