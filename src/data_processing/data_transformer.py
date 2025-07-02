import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from src.models.product import Product, ProductCategory, ProductStatus
from src.models.store import Store

class DataTransformer:
    """Transform and prepare data for optimization"""
    
    def __init__(self):
        self.transformations_applied = []
    
    def prepare_products_for_store(self, products: List[Product], 
                                  store: Store, 
                                  strategy: str = "balanced") -> List[Product]:
        """Prepare and filter products based on store type and strategy"""
        # Record transformation
        self.transformations_applied = []
        
        # Apply store-specific filtering
        filtered_products = store.filter_products_by_rules(products)
        self.transformations_applied.append(f"Store filtering: {len(products)} -> {len(filtered_products)} products")
        
        # Apply strategy-specific transformations
        if strategy == "sales_velocity":
            filtered_products = self._optimize_for_sales_velocity(filtered_products, store)
        elif strategy == "cohort_based":
            filtered_products = self._optimize_for_cohorts(filtered_products, store)
        elif strategy == "seasonal":
            filtered_products = self._apply_seasonal_adjustments(filtered_products)
        else:  # balanced
            filtered_products = self._apply_balanced_optimization(filtered_products, store)
        
        # Calculate optimal facings for each product
        for product in filtered_products:
            product.optimal_facings = self._calculate_optimal_facings(product, store, strategy)
        
        return filtered_products
    
    def _optimize_for_sales_velocity(self, products: List[Product], store: Store) -> List[Product]:
        """Optimize product selection based on sales velocity"""
        # Sort by sales velocity
        sorted_products = sorted(products, key=lambda p: p.sales_velocity, reverse=True)
        
        # Take top performers based on store capacity
        capacity = store.total_capacity
        selected = []
        
        for product in sorted_products:
            if len(selected) >= capacity:
                break
            selected.append(product)
        
        self.transformations_applied.append(f"Sales velocity optimization: selected top {len(selected)} products")
        return selected
    
    def _optimize_for_cohorts(self, products: List[Product], store: Store) -> List[Product]:
        """Optimize based on cohort attach rates"""
        # Prioritize products with high attach rates
        products_with_cohort = [p for p in products if hasattr(p, 'attach_rate') and p.attach_rate > 0]
        products_without = [p for p in products if p not in products_with_cohort]
        
        # Sort by attach rate
        products_with_cohort.sort(key=lambda p: p.attach_rate, reverse=True)
        
        # Combine with non-cohort products
        result = products_with_cohort + products_without[:max(0, store.total_capacity - len(products_with_cohort))]
        
        self.transformations_applied.append(f"Cohort optimization: prioritized {len(products_with_cohort)} products with attach rates")
        return result
    
    def _apply_seasonal_adjustments(self, products: List[Product]) -> List[Product]:
        """Apply seasonal adjustments to product selection"""
        current_month = datetime.now().month
        
        # Define seasonal categories
        seasonal_boosts = {
            'case': 1.2 if current_month in [9, 10, 11] else 1.0,  # Back to school, holidays
            'charger': 1.3 if current_month in [6, 7, 8] else 1.0,  # Summer travel
            'screen_protector': 1.2 if current_month in [9, 10, 11] else 1.0,  # New phone season
        }
        
        # Apply boosts
        for product in products:
            boost = seasonal_boosts.get(product.category.value, 1.0)
            product.seasonal_factor = boost
            # Adjust sales velocity estimate
            product.sales_velocity *= boost
        
        self.transformations_applied.append(f"Seasonal adjustments applied for month {current_month}")
        return products
    
    def _apply_balanced_optimization(self, products: List[Product], store: Store) -> List[Product]:
        """Apply balanced optimization considering multiple factors"""
        # Calculate composite score for each product
        for product in products:
            sales_score = min(product.sales_velocity / 50, 1.0)  # Normalize to 0-1
            stock_score = min(product.current_stock / (product.min_stock * 3), 1.0)
            attach_score = product.attach_rate if hasattr(product, 'attach_trate') else 0
            
            # Weighted composite score
            weights = store.optimization_weights
            product.composite_score = (
                sales_score * weights.get('sales_velocity', 0.4) +
                stock_score * weights.get('inventory_turnover', 0.3) +
                attach_score * weights.get('attach_rate', 0.3)
            )
        
        # Sort by composite score
        products.sort(key=lambda p: p.composite_score, reverse=True)
        
        self.transformations_applied.append("Balanced optimization using composite scores")
        return products
    
    def _calculate_optimal_facings(self, product: Product, store: Store, strategy: str) -> int:
        """Calculate optimal number of facings for a product"""
        base_facings = product.calculate_facings(strategy)
        
        # Apply store-specific multipliers
        if store.store_type == "flagship":
            multiplier = store.placement_rules.get('min_facings_multiplier', 1.5)
            base_facings = int(base_facings * multiplier)
        elif store.store_type == "express":
            # Express stores have limited space
            max_facings = store.rules.get('special_rules', {}).get('max_facings_per_product', 3)
            base_facings = min(base_facings, max_facings)
        
        # Adjust based on attach rate if available
        if hasattr(product, 'attach_rate') and product.attach_rate > 0:
            if product.attach_rate > 0.3:  # High attach rate
                base_facings = min(base_facings + 1, product.max_facings)
        
        # Ensure within product constraints
        return max(product.min_facings, min(base_facings, product.max_facings))
    
    def group_products_by_category(self, products: List[Product]) -> Dict[ProductCategory, List[Product]]:
        """Group products by category for category-based placement"""
        grouped = {}
        for product in products:
            if product.category not in grouped:
                grouped[product.category] = []
            grouped[product.category].append(product)
        
        # Sort products within each category by sales
        for category in grouped:
            grouped[category].sort(key=lambda p: p.sales_velocity, reverse=True)
        
        return grouped
    
    def group_products_by_series(self, products: List[Product]) -> Dict[str, List[Product]]:
        """Group products by series (e.g., iPhone 16, iPhone 15)"""
        grouped = {}
        for product in products:
            series = product.series
            if series not in grouped:
                grouped[series] = []
            grouped[series].append(product)
        
        return grouped
    
    def create_bundle_groups(self, products: List[Product], bundle_df: pd.DataFrame) -> List[List[Product]]:
        """Create product groups based on bundle recommendations"""
        bundle_groups = []
        
        if bundle_df.empty:
            return bundle_groups
        
        # Create product lookup
        product_dict = {p.product_id: p for p in products}
        
        # Process each bundle
        for _, bundle in bundle_df.iterrows():
            group = []
            
            # Try to find products in bundle
            for col in ['accessory_1', 'accessory_2', 'accessory_3']:
                if col in bundle and pd.notna(bundle[col]):
                    product_id = bundle[col]
                    if product_id in product_dict:
                        group.append(product_dict[product_id])
            
            if len(group) >= 2:  # Only create groups with at least 2 products
                bundle_groups.append(group)
        
        self.transformations_applied.append(f"Created {len(bundle_groups)} bundle groups")
        return bundle_groups
    
    def apply_inventory_constraints(self, products: List[Product], 
                                   min_days_of_stock: int = 7) -> List[Product]:
        """Filter products based on inventory constraints"""
        filtered = []
        
        for product in products:
            # Check if we have enough stock
            if product.stock_days >= min_days_of_stock:
                filtered.append(product)
            elif product.current_stock > 0:
                # Include but mark for reorder
                product.needs_urgent_restock = True
                filtered.append(product)
        
        removed_count = len(products) - len(filtered)
        if removed_count > 0:
            self.transformations_applied.append(f"Removed {removed_count} products due to low stock")
        
        return filtered
    
    def normalize_product_names(self, products: List[Product]) -> List[Product]:
        """Normalize product names for better matching with cohort data"""
        for product in products:
            # Standardize common variations
            normalized = product.product_name
            normalized = normalized.replace('iPhone', 'iPhone')  # Ensure consistent spacing
            normalized = normalized.replace('  ', ' ')  # Remove double spaces
            normalized = normalized.strip()
            
            product.normalized_name = normalized
        
        return products
    
    def calculate_space_allocation(self, products: List[Product], 
                                  total_width: float, 
                                  gap_size: float = 2.0) -> Dict[str, float]:
        """Calculate how much space to allocate to each product"""
        allocations = {}
        
        # Calculate total demand-weighted space need
        total_weight = sum(p.sales_velocity * p.optimal_facings * p.width for p in products)
        
        if total_weight == 0:
            # Equal allocation if no sales data
            available_width = total_width - (len(products) - 1) * gap_size
            equal_width = available_width / len(products)
            
            for product in products:
                allocations[product.product_id] = equal_width
        else:
            # Proportional allocation based on demand
            available_width = total_width - (len(products) - 1) * gap_size
            
            for product in products:
                weight = product.sales_velocity * product.optimal_facings * product.width
                allocation = (weight / total_weight) * available_width
                # Ensure minimum space for facings
                min_space = product.width * product.min_facings
                allocations[product.product_id] = max(allocation, min_space)
        
        return allocations
    
    def create_planogram_matrix(self, store: Store, products: List[Product]) -> pd.DataFrame:
        """Create a matrix representation of the planogram"""
        # Create empty matrix
        matrix_data = []
        
        for shelf in store.shelves:
            shelf_products = []
            for pos in shelf.positions:
                product = next((p for p in products if p.product_id == pos.product_id), None)
                if product:
                    shelf_products.append({
                        'product_name': product.product_name,
                        'category': product.category.value,
                        'facings': pos.facings,
                        'width': pos.width,
                        'position': pos.x_start
                    })
            
            matrix_data.append({
                'shelf_id': shelf.shelf_id,
                'shelf_name': shelf.shelf_name,
                'height': shelf.height,
                'y_position': shelf.y_position,
                'products': shelf_products,
                'utilization': shelf.utilization
            })
        
        return pd.DataFrame(matrix_data)
    
    def export_transformation_summary(self) -> Dict[str, any]:
        """Export summary of all transformations applied"""
        return {
            'timestamp': datetime.now().isoformat(),
            'transformations': self.transformations_applied,
            'total_transformations': len(self.transformations_applied)
        }
    
    @staticmethod
    def merge_product_data(sales_df: pd.DataFrame, 
                          cohort_df: pd.DataFrame, 
                          on_column: str = 'product_name') -> pd.DataFrame:
        """Merge sales data with cohort data"""
        # Perform left join to keep all products
        merged = sales_df.merge(
            cohort_df,
            left_on=on_column,
            right_on='accessory_product' if 'accessory_product' in cohort_df.columns else 'accessory_name',
            how='left'
        )
        
        # Fill missing cohort data with defaults
        merged['attach_rate'] = merged['attach_rate'].fillna(0)
        merged['purchase_frequency'] = merged['purchase_frequency'].fillna(0)
        
        return merged
    
    @staticmethod
    def aggregate_by_category(products: List[Product]) -> pd.DataFrame:
        """Create category-level aggregations"""
        data = []
        
        # Group by category
        categories = {}
        for product in products:
            if product.category not in categories:
                categories[product.category] = []
            categories[product.category].append(product)
        
        # Calculate aggregates
        for category, cat_products in categories.items():
            data.append({
                'category': category.value,
                'product_count': len(cat_products),
                'total_weekly_sales': sum(p.avg_weekly_sales for p in cat_products),
                'avg_price': sum(p.price for p in cat_products) / len(cat_products),
                'total_stock': sum(p.current_stock for p in cat_products),
                'avg_attach_rate': sum(getattr(p, 'attach_rate', 0) for p in cat_products) / len(cat_products)
            })
        
        return pd.DataFrame(data)