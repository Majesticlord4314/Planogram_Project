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
            # Calculate priority score with proper None handling
            
            # Sales score
            if hasattr(product, 'sales_velocity') and product.sales_velocity is not None:
                sales_score = product.sales_velocity * weights.get('sales_velocity', 0.3)
            else:
                # Use total_qty as fallback
                sales_score = product.total_qty * weights.get('sales_velocity', 0.3)
            
            # Attach score - handle None values properly
            attach_rate = getattr(product, 'attach_rate', 0)
            if attach_rate is None:
                attach_rate = 0
            attach_score = float(attach_rate) * weights.get('attach_rate', 0.3)
            
            # New product score
            new_product_score = 0
            if hasattr(product, 'status') and product.status is not None:
                try:
                    if product.status.value == 'new':
                        new_product_score = 1.0 * weights.get('new_product_priority', 0.2)
                except AttributeError:
                    # status might not be an enum
                    if str(product.status).lower() == 'new':
                        new_product_score = 1.0 * weights.get('new_product_priority', 0.2)
            
            product.priority_score = sales_score + attach_score + new_product_score
        
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
            # Validate basic dimensions first
            if product.height > shelf.height:
                self.logger.debug(f"Product {product.product_name} too tall ({product.height}cm) for shelf {shelf.shelf_name} ({shelf.height}cm)")
                return False
            
            if hasattr(product, 'depth') and hasattr(shelf, 'depth') and product.depth > shelf.depth:
                self.logger.debug(f"Product {product.product_name} too deep ({product.depth}cm) for shelf {shelf.shelf_name} ({shelf.depth}cm)")
                return False
            
            # Calculate required width
            product_width = product.width * facings
            
            # Calculate position
            if shelf.positions:
                # Place after last product with gap
                last_pos = max(shelf.positions, key=lambda p: p.x_end)
                x_position = last_pos.x_end + self.gap_size
            else:
                x_position = self.gap_size  # Start with gap from edge
            
            # Check if fits with end gap
            total_needed = x_position + product_width + self.gap_size
            if total_needed > shelf.width:
                # Try with minimum facings if we have more than minimum
                if facings > 1 and facings > (product.min_facings or 1):
                    min_facings = max(1, product.min_facings or 1)
                    self.logger.debug(f"Reducing facings from {facings} to {min_facings} for {product.product_name}")
                    return self._place_product_on_shelf(shelf, product, min_facings)
                
                self.logger.debug(f"Product {product.product_name} doesn't fit on shelf {shelf.shelf_name}: need {total_needed:.1f}cm, have {shelf.width}cm")
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
            if 'category_distribution' not in self.metrics:
                self.metrics['category_distribution'] = {}
            if product.category not in self.metrics['category_distribution']:
                self.metrics['category_distribution'][product.category] = 0
            self.metrics['category_distribution'][product.category] += facings
            
            self.logger.debug(f"Successfully placed {product.product_name} on {shelf.shelf_name}: {facings} facings, {product_width:.1f}cm wide at position {x_position:.1f}cm")
            
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
            'profit_density': 0,
            'quantity_density': 0
        }
        
        total_profit = 0
        total_quantity = 0
        total_width_used = 0
        
        # Check if we have products placed
        if not hasattr(self, 'products_placed'):
            self.products_placed = []
        
        # First, ensure all shelves are updated
        for shelf in self.store.shelves:
            shelf.update_utilization()
        
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
                # Find product from the list of placed products
                product = None
                for p in self.products_placed:
                    if p.product_id == pos.product_id:
                        product = p
                        break
                
                if product:
                    # Update category distribution
                    cat_key = product.category
                    if cat_key not in metrics['category_distribution']:
                        metrics['category_distribution'][cat_key] = 0
                    metrics['category_distribution'][cat_key] += pos.facings
                    
                    # Use profit if available, otherwise use price as fallback
                    profit_per_unit = getattr(product, 'profit', getattr(product, 'price', 0))
                    if profit_per_unit is None:
                        profit_per_unit = 0
                    
                    profit = float(profit_per_unit) * product.total_qty * pos.facings
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
        
        # Merge with existing metrics (preserve category_distribution from placement)
        if hasattr(self, 'metrics') and self.metrics:
            # Preserve the category distribution from placement process
            if 'category_distribution' in self.metrics and self.metrics['category_distribution']:
                metrics['category_distribution'].update(self.metrics['category_distribution'])
        
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