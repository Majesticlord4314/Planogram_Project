import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from src.models.product import Product, ProductCategory, ProductStatus
from src.models.shelf import Shelf
from src.models.store import Store

class DataLoader:
    """Handle all data loading operations"""
    
    def __init__(self, data_path: str = "data/raw"):
        self.data_path = Path(data_path)
        self.accessories_path = self.data_path / "accessories"
        self.cohorts_path = self.data_path / "cohorts"
        self.templates_path = self.data_path / "store_templates"
        
        # Validate paths exist
        self._validate_paths()
    
    def _validate_paths(self):
        """Ensure all required paths exist"""
        paths = [self.data_path, self.accessories_path, self.cohorts_path, self.templates_path]
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(f"Required path not found: {path}")
    
    def load_products_by_category(self, category: str) -> List[Product]:
        """Load products for a specific category"""
        file_mapping = {
            'cases': 'cases_sales.csv',
            'cables': 'cables_adapters_sales.csv',
            'screen_protectors': 'screen_protectors_sales.csv',
            'others': 'mounts_others_sales.csv'
        }
        
        if category not in file_mapping:
            raise ValueError(f"Unknown category: {category}. Available: {list(file_mapping.keys())}")
            
        file_path = self.accessories_path / file_mapping[category]
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
            
        df = pd.read_csv(file_path)
        return self._dataframe_to_products(df)
    
    def load_products_by_lob(self, lob: str, series_filter: Optional[str] = None) -> List[Product]:
        """Load all products for a specific LOB (iPhone, iPad, etc.)"""
        all_products = []
        
        # Load all accessory files
        for category in ['cases', 'cables', 'screen_protectors', 'others']:
            try:
                products = self.load_products_by_category(category)
                
                # Filter by LOB
                lob_products = [p for p in products if lob.lower() in p.core_product.lower()]
                
                # Further filter by series if specified
                if series_filter:
                    lob_products = [p for p in lob_products if series_filter.lower() in p.series.lower()]
                    
                all_products.extend(lob_products)
            except FileNotFoundError:
                print(f"Warning: Could not load {category} data")
                continue
                
        return all_products
    
    def load_all_products(self) -> List[Product]:
        """Load all products from all categories"""
        all_products = []
        
        for category in ['cases', 'cables', 'screen_protectors', 'others']:
            try:
                products = self.load_products_by_category(category)
                all_products.extend(products)
            except FileNotFoundError:
                print(f"Warning: Could not load {category} data")
                continue
                
        return all_products
    
    def load_cohort_data(self, lob: str, model: Optional[str] = None) -> pd.DataFrame:
        """Load cohort data for a specific LOB"""
        if lob.lower() == 'iphone' and model:
            # Use model-specific file for iPhone
            file_path = self.cohorts_path / 'iphone_cohorts_by_model.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                return df[df['core_product'] == model]
            else:
                print(f"Warning: iPhone model-specific cohort file not found")
                
        # Use general LOB file
        file_path = self.cohorts_path / f'{lob.lower()}_planogram_cohorts.csv'
        if not file_path.exists():
            # Try alternate naming
            file_path = self.cohorts_path / f'{lob.lower()}_cohorts.csv'
            
        if file_path.exists():
            return pd.read_csv(file_path)
        else:
            print(f"Warning: Cohort file not found for {lob}")
            return pd.DataFrame()
    
    def load_bundle_recommendations(self) -> pd.DataFrame:
        """Load bundle recommendations"""
        file_path = self.cohorts_path / 'bundle_recommendations.csv'
        if file_path.exists():
            return pd.read_csv(file_path)
        else:
            print("Warning: Bundle recommendations file not found")
            return pd.DataFrame()
    
    def load_master_cohorts(self) -> pd.DataFrame:
        """Load master cohort file with all LOBs"""
        file_path = self.cohorts_path / 'planogram_cohorts_master.csv'
        if file_path.exists():
            return pd.read_csv(file_path)
        else:
            print("Warning: Master cohort file not found")
            return pd.DataFrame()
    
    def enrich_products_with_cohorts(self, products: List[Product], 
                                   cohort_df: pd.DataFrame) -> List[Product]:
        """Add cohort data (attach rates, bundle info) to products"""
        if cohort_df.empty:
            return products
            
        # Create lookup dictionary from cohort data
        cohort_lookup = {}
        
        # Handle different column names in cohort files
        product_col = 'accessory_product' if 'accessory_product' in cohort_df.columns else 'accessory_name'
        
        for _, row in cohort_df.iterrows():
            key = row[product_col]
            cohort_lookup[key] = {
                'attach_rate': float(row.get('attach_rate', 0)),
                'purchase_frequency': int(row.get('purchase_frequency', 0)),
                'recommended_facings': int(row.get('recommended_facings', 0))
            }
        
        # Enrich products
        enriched = []
        for product in products:
            # Try to match by product name
            if product.product_name in cohort_lookup:
                product.attach_rate = cohort_lookup[product.product_name]['attach_rate']
                product.bundle_frequency = cohort_lookup[product.product_name]['purchase_frequency']
                
                # Adjust facings based on cohort data if provided
                recommended = cohort_lookup[product.product_name]['recommended_facings']
                if recommended > 0:
                    product.min_facings = max(1, recommended - 1)
                    product.max_facings = min(product.max_facings, recommended + 2)
            else:
                # Default values if not in cohort
                product.attach_rate = 0.0
                product.bundle_frequency = 0
                
            enriched.append(product)
            
        return enriched
    
    def load_store_template(self, store_type: str) -> Store:
        """Load store configuration"""
        file_path = self.templates_path / f"{store_type}_store.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Store template not found: {file_path}")
            
        with open(file_path, 'r') as f:
            template = json.load(f)
        
        # Create Shelf objects
        shelves = []
        for shelf_data in template['shelves']:
            shelf = Shelf(
                shelf_id=shelf_data['shelf_id'],
                shelf_name=shelf_data['shelf_name'],
                width=float(shelf_data['width']),
                height=float(shelf_data['height']),
                depth=float(shelf_data['depth']),
                y_position=float(shelf_data['y_position']),
                shelf_type=shelf_data['shelf_type'],
                eye_level_score=float(shelf_data['eye_level_score'])
            )
            shelves.append(shelf)
        
        # Create Store object
        store_info = template['store_info']
        store = Store(
            store_type=store_info['store_type'],
            store_name=store_info['store_name'],
            total_area_sqm=float(store_info['total_area_sqm']),
            accessory_area_sqm=float(store_info['accessory_area_sqm']),
            customer_flow=store_info['customer_flow'],
            restock_frequency_days=int(store_info['restock_frequency_days']),
            shelves=shelves,
            rules=template.get('product_mix_rules', {}),
            placement_rules=template.get('placement_rules', {}),
            optimization_weights=template.get('optimization_weights', {})
        )
        
        return store
    
    def _dataframe_to_products(self, df: pd.DataFrame) -> List[Product]:
        """Convert DataFrame to list of Product objects"""
        products = []
        
        for _, row in df.iterrows():
            try:
                # Map category string to enum
                cat_enum = self._map_category(row['category'])
                
                # Handle optional subcategory
                subcategory = str(row['subcategory']) if pd.notna(row['subcategory']) else ''
                
                product = Product(
                    product_name=str(row['product_name']).strip(),
                    series=str(row['series']).strip(),
                    category=cat_enum,
                    subcategory=subcategory,
                    brand=str(row['brand']),
                    width=float(row['width']),
                    height=float(row['height']),
                    depth=float(row['depth']),
                    pureqty=float(row['pureqty']),
                    impureqty=float(row['impureqty']),
                    core_product=str(row['core_product'])
                )
                products.append(product)
                
            except Exception as e:
                print(f"Error loading product {row.get('product_name', 'unknown')}: {e}")
                continue
                
        # Normalize sales velocity across all products
        if products:
            max_qty = max(p.total_qty for p in products)
            if max_qty > 0:
                for p in products:
                    p.sales_velocity = (p.total_qty / max_qty) * 100  # Normalize to 0-100
                    
        return products
    
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
    
    def get_available_stores(self) -> List[str]:
        """Get list of available store templates"""
        stores = []
        for file in self.templates_path.glob("*_store.json"):
            store_type = file.stem.replace('_store', '')
            stores.append(store_type)
        return stores
    
    def get_available_lobs(self) -> List[str]:
        """Get list of available LOBs from cohort files"""
        lobs = []
        for file in self.cohorts_path.glob("*_cohorts.csv"):
            if 'master' not in file.stem and 'by_model' not in file.stem:
                lob = file.stem.replace('_cohorts', '').replace('_planogram', '')
                lobs.append(lob.title())
        return lobs