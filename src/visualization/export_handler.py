import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from enum import Enum

from src.models.product import Product
from src.optimization.base_optimizer import OptimizationResult
from src.utils.logger import get_logger


def _recursive_convert(obj: Any) -> Any:
    """
    Recursively convert:
    - Dict keys that are Enums to their .value
    - Enum values to .value
    - Process nested lists and dicts
    """
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            # convert key
            new_key = k.value if isinstance(k, Enum) else k
            new_dict[new_key] = _recursive_convert(v)
        return new_dict
    elif isinstance(obj, list):
        return [_recursive_convert(item) for item in obj]
    elif isinstance(obj, Enum):
        return obj.value
    else:
        return obj

class ExportHandler:
    """Handle exporting planogram data in various formats"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = get_logger()
    
    def export_to_json(
        self,
        result: OptimizationResult, 
        product_lookup: Dict[str, Product],
        filename: str = "planogram.json"
    ) -> str:
        """Export planogram to JSON format"""
        
        export_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'store_type': result.store.store_type,
                'store_name': result.store.store_name,
                'optimization_time': result.optimization_time,
                'success': result.success
            },
            'metrics': result.metrics,
            'shelves': [],
            'products': {},
            'warnings': result.warnings
        }
        
        # Add shelf data
        for shelf in result.store.shelves:
            shelf_data = {
                'shelf_id': shelf.shelf_id,
                'shelf_name': shelf.shelf_name,
                'dimensions': {
                    'width': shelf.width,
                    'height': shelf.height,
                    'depth': shelf.depth
                },
                'y_position': shelf.y_position,
                'utilization': shelf.utilization,
                'products': []
            }
            
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    shelf_data['products'].append({
                        'product_id': position.product_id,
                        'product_name': product.product_name,
                        'x_start': position.x_start,
                        'x_end': position.x_end,
                        'facings': position.facings
                    })
                    
                    if position.product_id not in export_data['products']:
                        export_data['products'][position.product_id] = {
                            'name': product.product_name,
                            'category': product.category,
                            'price': product.price,
                            'dimensions': {
                                'width': product.width,
                                'height': product.height,
                                'depth': product.depth
                            }
                        }
            
            export_data['shelves'].append(shelf_data)
        
        # Convert any Enum keys/values recursively
        cleaned = _recursive_convert(export_data)

        # Write JSON
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(cleaned, f, indent=2)
        
        self.logger.info(f"Exported planogram to {filepath}")
        return str(filepath)
    
    def export_to_excel(
        self,
        result: OptimizationResult,
        product_lookup: Dict[str, Product],
        filename: str = "planogram.xlsx"
    ) -> str:
        """Export planogram to Excel format"""
        
        filepath = self.output_dir / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: Summary
            summary_data = {
                'Metric': [
                    'Total Products', 'Total Facings', 'Products Placed', 
                    'Products Rejected', 'Average Utilization', 'Optimization Time'
                ],
                'Value': [
                    len(product_lookup),
                    result.metrics.get('total_facings', 0),
                    len(result.products_placed),
                    len(result.products_rejected),
                    f"{result.metrics.get('average_utilization', 0):.1f}%",
                    f"{result.optimization_time:.2f}s"
                ]
            }
            pd.DataFrame(summary_data).to_excel(
                writer, sheet_name='Summary', index=False
            )
            
            # Sheet 2: Shelf Details
            shelf_data = []
            for shelf in result.store.shelves:
                for position in shelf.positions:
                    if position.product_id in product_lookup:
                        product = product_lookup[position.product_id]
                        shelf_data.append({
                            'Shelf ID': shelf.shelf_id,
                            'Shelf Name': shelf.shelf_name,
                            'Product ID': position.product_id,
                            'Product Name': product.product_name,
                            'Category': product.category.value,
                            'X Position': position.x_start,
                            'Width': position.width,
                            'Facings': position.facings,
                            'Price': product.price,
                            'Sales/Day': getattr(product, 'sales_velocity', None)
                        })
            
            if shelf_data:
                pd.DataFrame(shelf_data).to_excel(
                    writer, sheet_name='Shelf Details', index=False
                )
            
            # Sheet 3: Product List
            product_data = []
            for product in result.products_placed:
                product_data.append({
                    'Product ID': product.product_id,
                    'Product Name': product.product_name,
                    'Category': product.category.value,
                    'Status': 'Placed',
                    'Facings': result.metrics.get('facings_by_product', {}).get(product.product_id, 0)
                })
            
            for product in result.products_rejected:
                product_data.append({
                    'Product ID': product.product_id,
                    'Product Name': product.product_name,
                    'Category': product.category.value,
                    'Status': 'Rejected',
                    'Facings': 0
                })
            
            if product_data:
                pd.DataFrame(product_data).to_excel(
                    writer, sheet_name='Products', index=False
                )
        
        self.logger.info(f"Exported planogram to {filepath}")
        return str(filepath)
    
    def export_to_csv(
        self,
        result: OptimizationResult,
        product_lookup: Dict[str, Product],
        filename_prefix: str = "planogram"
    ) -> List[str]:
        """Export planogram to multiple CSV files"""
        
        files_created = []
        
        # Export shelf positions
        positions_file = self.output_dir / f"{filename_prefix}_positions.csv"
        positions_data = []
        
        for shelf in result.store.shelves:
            for position in shelf.positions:
                if position.product_id in product_lookup:
                    product = product_lookup[position.product_id]
                    positions_data.append({
                        'shelf_id': shelf.shelf_id,
                        'shelf_name': shelf.shelf_name,
                        'product_id': position.product_id,
                        'product_name': product.product_name,
                        'x_start': position.x_start,
                        'x_end': position.x_end,
                        'facings': position.facings
                    })
        
        pd.DataFrame(positions_data).to_csv(positions_file, index=False)
        files_created.append(str(positions_file))
        
        # Export metrics
        metrics_file = self.output_dir / f"{filename_prefix}_metrics.csv"
        metrics_data = []
        for key, value in result.metrics.items():
            if not isinstance(value, dict):
                metrics_data.append({'metric': key, 'value': value})
        
        pd.DataFrame(metrics_data).to_csv(metrics_file, index=False)
        files_created.append(str(metrics_file))
        
        self.logger.info(f"Exported {len(files_created)} CSV files")
        return files_created
