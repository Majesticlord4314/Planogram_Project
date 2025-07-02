from typing import List, Dict, Optional, Tuple
import numpy as np
from src.models.product import Product, ProductCategory
from src.models.shelf import Shelf
from .base_optimizer import BaseOptimizer, OptimizationResult
from src.utils.monitor import monitor

class ProductOptimizer(BaseOptimizer):
    """Optimizer for product-based planogram generation"""
    
    def __init__(self, store, gap_size: float = 2.0, strategy: str = "balanced"):
        super().__init__(store, gap_size)
        self.strategy = strategy
        self.category_shelf_assignments = {}
    
    @monitor.time_it
    def optimize(self, products: List[Product], **kwargs) -> OptimizationResult:
        """Optimize product placement based on selected strategy"""
        self.logger.info(f"Running product optimization with strategy: {self.strategy}")
        
        # Sort products by priority
        sorted_products = self._sort_products_by_priority(products)
        
        # Apply strategy-specific optimization
        if self.strategy == "sales_velocity":
            result = self._optimize_by_sales(sorted_products)
        elif self.strategy == "category_grouped":
            result = self._optimize_by_category(sorted_products)
        elif self.strategy == "value_density":
            result = self._optimize_by_value(sorted_products)
        else:  # balanced
            result = self._optimize_balanced(sorted_products)
        
        return result
    
    def _optimize_by_sales(self, products: List[Product]) -> OptimizationResult:
        """Optimize based on sales velocity"""
        products_placed = []
        products_rejected = []
        
        # Sort by sales velocity
        products.sort(key=lambda p: p.sales_velocity, reverse=True)
        
        # Assign high-velocity products to eye-level shelves
        eye_level_shelves = [s for s in self.store.shelves if s.eye_level_score >= 0.7]
        other_shelves = [s for s in self.store.shelves if s.eye_level_score < 0.7]
        
        # Place high-velocity items first
        for product in products:
            placed = False
            optimal_facings = product.calculate_facings("sales_based")
            
            # Try eye-level shelves first for top products
            if product.sales_velocity > 10:  # High velocity threshold
                for shelf in eye_level_shelves:
                    if self._try_place_product(shelf, product, optimal_facings):
                        products_placed.append(product)
                        placed = True
                        break
            
            # Try other shelves
            if not placed:
                for shelf in other_shelves + eye_level_shelves:
                    if self._try_place_product(shelf, product, optimal_facings):
                        products_placed.append(product)
                        placed = True
                        break
            
            if not placed:
                products_rejected.append(product)
                self.warnings.append(f"Could not place {product.product_name} (sales: {product.sales_velocity:.1f}/day)")
        
        return OptimizationResult(
            success=len(products_placed) > 0,
            store=self.store,
            products_placed=products_placed,
            products_rejected=products_rejected,
            metrics=self.metrics,
            warnings=self.warnings
        )
    
    def _optimize_by_category(self, products: List[Product]) -> OptimizationResult:
        """Optimize with category grouping"""
        products_placed = []
        products_rejected = []
        
        # Group products by category
        category_groups = self._group_by_category(products)
        
        # Calculate category priorities based on total value
        category_priorities = []
        for category, cat_products in category_groups.items():
            total_value = sum(p.price * p.sales_velocity for p in cat_products)
            category_priorities.append((category, total_value, cat_products))
        
        # Sort categories by priority
        category_priorities.sort(key=lambda x: x[1], reverse=True)
        
        # Assign categories to shelf zones
        shelf_assignments = self._assign_categories_to_shelves(category_priorities)
        
        # Place products by category
        for category, assigned_shelves in shelf_assignments.items():
            cat_products = category_groups[category]
            # Sort products within category by sales
            cat_products.sort(key=lambda p: p.sales_velocity, reverse=True)
            
            for product in cat_products:
                placed = False
                optimal_facings = product.calculate_facings("balanced")
                
                # Try assigned shelves first
                for shelf_id in assigned_shelves:
                    shelf = next(s for s in self.store.shelves if s.shelf_id == shelf_id)
                    if self._try_place_product(shelf, product, optimal_facings):
                        products_placed.append(product)
                        placed = True
                        break
                
                if not placed:
                    products_rejected.append(product)
                    self.warnings.append(f"Could not place {product.product_name} in category {category.value}")
        
        return OptimizationResult(
            success=len(products_placed) > 0,
            store=self.store,
            products_placed=products_placed,
            products_rejected=products_rejected,
            metrics=self.metrics,
            warnings=self.warnings
        )
    
    def _optimize_by_value(self, products: List[Product]) -> OptimizationResult:
        """Optimize based on value density (profit per cm)"""
        products_placed = []
        products_rejected = []
        
        # Calculate value density for each product
        for product in products:
            value_per_unit = product.price * product.sales_velocity
            space_per_unit = product.width
            product.value_density = value_per_unit / space_per_unit
        
        # Sort by value density
        products.sort(key=lambda p: p.value_density, reverse=True)
        
        # Place high-value-density items at prime locations
        for product in products:
            placed = False
            
            # Fewer facings for high-value items to maximize variety
            if product.price > 50:
                optimal_facings = max(product.min_facings, 2)
            else:
                optimal_facings = product.calculate_facings("balanced")
            
            # Try shelves by eye-level score
            shelves_by_score = sorted(self.store.shelves, 
                                    key=lambda s: s.eye_level_score, 
                                    reverse=True)
            
            for shelf in shelves_by_score:
                if self._try_place_product(shelf, product, optimal_facings):
                    products_placed.append(product)
                    placed = True
                    break
            
            if not placed:
                products_rejected.append(product)
        
        return OptimizationResult(
            success=len(products_placed) > 0,
            store=self.store,
            products_placed=products_placed,
            products_rejected=products_rejected,
            metrics=self.metrics,
            warnings=self.warnings
        )
    
    def _optimize_balanced(self, products: List[Product]) -> OptimizationResult:
        """Balanced optimization considering multiple factors"""
        products_placed = []
        products_rejected = []
        
        # Calculate composite scores
        for product in products:
            sales_score = min(product.sales_velocity / 20, 1.0)
            value_score = min(product.price / 100, 1.0)
            attach_score = getattr(product, 'attach_rate', 0)
            
            # Weighted combination
            product.composite_score = (
                sales_score * 0.4 +
                value_score * 0.3 +
                attach_score * 0.3
            )
        
        # Sort by composite score
        products.sort(key=lambda p: p.composite_score, reverse=True)
        
        # Group by category if required
        if self.store.placement_rules.get('category_grouping', False):
            return self._optimize_by_category(products)
        
        # Otherwise, place by score with smart shelf selection
        for product in products:
            placed = False
            optimal_facings = product.calculate_facings("balanced")
            
            # Find best shelf based on product characteristics
            best_shelf = self._find_optimal_shelf_for_product(product)
            
            if best_shelf and self._try_place_product(best_shelf, product, optimal_facings):
                products_placed.append(product)
                placed = True
            else:
                # Try any available shelf
                for shelf in self.store.shelves:
                    if self._try_place_product(shelf, product, optimal_facings):
                        products_placed.append(product)
                        placed = True
                        break
            
            if not placed:
                products_rejected.append(product)
        
        # Run post-optimization improvements
        self._post_optimization_improvements(products_placed)
        
        return OptimizationResult(
            success=len(products_placed) > 0,
            store=self.store,
            products_placed=products_placed,
            products_rejected=products_rejected,
            metrics=self.metrics,
            warnings=self.warnings
        )
    
    def _assign_categories_to_shelves(self, category_priorities: List[Tuple]) -> Dict[ProductCategory, List[int]]:
        """Assign categories to specific shelves"""
        assignments = {}
        
        # Group shelves by level
        eye_level = [s.shelf_id for s in self.store.shelves if s.eye_level_score >= 0.8]
        mid_level = [s.shelf_id for s in self.store.shelves if 0.4 <= s.eye_level_score < 0.8]
        low_level = [s.shelf_id for s in self.store.shelves if s.eye_level_score < 0.4]
        
        shelf_groups = [eye_level, mid_level, low_level]
        
        # Assign high-priority categories to better shelf positions
        for i, (category, _, _) in enumerate(category_priorities):
            # Rotate through shelf groups
            assigned_group = shelf_groups[i % len(shelf_groups)]
            assignments[category] = assigned_group
            
            # Record assignment
            self.category_shelf_assignments[category] = assigned_group
        
        return assignments
    
    def _try_place_product(self, shelf: Shelf, product: Product, facings: int) -> bool:
        """Try to place a product on a shelf with given facings"""
        # Check if product fits
        if not shelf.can_fit_product(product, facings):
            # Try with minimum facings
            if facings > product.min_facings:
                facings = product.min_facings
                if not shelf.can_fit_product(product, facings):
                    return False
            else:
                return False
        
        # Place the product
        return self._place_product_on_shelf(shelf, product, facings)
    
    def _find_optimal_shelf_for_product(self, product: Product) -> Optional[Shelf]:
        """Find the best shelf for a product based on its characteristics"""
        shelf_scores = []
        
        for shelf in self.store.shelves:
            score = 0
            
            # Base score from shelf
            score += shelf.get_placement_score(product)
            
            # Category consistency bonus
            if hasattr(self, 'category_shelf_assignments'):
                if product.category in self.category_shelf_assignments:
                    if shelf.shelf_id in self.category_shelf_assignments[product.category]:
                        score += 0.3
            
            # Height utilization score
            height_ratio = product.height / shelf.height
            if 0.6 <= height_ratio <= 0.8:
                score += 0.2
            
            # Current utilization penalty (prefer less crowded shelves)
            score -= (shelf.utilization / 100) * 0.3
            
            shelf_scores.append((shelf, score))
        
        if not shelf_scores:
            return None
        
        # Return best scoring shelf
        shelf_scores.sort(key=lambda x: x[1], reverse=True)
        return shelf_scores[0][0]
    
    def _post_optimization_improvements(self, products_placed: List[Product]):
        """Apply post-optimization improvements"""
        # 1. Balance shelf utilization
        self._balance_shelf_loads()
        
        # 2. Optimize spacing
        for shelf in self.store.shelves:
            shelf.optimize_positions(self.gap_size)
        
        # 3. Group similar products within shelves
        self._group_similar_products_on_shelves()
    
    def _balance_shelf_loads(self):
        """Balance product load across shelves"""
        # Find over and under-utilized shelves
        over_utilized = [s for s in self.store.shelves if s.utilization > 85]
        under_utilized = [s for s in self.store.shelves if s.utilization < 40 and s.positions]
        
        if not over_utilized or not under_utilized:
            return
        
        # Try to move products from over to under-utilized shelves
        for over_shelf in over_utilized:
            for under_shelf in under_utilized:
                # Find products that could be moved
                for pos in over_shelf.positions[:]:  # Copy list to modify during iteration
                    product = next((p for p in self.products_placed if p.product_id == pos.product_id), None)
                    if product and under_shelf.can_fit_product(product, pos.facings):
                        # Move product
                        over_shelf.positions.remove(pos)
                        self._place_product_on_shelf(under_shelf, product, pos.facings)
                        self.logger.debug(f"Moved {product.product_name} from shelf {over_shelf.shelf_id} to {under_shelf.shelf_id}")
                        break
    
    def _group_similar_products_on_shelves(self):
        """Group similar products together on shelves"""
        for shelf in self.store.shelves:
            if len(shelf.positions) < 2:
                continue
            
            # Get products on shelf
            shelf_products = []
            for pos in shelf.positions:
                product = next((p for p in self.products_placed if p.product_id == pos.product_id), None)
                if product:
                    shelf_products.append((pos, product))
            
            # Sort by category and series
            shelf_products.sort(key=lambda x: (x[1].category.value, x[1].series))
            
            # Reposition products
            current_x = self.gap_size
            new_positions = []
            
            for pos, product in shelf_products:
                width = pos.x_end - pos.x_start
                new_pos = ShelfPosition(
                    product_id=product.product_id,
                    x_start=current_x,
                    x_end=current_x + width,
                    facings=pos.facings
                )
                new_positions.append(new_pos)
                current_x += width + self.gap_size
            
            shelf.positions = new_positions
            shelf.update_utilization()