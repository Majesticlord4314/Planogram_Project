import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path
import os

from src.models.product import Product
from src.optimization.base_optimizer import OptimizationResult
from src.utils.logger import get_logger

class ExcelExporter:
    """Export planogram data to Excel format for easy reading"""
    
    def __init__(self):
        self.logger = get_logger()
    
    def export_planogram_to_excel(self, 
                                result: OptimizationResult,
                                product_lookup: Dict[str, Product],
                                filename: str,
                                title: str = "Planogram Export") -> str:
        """Export complete planogram data to Excel file"""
        
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Full file path
        excel_path = output_dir / f"{filename}.xlsx"
        
        # Create Excel writer
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            
            # Sheet 1: Product Details
            products_df = self._create_products_sheet(result, product_lookup)
            products_df.to_excel(writer, sheet_name='Product Details', index=False)
            
            # Sheet 2: Shelf Layout
            layout_df = self._create_layout_sheet(result, product_lookup)
            layout_df.to_excel(writer, sheet_name='Shelf Layout', index=False)
            
            # Sheet 3: Category Summary
            category_df = self._create_category_summary(result, product_lookup)
            category_df.to_excel(writer, sheet_name='Category Summary', index=False)
            
            # Sheet 4: Performance Metrics
            metrics_df = self._create_metrics_sheet(result)
            metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
            
            # Sheet 5: Grid Reference (Position Map)
            grid_df = self._create_grid_reference(result, product_lookup)
            grid_df.to_excel(writer, sheet_name='Grid Reference', index=False)
        
        self.logger.info(f"Excel export saved to {excel_path}")
        return str(excel_path)
    
    def _create_products_sheet(self, result: OptimizationResult, product_lookup: Dict[str, Product]) -> pd.DataFrame:
        """Create detailed product information sheet"""
        
        products_data = []
        position_counter = 1
        
        # Process placed products
        for shelf in result.store.shelves:
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    
                    products_data.append({
                        'Position #': position_counter,
                        'Shelf': shelf.shelf_name,
                        'Shelf Level': self._get_shelf_level(shelf.eye_level_score),
                        'Product Name': product.product_name,
                        'Brand': product.brand,
                        'Category': product.category.value.replace('_', ' ').title(),
                        'Series': product.series,
                        'Subcategory': product.subcategory,
                        'Facings': position.facings,
                        'Width (cm)': product.width,
                        'Height (cm)': product.height,
                        'Total Qty Sold': product.total_qty,
                        'Pure Qty': product.pureqty,
                        'Impure Qty': product.impureqty,
                        'Sales Velocity': getattr(product, 'sales_velocity', product.total_qty),
                        'Price': getattr(product, 'price', 'N/A'),
                        'Profit': getattr(product, 'profit', 'N/A'),
                        'Attach Rate': getattr(product, 'attach_rate', 'N/A'),
                        'Status': getattr(product, 'status', 'Active'),
                        'X Position (cm)': f"{position.x_start:.1f} - {position.x_end:.1f}",
                        'Product Width (cm)': position.width,
                        'Performance': self._get_performance_tier(product.total_qty)
                    })
                    position_counter += 1
        
        return pd.DataFrame(products_data)
    
    def _create_layout_sheet(self, result: OptimizationResult, product_lookup: Dict[str, Product]) -> pd.DataFrame:
        """Create shelf-by-shelf layout view"""
        
        layout_data = []
        
        for shelf in result.store.shelves:
            shelf_products = []
            total_facings = 0
            
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    short_name = self._shorten_name(product.product_name)
                    shelf_products.append(f"{short_name} ({position.facings}x)")
                    total_facings += position.facings
            
            layout_data.append({
                'Shelf Name': shelf.shelf_name,
                'Shelf Type': shelf.shelf_type.title(),
                'Eye Level Score': f"{shelf.eye_level_score:.1f}",
                'Dimensions (W×H)': f"{shelf.width}×{shelf.height} cm",
                'Utilization %': f"{shelf.utilization:.1f}%",
                'Total Products': len(shelf.positions),
                'Total Facings': total_facings,
                'Products (Facings)': ' | '.join(shelf_products) if shelf_products else 'Empty'
            })
        
        return pd.DataFrame(layout_data)
    
    def _create_category_summary(self, result: OptimizationResult, product_lookup: Dict[str, Product]) -> pd.DataFrame:
        """Create category distribution summary"""
        
        category_stats = {}
        
        # Initialize categories
        for shelf in result.store.shelves:
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    cat_name = product.category.value.replace('_', ' ').title()
                    
                    if cat_name not in category_stats:
                        category_stats[cat_name] = {
                            'Products': 0,
                            'Total Facings': 0,
                            'Total Sales': 0,
                            'Avg Price': 0,
                            'Top Seller': '',
                            'Brands': set()
                        }
                    
                    category_stats[cat_name]['Products'] += 1
                    category_stats[cat_name]['Total Facings'] += position.facings
                    category_stats[cat_name]['Total Sales'] += product.total_qty
                    category_stats[cat_name]['Brands'].add(product.brand)
                    
                    # Track top seller
                    if not category_stats[cat_name]['Top Seller'] or product.total_qty > 0:
                        category_stats[cat_name]['Top Seller'] = product.product_name
        
        # Convert to DataFrame format
        summary_data = []
        for category, stats in category_stats.items():
            summary_data.append({
                'Category': category,
                'Number of Products': stats['Products'],
                'Total Facings': stats['Total Facings'],
                'Total Sales Volume': stats['Total Sales'],
                'Avg Facings per Product': f"{stats['Total Facings'] / max(stats['Products'], 1):.1f}",
                'Brands': ', '.join(sorted(stats['Brands'])),
                'Top Selling Product': self._shorten_name(stats['Top Seller'])
            })
        
        # Sort by total facings
        summary_data.sort(key=lambda x: x['Total Facings'], reverse=True)
        
        return pd.DataFrame(summary_data)
    
    def _create_metrics_sheet(self, result: OptimizationResult) -> pd.DataFrame:
        """Create performance metrics sheet"""
        
        metrics_data = [
            {'Metric': 'Total Products Placed', 'Value': len(result.products_placed)},
            {'Metric': 'Total Products Rejected', 'Value': len(result.products_rejected)},
            {'Metric': 'Placement Success Rate', 'Value': f"{len(result.products_placed) / (len(result.products_placed) + len(result.products_rejected)) * 100:.1f}%"},
            {'Metric': 'Total Facings', 'Value': result.metrics.get('total_facings', 0)},
            {'Metric': 'Average Shelf Utilization', 'Value': f"{result.metrics.get('average_utilization', 0):.1f}%"},
            {'Metric': 'Optimization Time', 'Value': f"{result.optimization_time:.3f} seconds"},
            {'Metric': 'Profit Density', 'Value': f"${result.metrics.get('profit_density', 0):.2f}/cm"},
            {'Metric': 'Quantity Density', 'Value': f"{result.metrics.get('quantity_density', 0):.1f} units/cm"},
            {'Metric': 'Total Shelves', 'Value': len(result.store.shelves)},
            {'Metric': 'Store Type', 'Value': result.store.store_type.title()},
        ]
        
        # Add shelf utilization details
        if 'shelf_utilization' in result.metrics:
            for shelf_info in result.metrics['shelf_utilization']:
                metrics_data.append({
                    'Metric': f"{shelf_info['shelf_name']} Utilization",
                    'Value': f"{shelf_info['utilization']:.1f}% ({shelf_info['products']} products)"
                })
        
        return pd.DataFrame(metrics_data)
    
    def _create_grid_reference(self, result: OptimizationResult, product_lookup: Dict[str, Product]) -> pd.DataFrame:
        """Create a grid reference map showing positions like A1, A2, etc."""
        
        # Create a grid representation
        grid_data = []
        
        for shelf_idx, shelf in enumerate(result.store.shelves):
            shelf_letter = chr(65 + shelf_idx)  # A, B, C, etc.
            
            # Sort positions by x_start to get left-to-right order
            sorted_positions = sorted(shelf.positions, key=lambda p: p.x_start)
            
            for pos_idx, position in enumerate(sorted_positions):
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    
                    grid_data.append({
                        'Grid Position': f"{shelf_letter}{pos_idx + 1}",
                        'Shelf': shelf.shelf_name,
                        'Position Order': pos_idx + 1,
                        'Product Name': product.product_name,
                        'Brand': product.brand,
                        'Facings': position.facings,
                        'Category': product.category.value.replace('_', ' ').title(),
                        'Sales Qty': product.total_qty,
                        'X Position': f"{position.x_start:.1f}cm",
                        'Width': f"{position.width:.1f}cm"
                    })
        
        return pd.DataFrame(grid_data)
    
    def _get_shelf_level(self, eye_level_score: float) -> str:
        """Convert eye level score to readable level"""
        if eye_level_score >= 0.8:
            return "Eye Level"
        elif eye_level_score >= 0.6:
            return "Upper"
        elif eye_level_score >= 0.4:
            return "Mid"
        else:
            return "Lower"
    
    def _get_performance_tier(self, total_qty: float) -> str:
        """Categorize product performance"""
        if total_qty >= 500:
            return "Top Performer"
        elif total_qty >= 300:
            return "High Performer"
        elif total_qty >= 100:
            return "Good Performer"
        elif total_qty >= 50:
            return "Average Performer"
        else:
            return "Low Performer"
    
    def _shorten_name(self, name: str, max_length: int = 40) -> str:
        """Shorten product names for display"""
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."
