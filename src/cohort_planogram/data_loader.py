"""
Data loader for cohort planogram generation
Handles loading and processing of cohort data for different LOBs
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

class CohortDataLoader:
    """Loads and processes cohort data for planogram generation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path("data/raw")
        self.cohort_file = self.data_dir / "cohorts" / "planogram_cohorts_corrected.csv"
        
        # Cache for loaded data
        self._cohort_data = None
        self._lob_data_cache = {}
    
    def _load_cohort_data(self) -> pd.DataFrame:
        """Load the main cohort data file"""
        if self._cohort_data is None:
            try:
                if self.cohort_file.exists():
                    self._cohort_data = pd.read_csv(self.cohort_file)
                    self.logger.info(f"Loaded {len(self._cohort_data)} cohort records")
                else:
                    # Create dummy data if file doesn't exist
                    self.logger.warning(f"Cohort file not found: {self.cohort_file}")
                    self._cohort_data = self._create_dummy_cohort_data()
            except Exception as e:
                self.logger.error(f"Error loading cohort data: {e}")
                self._cohort_data = self._create_dummy_cohort_data()
        
        return self._cohort_data
    
    def _create_dummy_cohort_data(self) -> pd.DataFrame:
        """Create dummy cohort data for testing"""
        self.logger.info("Creating dummy cohort data for testing")
        
        # Create sample data for iPhone
        lobs = ['iPhone', 'iPad', 'Mac', 'Watch', 'AirPods']
        core_products = {
            'iPhone': ['iPhone 16', 'iPhone 16 Pro Max', 'iPhone 15', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 15 Pro Max'],
            'iPad': ['iPad Pro 12.9', 'iPad Air', 'iPad Pro 11', 'iPad', 'iPad mini'],
            'Mac': ['MacBook Pro 16', 'MacBook Pro 14', 'MacBook Air', 'iMac', 'Mac Studio'],
            'Watch': ['Apple Watch Series 9', 'Apple Watch Ultra 2', 'Apple Watch SE', 'Apple Watch Series 8'],
            'AirPods': ['AirPods Pro 2', 'AirPods 3', 'AirPods Max', 'AirPods 2']
        }
        
        categories = ['Screen Protector', 'Case', 'Wallet', 'PopSocket', 'Stand', 'Ring Holder', 'Wireless Charger', 'Headphones']
        
        dummy_data = []
        
        for lob in lobs:
            for core_product in core_products[lob]:
                for category in categories:
                    # Generate realistic attach rates and frequencies
                    attach_rate = np.random.beta(2, 8)  # Skewed towards lower rates
                    purchase_frequency = np.random.poisson(50) + 10
                    
                    dummy_data.append({
                        'lob': lob,
                        'core_product': core_product,
                        'accessory_category': category,
                        'accessory_product': f"{category} for {core_product}",
                        'attach_rate': attach_rate,
                        'purchase_frequency': purchase_frequency,
                        'recommended_facings': max(1, int(attach_rate * 5))
                    })
        
        return pd.DataFrame(dummy_data)
    
    def get_lob_data(self, lob: str) -> pd.DataFrame:
        """Get cohort data for a specific LOB"""
        if lob not in self._lob_data_cache:
            cohort_data = self._load_cohort_data()
            lob_data = cohort_data[cohort_data['lob'] == lob].copy()
            self._lob_data_cache[lob] = lob_data
            self.logger.info(f"Retrieved {len(lob_data)} records for LOB: {lob}")
        
        return self._lob_data_cache[lob]
    
    def get_top_core_products(self, lob: str, limit: int = 6) -> List[str]:
        """Get top core products by total accessory sales"""
        lob_data = self.get_lob_data(lob)
        
        if len(lob_data) == 0:
            return []
        
        # Group by core product and sum purchase frequency
        product_sales = lob_data.groupby('core_product')['purchase_frequency'].sum()
        top_products = product_sales.nlargest(limit).index.tolist()
        
        self.logger.info(f"Top {limit} core products for {lob}: {top_products}")
        return top_products
    
    def get_top_accessory_categories(self, lob: str, limit: int = 8) -> List[str]:
        """Get top accessory categories by average attach rate"""
        lob_data = self.get_lob_data(lob)
        
        if len(lob_data) == 0:
            return []
        
        # Group by category and calculate average attach rate
        category_stats = lob_data.groupby('accessory_category').agg({
            'attach_rate': 'mean',
            'purchase_frequency': 'sum'
        }).sort_values('attach_rate', ascending=False)
        
        top_categories = category_stats.head(limit).index.tolist()
        
        self.logger.info(f"Top {limit} accessory categories for {lob}: {top_categories}")
        return top_categories
    
    def get_cohort_matrix(self, lob: str, core_products: List[str], 
                         categories: List[str]) -> pd.DataFrame:
        """Get attach rate matrix for core products vs categories"""
        lob_data = self.get_lob_data(lob)
        
        # Create pivot table
        matrix = lob_data.pivot_table(
            index='accessory_category',
            columns='core_product',
            values='attach_rate',
            aggfunc='mean',
            fill_value=0
        )
        
        # Filter to requested products and categories
        available_products = [p for p in core_products if p in matrix.columns]
        available_categories = [c for c in categories if c in matrix.index]
        
        if available_products and available_categories:
            matrix = matrix.loc[available_categories, available_products]
        
        self.logger.info(f"Created cohort matrix: {matrix.shape}")
        return matrix
    
    def get_frequency_matrix(self, lob: str, core_products: List[str], 
                           categories: List[str]) -> pd.DataFrame:
        """Get purchase frequency matrix for core products vs categories"""
        lob_data = self.get_lob_data(lob)
        
        # Create pivot table
        matrix = lob_data.pivot_table(
            index='accessory_category',
            columns='core_product',
            values='purchase_frequency',
            aggfunc='sum',
            fill_value=0
        )
        
        # Filter to requested products and categories
        available_products = [p for p in core_products if p in matrix.columns]
        available_categories = [c for c in categories if c in matrix.index]
        
        if available_products and available_categories:
            matrix = matrix.loc[available_categories, available_products]
        
        return matrix
    
    def get_top_cohort_pairs(self, lob: str, limit: int = 8) -> List[Dict[str, Any]]:
        """Get top cohort pairs by attach rate"""
        lob_data = self.get_lob_data(lob)
        
        if len(lob_data) == 0:
            return []
        
        # Get top pairs by attach rate
        top_pairs = lob_data.nlargest(limit, 'attach_rate')
        
        pairs = []
        for _, row in top_pairs.iterrows():
            pairs.append({
                'core_product': row['core_product'],
                'accessory_category': row['accessory_category'],
                'accessory_product': row.get('accessory_product', ''),
                'attach_rate': row['attach_rate'],
                'purchase_frequency': row['purchase_frequency']
            })
        
        self.logger.info(f"Retrieved top {limit} cohort pairs")
        return pairs
    
    def get_lob_summary_stats(self, lob: str) -> Dict[str, Any]:
        """Get summary statistics for a LOB"""
        lob_data = self.get_lob_data(lob)
        
        if len(lob_data) == 0:
            return {
                'total_records': 0,
                'unique_core_products': 0,
                'unique_categories': 0,
                'avg_attach_rate': 0.0,
                'high_attach_count': 0
            }
        
        stats = {
            'total_records': len(lob_data),
            'unique_core_products': lob_data['core_product'].nunique(),
            'unique_categories': lob_data['accessory_category'].nunique(),
            'avg_attach_rate': lob_data['attach_rate'].mean(),
            'high_attach_count': len(lob_data[lob_data['attach_rate'] > 0.15])
        }
        
        self.logger.info(f"Generated summary stats for {lob}")
        return stats