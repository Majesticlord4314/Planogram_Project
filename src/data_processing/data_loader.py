"""
Data Loader for Planogram Project
Loads product data from CSV files
"""
import os
import sys
import pandas as pd
from pathlib import Path
from collections import namedtuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

class DataLoader:
    """Data loader for product data"""
    
    def __init__(self, data_dir=None):
        """Initialize the data loader"""
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = project_root / 'data' / 'raw'
    
    def load_products_from_file(self, file_path):
        """Load products from a CSV file"""
        try:
            # Handle both absolute and relative paths
            if os.path.isabs(file_path):
                full_path = Path(file_path)
            else:
                full_path = project_root / file_path
            
            # Check if file exists
            if not full_path.exists():
                print(f"File not found: {full_path}")
                return []
            
            # Read CSV file
            df = pd.read_csv(full_path)
            
            # Clean column names by stripping whitespace
            df.columns = df.columns.str.strip()
            
            # Create products from DataFrame
            products = []
            class Product:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)

            for _, row in df.iterrows():
                try:
                    product_data = {
                        'product_name': row.get('Product Name', row.get('product_name', '')),
                        'brand': row.get('Brand', row.get('brand', '')),
                        'series': row.get('Series', row.get('series', '')),
                        'total_qty': row.get('Total Qty', row.get('total_qty', 0)),
                        'pureqty': row.get('Pure Qty', row.get('pureqty', 0)),
                        'impureqty': row.get('Impure Qty', row.get('impureqty', 0)),
                        'product_id': row.get('Product ID', row.get('product_id', '')),
                        'color': row.get('Color', row.get('color', '')),
                        'price': row.get('Price', row.get('price', 0))
                    }
                    product = Product(**product_data)
                    products.append(product)
                except Exception as e:
                    print(f"Error creating product from row: {e}")
            
            return products
        
        except Exception as e:
            print(f"Error loading products from file: {e}")
            return []
    
    def load_all_products(self):
        """Load all products from all CSV files"""
        products = []
        
        # Find all CSV files in the accessories directory
        accessories_dir = self.data_dir / 'accessories'
        if accessories_dir.exists():
            for file_path in accessories_dir.glob('*.csv'):
                try:
                    file_products = self.load_products_from_file(file_path)
                    products.extend(file_products)
                    print(f"Loaded {len(file_products)} products from {file_path.name}")
                except Exception as e:
                    print(f"Error loading products from {file_path.name}: {e}")
        
        return products