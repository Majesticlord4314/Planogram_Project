#!/usr/bin/env python3
"""
Cohort Data Cleaner
Removes logically inconsistent cross-category purchases from cohort data files.
"""

import pandas as pd
import os
import shutil
from pathlib import Path
from typing import Dict, List, Set

class CohortDataCleaner:
    """Clean cohort data by removing illogical cross-category accessories"""
    
    def __init__(self, data_path: str = "data/raw/cohorts"):
        self.data_path = Path(data_path)
        self.backup_path = self.data_path / "backup_original"
        
        # Define valid accessory categories for each LOB
        self.valid_categories = {
            'Watch': {
                'categories': {'Watch Band', 'Charger/Adapter', 'Cable', 'Case', 'Other'},
                'keywords': {
                    'allow': ['watch', 'band', 'strap', 'charger', 'adapter', 'cable', 'usb', 'power', 
                             'cleaning', 'cleaner', 'spray', 'airtag', 'magnetic', 'power bank'],
                    'block': ['airpods', 'pencil', 'ipad', 'macbook', 'keyboard', 'mouse', 'hub', 
                             'ear tips', 'case for iphone', 'screen protector']
                }
            },
            'AirPods': {
                'categories': {'Cable', 'Charger/Adapter', 'Case', 'Other'},
                'keywords': {
                    'allow': ['airpods', 'ear tips', 'earbuds', 'audio', 'cable', 'charger', 'adapter',
                             'usb', 'power', 'cleaning', 'cleaner', 'spray', 'airtag', 'magnetic', 'power bank'],
                    'block': ['pencil', 'watch band', 'strap', 'keyboard', 'mouse', 'hub', 'ipad case',
                             'macbook', 'screen protector', 'case for iphone']
                }
            },
            'iPad': {
                'categories': {'Apple Pencil', 'Cable', 'Charger/Adapter', 'Case', 'Keyboard', 'Other'},
                'keywords': {
                    'allow': ['ipad', 'pencil', 'keyboard', 'case', 'stand', 'cable', 'charger', 
                             'adapter', 'usb', 'power', 'cleaning', 'cleaner', 'spray', 'airtag',
                             'magnetic', 'power bank', 'screen protector'],
                    'block': ['airpods', 'ear tips', 'watch band', 'strap', 'mouse', 'macbook',
                             'case for iphone']
                }
            },
            'Mac': {
                'categories': {'Keyboard', 'Mouse/Trackpad', 'Cable', 'Charger/Adapter', 'Case', 'Other'},
                'keywords': {
                    'allow': ['mac', 'macbook', 'keyboard', 'mouse', 'trackpad', 'hub', 'adapter',
                             'cable', 'charger', 'usb', 'power', 'cleaning', 'cleaner', 'spray',
                             'case', 'bag', 'privacy filter', 'display', 'surge', 'airtag',
                             'magnetic', 'power bank'],
                    'block': ['airpods', 'ear tips', 'pencil', 'ipad case', 'case for iphone',
                             'screen protector']
                }
            },
            'iPhone': {
                'categories': {'Cable', 'Charger/Adapter', 'Case', 'Screen Protector', 'Other'},
                'keywords': {
                    'allow': ['iphone', 'case', 'screen protector', 'cable', 'charger', 'adapter',
                             'usb', 'power', 'cleaning', 'cleaner', 'spray', 'airtag', 'magnetic',
                             'power bank', 'watch band'],  # Allow watch bands for iPhone (ecosystem)
                    'block': ['airpods', 'ear tips', 'pencil', 'keyboard', 'mouse', 'hub',
                             'macbook', 'ipad case']
                }
            }
        }
    
    def backup_original_files(self):
        """Create backup of original cohort files"""
        print("Creating backup of original cohort files...")
        
        if self.backup_path.exists():
            shutil.rmtree(self.backup_path)
        self.backup_path.mkdir(exist_ok=True)
        
        cohort_files = list(self.data_path.glob("*_cohorts.csv")) + \
                      list(self.data_path.glob("*_planogram_cohorts.csv")) + \
                      list(self.data_path.glob("bundle_recommendations.csv")) + \
                      list(self.data_path.glob("planogram_cohorts_master.csv"))
        
        for file in cohort_files:
            if file.is_file():
                shutil.copy2(file, self.backup_path / file.name)
                print(f"  Backed up: {file.name}")
    
    def is_valid_accessory(self, lob: str, category: str, product_name: str) -> bool:
        """Check if an accessory is valid for the given LOB"""
        if lob not in self.valid_categories:
            return True  # Keep unknown LOBs as-is
        
        rules = self.valid_categories[lob]
        product_lower = product_name.lower()
        category_lower = category.lower()
        
        # Check category validity
        if category not in rules['categories']:
            # Allow some flexibility for generic categories
            if category.lower() in ['other', 'cable', 'charger/adapter']:
                pass  # Continue to keyword check
            else:
                return False
        
        # Check blocked keywords
        for blocked_word in rules['keywords']['block']:
            if blocked_word.lower() in product_lower:
                return False
        
        # If it's a generic category, check for allowed keywords
        if category.lower() in ['other', 'cable', 'charger/adapter']:
            has_allowed_keyword = any(
                allowed_word.lower() in product_lower 
                for allowed_word in rules['keywords']['allow']
            )
            if not has_allowed_keyword:
                # For generic categories, require at least one allowed keyword
                # unless it's a very generic item
                generic_items = ['usb-c', 'lightning', 'power adapter', 'cable', 'charger']
                if not any(generic in product_lower for generic in generic_items):
                    return False
        
        return True
    
    def clean_cohort_file(self, file_path: Path) -> int:
        """Clean a single cohort file and return number of rows removed"""
        print(f"\nCleaning {file_path.name}...")
        
        try:
            df = pd.read_csv(file_path)
            original_count = len(df)
            
            if 'lob' not in df.columns or 'accessory_category' not in df.columns or 'accessory_product' not in df.columns:
                print(f"  Skipping {file_path.name} - missing required columns")
                return 0
            
            # Filter rows based on LOB-accessory logic
            valid_rows = []
            removed_count = 0
            
            for _, row in df.iterrows():
                lob = row['lob']
                category = row['accessory_category']
                product = row['accessory_product']
                
                if self.is_valid_accessory(lob, category, product):
                    valid_rows.append(row)
                else:
                    removed_count += 1
                    if removed_count <= 5:  # Show first 5 removals
                        print(f"  Removing: {lob} → {category}: {product[:50]}...")
            
            if removed_count > 5:
                print(f"  ... and {removed_count - 5} more removals")
            
            # Create cleaned dataframe
            if valid_rows:
                cleaned_df = pd.DataFrame(valid_rows)
                cleaned_df.to_csv(file_path, index=False)
                print(f"  Cleaned: {original_count} → {len(cleaned_df)} rows ({removed_count} removed)")
            else:
                print(f"  Warning: All rows removed from {file_path.name}")
            
            return removed_count
            
        except Exception as e:
            print(f"  Error cleaning {file_path.name}: {e}")
            return 0
    
    def clean_bundle_recommendations(self):
        """Clean bundle recommendations file"""
        bundle_file = self.data_path / "bundle_recommendations.csv"
        if not bundle_file.exists():
            print("Bundle recommendations file not found, skipping...")
            return
        
        print(f"\nCleaning bundle recommendations...")
        
        try:
            df = pd.read_csv(bundle_file)
            original_count = len(df)
            
            # For bundle recommendations, we'll be more lenient since bundles
            # can include cross-category items that make sense together
            # But we'll still remove obvious errors like AirPods + Apple Pencil
            
            valid_rows = []
            removed_count = 0
            
            for _, row in df.iterrows():
                # Check if bundle makes logical sense
                bundle_items = []
                lob = row.get('lob', '')
                
                # Extract bundle items from different possible column formats
                if 'accessories' in row and pd.notna(row['accessories']):
                    bundle_items = str(row['accessories']).split(' + ')
                else:
                    for col in ['accessory_1', 'accessory_2', 'accessory_3']:
                        if col in row and pd.notna(row[col]):
                            bundle_items.append(str(row[col]))
                
                # Check for obvious inconsistencies
                bundle_text = ' '.join(bundle_items).lower()
                is_valid = True
                
                if lob == 'AirPods' and ('pencil' in bundle_text or 'watch band' in bundle_text):
                    is_valid = False
                elif lob == 'Watch' and ('pencil' in bundle_text or 'airpods' in bundle_text):
                    is_valid = False
                elif lob == 'Mac' and ('watch band' in bundle_text or 'airpods' in bundle_text):
                    is_valid = False
                
                if is_valid:
                    valid_rows.append(row)
                else:
                    removed_count += 1
                    if removed_count <= 3:
                        print(f"  Removing bundle: {lob} → {bundle_items}")
            
            if valid_rows:
                cleaned_df = pd.DataFrame(valid_rows)
                cleaned_df.to_csv(bundle_file, index=False)
                print(f"  Cleaned bundles: {original_count} → {len(cleaned_df)} rows ({removed_count} removed)")
            
        except Exception as e:
            print(f"  Error cleaning bundle recommendations: {e}")
    
    def generate_cleaning_report(self, total_removed: int):
        """Generate a summary report of the cleaning process"""
        report_path = self.data_path / "cleaning_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("Cohort Data Cleaning Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total inconsistent entries removed: {total_removed}\n\n")
            
            f.write("Cleaning Rules Applied:\n")
            f.write("-" * 25 + "\n")
            for lob, rules in self.valid_categories.items():
                f.write(f"\n{lob}:\n")
                f.write(f"  Valid categories: {', '.join(rules['categories'])}\n")
                f.write(f"  Blocked keywords: {', '.join(rules['keywords']['block'][:5])}...\n")
            
            f.write(f"\nOriginal files backed up to: {self.backup_path}\n")
            f.write(f"Cleaned files saved in place.\n")
        
        print(f"\nCleaning report saved to: {report_path}")
    
    def clean_all_cohort_files(self):
        """Clean all cohort files"""
        print("Starting cohort data cleaning process...")
        
        # Backup original files
        self.backup_original_files()
        
        # Find all cohort files
        cohort_files = [
            "watch_planogram_cohorts.csv",
            "airpods_planogram_cohorts.csv", 
            "ipad_planogram_cohorts.csv",
            "mac_planogram_cohorts.csv",
            "iphone_planogram_cohorts.csv",
            "planogram_cohorts_master.csv"
        ]
        
        total_removed = 0
        
        # Clean individual cohort files
        for filename in cohort_files:
            file_path = self.data_path / filename
            if file_path.exists():
                removed = self.clean_cohort_file(file_path)
                total_removed += removed
            else:
                print(f"File not found: {filename}")
        
        # Clean bundle recommendations
        self.clean_bundle_recommendations()
        
        # Generate report
        self.generate_cleaning_report(total_removed)
        
        print(f"\n✅ Cleaning complete! {total_removed} inconsistent entries removed.")
        print(f"Original files backed up to: {self.backup_path}")

def main():
    """Main function to run the cleaner"""
    cleaner = CohortDataCleaner()
    cleaner.clean_all_cohort_files()

if __name__ == "__main__":
    main()
