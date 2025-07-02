from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import time
import sys
from pathlib import Path

# Fix imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.product import Product, ProductCategory
from src.models.shelf import Shelf, ShelfPosition
from src.models.store import Store
from src.utils.logger import get_logger
from src.utils.error_handler import OptimizationError, handle_errors
from src.utils.monitor import monitor

# Rest of the file remains the same...

@dataclass
class OptimizationResult:
    """Result of optimization process"""
    success: bool
    store: Store
    products_placed: List[Product]
    products_rejected: List[Product]
    metrics: Dict[str, float]
    warnings: List[str] = field(default_factory=list)
    optimization_time: float = 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get optimization summary"""
        return {
            'success': self.success,
            'products_placed': len(self.products_placed),
            'products_rejected': len(self.products_rejected),
            'total_facings': sum(self.metrics.get('facings_by_product', {}).values()),
            'space_utilization': self.metrics.get('average_utilization', 0),
            'optimization_time': self.optimization_time,
            'warnings': len(self.warnings)
        }

class BaseOptimizer(ABC):
    """Base class for all optimization strategies"""
    
    def __init__(self, store: Store, gap_size: float = 2.0):
        self.store = store
        self.gap_size = gap_size
        self.logger = get_logger()
        self.metrics = {}
        self.warnings = []
        
    @abstractmethod
    def optimize(self, products: List[Product], **kwargs) -> OptimizationResult:
        """Main optimization method to be implemented by subclasses"""
        pass
    
    def _reset_shelves(self):
        """Clear all product positions from shelves"""
        for shelf in self.store.shelves:
            shelf.positions = []
            shelf.update_utilization()
    
    def _sort_products_by_priority(self, products: List[Product]) -> List[Product]:
        """Sort products by priority based on store optimization weights"""
        weights = self.store.optimization_weights
        
        for product in products:
            # Sales score based on total quantity (normalized)
            max_qty = max(p.total_qty for p in products) if products else 1
            sales_score = (product.total_qty / max_qty) * weights.get('sales_velocity', 0.3)
            
            # Profit score
            profit_score = 0
            if hasattr(product, 'profit'):
                max_profit = max(getattr(p, 'profit', 0) for p in products) if products else 1
                profit_score = (product.profit / max_profit) * weights.get('profitability', 0.3)
            
            # Attach rate score
            attach_score = getattr(product, 'attach_rate', 0) * weights.get('attach_rate', 0.2)
            
            # New product score
            new_product_score = (1.0 if hasattr(product, 'status') and product.status.value == 'new' else 0) * weights.get('new_product_priority', 0.2)
            
            product.priority_score = sales_score + profit_score + attach_score + new_product_score
        
        return sorted(products, key=lambda p: p.priority_score, reverse=True)
    
    def _group_by_category(self, products: List[Product]) -> Dict[ProductCategory, List[Product]]:
        """Group products by category"""
        grouped = {}
        for product in products:
            if product.category not in grouped:
                grouped[product.category] = []
            grouped[product.category].append(product)
        return grouped
    
    def _find_best_shelf_for_product(self, product: Product, 
                                    required_width: float,
                                    category_preferences: Optional[Dict] = None) -> Optional[Shelf]:
        """Find the best available shelf for a product"""
        candidate_shelves = []
        
        for shelf in self.store.shelves:
            # Check if product fits
            if not shelf.can_fit_product(product, int(required_width / product.width)):
                continue
                
            # Calculate placement score
            score = shelf.get_placement_score(product)
            
            # Apply category preferences if provided
            if category_preferences and product.category in category_preferences:
                if shelf.shelf_id in category_preferences[product.category]:
                    score += 0.5  # Bonus for preferred shelf
            
            candidate_shelves.append((shelf, score))
        
        if not candidate_shelves:
            return None
            
        # Return shelf with highest score
        candidate_shelves.sort(key=lambda x: x[1], reverse=True)
        return candidate_shelves[0][0]
    
    def _place_product_on_shelf(self, shelf: Shelf, product: Product, facings: int) -> bool:
        """Place a product on a specific shelf"""
        try:
            # Calculate position
            if shelf.positions:
                # Place after last product with gap
                last_pos = max(shelf.positions, key=lambda p: p.x_end)
                x_position = last_pos.x_end + self.gap_size
            else:
                x_position = self.gap_size  # Start with gap from edge
            
            # Check if fits
            product_width = product.width * facings
            if x_position + product_width > shelf.width - self.gap_size:
                return False
            
            # Create position
            position = ShelfPosition(
                product_id=product.product_id,
                x_start=x_position,
                x_end=x_position + product_width,
                facings=facings
            )
            
            shelf.positions.append(position)
            shelf.update_utilization()
            
            # Update metrics
            if product.category not in self.metrics.get('category_distribution', {}):
                self.metrics.setdefault('category_distribution', {})[product.category] = 0
            self.metrics['category_distribution'][product.category] += facings
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error placing product {product.product_id}: {e}")
            return False
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate optimization metrics"""
        metrics = {
            'total_products': 0,
            'total_facings': 0,
            'category_distribution': {},
            'shelf_utilization': [],
            'average_utilization': 0,
            'facings_by_product': {},
            'profit_density': 0,  # CHANGED from value_density
            'quantity_density': 0  # ADD THIS for quantity-based metric
        }
        
        total_profit = 0  # CHANGED from total_value
        total_quantity = 0  # ADD THIS
        total_width_used = 0
        
        for shelf in self.store.shelves:
            shelf_facings = sum(pos.facings for pos in shelf.positions)
            metrics['total_products'] += len(shelf.positions)
            metrics['total_facings'] += shelf_facings
            
            metrics['shelf_utilization'].append({
                'shelf_id': shelf.shelf_id,
                'shelf_name': shelf.shelf_name,
                'utilization': shelf.utilization,
                'products': len(shelf.positions),
                'facings': shelf_facings
            })
            
            # Calculate profit and quantity on shelf
            for pos in shelf.positions:
                product = next((p for p in self.products_placed if p.product_id == pos.product_id), None)
                if product:
                    # Use profit if available, otherwise use price as fallback
                    profit_per_unit = getattr(product, 'profit', getattr(product, 'price', 0))
                    profit = profit_per_unit * product.total_qty * pos.facings
                    total_profit += profit
                    
                    # Add quantity metric
                    quantity = product.total_qty * pos.facings
                    total_quantity += quantity
                    
                    total_width_used += pos.width
                    
                    metrics['facings_by_product'][product.product_id] = pos.facings
        
        # Calculate averages
        if self.store.shelves:
            total_util = sum(shelf.utilization for shelf in self.store.shelves)
            metrics['average_utilization'] = total_util / len(self.store.shelves)
        
        if total_width_used > 0:
            metrics['profit_density'] = total_profit / total_width_used
            metrics['quantity_density'] = total_quantity / total_width_used
        
        # Merge with existing metrics
        metrics.update(self.metrics)
        
        return metrics
    
    def _validate_placement(self) -> List[str]:
        """Validate the placement and return any issues"""
        issues = []
        
        # Check minimum utilization
        for shelf in self.store.shelves:
            if shelf.utilization < 20 and len(shelf.positions) > 0:
                issues.append(f"Shelf {shelf.shelf_name} is underutilized ({shelf.utilization:.1f}%)")
        
        # Check category mixing if grouping is required
        if self.store.placement_rules.get('category_grouping', False):
            for shelf in self.store.shelves:
                categories = set()
                for pos in shelf.positions:
                    product = next((p for p in self.products_placed if p.product_id == pos.product_id), None)
                    if product:
                        categories.add(product.category)
                
                if len(categories) > 3:
                    issues.append(f"Shelf {shelf.shelf_name} has too many categories ({len(categories)})")
        
        return issues
    
    def _apply_store_rules(self, products: List[Product]) -> List[Product]:
        """Apply store-specific filtering rules"""
        return self.store.filter_products_by_rules(products)
    
    @handle_errors(raise_on_error=True)
    def create_planogram(self, products: List[Product], **kwargs) -> OptimizationResult:
        """Main entry point for creating a planogram"""
        start_time = time.time()
        self.logger.info(f"Starting optimization with {len(products)} products")
        
        # Reset state
        self._reset_shelves()
        self.metrics = {}
        self.warnings = []
        self.products_placed = []
        
        try:
            # Apply store rules
            filtered_products = self._apply_store_rules(products)
            self.logger.info(f"After store filtering: {len(filtered_products)} products")
            
            if not filtered_products:
                raise OptimizationError("No products remain after filtering")
            
            # Run optimization
            result = self.optimize(filtered_products, **kwargs)
            
            # Calculate final metrics
            result.metrics = self._calculate_metrics()
            
            # Validate placement
            validation_issues = self._validate_placement()
            result.warnings.extend(validation_issues)
            
            # Set optimization time
            result.optimization_time = time.time() - start_time
            
            self.logger.info(f"Optimization completed in {result.optimization_time:.2f}s")
            self.logger.info(f"Placed {len(result.products_placed)} products with {result.metrics['total_facings']} facings")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            raise OptimizationError(f"Optimization failed: {str(e)}")