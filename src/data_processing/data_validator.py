from typing import List, Dict, Tuple, Optional
import pandas as pd
from datetime import datetime
from src.models.product import Product, ProductCategory
from src.models.store import Store

class DataValidator:
    """Validate data quality and completeness"""
    
    def __init__(self):
        self.validation_results = []
        self.warnings = []
        self.errors = []
    
    def validate_products(self, products: List[Product]) -> Tuple[bool, List[str]]:
        """Validate product data and return (is_valid, issues)"""
        self.validation_results = []
        self.warnings = []
        self.errors = []
        
        if not products:
            self.errors.append("No products provided for validation")
            return False, self.errors
        
        # Check for duplicates
        product_ids = [p.product_id for p in products]
        if len(product_ids) != len(set(product_ids)):
            duplicates = [pid for pid in product_ids if product_ids.count(pid) > 1]
            self.errors.append(f"Duplicate product IDs found: {set(duplicates)}")
        
        # Validate each product
        for product in products:
            self._validate_single_product(product)
        
        # Check category distribution
        self._validate_category_distribution(products)
        
        # Check price distribution
        self._validate_price_distribution(products)
        
        # Compile all issues
        all_issues = self.errors + self.warnings
        is_valid = len(self.errors) == 0
        
        return is_valid, all_issues
    
    def _validate_single_product(self, product: Product):
        """Validate individual product data"""
        # Check dimensions
        if product.width <= 0 or product.height <= 0 or product.depth <= 0:
            self.errors.append(f"{product.product_name}: Invalid dimensions")
        
        # Check if dimensions are reasonable (in cm)
        if product.width > 50:
            self.warnings.append(f"{product.product_name}: Unusually wide ({product.width}cm)")
        if product.height > 50:
            self.warnings.append(f"{product.product_name}: Unusually tall ({product.height}cm)")
        
        # Check quantity data
        if hasattr(product, 'pureqty') and product.pureqty < 0:
            self.errors.append(f"{product.product_name}: Negative pure quantity")
        
        if hasattr(product, 'impureqty') and product.impureqty < 0:
            self.errors.append(f"{product.product_name}: Negative impure quantity")
        
        # Check facing constraints if they exist
        if hasattr(product, 'min_facings') and hasattr(product, 'max_facings'):
            if product.min_facings > product.max_facings:
                self.errors.append(f"{product.product_name}: Min facings > Max facings")
        
        # Check profit/price if exists
        if hasattr(product, 'profit') and product.profit < 0:
            self.warnings.append(f"{product.product_name}: Negative profit margin")
    
    def _validate_category_distribution(self, products: List[Product]):
        """Check if category distribution is reasonable"""
        category_counts = {}
        for product in products:
            category_counts[product.category] = category_counts.get(product.category, 0) + 1
        
        total_products = len(products)
        
        # Check if any category dominates
        for category, count in category_counts.items():
            percentage = (count / total_products) * 100
            if percentage > 60:
                self.warnings.append(f"Category {category.value} dominates with {percentage:.1f}% of products")
            elif percentage < 5 and count > 0:
                self.warnings.append(f"Category {category.value} has very few products ({count})")
    
    def _validate_price_distribution(self, products: List[Product]):
        """Check profit distribution for anomalies"""
        # Use profit if available, otherwise skip
        profits = [getattr(p, 'profit', 0) for p in products if hasattr(p, 'profit')]
        
        if not profits:
            return
        
        avg_profit = sum(profits) / len(profits)
        
        # Check for extreme outliers
        for product in products:
            if hasattr(product, 'profit'):
                if product.profit > avg_profit * 5:
                    self.warnings.append(f"{product.product_name}: Very high margin ({product.profit})")
                elif product.profit < avg_profit * 0.1 and product.profit > 0:
                    self.warnings.append(f"{product.product_name}: Very low margin ({product.profit})")
    
    def validate_store_template(self, store: Store) -> Tuple[bool, List[str]]:
        """Validate store configuration"""
        issues = []
        
        # Check if shelves exist
        if not store.shelves:
            issues.append("Store has no shelves defined")
            return False, issues
        
        # Check shelf dimensions
        for shelf in store.shelves:
            if shelf.width <= 0 or shelf.height <= 0:
                issues.append(f"Shelf {shelf.shelf_id} has invalid dimensions")
            
            if shelf.eye_level_score < 0 or shelf.eye_level_score > 1:
                issues.append(f"Shelf {shelf.shelf_id} has invalid eye_level_score ({shelf.eye_level_score})")
        
        # Check shelf ordering (should be bottom to top)
        y_positions = [s.y_position for s in store.shelves]
        if y_positions != sorted(y_positions):
            issues.append("Shelves are not ordered from bottom to top")
        
        # Check for overlapping shelves
        for i, shelf1 in enumerate(store.shelves):
            for shelf2 in store.shelves[i+1:]:
                if abs(shelf1.y_position - shelf2.y_position) < shelf1.height:
                    issues.append(f"Shelves {shelf1.shelf_id} and {shelf2.shelf_id} may overlap")
        
        # Validate rules
        if store.rules.get('min_skus_per_category', 0) > store.rules.get('max_skus_total', float('inf')):
            issues.append("min_skus_per_category cannot exceed max_skus_total")
        
        return len(issues) == 0, issues
    
    def validate_cohort_data(self, cohort_df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate cohort data structure"""
        issues = []
        
        if cohort_df.empty:
            issues.append("Cohort data is empty")
            return False, issues
        
        # Check required columns
        required_columns = ['lob', 'core_product', 'accessory_category']
        missing_columns = set(required_columns) - set(cohort_df.columns)
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")
        
        # Check attach rates
        if 'attach_rate' in cohort_df.columns:
            invalid_rates = cohort_df[(cohort_df['attach_rate'] < 0) | (cohort_df['attach_rate'] > 1)]
            if not invalid_rates.empty:
                issues.append(f"Invalid attach rates found: {len(invalid_rates)} records")
        
        # Check for duplicates
        if 'accessory_product' in cohort_df.columns and 'core_product' in cohort_df.columns:
            duplicates = cohort_df.duplicated(subset=['core_product', 'accessory_product'])
            if duplicates.any():
                issues.append(f"Duplicate cohort entries found: {duplicates.sum()} records")
        
        return len(issues) == 0, issues
    
    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report"""
        report = []
        report.append("DATA VALIDATION REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if self.errors:
            report.append(f"ERRORS ({len(self.errors)}):")
            report.append("-" * 30)
            for error in self.errors:
                report.append(f"❌ {error}")
            report.append("")
        
        if self.warnings:
            report.append(f"WARNINGS ({len(self.warnings)}):")
            report.append("-" * 30)
            for warning in self.warnings:
                report.append(f"⚠️  {warning}")
            report.append("")
        
        if not self.errors and not self.warnings:
            report.append("✅ All validations passed!")
        
        return "\n".join(report)