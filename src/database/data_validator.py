#!/usr/bin/env python3
"""
Data validation utilities for store database
"""

import pandas as pd
import logging
from typing import Dict, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates CSV data before database import"""
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_csv_file(self, csv_path: str) -> Tuple[bool, List[str], List[str]]:
        """Validate CSV file structure and data quality"""
        self.validation_errors = []
        self.validation_warnings = []
        
        try:
            # Check if file exists
            if not Path(csv_path).exists():
                self.validation_errors.append(f"CSV file not found: {csv_path}")
                return False, self.validation_errors, self.validation_warnings
            
            # Load CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
            
            # Validate required columns
            self._validate_required_columns(df)
            
            # Validate data quality
            self._validate_data_quality(df)
            
            # Validate store data consistency
            self._validate_store_consistency(df)
            
            # Validate wall data
            self._validate_wall_data(df)
            
            # Check for duplicates
            self._check_duplicates(df)
            
            is_valid = len(self.validation_errors) == 0
            return is_valid, self.validation_errors, self.validation_warnings
            
        except Exception as e:
            self.validation_errors.append(f"Error reading CSV file: {e}")
            return False, self.validation_errors, self.validation_warnings
    
    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        """Check for required columns"""
        required_columns = [
            'Store name', 'LOCATION', 'CITY', 'CM', 'Wall', 
            'Panel Name', 'BRAND', 'Product'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.validation_errors.append(f"Missing required columns: {missing_columns}")
        
        # Check for empty required columns
        for col in required_columns:
            if col in df.columns:
                empty_count = df[col].isna().sum()
                if empty_count > 0:
                    self.validation_warnings.append(f"Column '{col}' has {empty_count} empty values")
    
    def _validate_data_quality(self, df: pd.DataFrame) -> None:
        """Validate data quality issues"""
        # Check for completely empty rows
        empty_rows = df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            self.validation_warnings.append(f"Found {empty_rows} completely empty rows")
        
        # Check for stores without names
        unnamed_stores = df['Store name'].isna().sum()
        if unnamed_stores > 0:
            self.validation_errors.append(f"Found {unnamed_stores} rows without store names")
        
        # Check for walls without identifiers
        if 'Wall' in df.columns:
            unnamed_walls = df['Wall'].isna().sum()
            if unnamed_walls > 0:
                self.validation_warnings.append(f"Found {unnamed_walls} rows without wall identifiers")
    
    def _validate_store_consistency(self, df: pd.DataFrame) -> None:
        """Validate store data consistency"""
        # Check for stores with inconsistent location/city data
        store_groups = df.groupby('Store name').agg({
            'LOCATION': 'nunique',
            'CITY': 'nunique',
            'CM': 'nunique'
        })
        
        inconsistent_stores = store_groups[
            (store_groups['LOCATION'] > 1) | 
            (store_groups['CITY'] > 1) | 
            (store_groups['CM'] > 1)
        ]
        
        if not inconsistent_stores.empty:
            self.validation_warnings.append(
                f"Found {len(inconsistent_stores)} stores with inconsistent location/city/CM data"
            )
    
    def _validate_wall_data(self, df: pd.DataFrame) -> None:
        """Validate wall-specific data"""
        if 'Wall' not in df.columns:
            return
        
        # Check for valid wall formats
        wall_patterns = [r'W\d+', r'WALL\s*\d+', r'^\d+$', r'GONDOLA\s*\d+']
        
        valid_walls = 0
        for _, row in df.iterrows():
            wall_str = str(row.get('Wall', ''))
            if any(pd.Series([wall_str]).str.contains(pattern, case=False, na=False).any() 
                   for pattern in wall_patterns):
                valid_walls += 1
        
        invalid_walls = len(df) - valid_walls
        if invalid_walls > 0:
            self.validation_warnings.append(f"Found {invalid_walls} rows with invalid wall formats")
    
    def _check_duplicates(self, df: pd.DataFrame) -> None:
        """Check for duplicate entries"""
        # Check for duplicate store-wall combinations
        if all(col in df.columns for col in ['Store name', 'Wall']):
            duplicates = df.duplicated(subset=['Store name', 'Wall']).sum()
            if duplicates > 0:
                self.validation_warnings.append(f"Found {duplicates} duplicate store-wall combinations")
    
    def generate_validation_report(self, csv_path: str) -> Dict:
        """Generate a comprehensive validation report"""
        is_valid, errors, warnings = self.validate_csv_file(csv_path)
        
        # Additional statistics
        df = pd.read_csv(csv_path)
        
        unique_stores = df['Store name'].nunique()
        unique_walls = df['Wall'].nunique() if 'Wall' in df.columns else 0
        
        return {
            'file_path': csv_path,
            'is_valid': is_valid,
            'total_rows': len(df),
            'unique_stores': unique_stores,
            'unique_walls': unique_walls,
            'errors': errors,
            'warnings': warnings,
            'validation_summary': {
                'error_count': len(errors),
                'warning_count': len(warnings),
                'status': 'PASS' if is_valid else 'FAIL'
            }
        }

def main():
    """Test data validation"""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.parent.absolute()
    csv_path = project_root / "data" / "raw" / "store_templates" / "Plannogram compiled_16052025.backup.csv"
    
    validator = DataValidator()
    report = validator.generate_validation_report(str(csv_path))
    
    print("=== Data Validation Report ===")
    print(f"File: {report['file_path']}")
    print(f"Status: {report['validation_summary']['status']}")
    print(f"Total rows: {report['total_rows']}")
    print(f"Unique stores: {report['unique_stores']}")
    print(f"Unique walls: {report['unique_walls']}")
    
    if report['errors']:
        print(f"\nErrors ({len(report['errors'])}):")
        for error in report['errors']:
            print(f"  - {error}")
    
    if report['warnings']:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for warning in report['warnings']:
            print(f"  - {warning}")
    
    if not report['errors'] and not report['warnings']:
        print("\nNo validation issues found!")

if __name__ == "__main__":
    main()