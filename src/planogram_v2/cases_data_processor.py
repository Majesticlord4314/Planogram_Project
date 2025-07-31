#!/usr/bin/env python3
"""
Cases & Covers Data Processor - Simplified Planogram Generation
Breaks down cases sales data by category and sales frequency for top products
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json

class CasesDataProcessor:
    """Process cases sales data for planogram generation"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.cases_data = None
        self.processed_data = {}
        
    def load_cases_data(self) -> pd.DataFrame:
        """Load cases sales data"""
        cases_file = self.data_path / 'data' / 'raw' / 'accessories' / 'cases_sales.csv'
        if not cases_file.exists():
            raise FileNotFoundError(f"Cases data not found: {cases_file}")
            
        self.cases_data = pd.read_csv(cases_file)
        
        # Clean column names (remove trailing spaces)
        self.cases_data.columns = self.cases_data.columns.str.strip()
        
        # Clean data values (remove trailing spaces)
        for col in ['series', 'category', 'subcategory', 'brand']:
            if col in self.cases_data.columns:
                self.cases_data[col] = self.cases_data[col].astype(str).str.strip()
        
        print(f"Loaded {len(self.cases_data)} case products")
        print(f"Columns: {self.cases_data.columns.tolist()}")
        return self.cases_data
    
    def categorize_by_series_and_type(self) -> Dict:
        """Break down cases by iPhone series and case type"""
        if self.cases_data is None:
            self.load_cases_data()
            
        # Clean and categorize data
        df = self.cases_data.copy()
        df['total_sales'] = df['pureqty'] + df['impureqty']
        
        # Group by series and category
        series_breakdown = {}
        
        for series in df['series'].unique():
            if pd.isna(series) or series == 'nan':
                continue
                
            series_data = df[df['series'] == series].copy()
            
            # Categorize by subcategory/type
            category_breakdown = {}
            
            for category in series_data['subcategory'].unique():
                if pd.isna(category) or category == 'nan':
                    category = 'other'
                    
                cat_data = series_data[series_data['subcategory'] == category]
                
                # Sort by sales performance
                top_products = cat_data.nlargest(10, 'total_sales')[
                    ['product_name', 'brand', 'subcategory', 'total_sales', 'pureqty', 'impureqty']
                ].to_dict('records')
                
                category_breakdown[category] = {
                    'total_products': len(cat_data),
                    'total_sales': cat_data['total_sales'].sum(),
                    'top_products': top_products
                }
            
            series_breakdown[series] = category_breakdown
            
        self.processed_data = series_breakdown
        return series_breakdown
    
    def get_top_products_by_priority(self, max_products_per_wall: int = 30) -> Dict:
        """Get top products organized by priority for planogram placement"""
        if not self.processed_data:
            self.categorize_by_series_and_type()
            
        # Priority order: iPhone 16 Pro Max > iPhone 16 Pro > iPhone 16 Plus > iPhone 16 Base > iPhone 15 series
        priority_series = [
            'iPhone 16 Pro Max',
            'iPhone 16 Pro', 
            'iPhone 16 Plus',
            'iPhone 16 Base',
            'iPhone 15 Pro Max',
            'iPhone 15 Pro',
            'iPhone 15 Plus', 
            'iPhone 15 Base'
        ]
        
        # Priority categories: Clear > Silicone > MagSafe > Others
        priority_categories = ['clear', 'silicone', 'magsafe', 'case', 'other']
        
        planogram_data = {}
        
        for series in priority_series:
            if series not in self.processed_data:
                continue
                
            series_products = []
            
            # Get products by category priority
            for category in priority_categories:
                if category in self.processed_data[series]:
                    cat_data = self.processed_data[series][category]
                    
                    # Add top products from this category
                    for product in cat_data['top_products'][:5]:  # Top 5 per category
                        product['series'] = series
                        product['category'] = category
                        product['priority_score'] = self._calculate_priority_score(series, category, product['total_sales'])
                        series_products.append(product)
            
            # Sort by priority score and limit
            series_products.sort(key=lambda x: x['priority_score'], reverse=True)
            planogram_data[series] = series_products[:max_products_per_wall]
            
        return planogram_data
    
    def _calculate_priority_score(self, series: str, category: str, sales: int) -> float:
        """Calculate priority score for product placement"""
        # Series weights
        series_weights = {
            'iPhone 16 Pro Max': 100,
            'iPhone 16 Pro': 90,
            'iPhone 16 Plus': 80,
            'iPhone 16 Base': 70,
            'iPhone 15 Pro Max': 60,
            'iPhone 15 Pro': 50,
            'iPhone 15 Plus': 40,
            'iPhone 15 Base': 30
        }
        
        # Category weights
        category_weights = {
            'clear': 20,
            'silicone': 18,
            'magsafe': 16,
            'case': 14,
            'other': 10
        }
        
        series_weight = series_weights.get(series, 10)
        category_weight = category_weights.get(category, 5)
        sales_weight = min(sales / 100, 50)  # Cap sales influence
        
        return series_weight + category_weight + sales_weight
    
    def generate_wall_layouts(self, store_name: str, walls_allocated: int = 3) -> Dict:
        """Generate specific wall layouts for a store"""
        top_products = self.get_top_products_by_priority()
        
        # Load store configuration
        config_file = self.data_path / 'store_wall_config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                store_config = json.load(f)
                
            if store_name in store_config['stores']:
                walls_allocated = store_config['stores'][store_name]['wall_allocation'].get('Cases & Covers', walls_allocated)
        
        # Distribute products across walls
        wall_layouts = {}
        products_per_wall = 25  # Standard wall capacity
        
        all_products = []
        for series, products in top_products.items():
            all_products.extend(products)
        
        # Sort all products by priority
        all_products.sort(key=lambda x: x['priority_score'], reverse=True)
        
        print(f"Total products for distribution: {len(all_products)}")
        
        # Distribute across walls
        for wall_num in range(1, walls_allocated + 1):
            start_idx = (wall_num - 1) * products_per_wall
            end_idx = start_idx + products_per_wall
            
            wall_products = all_products[start_idx:end_idx]
            
            wall_layouts[f'Wall_{wall_num}'] = {
                'products': wall_products,
                'total_products': len(wall_products),
                'total_capacity': sum(p['total_sales'] for p in wall_products),
                'series_distribution': self._get_series_distribution(wall_products),
                'category_distribution': self._get_category_distribution(wall_products)
            }
        
        return wall_layouts
    
    def _get_series_distribution(self, products: List[Dict]) -> Dict:
        """Get series distribution for a wall"""
        series_count = {}
        for product in products:
            series = product['series']
            series_count[series] = series_count.get(series, 0) + 1
        return series_count
    
    def _get_category_distribution(self, products: List[Dict]) -> Dict:
        """Get category distribution for a wall"""
        category_count = {}
        for product in products:
            category = product['category']
            category_count[category] = category_count.get(category, 0) + 1
        return category_count
    
    def save_processed_data(self, output_file: str = None):
        """Save processed data for planogram generation"""
        if output_file is None:
            output_file = self.data_path / 'data' / 'processed' / 'cases_planogram_data.json'
        
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            'processed_data': self.processed_data,
            'top_products': self.get_top_products_by_priority(),
            'metadata': {
                'total_products': len(self.cases_data) if self.cases_data is not None else 0,
                'processing_date': pd.Timestamp.now().isoformat(),
                'data_source': str(self.data_path / 'data' / 'raw' / 'accessories' / 'cases_sales.csv')
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Processed data saved to: {output_file}")
        return output_file

# Example usage
if __name__ == "__main__":
    # Initialize processor
    processor = CasesDataProcessor("c:/Users/Shivansh Pal/Desktop/Planogram_Project")
    
    # Load and process data
    processor.load_cases_data()
    breakdown = processor.categorize_by_series_and_type()
    
    # Print summary
    print("\n=== CASES DATA BREAKDOWN ===")
    for series, categories in breakdown.items():
        print(f"\n{series}:")
        for category, data in categories.items():
            print(f"  {category}: {data['total_products']} products, {data['total_sales']} total sales")
    
    # Generate wall layouts for KORAMANGALA
    wall_layouts = processor.generate_wall_layouts("IMAGINE- KORAMANGALA BENGALURU")
    
    print("\n=== WALL LAYOUTS FOR KORAMANGALA ===")
    for wall, layout in wall_layouts.items():
        print(f"\n{wall}: {layout['total_products']} products")
        print(f"  Series: {layout['series_distribution']}")
        print(f"  Categories: {layout['category_distribution']}")
    
    # Save processed data
    processor.save_processed_data()