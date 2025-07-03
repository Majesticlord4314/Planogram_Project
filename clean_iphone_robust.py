#!/usr/bin/env python3
"""
Robust iPhone Cohort Cleaner - Remove watch straps and other cross-contamination
"""

import pandas as pd
from pathlib import Path

def clean_iphone_robust():
    """Robust iPhone cohort cleaning"""
    
    data_path = Path("data/raw/cohorts")
    backup_file = data_path / "backup_original" / "iphone_planogram_cohorts.csv"
    output_file = data_path / "iphone_planogram_cohorts.csv"
    
    print("🧹 ROBUST iPhone cohort cleaning...")
    
    df = pd.read_csv(backup_file)
    print(f"Original entries: {len(df)}")
    
    # Keep these categories completely (but with strict filtering)
    keep_categories = {'Case', 'Screen Protector', 'Cable', 'Charger/Adapter'}
    
    # Strict filtering keywords - BLOCK anything with these terms
    strict_block_keywords = [
        'watch band', 'watch strap', 'strap', 'band', 'airpods', 'ear tips', 'earpods',
        'pencil', 'macbook', 'mac mini', 'imac', 'laptop', 'ipad', 'keyboard', 'mouse',
        'trackpad', 'hub', 'jewelry', 'jewellery', 'diamond', 'apple tv'
    ]
    
    # For iPhone cases - only keep if it explicitly mentions iPhone
    iphone_case_keywords = ['iphone']
    
    # For Other category - very selective iPhone accessories only
    valuable_other_keywords = [
        'cleaning spray', 'screen cleaner', 'airtag', 'power bank', 'iphone',
        'phone', 'magnetic', 'magsafe', 'wireless charging', 'car mount',
        'phone holder', 'grip', 'ring'
    ]
    
    # Special exception: Allow watch bands for iPhone (ecosystem connection)
    # But be very selective about it
    ecosystem_watch_keywords = ['apple watch', 'watch band', 'watch strap']
    
    filtered_rows = []
    removed_watch_bands = 0
    removed_airpods = 0
    removed_pencils = 0
    removed_other = 0
    
    for _, row in df.iterrows():
        category = row['accessory_category']
        product = row['accessory_product'].lower()
        
        # Special handling for watch bands - keep some for iPhone (ecosystem)
        if any(watch_term in product for watch_term in ['watch band', 'watch strap', 'strap', 'band']):
            # Only keep if it's clearly an Apple Watch band and attach rate is reasonable
            if any(apple_watch in product for apple_watch in ['apple watch', 'watch band', 'magnetic']) and row['attach_rate'] > 0.001:
                filtered_rows.append(row)  # Keep for ecosystem
            else:
                removed_watch_bands += 1
            continue
        
        # STRICT BLOCK for obvious non-iPhone items
        if 'airpods' in product or 'ear tips' in product or 'earpods' in product:
            removed_airpods += 1
            continue
        
        if 'pencil' in product:
            removed_pencils += 1
            continue
        
        if any(block_word in product for block_word in ['macbook', 'ipad', 'mac mini', 'imac', 'laptop', 'keyboard', 'mouse', 'hub']):
            removed_other += 1
            continue
        
        # Handle Case category with strict iPhone-only filtering
        if category == 'Case':
            # Only keep if it explicitly mentions iPhone
            if any(iphone_word in product for iphone_word in iphone_case_keywords):
                filtered_rows.append(row)
            else:
                removed_other += 1
            continue
        
        # Handle Screen Protector - keep all (should be iPhone-specific)
        elif category == 'Screen Protector':
            filtered_rows.append(row)
        
        # Keep other valid categories (Cable, Charger/Adapter)
        elif category in keep_categories:
            filtered_rows.append(row)
        
        # For Other category - strict iPhone-only filtering
        elif category == 'Other':
            if any(valuable in product for valuable in valuable_other_keywords):
                # Extra check - make sure it doesn't contain non-iPhone terms
                if not any(non_iphone in product for non_iphone in ['ipad', 'macbook', 'watch']):
                    filtered_rows.append(row)
                else:
                    removed_other += 1
            else:
                removed_other += 1
    
    cleaned_df = pd.DataFrame(filtered_rows)
    cleaned_df = cleaned_df.sort_values('attach_rate', ascending=False)
    
    print(f"Cleaned entries: {len(cleaned_df)}")
    print(f"Removed: {len(df) - len(cleaned_df)} entries")
    print(f"  - Watch bands/straps removed: {removed_watch_bands}")
    print(f"  - AirPods accessories removed: {removed_airpods}")
    print(f"  - Apple Pencils removed: {removed_pencils}")
    print(f"  - Other cross-contamination removed: {removed_other}")
    
    # Show category breakdown
    print(f"\nCategory breakdown:")
    for category, count in cleaned_df['accessory_category'].value_counts().items():
        print(f"  {category}: {count}")
    
    cleaned_df.to_csv(output_file, index=False)
    print(f"✅ Saved robust iPhone cohorts to: {output_file}")
    
    # Show top 10
    print(f"\n🏆 Top 10 iPhone accessories:")
    for _, row in cleaned_df.head(10).iterrows():
        print(f"  {row['attach_rate']:.3f} - {row['accessory_category']}: {row['accessory_product'][:50]}...")

def main():
    """Run robust iPhone cleaning"""
    clean_iphone_robust()

if __name__ == "__main__":
    main()
