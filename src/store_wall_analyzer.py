"""
Store Wall Analyzer - Groups walls by store and LOB categories based on product data
"""

import pandas as pd
import numpy as np
import re
from collections import defaultdict
import json

class StoreWallAnalyzer:
    def __init__(self, csv_path):
        """Initialize with store template CSV path"""
        self.csv_path = csv_path
        self.df = None
        self.lob_mapping = {
            # iPhone related
            'iphone_cases': ['iphone case', 'phone case', 'iphone cases', 'phone cases'],
            'iphone_accessories': ['iphone', 'phone', 'apple phone', 'lens protector', 'tg', 'apple accessories'],
            
            # iPad related  
            'ipad_cases': ['ipad case', 'ipad cases', 'ipad tg'],
            'ipad_accessories': ['ipad', 'apple tv', 'magic keyboard'],
            
            # Mac related
            'mac_accessories': ['mac', 'macbook', 'magic mouse', 'magic keyboard for ipad'],
            
            # Watch related
            'watch_bands': ['watch band', 'watch bands', 'apple watch'],
            
            # Audio/Accessories (skip for now as requested)
            'audio': ['airpods', 'beats', 'headphone', 'earphone', 'speakers', 'homepod'],
            
            # Charging/Cables
            'charging_cables': ['cable', 'cables', 'adapter', 'adaptors', 'charger', 'power bank', 'wireless charger'],
            
            # Accessories
            'organizers': ['organiser', 'organizer', 'hub', 'hubs'],
            'bags_sleeves': ['sleeve', 'sleeves', 'bagpack', 'macbook sleeve'],
            'gaming': ['gaming', 'mouse'],
            'misc_accessories': ['popsocket', 'ssd drive', 'card holder', 'mobile holder', 'privacy filter', 'apple accessories']
        }
        
    def load_data(self):
        """Load and clean the CSV data"""
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            # Clean column names
            self.df.columns = self.df.columns.str.strip()
            
            # Fill NaN values
            self.df['Product'] = self.df['Product'].fillna('')
            self.df['Store name'] = self.df['Store name'].fillna('')
            self.df['Wall'] = self.df['Wall'].fillna('')
            
            # Handle multiple capacity columns - combine shelf and peg capacities
            capacity_cols = [col for col in self.df.columns if 'Capacity' in col]
            if len(capacity_cols) > 1:
                print(f"Found multiple capacity columns: {capacity_cols}")
                # Convert all capacity columns to numeric and sum them
                total_capacity = 0
                for col in capacity_cols:
                    capacity_values = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
                    total_capacity += capacity_values
                self.df['Total_Capacity'] = total_capacity
            else:
                # Single capacity column
                self.df['Total_Capacity'] = pd.to_numeric(self.df.get('Capacity', 0), errors='coerce').fillna(0)
            
            print(f"Loaded {len(self.df)} rows from CSV")
            return True
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False
    
    def standardize_lob(self, product_text):
        """Extract and standardize LOB from product text"""
        if not product_text or pd.isna(product_text):
            return 'unknown'
            
        product_lower = str(product_text).lower().strip()
        
        # Check each LOB category
        for lob_category, keywords in self.lob_mapping.items():
            for keyword in keywords:
                if keyword in product_lower:
                    return lob_category
        
        # If no match found, try to categorize based on common patterns
        if any(word in product_lower for word in ['case', 'cover', 'protection']):
            if 'iphone' in product_lower or 'phone' in product_lower:
                return 'iphone_cases'
            elif 'ipad' in product_lower:
                return 'ipad_cases'
            else:
                return 'misc_cases'
        
        return 'misc_accessories'
    
    def analyze_store_walls(self):
        """Analyze walls by store and LOB"""
        if self.df is None:
            if not self.load_data():
                return None
        
        # Add LOB column
        self.df['LOB'] = self.df['Product'].apply(self.standardize_lob)
        
        # Group by store and analyze
        store_analysis = {}
        
        for store_name in self.df['Store name'].unique():
            if not store_name:
                continue
                
            store_data = self.df[self.df['Store name'] == store_name]
            
            # Count walls by LOB
            lob_counts = store_data['LOB'].value_counts().to_dict()
            
            # Get total capacity per LOB
            lob_capacity = store_data.groupby('LOB').agg({
                'Total_Capacity': 'sum',
                'Wall': 'nunique'
            }).to_dict()
            
            # Wall details by LOB
            wall_details = {}
            for lob in store_data['LOB'].unique():
                lob_walls = store_data[store_data['LOB'] == lob]
                wall_details[lob] = {
                    'walls': lob_walls['Wall'].unique().tolist(),
                    'total_capacity': lob_walls['Total_Capacity'].sum(),
                    'wall_count': lob_walls['Wall'].nunique(),
                    'products': lob_walls['Product'].unique().tolist()
                }
            
            store_analysis[store_name] = {
                'total_walls': store_data['Wall'].nunique(),
                'lob_counts': lob_counts,
                'lob_capacity': lob_capacity,
                'wall_details': wall_details,
                'location': store_data['LOCATION'].iloc[0] if len(store_data) > 0 else '',
                'city': store_data['CITY'].iloc[0] if len(store_data) > 0 else ''
            }
        
        return store_analysis
    
    def get_lob_summary(self):
        """Get overall LOB distribution summary"""
        if self.df is None:
            if not self.load_data():
                return None
        
        # Add LOB column if not exists
        if 'LOB' not in self.df.columns:
            self.df['LOB'] = self.df['Product'].apply(self.standardize_lob)
        
        # Overall LOB distribution
        lob_distribution = self.df['LOB'].value_counts().to_dict()
        
        # LOB by store count
        lob_by_store = self.df.groupby(['Store name', 'LOB']).size().reset_index(name='wall_count')
        
        return {
            'overall_distribution': lob_distribution,
            'lob_by_store': lob_by_store.to_dict('records'),
            'total_stores': self.df['Store name'].nunique(),
            'total_walls': self.df['Wall'].nunique()
        }
    
    def create_store_selector_data(self):
        """Create data structure for store selection interface"""
        analysis = self.analyze_store_walls()
        if not analysis:
            return None
        
        store_selector = {}
        
        for store_name, data in analysis.items():
            # Display all LOB categories with wall counts
            lob_display = {}
            for lob_key, lob_data in data['wall_details'].items():
                wall_count = lob_data.get('wall_count', 0)
                if wall_count > 0:  # Only show categories with walls
                    display_name = {
                        'iphone_cases': 'iPhone Cases',
                        'iphone_accessories': 'iPhone Accessories', 
                        'ipad_cases': 'iPad Cases',
                        'ipad_accessories': 'iPad Accessories',
                        'mac_accessories': 'Mac Accessories',
                        'watch_bands': 'Watch Bands',
                        'audio': 'Audio Products',
                        'charging_cables': 'Charging & Cables',
                        'bags_sleeves': 'Bags & Sleeves',
                        'organizers': 'Organizers',
                        'gaming': 'Gaming',
                        'misc_accessories': 'Mixed/Other'
                    }.get(lob_key, lob_key.replace('_', ' ').title())
                    
                    lob_display[lob_key] = f"{display_name} ({wall_count} walls)"
            
            store_selector[store_name] = {
                'location': data['location'],
                'city': data['city'],
                'total_walls': data['total_walls'],
                'lob_breakdown': lob_display,
                'capacity_summary': {
                    lob: details.get('total_capacity', 0) 
                    for lob, details in data['wall_details'].items()
                }
            }
        
        return store_selector
    
    def save_analysis(self, output_path):
        """Save analysis results to JSON"""
        analysis = self.analyze_store_walls()
        summary = self.get_lob_summary()
        selector_data = self.create_store_selector_data()
        
        output_data = {
            'store_analysis': analysis,
            'lob_summary': summary,
            'store_selector': selector_data,
            'lob_categories': list(self.lob_mapping.keys())
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"Analysis saved to {output_path}")
        return output_data

def main():
    """Main function to run the analysis"""
    analyzer = StoreWallAnalyzer('data/raw/store_templates/Plannogram compiled_16052025.csv')
    
    # Run analysis
    results = analyzer.save_analysis('output/store_wall_analysis.json')
    
    # Print summary
    if results:
        print("\n=== STORE WALL ANALYSIS SUMMARY ===")
        print(f"Total Stores: {results['lob_summary']['total_stores']}")
        print(f"Total Walls: {results['lob_summary']['total_walls']}")
        
        print("\n=== LOB DISTRIBUTION ===")
        for lob, count in results['lob_summary']['overall_distribution'].items():
            print(f"{lob}: {count} walls")
        
        print("\n=== STORE SELECTOR PREVIEW ===")
        for store_name, data in list(results['store_selector'].items())[:3]:
            print(f"\n{store_name} ({data['city']})")
            print(f"  Total Walls: {data['total_walls']}")
            for lob, description in data['lob_breakdown'].items():
                if '(0 walls)' not in description:
                    print(f"  - {description}")

if __name__ == "__main__":
    main()
