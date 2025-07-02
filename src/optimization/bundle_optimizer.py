from typing import List, Dict, Optional, Tuple, Set
import pandas as pd
from src.models.product import Product, ProductCategory
from src.models.shelf import Shelf
from .base_optimizer import BaseOptimizer, OptimizationResult
from src.utils.monitor import monitor

class BundleOptimizer(BaseOptimizer):
    """Optimizer for bundle-based planogram generation"""
    
    def __init__(self, store, gap_size: float = 2.0, bundle_data: Optional[pd.DataFrame] = None):
        super().__init__(store, gap_size)
        self.bundle_data = bundle_data
        self.bundle_groups = []
        self.bundle_placements = {}
    
    @monitor.time_it
    def optimize(self, products: List[Product], **kwargs) -> OptimizationResult:
        """Optimize product placement based on bundle relationships"""
        self.logger.info("Running bundle-based optimization")
        
        # Load bundle data if provided in kwargs
        if 'bundle_data' in kwargs:
            self.bundle_data = kwargs['bundle_data']
        
        if self.bundle_data is None or self.bundle_data.empty:
            self.logger.warning("No bundle data provided, falling back to regular optimization")
            # Fall back to basic placement
            return self._fallback_optimization(products)
        
        # Create product lookup
        self.product_lookup = {p.product_id: p for p in products}
        
        # Extract bundle groups
        self.bundle_groups = self._extract_bundle_groups(products)
        
        # Optimize placement
        products_placed = []
        products_rejected = []
        
        # Place bundles first
        placed_ids = set()
        for bundle_group in self.bundle_groups:
            if self._place_bundle(bundle_group):
                for product in bundle_group:
                    if product.product_id not in placed_ids:
                        products_placed.append(product)
                        placed_ids.add(product.product_id)
            else:
                self.warnings.append(f"Could not place bundle with {len(bundle_group)} products")
        
        # Place remaining products
        remaining_products = [p for p in products if p.product_id not in placed_ids]
        remaining_placed, remaining_rejected = self._place_remaining_products(remaining_products)
        
        products_placed.extend(remaining_placed)
        products_rejected.extend(remaining_rejected)
        
        # Post-optimization
        self._optimize_bundle_spacing()
        
        return OptimizationResult(
            success=len(products_placed) > 0,
            store=self.store,
            products_placed=products_placed,
            products_rejected=products_rejected,
            metrics=self.metrics,
            warnings=self.warnings
        )
    
    def _extract_bundle_groups(self, products: List[Product]) -> List[List[Product]]:
        """Extract bundle groups from bundle data"""
        bundle_groups = []
        product_ids = {p.product_id for p in products}
        
        # Process bundle recommendations
        for _, bundle in self.bundle_data.iterrows():
            group = []
            
            # Check different bundle formats
            if 'accessories' in bundle and isinstance(bundle['accessories'], str):
                # Format: "Case + Screen Protector + Cable"
                accessory_names = bundle['accessories'].split(' + ')
                for name in accessory_names:
                    # Find matching products
                    matching = [p for p in products if name.lower() in p.product_name.lower()]
                    if matching:
                        group.append(matching[0])
            else:
                # Format: separate columns for each accessory
                for col in ['accessory_1', 'accessory_2', 'accessory_3']:
                    if col in bundle and pd.notna(bundle[col]):
                        product_id = bundle[col]
                        if product_id in self.product_lookup:
                            group.append(self.product_lookup[product_id])
            
            # Only create groups with 2+ products that are in our product list
            if len(group) >= 2:
                # Filter to only products we're placing
                group = [p for p in group if p.product_id in product_ids]
                if len(group) >= 2:
                    bundle_groups.append(group)
                    
                    # Record bundle frequency if available
                    if 'frequency' in bundle:
                        for product in group:
                            product.bundle_frequency = int(bundle['frequency'])
        
        # Sort bundles by frequency/importance
        bundle_groups.sort(key=lambda g: sum(getattr(p, 'bundle_frequency', 0) for p in g), reverse=True)
        
        self.logger.info(f"Extracted {len(bundle_groups)} bundle groups")
        return bundle_groups
    
    def _place_bundle(self, bundle: List[Product]) -> bool:
        """Place a bundle of products together"""
        # Calculate total width needed
        total_width = sum(p.width * p.calculate_facings("balanced") for p in bundle)
        total_width += self.gap_size * (len(bundle) - 1)  # Gaps between products
        
        # Find shelf that can fit the entire bundle
        best_shelf = None
        best_score = -1
        
        for shelf in self.store.shelves:
            if shelf.get_available_width() >= total_width:
                # Calculate bundle placement score
                score = self._calculate_bundle_placement_score(bundle, shelf)
                if score > best_score:
                    best_score = score
                    best_shelf = shelf
        
        if best_shelf is None:
            # Try to split bundle across adjacent shelves
            return self._place_split_bundle(bundle)
        
        # Place bundle on best shelf
        bundle_start_x = self._find_bundle_position(best_shelf, total_width)
        current_x = bundle_start_x
        
        for product in bundle:
            facings = product.calculate_facings("balanced")
            if not self._place_product_at_position(best_shelf, product, facings, current_x):
                return False
            current_x += product.width * facings + self.gap_size
        
        # Record bundle placement
        self.bundle_placements[tuple(p.product_id for p in bundle)] = {
            'shelf_id': best_shelf.shelf_id,
            'start_x': bundle_start_x,
            'end_x': current_x
        }
        
        return True
    
    def _place_split_bundle(self, bundle: List[Product]) -> bool:
        """Try to place bundle split across adjacent shelves"""
        # Find vertically adjacent shelves
        shelves_by_height = sorted(self.store.shelves, key=lambda s: s.y_position)
        
        for i in range(len(shelves_by_height) - 1):
            shelf1 = shelves_by_height[i]
            shelf2 = shelves_by_height[i + 1]
            
            # Check if shelves are adjacent (close in height)
            if abs(shelf2.y_position - (shelf1.y_position + shelf1.height)) < 10:
                # Try to split bundle
                mid_point = len(bundle) // 2
                part1 = bundle[:mid_point]
                part2 = bundle[mid_point:]
                
                # Check if parts fit
                width1 = sum(p.width * p.calculate_facings("balanced") for p in part1)
                width2 = sum(p.width * p.calculate_facings("balanced") for p in part2)
                
                if shelf1.get_available_width() >= width1 and shelf2.get_available_width() >= width2:
                    # Place both parts
                    success1 = all(self._try_place_product(shelf1, p, p.calculate_facings("balanced")) 
                                  for p in part1)
                    success2 = all(self._try_place_product(shelf2, p, p.calculate_facings("balanced")) 
                                  for p in part2)
                    
                    if success1 and success2:
                        self.warnings.append(f"Split bundle across shelves {shelf1.shelf_id} and {shelf2.shelf_id}")
                        return True
        
        return False
    
    def _calculate_bundle_placement_score(self, bundle: List[Product], shelf: Shelf) -> float:
        """Calculate score for placing a bundle on a shelf"""
        score = 0
        
        # Base shelf score
        avg_placement_score = sum(shelf.get_placement_score(p) for p in bundle) / len(bundle)
        score += avg_placement_score
        
        # Bundle value score
        bundle_value = sum(p.price * p.sales_velocity for p in bundle)
        if bundle_value > 100:  # High-value bundle
            if shelf.is_eye_level:
                score += 0.5
            elif shelf.is_premium:
                score += 0.3
        
        # Space efficiency
        total_width = sum(p.width * p.calculate_facings("balanced") for p in bundle)
        space_efficiency = total_width / shelf.get_available_width()
        if 0.3 <= space_efficiency <= 0.7:  # Good fit
            score += 0.3
        
        # Category consistency
        categories = {p.category for p in bundle}
        if len(categories) <= 2:  # Similar categories
            score += 0.2
        
        return score
    
    def _find_bundle_position(self, shelf: Shelf, required_width: float) -> float:
        """Find optimal position for bundle on shelf"""
        if not shelf.positions:
            # Empty shelf - prefer center for bundles
            available = shelf.width - required_width
            if available > 0:
                return available / 2
            return self.gap_size
        
        # Find gaps between existing products
        gaps = []
        
        # Check gap at start
        if shelf.positions[0].x_start >= required_width + self.gap_size:
            gaps.append((0, shelf.positions[0].x_start))
        
        # Check gaps between products
        for i in range(len(shelf.positions) - 1):
            gap_start = shelf.positions[i].x_end + self.gap_size
            gap_end = shelf.positions[i + 1].x_start - self.gap_size
            gap_width = gap_end - gap_start
            
            if gap_width >= required_width:
                gaps.append((gap_start, gap_width))
        
        # Check gap at end
        last_end = shelf.positions[-1].x_end + self.gap_size
        if shelf.width - last_end >= required_width:
            gaps.append((last_end, shelf.width - last_end))
        
        # Choose best gap (prefer centered positions)
        if gaps:
            # Sort by distance from center
            shelf_center = shelf.width / 2
            gaps.sort(key=lambda g: abs(g[0] + required_width/2 - shelf_center))
            return gaps[0][0]
        
        return shelf.positions[-1].x_end + self.gap_size
    
    def _place_product_at_position(self, shelf: Shelf, product: Product, 
                                  facings: int, x_position: float) -> bool:
        """Place product at specific position"""
        from src.models.shelf import ShelfPosition
        
        product_width = product.width * facings
        
        # Check if position is valid
        if x_position + product_width > shelf.width:
            return False
        
        # Check for overlaps
        for pos in shelf.positions:
            if not (x_position + product_width <= pos.x_start or x_position >= pos.x_end):
                return False
        
        # Create position
        position = ShelfPosition(
            product_id=product.product_id,
            x_start=x_position,
            x_end=x_position + product_width,
            facings=facings
        )
        
        shelf.positions.append(position)
        shelf.positions.sort(key=lambda p: p.x_start)  # Keep positions sorted
        shelf.update_utilization()
        
        # Update metrics
        if product.category not in self.metrics.get('category_distribution', {}):
            self.metrics.setdefault('category_distribution', {})[product.category] = 0
        self.metrics['category_distribution'][product.category] += facings
        
        return True
    
    def _place_remaining_products(self, products: List[Product]) -> Tuple[List[Product], List[Product]]:
        """Place products that aren't part of bundles"""
        placed = []
        rejected = []
        
        # Sort by priority
        products = self._sort_products_by_priority(products)
        
        for product in products:
            facings = product.calculate_facings("balanced")
            
            # Try to place near related products if possible
            related_shelf = self._find_related_product_shelf(product)
            
            if related_shelf and self._try_place_product(related_shelf, product, facings):
                placed.append(product)
            else:
                # Try any available shelf
                placed_on_any = False
                for shelf in sorted(self.store.shelves, 
                                  key=lambda s: s.utilization):  # Try less utilized shelves first
                    if self._try_place_product(shelf, product, facings):
                        placed.append(product)
                        placed_on_any = True
                        break
                
                if not placed_on_any:
                    rejected.append(product)
        
        return placed, rejected
    
    def _find_related_product_shelf(self, product: Product) -> Optional[Shelf]:
        """Find shelf with related products"""
        # Check if product appears in any bundles
        for bundle_ids, placement in self.bundle_placements.items():
            # Check if this product type appears in bundles (by category/name similarity)
            for placed_id in bundle_ids:
                if placed_id in self.product_lookup:
                    placed_product = self.product_lookup[placed_id]
                    # Same category or series
                    if (placed_product.category == product.category or 
                        placed_product.series == product.series):
                        shelf_id = placement['shelf_id']
                        return next(s for s in self.store.shelves if s.shelf_id == shelf_id)
        
        # Look for shelves with same category products
        category_shelf_counts = {}
        for shelf in self.store.shelves:
            category_count = 0
            for pos in shelf.positions:
                if pos.product_id in self.product_lookup:
                    shelf_product = self.product_lookup[pos.product_id]
                    if shelf_product.category == product.category:
                        category_count += 1
            
            if category_count > 0:
                category_shelf_counts[shelf] = category_count
        
        # Return shelf with most same-category products
        if category_shelf_counts:
            return max(category_shelf_counts.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _optimize_bundle_spacing(self):
        """Optimize spacing between bundles and ensure visual separation"""
        for shelf in self.store.shelves:
            if len(shelf.positions) < 2:
                continue
            
            # Identify bundle boundaries
            bundle_boundaries = set()
            for bundle_ids, placement in self.bundle_placements.items():
                if placement['shelf_id'] == shelf.shelf_id:
                    # Mark start and end of bundle
                    for pos in shelf.positions:
                        if pos.product_id in bundle_ids:
                            bundle_boundaries.add(pos.x_start)
                            bundle_boundaries.add(pos.x_end)
            
            # Adjust spacing
            if bundle_boundaries:
                new_positions = []
                current_x = self.gap_size
                
                for pos in sorted(shelf.positions, key=lambda p: p.x_start):
                    # Extra gap before bundle starts
                    if pos.x_start in bundle_boundaries:
                        current_x += self.gap_size  # Double gap for bundle separation
                    
                    width = pos.x_end - pos.x_start
                    from src.models.shelf import ShelfPosition
                    new_pos = ShelfPosition(
                        product_id=pos.product_id,
                        x_start=current_x,
                        x_end=current_x + width,
                        facings=pos.facings
                    )
                    new_positions.append(new_pos)
                    current_x = new_pos.x_end + self.gap_size
                    
                    # Extra gap after bundle ends
                    if pos.x_end in bundle_boundaries:
                        current_x += self.gap_size
                
                shelf.positions = new_positions
                shelf.update_utilization()
    
    def _fallback_optimization(self, products: List[Product]) -> OptimizationResult:
        """Fallback to basic optimization when no bundle data available"""
        from .product_optimizer import ProductOptimizer
        
        # Use product optimizer with balanced strategy
        product_optimizer = ProductOptimizer(self.store, self.gap_size, strategy="balanced")
        
        # Copy over the current state
        product_optimizer.metrics = self.metrics
        product_optimizer.warnings = self.warnings
        
        return product_optimizer.optimize(products)
    
    def _try_place_product(self, shelf: Shelf, product: Product, facings: int) -> bool:
        """Try to place a product on a shelf"""
        if not shelf.can_fit_product(product, facings):
            # Try with minimum facings
            if facings > product.min_facings:
                facings = product.min_facings
                if not shelf.can_fit_product(product, facings):
                    return False
            else:
                return False
        
        return self._place_product_on_shelf(shelf, product, facings)
    
    def get_bundle_metrics(self) -> Dict[str, any]:
        """Get metrics specific to bundle optimization"""
        bundle_metrics = {
            'total_bundles': len(self.bundle_groups),
            'bundles_placed': len(self.bundle_placements),
            'products_in_bundles': sum(len(b) for b in self.bundle_groups),
            'bundle_coverage': 0,
            'average_bundle_size': 0
        }
        
        if self.bundle_groups:
            bundle_metrics['average_bundle_size'] = (
                bundle_metrics['products_in_bundles'] / bundle_metrics['total_bundles']
            )
        
        # Calculate coverage
        if self.products_placed:
            products_in_bundles = set()
            for bundle in self.bundle_groups:
                products_in_bundles.update(p.product_id for p in bundle)
            
            placed_in_bundles = len([p for p in self.products_placed 
                                   if p.product_id in products_in_bundles])
            bundle_metrics['bundle_coverage'] = placed_in_bundles / len(self.products_placed)
        
        # Add to overall metrics
        self.metrics['bundle_metrics'] = bundle_metrics
        
        return bundle_metrics