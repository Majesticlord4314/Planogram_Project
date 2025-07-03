#!/usr/bin/env python3
"""
Robust Cohort Data Cleaner - Much stricter cross-contamination removal
"""

import pandas as pd
from pathlib import Path

def clean_ipad_robust():
    """Robust iPad cohort cleaning"""
    
    data_path = Path("data/raw/cohorts")
    backup_file = data_path / "backup_original" / "ipad_planogram_cohorts.csv"
    output_file = data_path / "ipad_planogram_cohorts.csv"
    
    print("🧹 ROBUST iPad cohort cleaning...")
    
    df = pd.read_csv(backup_file)
    print(f"Original entries: {len(df)}")
    
    # Keep these categories completely (but with strict filtering)
    keep_categories = {'Apple Pencil', 'Keyboard', 'Cable', 'Charger/Adapter', 'Screen Protector'}
    
    # Strict filtering keywords - BLOCK anything with these terms
    strict_block_keywords = [
        'iphone', 'airpods', 'watch band', 'strap', 'macbook', 'mac mini', 'imac',
        'laptop', 'mouse', 'trackpad', 'jewelry', 'jewellery', 'diamond', 'apple tv'
    ]
    
    # For iPad cases - only keep if it explicitly mentions iPad
    ipad_case_keywords = ['ipad', 'tablet']
    
    # For Other category - very selective
    valuable_other_keywords = [
        'cleaning spray', 'screen cleaner', 'airtag', 'power bank', 'ipad',
        'tablet', 'pencil tip', 'stylus', 'stand'
    ]
    
    filtered_rows = []
    removed_iphone_cases = 0
    
    for _, row in df.iterrows():
        category = row['accessory_category']
        product = row['accessory_product'].lower()
        
        # STRICT BLOCK - remove anything with blocked keywords
        if any(block_word in product for block_word in strict_block_keywords):
            if 'iphone' in product:
                removed_iphone_cases += 1
            continue
        
        # Handle Case category with strict iPad-only filtering
        if category == 'Case':
            # Only keep if it explicitly mentions iPad/tablet
            if any(ipad_word in product for ipad_word in ipad_case_keywords):
                filtered_rows.append(row)
            # Otherwise skip (this removes iPhone cases, etc.)
            continue
        
        # Keep other valid categories
        elif category in keep_categories:
            filtered_rows.append(row)
        
        # For Other category - very strict filtering
        elif category == 'Other':
            if any(valuable in product for valuable in valuable_other_keywords):
                filtered_rows.append(row)
    
    cleaned_df = pd.DataFrame(filtered_rows)
    cleaned_df = cleaned_df.sort_values('attach_rate', ascending=False)
    
    print(f"Cleaned entries: {len(cleaned_df)}")
    print(f"Removed: {len(df) - len(cleaned_df)} entries")
    print(f"iPhone cases removed: {removed_iphone_cases}")
    
    # Show category breakdown
    print(f"\nCategory breakdown:")
    for category, count in cleaned_df['accessory_category'].value_counts().items():
        print(f"  {category}: {count}")
    
    cleaned_df.to_csv(output_file, index=False)
    print(f"✅ Saved robust iPad cohorts to: {output_file}")

def clean_mac_robust():
    """Robust Mac cohort cleaning"""
    
    data_path = Path("data/raw/cohorts")
    backup_file = data_path / "backup_original" / "mac_planogram_cohorts.csv"
    output_file = data_path / "mac_planogram_cohorts.csv"
    
    print(f"\n🧹 ROBUST Mac cohort cleaning...")
    
    df = pd.read_csv(backup_file)
    print(f"Original entries: {len(df)}")
    
    # Keep these categories completely (but with strict filtering)
    keep_categories = {'Keyboard', 'Mouse/Trackpad', 'Cable', 'Charger/Adapter'}
    
    # Strict filtering keywords - BLOCK anything with these terms
    strict_block_keywords = [
        'iphone', 'ipad', 'airpods', 'watch band', 'strap', 'jewelry', 'jewellery', 
        'diamond', 'apple tv', 'ear tips', 'pencil'
    ]
    
    # For Mac cases - only keep if it explicitly mentions Mac/laptop
    mac_case_keywords = ['macbook', 'mac mini', 'imac', 'laptop', 'notebook']
    
    # For Other category - selective but keep valuable Mac accessories
    valuable_other_keywords = [
        'hub', 'privacy filter', 'surge protector', 'display', 'organizer', 'organiser',
        'cleaning spray', 'screen cleaner', 'macbook', 'laptop', 'stand', 'dock',
        'power bank', 'airtag'
    ]
    
    filtered_rows = []
    removed_iphone_cases = 0
    
    for _, row in df.iterrows():
        category = row['accessory_category']
        product = row['accessory_product'].lower()
        
        # STRICT BLOCK - remove anything with blocked keywords
        if any(block_word in product for block_word in strict_block_keywords):
            if 'iphone' in product:
                removed_iphone_cases += 1
            continue
        
        # Handle Case category with strict Mac-only filtering
        if category == 'Case':
            # Only keep if it explicitly mentions Mac/laptop
            if any(mac_word in product for mac_word in mac_case_keywords):
                filtered_rows.append(row)
            # Otherwise skip (this removes iPhone cases, etc.)
            continue
        
        # Keep other valid categories
        elif category in keep_categories:
            filtered_rows.append(row)
        
        # For Other category - strict filtering
        elif category == 'Other':
            if any(valuable in product for valuable in valuable_other_keywords):
                filtered_rows.append(row)
    
    cleaned_df = pd.DataFrame(filtered_rows)
    cleaned_df = cleaned_df.sort_values('attach_rate', ascending=False)
    
    print(f"Cleaned entries: {len(cleaned_df)}")
    print(f"Removed: {len(df) - len(cleaned_df)} entries")
    print(f"iPhone cases removed: {removed_iphone_cases}")
    
    # Show category breakdown
    print(f"\nCategory breakdown:")
    for category, count in cleaned_df['accessory_category'].value_counts().items():
        print(f"  {category}: {count}")
    
    cleaned_df.to_csv(output_file, index=False)
    print(f"✅ Saved robust Mac cohorts to: {output_file}")

def clean_watch_robust():
    """Robust Watch cohort cleaning - Watch bands and charging only"""
    
    data_path = Path("data/raw/cohorts")
    backup_file = data_path / "backup_original" / "watch_planogram_cohorts.csv"
    output_file = data_path / "watch_planogram_cohorts.csv"
    
    print(f"\n🧹 ROBUST Watch cohort cleaning...")
    
    df = pd.read_csv(backup_file)
    print(f"Original entries: {len(df)}")
    
    # Keep these categories completely
    keep_categories = {'Watch Band', 'Charger/Adapter'}
    
    # Strict filtering keywords - BLOCK anything with these terms
    strict_block_keywords = [
        'iphone', 'ipad', 'airpods', 'macbook', 'mac mini', 'imac', 'laptop',
        'pencil', 'keyboard', 'mouse', 'hub', 'jewelry', 'jewellery', 'diamond',
        'apple tv', 'ear tips', 'earpods'
    ]
    
    # For cables - only keep watch-relevant charging cables
    watch_cable_keywords = ['magnetic', 'watch', 'usb-c', 'lightning']
    
    # For Other category - very selective watch accessories
    valuable_other_keywords = [
        'watch', 'cleaning spray', 'screen cleaner', 'airtag', 'magnetic',
        'charging dock', 'stand'
    ]
    
    # For cases - only watch cases
    watch_case_keywords = ['watch', 'apple watch']
    
    filtered_rows = []
    removed_non_watch = 0
    
    for _, row in df.iterrows():
        category = row['accessory_category']
        product = row['accessory_product'].lower()
        
        # STRICT BLOCK - remove anything with blocked keywords
        if any(block_word in product for block_word in strict_block_keywords):
            removed_non_watch += 1
            continue
        
        # Keep Watch Band and Charger/Adapter categories
        if category in keep_categories:
            filtered_rows.append(row)
        
        # Handle Cable category - only watch-relevant cables
        elif category == 'Cable':
            if any(watch_word in product for watch_word in watch_cable_keywords):
                # But make sure it's not an iPhone/iPad cable
                if not any(block in product for block in ['iphone', 'ipad', 'macbook']):
                    filtered_rows.append(row)
        
        # Handle Case category - only watch cases
        elif category == 'Case':
            if any(watch_word in product for watch_word in watch_case_keywords):
                filtered_rows.append(row)
        
        # For Other category - very strict watch-only filtering
        elif category == 'Other':
            if any(valuable in product for valuable in valuable_other_keywords):
                # Extra check - make sure it doesn't contain non-watch terms
                if not any(non_watch in product for non_watch in ['iphone', 'ipad', 'macbook', 'airpods']):
                    filtered_rows.append(row)
    
    cleaned_df = pd.DataFrame(filtered_rows)
    cleaned_df = cleaned_df.sort_values('attach_rate', ascending=False)
    
    print(f"Cleaned entries: {len(cleaned_df)}")
    print(f"Removed: {len(df) - len(cleaned_df)} entries")
    print(f"Non-watch items removed: {removed_non_watch}")
    
    # Show category breakdown
    print(f"\nCategory breakdown:")
    for category, count in cleaned_df['accessory_category'].value_counts().items():
        print(f"  {category}: {count}")
    
    cleaned_df.to_csv(output_file, index=False)
    print(f"✅ Saved robust Watch cohorts to: {output_file}")

def main():
    """Run robust cleaning for all problematic LOBs"""
    print("🔧 ROBUST COHORT CLEANING - Removing ALL cross-contamination")
    
    clean_ipad_robust()
    clean_mac_robust() 
    clean_watch_robust()
    
    print(f"\n✅ Robust cleaning complete! All iPhone cases and cross-contamination removed.")

if __name__ == "__main__":
    main()
