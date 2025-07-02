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
        print("3. All Products (Full store optimization)")  # NEW OPTION
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            run_product_category_optimization(loader, logger)
        elif choice == "2":
            run_lob_optimization(loader, logger)
        elif choice == "3":
            run_full_store_optimization(loader, logger)  # NEW
        else:
            print("Invalid choice. Exiting.")
            return
            
    except Exception as e:
        logger.error(f"Error in interactive mode: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")

def run_product_category_optimization(loader, logger):
    """Run optimization for a specific product category"""
    from src.data_processing.data_transformer import DataTransformer
    from src.data_processing.data_validator import DataValidator
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
        print(f"\n⚠️  Warning: Could not load {category_key} data file")
        print("Attempting to load all products and filter...")
        
        # Try loading all products instead
        try:
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
        except Exception as e2:
            logger.error(f"Failed to load any products: {e2}")
            print(f"\n❌ Error: No product data found. Please check your data files.")
            return
    
    if not products:
        print(f"No products found for category {category_name}")
        return
    
    # Validate data
    validator = DataValidator()
    is_valid, issues = validator.validate_products(products)
    if not is_valid:
        print(f"\n⚠️  Data validation found {len(issues)} issues:")
        for issue in issues[:5]:  # Show first 5 issues
            print(f"  - {issue}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more issues")
    
    # Load store
    store = loader.load_store_template(store_type)
    
    # Step 5: Transform and optimize
    transformer = DataTransformer()
    products = transformer.prepare_products_for_store(products, store, strategy)
    
    # Ensure products have required attributes
    for product in products:
        if not hasattr(product, 'attach_rate'):
            product.attach_rate = 0.0
        if not hasattr(product, 'bundle_frequency'):
            product.bundle_frequency = 0
        if not hasattr(product, 'optimal_facings'):
            product.optimal_facings = product.calculate_facings("balanced")
    
    logger.info(f"Running {strategy} optimization...")
    optimizer = ProductOptimizer(store, gap_size=2.0, strategy=strategy)
    optimizer.products_placed = []
    
    result = optimizer.create_planogram(products)
    
    # Step 6: Visualize and export
    output_name = f"{category_key}_{store_type}_{strategy}"
    title = f"{category_name} - {store_type.title()} Store"
    
    # Add strategy info to title
    if strategy == "profit_efficiency":
        title += " - Profit Maximization"
    else:
        title += f" - {strategy.replace('_', ' ').title()}"
    
    visualize_and_export_results(result, products, output_name, title)

def run_full_store_optimization(loader, logger):
    """Run optimization for all products"""
    from src.data_processing.data_transformer import DataTransformer
    from src.data_processing.data_validator import DataValidator
    from src.optimization.product_optimizer import ProductOptimizer
    
    print("\nRunning full store optimization...")
    
    # Select store type
    store_type = select_store_type(loader)
    if not store_type:
        return
    
    # Select optimization strategy
    strategy = select_optimization_strategy()
    
    # Load all products
    logger.info("Loading all products...")
    try:
        products = loader.load_all_products()
        logger.info(f"Loaded {len(products)} total products")
    except Exception as e:
        logger.error(f"Failed to load products: {e}")
        print(f"\n❌ Error: Could not load product data: {e}")
        return
    
    if not products:
        print("No products found")
        return
    
    # Show product distribution
    from collections import Counter
    category_counts = Counter(p.category.value for p in products)
    print(f"\nProduct distribution:")
    for cat, count in category_counts.most_common():
        print(f"  - {cat}: {count} products")
    
    # Load store
    store = loader.load_store_template(store_type)
    
    # Transform and optimize
    transformer = DataTransformer()
    products = transformer.prepare_products_for_store(products, store, strategy)
    
    logger.info(f"Running {strategy} optimization for full store...")
    optimizer = ProductOptimizer(store, gap_size=2.0, strategy=strategy)
    optimizer.products_placed = []
    
    result = optimizer.create_planogram(products)
    
    # Visualize and export
    output_name = f"full_store_{store_type}_{strategy}"
    title = f"Full Store - {store_type.title()}"
    
    if strategy == "profit_efficiency":
        title += " - Profit Maximization"
    else:
        title += f" - {strategy.replace('_', ' ').title()}"
    
    visualize_and_export_results(result, products, output_name, title)

def select_store_type(loader) -> Optional[str]:
    """Select store type from available templates"""
    available_stores = loader.get_available_stores()
    
    if not available_stores:
        print("\n⚠️  No store templates found!")
        print("Please ensure store templates exist in data/raw/store_templates/")
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
        '2': ('sales_velocity', 'Sales Velocity (prioritize high-quantity items)'),
        '3': ('category_grouped', 'Category Grouped (group similar products)'),
        '4': ('value_density', 'Value Density (maximize revenue per cm)'),
        '5': ('profit_efficiency', 'Profit Efficiency (maximize profit per cm)')  # NEW
    }
    
    for key, (_, desc) in strategies.items():
        print(f"{key}. {desc}")
    
    strat_choice = input("\nSelect strategy (1-5): ").strip()
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
    
    # Create main planogram
    fig = visualizer.visualize_planogram(
        result,
        product_lookup,
        title=title,
        save_path=f"output/{output_name}.png",
        show_metrics=True
    )
    
    # Create additional visualizations
    if hasattr(products[0], 'profit') and any(getattr(p, 'profit', 0) > 0 for p in products):
        # Create profit heatmap
        logger.info("Creating profit heatmap...")
        profit_fig = visualizer.create_profit_heatmap(
            result,
            product_lookup,
            save_path=f"output/{output_name}_profit_heatmap.png"
        )
        print(f"  📊 {output_name}_profit_heatmap.png (profit analysis)")
    
    # Create quantity heatmap
    logger.info("Creating quantity heatmap...")
    qty_fig = visualizer.create_heatmap_view(
        result,
        product_lookup,
        metric='total_qty',  # Use total_qty instead of sales_velocity
        save_path=f"output/{output_name}_quantity_heatmap.png"
    )
    
    # Export
    logger.info("Exporting results...")
    exporter = ExportHandler()
    json_file = exporter.export_to_json(result, product_lookup, f"{output_name}.json")
    excel_file = exporter.export_to_excel(result, product_lookup, f"{output_name}.xlsx")
    csv_files = exporter.export_to_csv(result, product_lookup, output_name)
    
    # Print summary
    print("\n" + "="*60)
    print("OPTIMIZATION COMPLETE")
    print("="*60)
    print(f"Products placed: {len(result.products_placed)}")
    print(f"Products rejected: {len(result.products_rejected)}")
    print(f"Average shelf utilization: {result.metrics.get('average_utilization', 0):.1f}%")
    
    # Show profit metrics if available
    if 'profit_density' in result.metrics:
        print(f"Profit density: ${result.metrics['profit_density']:.2f}/cm")
    if 'quantity_density' in result.metrics:
        print(f"Quantity density: {result.metrics['quantity_density']:.1f} units/cm")
    
    print(f"\nTotal facings: {result.metrics.get('total_facings', 0)}")
    
    # Show category distribution
    if 'category_distribution' in result.metrics:
        print("\nCategory distribution:")
        for cat, facings in result.metrics['category_distribution'].items():
            cat_name = cat.value if hasattr(cat, 'value') else str(cat)
            print(f"  - {cat_name}: {facings} facings")
    
    # Show warnings if any
    if result.warnings:
        print(f"\n⚠️  Warnings ({len(result.warnings)}):")
        for warning in result.warnings[:5]:
            print(f"  - {warning}")
        if len(result.warnings) > 5:
            print(f"  ... and {len(result.warnings) - 5} more warnings")
    
    print(f"\nFiles generated:")
    print(f"  📊 {output_name}.png (visual planogram)")
    print(f"  📊 {output_name}_quantity_heatmap.png (quantity analysis)")
    if hasattr(products[0], 'profit'):
        print(f"  📊 {output_name}_profit_heatmap.png (profit analysis)")
    print(f"  📄 {output_name}.json (data export)")
    print(f"  📑 {output_name}.xlsx (Excel report)")
    print(f"  📃 {len(csv_files)} CSV files")
    
    # Show top products
    print("\nTop 5 placed products by quantity:")
    placed_by_qty = sorted(result.products_placed, key=lambda p: p.total_qty, reverse=True)[:5]
    for i, product in enumerate(placed_by_qty, 1):
        facings = result.metrics.get('facings_by_product', {}).get(product.product_id, 0)
        print(f"  {i}. {product.product_name[:40]:40} | Qty: {product.total_qty:3.0f} | Facings: {facings}")

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
  python main.py --all --store standard --strategy profit_efficiency
        """
    )
    
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Run in interactive mode (default)')
    parser.add_argument('--category', '-c', choices=['cases', 'cables', 'screen_protectors', 'others'],
                       help='Optimize specific product category')
    parser.add_argument('--lob', '-l', choices=['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods'],
                       help='Optimize by Line of Business')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Optimize all products (full store)')
    parser.add_argument('--model', '-m', help='Specific model for LOB (e.g., "iPhone 16 Pro Max")')
    parser.add_argument('--store', '-s', choices=['flagship', 'standard', 'express'],
                       default='standard', help='Store type')
    parser.add_argument('--strategy', choices=['balanced', 'sales_velocity', 'category_grouped', 
                                             'value_density', 'profit_efficiency'],
                       default='balanced', help='Optimization strategy')
    parser.add_argument('--validate', '-v', action='store_true',
                       help='Run data validation before optimization')
    
    args = parser.parse_args()
    
    # If no specific mode selected, run interactive
    if not args.category and not args.lob and not args.all:
        interactive_mode()
    else:
        # Run with command line arguments
        from src.data_processing.data_loader import DataLoader
        from src.utils.logger import get_logger
        
        loader = DataLoader()
        logger = get_logger()
        
        try:
            if args.category:
                # Quick category mode
                logger.info(f"Running category optimization: {args.category}")
                # Implement direct category optimization
                run_direct_category_optimization(loader, logger, args.category, 
                                               args.store, args.strategy)
            elif args.lob:
                # Quick LOB mode
                logger.info(f"Running LOB optimization: {args.lob}")
                # Implement direct LOB optimization
                run_direct_lob_optimization(loader, logger, args.lob, 
                                          args.model, args.store, args.strategy)
            elif args.all:
                # Full store optimization
                logger.info("Running full store optimization")
                run_direct_full_optimization(loader, logger, args.store, args.strategy)
                
        except Exception as e:
            logger.error(f"Error during optimization: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")
            sys.exit(1)

def run_direct_category_optimization(loader, logger, category, store_type, strategy):
    """Direct category optimization from command line"""
    from src.data_processing.data_transformer import DataTransformer
    from src.optimization.product_optimizer import ProductOptimizer
    
    # Load products
    try:
        products = loader.load_products_by_category(category)
    except:
        products = loader.load_all_products()
        from src.models.product import ProductCategory
        cat_map = {
            'cases': ProductCategory.CASE,
            'cables': ProductCategory.CABLE,
            'screen_protectors': ProductCategory.SCREEN_PROTECTOR
        }
        if category in cat_map:
            products = [p for p in products if p.category == cat_map[category]]
    
    if not products:
        raise ValueError(f"No products found for category {category}")
    
    # Load store and optimize
    store = loader.load_store_template(store_type)
    transformer = DataTransformer()
    products = transformer.prepare_products_for_store(products, store, strategy)
    
    optimizer = ProductOptimizer(store, gap_size=2.0, strategy=strategy)
    optimizer.products_placed = []
    result = optimizer.create_planogram(products)
    
    output_name = f"{category}_{store_type}_{strategy}"
    title = f"{category.title()} - {store_type.title()} Store - {strategy.replace('_', ' ').title()}"
    visualize_and_export_results(result, products, output_name, title)

def run_direct_lob_optimization(loader, logger, lob, model, store_type, strategy):
    """Direct LOB optimization from command line"""
    from src.data_processing.data_transformer import DataTransformer
    from src.optimization.bundle_optimizer import BundleOptimizer
    from src.optimization.product_optimizer import ProductOptimizer
    
    # Load products
    if model:
        products = loader.load_products_by_lob(lob, model)
    else:
        products = loader.load_products_by_lob(lob)
    
    if not products:
        raise ValueError(f"No products found for {lob}")
    
    # Load cohort data
    cohort_df = loader.load_cohort_data(lob, model)
    if not cohort_df.empty:
        products = loader.enrich_products_with_cohorts(products, cohort_df)
    
    # Load store and optimize
    store = loader.load_store_template(store_type)
    transformer = DataTransformer()
    products = transformer.prepare_products_for_store(products, store, "cohort_based")
    
    # Use bundle optimizer if we have bundle data
    bundle_df = loader.load_bundle_recommendations()
    if not bundle_df.empty and lob in bundle_df['lob'].values:
        optimizer = BundleOptimizer(store, gap_size=3.0, bundle_data=bundle_df)
    else:
        optimizer = ProductOptimizer(store, gap_size=2.0, strategy=strategy)
    
    optimizer.products_placed = []
    result = optimizer.create_planogram(products)
    
    model_suffix = f"_{model.replace(' ', '_')}" if model else ""
    output_name = f"{lob}{model_suffix}_{store_type}_{strategy}"
    title = f"{lob} Accessories"
    if model:
        title += f" ({model})"
    title += f" - {store_type.title()} Store - {strategy.replace('_', ' ').title()}"
    
    visualize_and_export_results(result, products, output_name, title)

def run_direct_full_optimization(loader, logger, store_type, strategy):
    """Direct full store optimization from command line"""
    from src.data_processing.data_transformer import DataTransformer
    from src.optimization.product_optimizer import ProductOptimizer
    
    # Load all products
    products = loader.load_all_products()
    if not products:
        raise ValueError("No products found")
    
    # Load store and optimize
    store = loader.load_store_template(store_type)
    transformer = DataTransformer()
    products = transformer.prepare_products_for_store(products, store, strategy)
    
    optimizer = ProductOptimizer(store, gap_size=2.0, strategy=strategy)
    optimizer.products_placed = []
    result = optimizer.create_planogram(products)
    
    output_name = f"full_store_{store_type}_{strategy}"
    title = f"Full Store - {store_type.title()} - {strategy.replace('_', ' ').title()}"
    visualize_and_export_results(result, products, output_name, title)

if __name__ == "__main__":
    main()        