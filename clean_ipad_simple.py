#!/usr/bin/env python3
"""
Simple iPad Cohort Cleaner - Automated approach
"""

import pandas as pd
from pathlib import Path

def clean_ipad_cohorts():
    """Clean iPad cohorts with clear automated rules"""
    
    data_path = Path("data/raw/cohorts")
    backup_file = data_path / "backup_original" / "ipad_planogram_cohorts.csv"
    output_file = data_path / "ipad_planogram_cohorts.csv"
    
    print("🧹 Cleaning iPad cohort data...")
    
    # Load original data
    df = pd.read_csv(backup_file)
    print(f"Original entries: {len(df)}")
    
    # Keep these categories completely
    keep_categories = {'Apple Pencil', 'Case', 'Keyboard', 'Cable', 'Charger/Adapter', 'Screen Protector'}
    
    # For "Other" category, keep items with these keywords
    valuable_other_keywords = [
        'cleaning spray', 'screen cleaner', 'stand', 'holder', 'mount',
        'airtag', 'power bank', 'hub', 'adapter', 'dock', 'grip',
        'screen protector', 'film', 'protector', 'ipad', 'tablet',
        'stylus', 'pen', 'tip', 'magnetic', 'folio'
    ]
    
    # Remove "Other" items with these keywords
    garbage_keywords = [
        'airpods', 'ear tips', 'earpods', 'watch band', 'strap',
        'jewelry', 'jewellery', 'diamond', 'apple tv', 'tv 4k',
        'iphone case', 'macbook', 'mac mini', 'imac', 'laptop',
        'keyboard standalone', 'mouse', 'trackpad'
    ]
    
    # Filter data
    filtered_rows = []
    
    for _, row in df.iterrows():
        category = row['accessory_category']
        product = row['accessory_product'].lower()
        
        # Keep all non-Other categories in our list
        if category in keep_categories:
            filtered_rows.append(row)
        
        # For Other category, apply keyword filtering
        elif category == 'Other':
            # Remove if contains garbage keywords
            if any(garbage in product for garbage in garbage_keywords):
                continue
            
            # Keep if contains valuable keywords
            if any(valuable in product for valuable in valuable_other_keywords):
                filtered_rows.append(row)
            
            # Also keep some generic iPad-related items
            elif any(ipad_term in product for ipad_term in ['ipad', 'tablet', 'usb-c', 'lightning', 'magnetic']):
                filtered_rows.append(row)
    
    # Create cleaned dataframe
    cleaned_df = pd.DataFrame(filtered_rows)
    cleaned_df = cleaned_df.sort_values('attach_rate', ascending=False)
    
    print(f"Cleaned entries: {len(cleaned_df)}")
    print(f"Removed: {len(df) - len(cleaned_df)} entries")
    
    # Show category breakdown
    print(f"\nCategory breakdown:")
    for category, count in cleaned_df['accessory_category'].value_counts().items():
        print(f"  {category}: {count}")
    
    # Save cleaned data
    cleaned_df.to_csv(output_file, index=False)
    print(f"\n✅ Saved cleaned iPad cohorts to: {output_file}")
    
    # Show top 10
    print(f"\n🏆 Top 10 iPad accessories:")
    for _, row in cleaned_df.head(10).iterrows():
        print(f"  {row['attach_rate']:.3f} - {row['accessory_category']}: {row['accessory_product'][:50]}...")

if __name__ == "__main__":
    clean_ipad_cohorts()
