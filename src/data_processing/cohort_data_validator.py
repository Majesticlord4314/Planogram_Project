import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Tuple
from src.utils.logger import get_logger

class CohortDataValidator:
    """Validate and analyze cohort data for LOB-accessory associations"""
    
    def __init__(self):
        self.logger = get_logger()
        self.cohort_file = Path("data/raw/cohorts/planogram_cohorts_master.csv")
        self.validation_results = {}
        
        # Define expected accessory categories for each LOB
        self.expected_accessories = {
            'iPhone': {
                'Case', 'Screen Protector', 'Cable', 'Charger/Adapter', 
                'Wireless Charger', 'Car Mount', 'PopSocket', 'Power Bank',
                'Headphones', 'Cleaning Kit', 'Ring Holder', 'Wallet', 'Stand'
            },
            'iPad': {
                'Case', 'Screen Protector', 'Cable', 'Charger/Adapter',
                'Apple Pencil', 'Keyboard', 'Stand', 'Wireless Charger',
                'Cleaning Kit', 'Power Bank', 'Hub/Adapter'
            },
            'Mac': {
                'Case', 'Sleeve', 'Bag', 'Cable', 'Charger/Adapter',
                'Hub/Adapter', 'Stand', 'Keyboard', 'Mouse/Trackpad',
                'Cleaning Kit', 'Privacy Filter', 'Storage'
            },
            'Watch': {
                'Case', 'Screen Protector', 'Watch Band', 'Cable', 
                'Charger/Adapter', 'Wireless Charger', 'Cleaning Kit',
                'Stand', 'Power Bank'
            },
            'AirPods': {
                'Case', 'Cable', 'Charger/Adapter', 'Wireless Charger',
                'Cleaning Kit', 'Hooks/Holders', 'Power Bank'
            }
        }
        
        # Define expected core products for each LOB
        self.expected_core_products = {
            'iPhone': {
                'iPhone 16 Pro Max', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16',
                'iPhone 15 Pro Max', 'iPhone 15 Pro', 'iPhone 15 Plus', 'iPhone 15',
                'iPhone 14 Pro Max', 'iPhone 14 Pro', 'iPhone 14 Plus', 'iPhone 14',
                'iPhone 13 Pro Max', 'iPhone 13 Pro', 'iPhone 13 mini', 'iPhone 13',
                'iPhone 12 Pro Max', 'iPhone 12 Pro', 'iPhone 12 mini', 'iPhone 12'
            },
            'iPad': {
                'iPad Pro 12.9"', 'iPad Pro 11"', 'iPad Air', 'iPad',
                'iPad mini', 'iPad Pro M4 11"', 'iPad Pro M4 12.9"'
            },
            'Mac': {
                'MacBook Pro 16"', 'MacBook Pro 14"', 'MacBook Pro 13"',
                'MacBook Air 15"', 'MacBook Air 13"', 'iMac 24"',
                'Mac Studio', 'Mac Pro', 'Mac mini'
            },
            'Watch': {
                'Apple Watch Ultra 2', 'Apple Watch Series 9', 'Apple Watch SE',
                'Apple Watch Ultra', 'Apple Watch Series 8', 'Apple Watch Series 7'
            },
            'AirPods': {
                'AirPods Pro 2nd Gen', 'AirPods 3rd Gen', 'AirPods Max',
                'AirPods Pro', 'AirPods 2nd Gen'
            }
        }
    
    def validate_cohort_data(self) -> Dict:
        """Comprehensive validation of cohort data"""
        self.logger.info("Starting cohort data validation...")
        
        # Load data
        if not self.cohort_file.exists():
            self.logger.error(f"Cohort data file not found: {self.cohort_file}")
            return {'error': 'File not found'}
        
        df = pd.read_csv(self.cohort_file)
        
        # Run validation checks
        self.validation_results = {
            'data_overview': self._analyze_data_overview(df),
            'missing_accessories': self._check_missing_accessories(df),
            'missing_core_products': self._check_missing_core_products(df),
            'data_quality_issues': self._check_data_quality(df),
            'miscategorized_accessories': self._check_miscategorized_accessories(df),
            'recommendations': self._generate_recommendations()
        }
        
        return self.validation_results
    
    def _analyze_data_overview(self, df: pd.DataFrame) -> Dict:
        """Analyze overall data structure"""
        overview = {
            'total_records': len(df),
            'lob_distribution': df['lob'].value_counts().to_dict(),
            'categories_per_lob': {},
            'core_products_per_lob': {}
        }
        
        for lob in df['lob'].unique():
            lob_data = df[df['lob'] == lob]
            overview['categories_per_lob'][lob] = lob_data['accessory_category'].value_counts().to_dict()
            overview['core_products_per_lob'][lob] = lob_data['core_product'].value_counts().to_dict()
        
        return overview
    
    def _check_missing_accessories(self, df: pd.DataFrame) -> Dict:
        """Check for missing accessory categories per LOB"""
        missing_accessories = {}
        
        for lob in df['lob'].unique():
            lob_data = df[df['lob'] == lob]
            current_categories = set(lob_data['accessory_category'].unique())
            expected_categories = self.expected_accessories.get(lob, set())
            
            missing_accessories[lob] = {
                'current_categories': list(current_categories),
                'expected_categories': list(expected_categories),
                'missing_categories': list(expected_categories - current_categories),
                'unexpected_categories': list(current_categories - expected_categories)
            }
        
        return missing_accessories
    
    def _check_missing_core_products(self, df: pd.DataFrame) -> Dict:
        """Check for missing core products per LOB"""
        missing_core_products = {}
        
        for lob in df['lob'].unique():
            lob_data = df[df['lob'] == lob]
            current_products = set(lob_data['core_product'].unique())
            expected_products = self.expected_core_products.get(lob, set())
            
            missing_core_products[lob] = {
                'current_products': list(current_products),
                'expected_products': list(expected_products),
                'missing_products': list(expected_products - current_products),
                'unexpected_products': list(current_products - expected_products)
            }
        
        return missing_core_products
    
    def _check_data_quality(self, df: pd.DataFrame) -> Dict:
        """Check for data quality issues"""
        quality_issues = {
            'null_values': df.isnull().sum().to_dict(),
            'duplicate_records': len(df) - len(df.drop_duplicates()),
            'invalid_attach_rates': len(df[(df['attach_rate'] < 0) | (df['attach_rate'] > 1)]),
            'zero_frequency_records': len(df[df['purchase_frequency'] == 0]),
            'negative_facings': len(df[df['recommended_facings'] < 0])
        }
        
        return quality_issues
    
    def _check_miscategorized_accessories(self, df: pd.DataFrame) -> Dict:
        """Check for accessories that might be miscategorized"""
        miscategorized = {}
        
        # Check 'Other' category for items that should have specific categories
        other_data = df[df['accessory_category'] == 'Other']
        
        # Define patterns for reclassification
        reclassification_patterns = {
            'Screen Protector': ['screen protector', 'tempered glass', 'privacy screen'],
            'Cleaning Kit': ['cleaning', 'cloth', 'wipe', 'spray'],
            'Power Bank': ['power bank', 'battery pack', 'portable charger'],
            'Wireless Charger': ['wireless charger', 'magsafe', 'qi charger'],
            'Car Mount': ['car mount', 'car holder', 'dashboard'],
            'PopSocket': ['popsocket', 'grip', 'ring holder'],
            'Headphones': ['earpods', 'headphones', 'earphones'],
            'Ring Holder': ['ring holder', 'finger ring'],
            'Wallet': ['wallet', 'cardholder', 'folio']
        }
        
        for lob in df['lob'].unique():
            lob_other = other_data[other_data['lob'] == lob]
            lob_miscategorized = {}
            
            for new_category, patterns in reclassification_patterns.items():
                matching_products = []
                for _, row in lob_other.iterrows():
                    product_name = str(row['accessory_product']).lower()
                    if any(pattern in product_name for pattern in patterns):
                        matching_products.append({
                            'product': row['accessory_product'],
                            'core_product': row['core_product'],
                            'current_category': row['accessory_category'],
                            'suggested_category': new_category
                        })
                
                if matching_products:
                    lob_miscategorized[new_category] = matching_products
            
            if lob_miscategorized:
                miscategorized[lob] = lob_miscategorized
        
        return miscategorized
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check if we have missing accessories data
        if 'missing_accessories' in self.validation_results:
            for lob, missing_info in self.validation_results['missing_accessories'].items():
                if missing_info['missing_categories']:
                    recommendations.append(
                        f"Add missing accessory categories for {lob}: {missing_info['missing_categories']}"
                    )
        
        # Check for miscategorized items
        if 'miscategorized_accessories' in self.validation_results:
            for lob, miscategorized in self.validation_results['miscategorized_accessories'].items():
                for suggested_category, products in miscategorized.items():
                    recommendations.append(
                        f"Reclassify {len(products)} products in {lob} from 'Other' to '{suggested_category}'"
                    )
        
        # Data quality recommendations
        if 'data_quality_issues' in self.validation_results:
            quality_issues = self.validation_results['data_quality_issues']
            if quality_issues['duplicate_records'] > 0:
                recommendations.append(f"Remove {quality_issues['duplicate_records']} duplicate records")
            if quality_issues['invalid_attach_rates'] > 0:
                recommendations.append(f"Fix {quality_issues['invalid_attach_rates']} invalid attach rates")
        
        return recommendations
    
    def generate_validation_report(self) -> None:
        """Generate a detailed validation report"""
        if not self.validation_results:
            self.validate_cohort_data()
        
        report_path = Path("logs/cohort_validation_report.txt")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write("COHORT DATA VALIDATION REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Data Overview
            f.write("DATA OVERVIEW\n")
            f.write("-" * 20 + "\n")
            overview = self.validation_results['data_overview']
            f.write(f"Total Records: {overview['total_records']}\n")
            f.write(f"LOB Distribution: {overview['lob_distribution']}\n\n")
            
            # Missing Accessories
            f.write("MISSING ACCESSORIES BY LOB\n")
            f.write("-" * 30 + "\n")
            for lob, missing_info in self.validation_results['missing_accessories'].items():
                f.write(f"\n{lob}:\n")
                f.write(f"  Missing Categories: {missing_info['missing_categories']}\n")
                f.write(f"  Current Categories: {missing_info['current_categories']}\n")
            
            # Miscategorized Accessories
            f.write("\nMISCATEGORIZED ACCESSORIES\n")
            f.write("-" * 30 + "\n")
            for lob, miscategorized in self.validation_results['miscategorized_accessories'].items():
                f.write(f"\n{lob}:\n")
                for suggested_category, products in miscategorized.items():
                    f.write(f"  {suggested_category}: {len(products)} products\n")
            
            # Recommendations
            f.write("\nRECOMMENDATIONS\n")
            f.write("-" * 20 + "\n")
            for i, recommendation in enumerate(self.validation_results['recommendations'], 1):
                f.write(f"{i}. {recommendation}\n")
        
        self.logger.info(f"Validation report generated: {report_path}")
        print(f"Validation report saved to: {report_path}")

def main():
    """Run cohort data validation"""
    validator = CohortDataValidator()
    results = validator.validate_cohort_data()
    validator.generate_validation_report()
    
    # Print summary
    print("\n=== COHORT DATA VALIDATION SUMMARY ===")
    print(f"Total records: {results['data_overview']['total_records']}")
    print(f"LOBs analyzed: {list(results['data_overview']['lob_distribution'].keys())}")
    print(f"Issues found: {len(results['recommendations'])}")
    
    print("\n=== KEY ISSUES ===")
    for i, rec in enumerate(results['recommendations'][:5], 1):
        print(f"{i}. {rec}")
    
    if len(results['recommendations']) > 5:
        print(f"... and {len(results['recommendations']) - 5} more issues")

if __name__ == "__main__":
    main()
