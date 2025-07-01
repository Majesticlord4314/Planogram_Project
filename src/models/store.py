from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from .shelf import Shelf, ShelfPosition
from .product import Product, ProductCategory
import json

@dataclass
class Store:
    """Store configuration model"""
    # Basic info
    store_type: str  # flagship, standard, express
    store_name: str
    total_area_sqm: float
    accessory_area_sqm: float
    customer_flow: str  # high, medium, low
    restock_frequency_days: int
    
    # Shelves
    shelves: List[Shelf] = field(default_factory=list)
    
    # Configuration rules
    rules: Dict = field(default_factory=dict)
    placement_rules: Dict = field(default_factory=dict)
    optimization_weights: Dict = field(default_factory=dict)
    
    # Calculated properties
    total_shelf_area: Optional[float] = field(init=False)
    eye_level_shelves: Optional[List[Shelf]] = field(init=False)
    premium_shelves: Optional[List[Shelf]] = field(init=False)
    total_capacity: Optional[int] = field(init=False)
    
    def __post_init__(self):
        """Calculate store metrics"""
        self.total_shelf_area = sum(shelf.area for shelf in self.shelves)
        self.eye_level_shelves = [s for s in self.shelves if s.is_eye_level]
        self.premium_shelves = [s for s in self.shelves if s.is_premium]
        self.total_capacity = self._estimate_capacity()
    
    def _estimate_capacity(self) -> int:
        """Estimate total product capacity"""
        avg_product_width = 8  # cm, average accessory width
        total_width = sum(shelf.width for shelf in self.shelves)
        return int(total_width / avg_product_width)
    
    def filter_products_by_rules(self, products: List[Product]) -> List[Product]:
        """Filter products based on store rules"""
        filtered = products.copy()
        
        # Apply store type specific filtering
        if self.store_type == "express":
            # Only top sellers
            if self.rules.get('only_bestsellers', False):
                max_products = self.rules.get('max_skus_total', 30)
                filtered = sorted(filtered, key=lambda p: p.avg_weekly_sales, reverse=True)[:max_products]
        
        elif self.store_type == "standard":
            # Apply 80/20 rule if specified
            if self.rules.get('filter_by_sales_rank', False):
                max_rank = self.rules.get('max_rank_included', 20)
                # Sort by sales and take top products
                filtered = sorted(filtered, key=lambda p: p.avg_weekly_sales, reverse=True)[:max_rank]
        
        # Filter by minimum sales threshold
        if 'min_weekly_sales' in self.rules:
            min_sales = self.rules['min_weekly_sales']
            filtered = [p for p in filtered if p.avg_weekly_sales >= min_sales]
        
        # Category limits
        if self.rules.get('min_skus_per_category'):
            filtered = self._apply_category_limits(filtered)
        
        return filtered
    
    def _apply_category_limits(self, products: List[Product]) -> List[Product]:
        """Ensure minimum/maximum SKUs per category"""
        min_per_cat = self.rules.get('min_skus_per_category', 1)
        max_per_cat = self.rules.get('max_skus_per_category', 999)
        
        # Group by category
        by_category = {}
        for product in products:
            if product.category not in by_category:
                by_category[product.category] = []
            by_category[product.category].append(product)
        
        # Apply limits
        result = []
        for category, cat_products in by_category.items():
            # Sort by sales within category
            cat_products.sort(key=lambda p: p.avg_weekly_sales, reverse=True)
            
            # Take between min and max
            to_take = max(min_per_cat, min(len(cat_products), max_per_cat))
            result.extend(cat_products[:to_take])
        
        return result
    
    def get_shelf_for_product(self, product: Product) -> Optional[Shelf]:
        """Find best shelf for a product based on rules and availability"""
        candidate_shelves = []
        
        for shelf in self.shelves:
            if shelf.can_fit_product(product):
                score = shelf.get_placement_score(product)
                candidate_shelves.append((shelf, score))
        
        if not candidate_shelves:
            return None
        
        # Sort by score and return best
        candidate_shelves.sort(key=lambda x: x[1], reverse=True)
        return candidate_shelves[0][0]
    
    def calculate_metrics(self) -> Dict:
        """Calculate store performance metrics"""
        metrics = {
            'total_shelves': len(self.shelves),
            'total_shelf_area': self.total_shelf_area,
            'eye_level_shelves': len(self.eye_level_shelves),
            'premium_shelves': len(self.premium_shelves),
            'average_utilization': 0,
            'total_products': 0,
            'total_facings': 0,
            'category_distribution': {},
            'shelf_utilization': []
        }
        
        # Calculate utilization and product counts
        total_util = 0
        for shelf in self.shelves:
            total_util += shelf.utilization
            metrics['total_products'] += len(shelf.positions)
            metrics['total_facings'] += sum(pos.facings for pos in shelf.positions)
            
            metrics['shelf_utilization'].append({
                'shelf_id': shelf.shelf_id,
                'shelf_name': shelf.shelf_name,
                'utilization': shelf.utilization
            })
        
        metrics['average_utilization'] = total_util / len(self.shelves) if self.shelves else 0
        
        return metrics
    
    def validate_planogram(self, products: Dict[str, Product]) -> List[str]:
        """Validate the current planogram and return any issues"""
        issues = []
        
        # Check shelf utilization
        for shelf in self.shelves:
            if shelf.utilization < 30:
                issues.append(f"Shelf {shelf.shelf_name} is underutilized ({shelf.utilization:.1f}%)")
            elif shelf.utilization > 95:
                issues.append(f"Shelf {shelf.shelf_name} is overcrowded ({shelf.utilization:.1f}%)")
        
        # Check product placement rules
        eye_level_products = []
        for shelf in self.eye_level_shelves:
            for pos in shelf.positions:
                if pos.product_id in products:
                    eye_level_products.append(products[pos.product_id])
        
        # Verify high-value items are at eye level
        if eye_level_products:
            avg_price = sum(p.price for p in eye_level_products) / len(eye_level_products)
            all_avg_price = sum(p.price for p in products.values()) / len(products)
            if avg_price < all_avg_price:
                issues.append("Eye level shelves have below-average priced items")
        
        # Check category distribution
        category_counts = {}
        for shelf in self.shelves:
            shelf_categories = set()
            for pos in shelf.positions:
                if pos.product_id in products:
                    product = products[pos.product_id]
                    shelf_categories.add(product.category)
                    category_counts[product.category] = category_counts.get(product.category, 0) + 1
            
            # Check if too many categories on one shelf
            if len(shelf_categories) > 4 and self.placement_rules.get('category_grouping', True):
                issues.append(f"Shelf {shelf.shelf_name} has too many categories ({len(shelf_categories)})")
        
        # Check minimum SKUs per category
        if 'min_skus_per_category' in self.rules:
            min_skus = self.rules['min_skus_per_category']
            for category, count in category_counts.items():
                if count < min_skus:
                    issues.append(f"Category {category.value} has only {count} SKUs (minimum: {min_skus})")
        
        # Check facing rules
        for shelf in self.shelves:
            for pos in shelf.positions:
                if pos.product_id in products:
                    product = products[pos.product_id]
                    if pos.facings < product.min_facings:
                        issues.append(f"Product {product.product_name} has insufficient facings")
                    elif pos.facings > product.max_facings:
                        issues.append(f"Product {product.product_name} has too many facings")
        
        return issues
    
    def get_reorder_list(self, products: Dict[str, Product]) -> List[Dict]:
        """Generate reorder list based on current stock and sales velocity"""
        reorder_list = []
        
        for shelf in self.shelves:
            for pos in shelf.positions:
                if pos.product_id in products:
                    product = products[pos.product_id]
                    
                    # Calculate days until stockout
                    days_of_stock = product.stock_days
                    
                    # If stock won't last until next restock
                    if days_of_stock < self.restock_frequency_days * 1.5:
                        reorder_qty = int(product.sales_velocity * self.restock_frequency_days * 2)
                        reorder_list.append({
                            'product_id': product.product_id,
                            'product_name': product.product_name,
                            'current_stock': product.current_stock,
                            'days_of_stock': days_of_stock,
                            'recommended_order': reorder_qty,
                            'priority': 'urgent' if days_of_stock < self.restock_frequency_days else 'normal'
                        })
        
        # Sort by priority and days of stock
        reorder_list.sort(key=lambda x: (x['priority'] != 'urgent', x['days_of_stock']))
        return reorder_list
    
    def optimize_shelf_assignment(self, products: List[Product]) -> Dict[int, List[Product]]:
        """Assign products to shelves optimally"""
        assignments = {shelf.shelf_id: [] for shelf in self.shelves}
        
        # Sort products by value (price * sales_velocity)
        products_sorted = sorted(products, 
                               key=lambda p: p.price * p.sales_velocity, 
                               reverse=True)
        
        # Assign high-value products to eye-level shelves
        eye_level_ids = [s.shelf_id for s in self.eye_level_shelves]
        premium_ids = [s.shelf_id for s in self.premium_shelves]
        standard_ids = [s.shelf_id for s in self.shelves 
                       if s.shelf_id not in eye_level_ids and s.shelf_id not in premium_ids]
        
        # Group products by category if required
        if self.placement_rules.get('category_grouping', False):
            # Group by category
            by_category = {}
            for product in products_sorted:
                if product.category not in by_category:
                    by_category[product.category] = []
                by_category[product.category].append(product)
            
            # Assign categories to shelf levels
            shelf_groups = [eye_level_ids, premium_ids, standard_ids]
            category_idx = 0
            
            for category, cat_products in by_category.items():
                target_shelves = shelf_groups[category_idx % len(shelf_groups)]
                for product in cat_products:
                    # Find shelf with space
                    for shelf_id in target_shelves:
                        shelf = next(s for s in self.shelves if s.shelf_id == shelf_id)
                        if shelf.can_fit_product(product):
                            assignments[shelf_id].append(product)
                            break
                category_idx += 1
        else:
            # Simple assignment based on value
            for product in products_sorted:
                assigned = False
                
                # Try eye level first for high-value
                if product.price * product.sales_velocity > 100:
                    for shelf_id in eye_level_ids:
                        shelf = next(s for s in self.shelves if s.shelf_id == shelf_id)
                        if shelf.can_fit_product(product):
                            assignments[shelf_id].append(product)
                            assigned = True
                            break
                
                # Then try any available shelf
                if not assigned:
                    for shelf in self.shelves:
                        if shelf.can_fit_product(product):
                            assignments[shelf.shelf_id].append(product)
                            break
        
        return assignments
    
    def to_dict(self) -> Dict:
        """Export store configuration as dictionary"""
        return {
            'store_info': {
                'store_type': self.store_type,
                'store_name': self.store_name,
                'total_area_sqm': self.total_area_sqm,
                'accessory_area_sqm': self.accessory_area_sqm,
                'customer_flow': self.customer_flow,
                'restock_frequency_days': self.restock_frequency_days
            },
            'shelves': [shelf.to_dict() for shelf in self.shelves],
            'metrics': self.calculate_metrics(),
            'rules': self.rules,
            'placement_rules': self.placement_rules,
            'optimization_weights': self.optimization_weights
        }
    
    def save_planogram(self, filename: str, products: Dict[str, Product]):
        """Save current planogram to file"""
        data = self.to_dict()
        
        # Add product details
        data['products'] = {}
        for shelf in self.shelves:
            for pos in shelf.positions:
                if pos.product_id in products:
                    product = products[pos.product_id]
                    data['products'][pos.product_id] = {
                        'name': product.product_name,
                        'category': product.category.value,
                        'price': product.price,
                        'sales_velocity': product.sales_velocity
                    }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Planogram saved to {filename}")