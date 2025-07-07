from typing import List, Dict, Optional, Tuple
import numpy as np
from src.models.product import Product, ProductCategory
from src.models.shelf import Shelf, ShelfPosition  # ADD ShelfPosition here
from .base_optimizer import BaseOptimizer, OptimizationResult
from src.utils.monitor import monitor

class ProductOptimizer(BaseOptimizer):
    """Optimizer for product-based planogram generation"""
    
    def __init__(self, store, gap_size: float = 0.5, strategy: str = "balanced"):
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
        elif self.strategy == "profit_efficiency":  
            result = self._optimize_by_profit_efficiency(sorted_products)
        else:  # balanced
            result = self._optimize_balanced(sorted_products)
        
        return result
    
    def _force_place_high_priority_product(self, product: Product, products_placed: List[Product]) -> bool:
        """Force place a high-priority product by bumping out lower-selling products"""
        all_shelves = self.store.shelves
        
        # Try to place with 1 facing first
        for shelf in all_shelves:
            if self._try_place_product(shelf, product, 1):
                return True
        
        # If that fails, find products with lower sales velocity to bump out
        for shelf in all_shelves:
            # Find all products on this shelf with lower sales velocity
            lower_velocity_positions = []
            for position in shelf.positions:
                existing_product = next((p for p in products_placed if p.product_id == position.product_id), None)
                if existing_product and existing_product.sales_velocity < product.sales_velocity:
                    lower_velocity_positions.append((position, existing_product))
            
            # Sort by sales velocity (lowest first) to remove the worst performers first
            lower_velocity_positions.sort(key=lambda x: x[1].sales_velocity)
            
            # Try removing products one by one until we have space
            for position, existing_product in lower_velocity_positions:
                shelf.positions.remove(position)
                products_placed.remove(existing_product)
                
                # Try to place the high-priority product
                if self._try_place_product(shelf, product, 1):
                    self.logger.info(f"  -> BUMPED OUT {existing_product.product_name[:20]}... (sales: {existing_product.sales_velocity:.1f}/day) for higher priority product")
                    return True
                else:
                    # If we still can't place it, restore the removed product and try next
                    self._try_place_product(shelf, existing_product, position.facings)
                    products_placed.append(existing_product)
        
        return False
    
    def _sort_by_sales_and_iphone16_priority(self, products: List[Product]) -> List[Product]:
        """Sort products by sales velocity with iPhone 16 models getting priority and series balancing"""
        
        # First, sort by sales velocity with iPhone 16 bonus
        def initial_sort_key(product):
            sales_velocity = product.sales_velocity
            iphone16_bonus = 0
            series = getattr(product, 'series', '')
            if 'iPhone 16' in series:
                iphone16_bonus = 1000
            return sales_velocity + iphone16_bonus
        
        initial_sorted = sorted(products, key=initial_sort_key, reverse=True)
        
        # Then apply series balancing to ensure all iPhone variants get representation
        balanced_products = []
        series_counts = {}
        
        # First pass: Ensure each iPhone 16 variant gets at least 1 product
        iphone16_variants = ['iPhone 16 Base', 'iPhone 16 Plus', 'iPhone 16 Pro', 'iPhone 16 Pro Max']
        
        for variant in iphone16_variants:
            variant_products = [p for p in initial_sorted if getattr(p, 'series', '') == variant]
            if variant_products and len(balanced_products) < 8:  # Limit to prevent overflow
                best_product = variant_products[0]  # Already sorted by sales+bonus
                balanced_products.append(best_product)
                series_counts[variant] = 1
                self.logger.debug(f"Ensured representation: {variant} - {best_product.product_name[:20]}")
        
        # Second pass: Fill remaining spots with rotation, max 2 per series
        remaining_products = [p for p in initial_sorted if p not in balanced_products]
        
        for product in remaining_products:
            if len(balanced_products) >= 20:  # Reasonable limit
                break
                
            series = getattr(product, 'series', 'Unknown')
            current_count = series_counts.get(series, 0)
            
            # Allow max 2 per series after initial representation
            if current_count < 2:
                balanced_products.append(product)
                series_counts[series] = current_count + 1
        
        # Add any remaining products if space allows
        for product in initial_sorted:
            if product not in balanced_products and len(balanced_products) < 30:
                balanced_products.append(product)
        
        return balanced_products
    
    def _get_brand_shelf_allocation(self):
        """Allocate shelves between Apple and Third-party based on store type"""
        all_shelves = self.store.shelves
        store_type = self.store.store_type
        
        if store_type == 'flagship':
            # Flagship: First half of each shelf for Apple, second half for TPA
            apple_shelves = all_shelves.copy()  # Apple can use all shelves (first half)
            tpa_shelves = all_shelves.copy()    # TPA can use all shelves (second half)
            
        elif store_type == 'express':
            # Express: Apple gets limited space (like top row), TPA gets most space
            # Use all shelves but with different capacity allocation
            apple_shelves = all_shelves.copy()  # Apple can use all shelves but limited
            tpa_shelves = all_shelves.copy()    # TPA can use all shelves
            
        else:  # standard
            # Standard: Top shelf for Apple, other shelves for TPA
            eye_level_shelves = [s for s in all_shelves if s.eye_level_score >= 0.8]
            other_shelves = [s for s in all_shelves if s.eye_level_score < 0.8]
            apple_shelves = eye_level_shelves
            tpa_shelves = other_shelves
        
        return apple_shelves, tpa_shelves
    
    def _filter_tpa_brands(self, products: List[Product]) -> List[Product]:
        """Filter TPA products to focus on main brands: Tekne, Pulse, Gripp"""
        main_brands = ['Tekne', 'Pulse', 'Gripp']
        
        # Group products by brand
        brand_products = {}
        for product in products:
            brand = getattr(product, 'brand', '')
            if brand in main_brands:
                if brand not in brand_products:
                    brand_products[brand] = []
                brand_products[brand].append(product)
        
        # Calculate total sales for each brand to determine proportions
        brand_sales = {}
        for brand, prods in brand_products.items():
            total_sales = sum(getattr(p, 'sales_velocity', 0) for p in prods)
            brand_sales[brand] = total_sales
        
        # Sort brands by sales and select top products from each proportionally
        sorted_brands = sorted(brand_sales.items(), key=lambda x: x[1], reverse=True)
        
        selected_products = []
        total_slots = 15  # Adjust based on available TPA space
        
        for brand, total_sales in sorted_brands:
            # Calculate proportion of slots for this brand
            brand_proportion = total_sales / sum(brand_sales.values())
            brand_slots = max(1, int(total_slots * brand_proportion))
            
            # Select top products from this brand
            brand_prods = sorted(brand_products[brand], 
                               key=lambda p: getattr(p, 'sales_velocity', 0), 
                               reverse=True)
            selected_products.extend(brand_prods[:brand_slots])
        
        self.logger.info(f"Filtered TPA brands: {len(selected_products)} products from {list(brand_products.keys())}")
        return selected_products

    def _diversify_apple_products(self, products: List[Product], max_products: int = 20) -> List[Product]:
        """
        Select Apple products to maximize color diversity: cycle through all unique color groups, picking the top-selling SKU per color,
        before repeating any color, until reaching max_products or exhausting products.
        """
        # Group products by color
        color_groups = {}
        for product in products:
            subcat = getattr(product, 'subcategory', '').lower()
            if subcat == 'clear':
                color = 'clear'
            elif subcat == 'silicone':
                name = getattr(product, 'product_name', '').strip()
                if '-' in name:
                    color = name.split('-')[-1].strip().lower().replace(' ', '_')
                else:
                    color = 'silicone'
            else:
                color = subcat.replace(' ', '_')
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append(product)
        # Sort each color group by sales velocity
        for color in color_groups:
            color_groups[color].sort(key=lambda p: getattr(p, 'sales_velocity', 0), reverse=True)
        color_list = list(color_groups.keys())
        selected_products = []
        color_indices = {color: 0 for color in color_list}
        # Cycle through colors, picking one from each group per round
        while len(selected_products) < min(max_products, len(products)):
            added_this_round = False
            for color in color_list:
                idx = color_indices[color]
                if idx < len(color_groups[color]):
                    product = color_groups[color][idx]
                    if product not in selected_products:
                        selected_products.append(product)
                        self.logger.info(f"Selected Apple {color} product: {product.product_name[:50]}... (sales: {getattr(product, 'sales_velocity', 0):.1f}/day)")
                        added_this_round = True
                color_indices[color] += 1
                if len(selected_products) >= min(max_products, len(products)):
                    break
            if not added_this_round:
                break  # No more products left to add
        self.logger.info(f"Apple color diversity: {len(selected_products)} products selected with maximum unique color representation")
        return selected_products

    def _diversify_tpa_products(self, products: List[Product], max_products: int = 20) -> List[Product]:
        """
        Select TPA products to maximize color diversity: cycle through all unique color groups, picking the top-selling SKU per color,
        before repeating any color, until reaching max_products or exhausting products.
        """
        # Group products by color (use subcategory or color field)
        color_groups = {}
        import re
        COMMON_COLORS = [
            'clear', 'black', 'white', 'blue', 'red', 'green', 'yellow', 'pink', 'purple',
            'orange', 'grey', 'gray', 'gold', 'silver', 'midnight', 'starlight', 'ice', 'frost',
            'plum', 'denim', 'ultramarine', 'fuchsia', 'stone', 'star', 'lake', 'armour',
            'privacy', 'smoke', 'mint', 'lavender', 'beige', 'brown', 'graphite', 'coral',
            'sky', 'forest', 'navy', 'rose', 'sand', 'olive', 'teal', 'indigo', 'champagne',
            'bronze', 'violet', 'charcoal', 'magenta', 'cream', 'peach', 'lime', 'maroon', 'aqua', 'ruby', 'sapphire', 'emerald', 'jade', 'onyx', 'slate', 'taupe', 'wine', 'copper', 'steel'
        ]
        def extract_color(name, subcat):
            name_lc = name.lower()
            for color in COMMON_COLORS:
                # Use word boundaries to avoid partial matches
                if re.search(rf'\b{re.escape(color)}\b', name_lc):
                    return color.replace(' ', '_')
            if subcat:
                return subcat.replace(' ', '_')
            return 'unknown'
        for product in products:
            name = getattr(product, 'product_name', '').strip()
            subcat = getattr(product, 'subcategory', '').lower()
            color = extract_color(name, subcat)
            self.logger.info(f"[COLOR DEBUG] Product: '{name}' | Subcat: '{subcat}' | Detected color: '{color}'")
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append(product)
        for color in color_groups:
            color_groups[color].sort(key=lambda p: getattr(p, 'sales_velocity', 0), reverse=True)
        color_list = list(color_groups.keys())
        selected_products = []
        color_indices = {color: 0 for color in color_list}
        while len(selected_products) < min(max_products, len(products)):
            added_this_round = False
            for color in color_list:
                idx = color_indices[color]
                if idx < len(color_groups[color]):
                    product = color_groups[color][idx]
                    if product not in selected_products:
                        selected_products.append(product)
                        self.logger.info(f"Selected TPA {color} product: {product.product_name[:50]}... (sales: {getattr(product, 'sales_velocity', 0):.1f}/day)")
                        added_this_round = True
                color_indices[color] += 1
                if len(selected_products) >= min(max_products, len(products)):
                    break
            if not added_this_round:
                break
        self.logger.info(f"TPA color diversity: {len(selected_products)} products selected with maximum unique color representation")
        return selected_products


    def _place_brand_products(self, products: List[Product], allowed_shelves: List, 
                             products_placed: List[Product], products_rejected: List[Product], 
                             brand_type: str):
        """Place products of a specific brand on their allocated shelves"""
        store_type = self.store.store_type
        
        # For TPA products, filter to main brands only and maximize color diversity
        if brand_type == "TPA":
            products = self._filter_tpa_brands(products)
            products = self._diversify_tpa_products(products, max_products=20)
        # For Apple products, always maximize color diversity
        elif brand_type == "Apple":
            products = self._diversify_apple_products(products, max_products=20)
        
        for i, product in enumerate(products):
            placed = False
            
            # Different placement logic based on store type
            if store_type == 'flagship':
                # Flagship: Use half-shelf logic (Apple first half, TPA second half)
                placed = self._try_place_with_half_shelf_logic(product, allowed_shelves, brand_type)
            elif store_type == 'express':
                # Express: Limited Apple placement (like top row concept)
                if brand_type == "Apple":
                    # Limit Apple products to ~30% of total capacity
                    apple_count = len([p for p in products_placed if getattr(p, 'brand', '').lower() == 'apple'])
                    total_capacity = len(products) * 0.30  # Apple gets 30% of slots
                    if apple_count < total_capacity:
                        for shelf in sorted(allowed_shelves, key=lambda s: s.utilization):
                            if self._try_place_product(shelf, product, 1):
                                placed = True
                                break
                else:
                    for shelf in sorted(allowed_shelves, key=lambda s: s.utilization):
                        if self._try_place_product(shelf, product, 1):
                            placed = True
                            break
            else:
                # Standard: Try to place on any allowed shelf
                for shelf in sorted(allowed_shelves, key=lambda s: s.utilization):
                    if self._try_place_product(shelf, product, 1):
                        placed = True
                        break
            if placed:
                products_placed.append(product)
                if i < 10:
                    brand_label = "APPLE" if brand_type == "Apple" else "TPA"
                    self.logger.info(f"[{brand_label}] #{i+1}: Placed {product.product_name[:30]}... (sales: {product.sales_velocity:.1f}/day)")
            else:
                products_rejected.append(product)
                self.warnings.append(f"Could not place {product.product_name} (sales: {product.sales_velocity:.1f}/day)")
                if i < 10:
                    self.logger.info(f"[REJECTED] #{i+1}: {product.product_name[:30]}... (sales: {product.sales_velocity:.1f}/day)")
        
        return products_placed, products_rejected
    
    def _try_place_with_half_shelf_logic(self, product: Product, allowed_shelves: List, brand_type: str) -> bool:
        """Try to place product using half-shelf allocation logic"""
        for shelf in sorted(allowed_shelves, key=lambda s: s.utilization):
            shelf_width = shelf.width
            half_width = shelf_width / 2
            
            # Calculate current shelf usage by brand
            apple_width = 0
            tpa_width = 0
            
            for pos in shelf.positions:
                # Try to determine brand from existing products (simplified)
                if pos.x_start < half_width:
                    apple_width += pos.width
                else:
                    tpa_width += pos.width
            
            # More flexible placement logic
            if brand_type == "Apple":
                # Apple gets first half, but can overflow if TPA section is empty
                target_section_used = apple_width
                available_space = half_width - target_section_used
                
                # If not enough space in Apple section, but TPA section is empty, allow overflow
                if available_space < product.width and tpa_width == 0:
                    available_space = shelf_width - (apple_width + tpa_width)
                
                if available_space >= product.width:
                    if self._try_place_product(shelf, product, 1):
                        self.logger.debug(f"Placed Apple product on {shelf.shelf_name} (Apple section: {apple_width:.1f}cm used)")
                        return True
            else:
                # TPA gets second half, but can use full shelf if Apple section has reasonable space
                if apple_width <= half_width * 1.2:  # Allow 20% overflow for Apple
                    remaining_space = shelf_width - (apple_width + tpa_width)
                    if remaining_space >= product.width:
                        if self._try_place_product(shelf, product, 1):
                            self.logger.debug(f"Placed TPA product on {shelf.shelf_name} (TPA section: {tpa_width:.1f}cm used)")
                            return True
        
        return False
    
    def _optimize_by_sales(self, products: List[Product]) -> OptimizationResult:
        """Optimize based on sales velocity with Apple/Third-party brand allocation"""
        products_placed = []
        products_rejected = []
        
        # Separate Apple and Third-party products
        apple_products = [p for p in products if getattr(p, 'brand', '').lower() == 'apple']
        tpa_products = [p for p in products if getattr(p, 'brand', '').lower() != 'apple']
        
        # Debug: Show brand distribution
        brand_counts = {}
        for p in products:
            brand = getattr(p, 'brand', 'Unknown')
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
        self.logger.info(f"Brand distribution: {brand_counts}")
        
        # Sort each group by sales velocity and iPhone 16 priority
        apple_products = self._sort_by_sales_and_iphone16_priority(apple_products)
        tpa_products = self._sort_by_sales_and_iphone16_priority(tpa_products)
        
        # Debug: Show series distribution in sorted Apple products
        if apple_products:
            apple_series = {}
            for p in apple_products[:10]:  # First 10
                series = getattr(p, 'series', 'Unknown')
                apple_series[series] = apple_series.get(series, 0) + 1
            self.logger.info(f"Apple series in top 10: {apple_series}")
        
        # Get shelf allocation based on store type
        apple_shelves, tpa_shelves = self._get_brand_shelf_allocation()
        
        self.logger.info(f"Apple products: {len(apple_products)} | Third-party products: {len(tpa_products)}")
        self.logger.info(f"Store type: {self.store.store_type}")
        
        if self.store.store_type == 'flagship':
            self.logger.info("Strategy: Apple first half, TPA second half (all shelves)")
        elif self.store.store_type == 'express':
            self.logger.info("Strategy: Apple limited to 25% (top row concept), TPA gets 75%")
        else:
            self.logger.info("Strategy: Apple top shelf, TPA other shelves")
            
        self.logger.info(f"Apple shelves: {[s.shelf_name for s in apple_shelves]} | TPA shelves: {[s.shelf_name for s in tpa_shelves]}")
        
        # Debug shelf capacities
        total_shelf_width = sum(s.width for s in self.store.shelves)
        self.logger.info(f"Total shelf width available: {total_shelf_width:.1f}cm")
        
        # Place Apple products first on their designated shelves
        self.logger.info("=== PLACING APPLE PRODUCTS ===")
        products_placed, products_rejected = self._place_brand_products(
            apple_products, apple_shelves, products_placed, products_rejected, "Apple"
        )
        
        # Then place Third-party products on their designated shelves
        self.logger.info("=== PLACING THIRD-PARTY PRODUCTS ===")
        products_placed, products_rejected = self._place_brand_products(
            tpa_products, tpa_shelves, products_placed, products_rejected, "TPA"
        )
        
        # Store products_placed for metrics calculation
        self.products_placed = products_placed
        
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
            # Safely get price and sales_velocity
            total_value = 0
            for p in cat_products:
                price = getattr(p, 'price', 0) or 0
                sales_velocity = getattr(p, 'sales_velocity', p.total_qty) or p.total_qty
                total_value += price * sales_velocity
            category_priorities.append((category, total_value, cat_products))
        
        # Sort categories by priority
        category_priorities.sort(key=lambda x: x[1], reverse=True)
        
        # Assign categories to shelf zones
        shelf_assignments = self._assign_categories_to_shelves(category_priorities)
        
        # Place products by category with improved logic
        for category, assigned_shelves in shelf_assignments.items():
            cat_products = category_groups[category]
            # Sort products within category by sales
            cat_products.sort(key=lambda p: p.sales_velocity, reverse=True)
            
            for product in cat_products:
                placed = False
                # Calculate optimal facings with store constraints
                optimal_facings = self._calculate_optimal_facings_for_store(product)
                
                # Try assigned shelves first
                for shelf_id in assigned_shelves:
                    shelf = next(s for s in self.store.shelves if s.shelf_id == shelf_id)
                    if self._try_place_product(shelf, product, optimal_facings):
                        products_placed.append(product)
                        placed = True
                        break
                
                # If not placed, try any available shelf with reduced facings
                if not placed:
                    for shelf in self.store.shelves:
                        min_facings = max(1, product.min_facings or 1)
                        if self._try_place_product(shelf, product, min_facings):
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
            # Get price/profit safely
            price = getattr(product, 'profit', getattr(product, 'price', 0))
            if price is None:
                price = 0
            
            # Get sales velocity safely
            if hasattr(product, 'sales_velocity') and product.sales_velocity is not None:
                sales_velocity = product.sales_velocity
            else:
                sales_velocity = product.total_qty
            
            value_per_unit = float(price) * float(sales_velocity)
            space_per_unit = product.width
            product.value_density = value_per_unit / space_per_unit if space_per_unit > 0 else 0
        
        # Sort by value density
        products.sort(key=lambda p: p.value_density, reverse=True)
        
        # Place high-value-density items at prime locations
        for product in products:
            placed = False
            
            # Get price safely for facing calculation
            price = getattr(product, 'profit', getattr(product, 'price', 0))
            if price is None:
                price = 0
                
            # Fewer facings for high-value items to maximize variety
            if price > 50:
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
                self.warnings.append(f"Could not place {product.product_name} (value density: {product.value_density:.2f})")
        
        # Store products_placed for metrics calculation
        self.products_placed = products_placed
        
        return OptimizationResult(
            success=len(products_placed) > 0,
            store=self.store,
            products_placed=products_placed,
            products_rejected=products_rejected,
            metrics=self.metrics,
            warnings=self.warnings
        )
    
    def _optimize_by_profit_efficiency(self, products: List[Product]) -> OptimizationResult:
        products_placed = []
        products_rejected = []
        
        # Calculate profit efficiency for each product
        for product in products:
            profit_per_unit = getattr(product, 'profit', getattr(product, 'price', 0))
            total_profit_potential = profit_per_unit * product.total_qty
            
            # Profit efficiency = total profit potential per cm of space needed
            min_space_needed = product.width * product.min_facings
            product.profit_efficiency = total_profit_potential / min_space_needed if min_space_needed > 0 else 0
        
        # Sort by profit efficiency
        products.sort(key=lambda p: p.profit_efficiency, reverse=True)
        
        # Place products prioritizing profit efficiency
        for product in products:
            placed = False
            
            # Calculate optimal facings based on profit margin
            profit_margin = getattr(product, 'profit', 0)
            if profit_margin > 40:  # High margin
                optimal_facings = min(product.max_facings, 4)
            elif profit_margin > 20:  # Medium margin
                optimal_facings = min(product.max_facings, 3)
            else:
                optimal_facings = product.calculate_facings("balanced")
            
            # Try eye-level shelves first for high-efficiency products
            if product.profit_efficiency > 50:  # High efficiency threshold
                eye_level_shelves = [s for s in self.store.shelves if s.eye_level_score >= 0.7]
                for shelf in eye_level_shelves:
                    if self._try_place_product(shelf, product, optimal_facings):
                        products_placed.append(product)
                        placed = True
                        break
            
            # Try any shelf if not placed
            if not placed:
                for shelf in sorted(self.store.shelves, key=lambda s: s.utilization):
                    if self._try_place_product(shelf, product, optimal_facings):
                        products_placed.append(product)
                        placed = True
                        break
            
            if not placed:
                products_rejected.append(product)
        
        # Store products_placed for metrics calculation
        self.products_placed = products_placed
        
        return OptimizationResult(
            success=len(products_placed) > 0,
            store=self.store,
            products_placed=products_placed,
            products_rejected=products_rejected,
            metrics=self.metrics,
            warnings=self.warnings
        )
        
    def _optimize_balanced(self, products: List[Product]) -> OptimizationResult:
        products_placed = []
        products_rejected = []
        
        # Calculate composite scores
        for product in products:
            # Sales score based on total quantity
            if hasattr(product, 'sales_velocity') and product.sales_velocity is not None:
                sales_score = min(product.sales_velocity / 20, 1.0)
            else:
                sales_score = min(product.total_qty / 300, 1.0)
            
            # Value/price score
            if hasattr(product, 'price') and product.price is not None and product.price > 0:
                value_score = min(product.price / 100, 1.0)
            else:
                value_score = 0.5
            
            # Attach score - handle None properly
            attach_rate = getattr(product, 'attach_rate', 0)
            if attach_rate is None:
                attach_rate = 0
            attach_score = float(attach_rate)
            
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
        for i, product in enumerate(products):
            placed = False
            optimal_facings = product.calculate_facings("balanced")
            
            # Debug logging
            if i < 5:  # Log first 5 products
                self.logger.debug(f"Trying to place {product.product_name}: {product.width}x{product.height}cm, facings: {optimal_facings}")
            
            # Find best shelf based on product characteristics
            best_shelf = self._find_optimal_shelf_for_product(product)
            
            if best_shelf:
                if self._try_place_product(best_shelf, product, optimal_facings):
                    products_placed.append(product)
                    placed = True
                    self.logger.debug(f"Placed {product.product_name} on shelf {best_shelf.shelf_name}")
                else:
                    self.logger.debug(f"Could not fit {product.product_name} on best shelf {best_shelf.shelf_name}")
            
            if not placed:
                # Try any available shelf
                for shelf in sorted(self.store.shelves, key=lambda s: s.utilization):
                    if self._try_place_product(shelf, product, optimal_facings):
                        products_placed.append(product)
                        placed = True
                        self.logger.debug(f"Placed {product.product_name} on shelf {shelf.shelf_name}")
                        break
            
            if not placed:
                products_rejected.append(product)
                self.warnings.append(f"Could not place {product.product_name} - no space available")
                self.logger.debug(f"Rejected {product.product_name} - no suitable shelf found")
        
        # Run post-optimization improvements
        if products_placed:
            self._post_optimization_improvements(products_placed)
        
        # Store products_placed for metrics calculation
        self.products_placed = products_placed
        
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
                if shelf.can_fit_product(product, facings):
                    return self._place_product_on_shelf(shelf, product, facings)
            # Always try with 1 facing for color diversity
            if shelf.can_fit_product(product, 1):
                return self._place_product_on_shelf(shelf, product, 1)
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
    
    def _calculate_optimal_facings_for_store(self, product: Product) -> int:
        """Calculate optimal facings considering store constraints"""
        # Get store rules - check different sources for max facings
        max_facings_per_product = 4  # Default
        
        # Try to get from store rules
        if hasattr(self.store, 'rules') and self.store.rules:
            max_facings_per_product = self.store.rules.get('max_facings_per_product', 4)
        
        # For express stores, limit facings further
        if self.store.store_type == 'express':
            max_facings_per_product = min(max_facings_per_product, 2)
        
        # Calculate base facings
        base_facings = product.calculate_facings("balanced")
        
        # Apply store constraints
        optimal_facings = min(base_facings, max_facings_per_product)
        
        # Ensure minimum facings
        optimal_facings = max(optimal_facings, product.min_facings or 1)
        
        return optimal_facings
