import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from ..models.product import Product, ProductCategory, ProductStatus
from ..models.shelf import Shelf
from ..models.store import Store

class DataLoader:
    """Handle all data loading operations"""
    
    def __init__(self, data_path: str = "data/raw"):
        self.data_path = Path(data_path)
        self.accessories_path = self.data_path / "accessories"
        self.cohorts_path = self.data_path / "cohorts"
        self.templates_path = self.data_path / "store_templates"
        
    def load_products_by_category(self, category: str) -> List[Product]:
        """Load products for a specific category"""
        file_mapping = {
            'cases': 'cases_sales.csv',
            'cables': 'cables_adapters_sales.csv',
            'screen_protectors': 'screen_protectors_sales.csv',
            'others': 'mounts_others_sales.csv'
        }
        
        if category not in file_mapping:
            raise ValueError(f"Unknown category: {category}")
            
        file_path = self.accessories_path / file_mapping[category]
        df = pd.read_csv(file_path)
        
        products = []
        for _, row in df.iterrows():
            # Map category string to enum
            cat_enum = self._map_category(row['category'])
            status_enum = ProductStatus(row['status']) if 'status' in row else ProductStatus.ACTIVE
            
            product = Product(
                product_id=row['product_id'],
                product_name=row['product_name'],
                series=row['series'],
                category=cat_enum,
                subcategory=row['subcategory'],
                brand=row['brand'],
                width=float(row['width']),
                height=float(row['height']),
                depth=float(row['depth']),
                weight=float(row['weight']),
                qty_sold_last_week=int(row['qty_sold_last_week']),
                qty_sold_last_month=int(row['qty_sold_last_month']),
                avg_weekly_sales=float(row['avg_weekly_sales']),
                current_stock=int(row['current_stock']),
                min_stock=int(row['min_stock']),
                min_facings=int(row['min_facings']),
                max_facings=int(row['max_facings']),
                color=row['color'],
                price=float(row['price']),
                core_product=row['core_product'],
                launch_date=row['launch_date'],
                status=status_enum
            )
            products.append(product)
            
        return products
    
    def load_products_by_lob(self, lob: str, series_filter: Optional[str] = None) -> List[Product]:
        """Load all products for a specific LOB (iPhone, iPad, etc.)"""
        all_products = []
        
        # Load all accessory files
        for category in ['cases', 'cables', 'screen_protectors', 'others']:
            products = self.load_products_by_category(category)
            
            # Filter by LOB
            lob_products = [p for p in products if lob.lower() in p.core_product.lower()]
            
            # Further filter by series if specified
            if series_filter:
                lob_products = [p for p in lob_products if series_filter in p.series]
                
            all_products.extend(lob_products)
            
        return all_products
    
    def load_cohort_data(self, lob: str, model: Optional[str] = None) -> pd.DataFrame:
        """Load cohort data for a specific LOB"""
        if lob.lower() == 'iphone' and model:
            # Use model-specific file
            file_path = self.cohorts_path / 'iphone_cohorts_by_model.csv'
            df = pd.read_csv(file_path)
            return df[df['core_product'] == model]
        else:
            # Use general LOB file
            file_path = self.cohorts_path / f'{lob.lower()}_planogram_cohorts.csv'
            return pd.read_csv(file_path)
    
    def enrich_products_with_cohorts(self, products: List[Product], 
                                   cohort_df: pd.DataFrame) -> List[Product]:
        """Add cohort data (attach rates, bundle info) to products"""
        # Create lookup dictionary
        cohort_lookup = {}
        for _, row in cohort_df.iterrows():
            key = row['accessory_product'] if 'accessory_product' in row else row['accessory_name']
            cohort_lookup[key] = {
                'attach_rate': row.get('attach_rate', 0),
                'purchase_frequency': row.get('purchase_frequency', 0)
            }
        
        # Enrich products
        for product in products:
            if product.product_name in cohort_lookup:
                product.attach_rate = cohort_lookup[product.product_name]['attach_rate']
                product.bundle_frequency = cohort_lookup[product.product_name]['purchase_frequency']
            else:
                product.attach_rate = 0
                product.bundle_frequency = 0
                
        return products
    
    def load_store_template(self, store_type: str) -> Store:
        """Load store configuration"""
        file_path = self.templates_path / f"{store_type}_store.json"
        
        with open(file_path, 'r') as f:
            template = json.load(f)
        
        # Create Shelf objects
        shelves = []
        for shelf_data in template['shelves']:
            shelf = Shelf(
                shelf_id=shelf_data['shelf_id'],
                shelf_name=shelf_data['shelf_name'],
                width=shelf_data['width'],
                height=shelf_data['height'],
                depth=shelf_data['depth'],
                y_position=shelf_data['y_position'],
                shelf_type=shelf_data['shelf_type'],
                eye_level_score=shelf_data['eye_level_score']
            )
            shelves.append(shelf)
        
        # Create Store object
        store = Store(
            store_type=template['store_info']['store_type'],
            store_name=template['store_info']['store_name'],
            total_area_sqm=template['store_info']['total_area_sqm'],
            accessory_area_sqm=template['store_info']['accessory_area_sqm'],
            customer_flow=template['store_info']['customer_flow'],
            restock_frequency_days=template['store_info']['restock_frequency_days'],
            shelves=shelves,
            rules=template.get('product_mix_rules', {}),
            placement_rules=template.get('placement_rules', {}),
            optimization_weights=template.get('optimization_weights', {})
        )
        
        return store
    
    def _map_category(self, category_str: str) -> ProductCategory:
        """Map string category to enum"""
        mapping = {
            'case': ProductCategory.CASE,
            'cable': ProductCategory.CABLE,
            'adapter': ProductCategory.ADAPTER,
            'screen_protector': ProductCategory.SCREEN_PROTECTOR,
            'charger': ProductCategory.CHARGER,
            'mount': ProductCategory.MOUNT,
            'audio': ProductCategory.AUDIO,
            'keyboard': ProductCategory.KEYBOARD,
            'mouse': ProductCategory.MOUSE,
            'pencil': ProductCategory.PENCIL,
            'watch_band': ProductCategory.WATCH_BAND
        }
        return mapping.get(category_str.lower(), ProductCategory.OTHER)