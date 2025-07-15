"""
Cohort Data Loader for Cohort-Based Planograms

This module handles loading and processing of corrected cohort data
for generating cohort-based planograms.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

class CohortDataLoader:
    """Load and process cohort data for planogram generation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cohort_file = Path("data/raw/cohorts/planogram_cohorts_corrected.csv")
        self._data = None
        
    def load_cohort_data(self) -> pd.DataFrame:
        """Load corrected cohort data"""
        if self._data is None:
            if not self.cohort_file.exists():
                raise FileNotFoundError(f"Cohort data file not found: {self.cohort_file}")
            
            self._data = pd.read_csv(self.cohort_file)
            self.logger.info(f"Loaded {len(self._data)} cohort records")
        
        return self._data
    
    def get_lob_data(self, lob: str) -> pd.DataFrame:
        """Get cohort data for specific LOB"""
        data = self.load_cohort_data()
        lob_data = data[data['lob'] == lob].copy()
        
        if len(lob_data) == 0:
            raise ValueError(f"No cohort data found for LOB: {lob}")
        
        self.logger.info(f"Retrieved {len(lob_data)} records for LOB: {lob}")
        return lob_data
    
    def get_top_core_products(self, lob: str, limit: int = 6) -> List[str]:
        """Get top core products by total accessory sales"""
        lob_data = self.get_lob_data(lob)
        
        core_product_sales = lob_data.groupby('core_product')['purchase_frequency'].sum()
        top_products = core_product_sales.nlargest(limit).index.tolist()
        
        self.logger.info(f"Top {limit} core products for {lob}: {top_products}")
        return top_products
    
    def get_top_accessory_categories(self, lob: str, limit: int = 10) -> List[str]:
        """Get top accessory categories by average attach rate"""
        lob_data = self.get_lob_data(lob)
        
        category_stats = lob_data.groupby('accessory_category').agg({
            'attach_rate': 'mean',
            'purchase_frequency': 'sum'
        }).sort_values('attach_rate', ascending=False)
        
        top_categories = category_stats.head(limit).index.tolist()
        
        self.logger.info(f"Top {limit} accessory categories for {lob}: {top_categories}")
        return top_categories
    
    def get_cohort_matrix(self, lob: str, core_products: List[str], 
                         categories: List[str]) -> pd.DataFrame:
        """Get cohort matrix for core products vs accessory categories"""
        lob_data = self.get_lob_data(lob)
        
        # Filter data for specified products and categories
        matrix_data = lob_data[
            (lob_data['core_product'].isin(core_products)) &
            (lob_data['accessory_category'].isin(categories))
        ]
        
        # Create pivot table
        matrix = matrix_data.pivot_table(
            values='attach_rate',
            index='accessory_category',
            columns='core_product',
            aggfunc='mean',
            fill_value=0
        )
        
        # Reorder columns and rows
        matrix = matrix.reindex(columns=core_products, fill_value=0)
        matrix = matrix.reindex(categories, fill_value=0)
        
        self.logger.info(f"Created cohort matrix: {matrix.shape}")
        return matrix
    
    def get_frequency_matrix(self, lob: str, core_products: List[str], 
                           categories: List[str]) -> pd.DataFrame:
        """Get frequency matrix for core products vs accessory categories"""
        lob_data = self.get_lob_data(lob)
        
        # Filter data for specified products and categories
        matrix_data = lob_data[
            (lob_data['core_product'].isin(core_products)) &
            (lob_data['accessory_category'].isin(categories))
        ]
        
        # Create pivot table
        matrix = matrix_data.pivot_table(
            values='purchase_frequency',
            index='accessory_category',
            columns='core_product',
            aggfunc='sum',
            fill_value=0
        )
        
        # Reorder columns and rows
        matrix = matrix.reindex(columns=core_products, fill_value=0)
        matrix = matrix.reindex(categories, fill_value=0)
        
        return matrix
    
    def get_top_cohort_pairs(self, lob: str, limit: int = 10) -> List[Dict]:
        """Get top cohort pairs by attach rate"""
        lob_data = self.get_lob_data(lob)
        
        top_pairs = lob_data.nlargest(limit, 'attach_rate')[
            ['core_product', 'accessory_category', 'accessory_product', 'attach_rate', 'purchase_frequency']
        ].to_dict('records')
        
        self.logger.info(f"Retrieved top {limit} cohort pairs")
        return top_pairs
    
    def get_lob_summary_stats(self, lob: str) -> Dict:
        """Get summary statistics for LOB"""
        lob_data = self.get_lob_data(lob)
        
        stats = {
            'total_records': len(lob_data),
            'unique_core_products': lob_data['core_product'].nunique(),
            'unique_categories': lob_data['accessory_category'].nunique(),
            'avg_attach_rate': lob_data['attach_rate'].mean(),
            'median_attach_rate': lob_data['attach_rate'].median(),
            'high_attach_count': len(lob_data[lob_data['attach_rate'] > 0.15]),
            'total_frequency': lob_data['purchase_frequency'].sum()
        }
        
        self.logger.info(f"Generated summary stats for {lob}")
        return stats
    
    def get_category_performance(self, lob: str) -> pd.DataFrame:
        """Get performance metrics for each accessory category"""
        lob_data = self.get_lob_data(lob)
        
        category_performance = lob_data.groupby('accessory_category').agg({
            'attach_rate': ['mean', 'median', 'std', 'count'],
            'purchase_frequency': ['sum', 'mean'],
            'recommended_facings': 'mean'
        }).round(3)
        
        # Flatten column names
        category_performance.columns = ['_'.join(col).strip() for col in category_performance.columns]
        
        # Sort by mean attach rate
        category_performance = category_performance.sort_values('attach_rate_mean', ascending=False)
        
        return category_performance
