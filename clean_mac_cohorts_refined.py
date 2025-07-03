#!/usr/bin/env python3
"""
Refined Mac Cohort Data Cleaner
Step-by-step cleaning with user control for "Other" category items
"""

import pandas as pd
from pathlib import Path
from typing import List, Set

class RefinedMacCohortCleaner:
    """Refined cleaner for Mac cohort data with selective Other category filtering"""
    
    def __init__(self, data_path: str = "data/raw/cohorts"):
        self.data_path = Path(data_path)
        
        # Define what to keep for Mac
        self.valid_categories = {
            'Case', 'Charger/Adapter', 'Mouse/Trackpad', 'Keyboard', 'Cable'
        }
        
        # Define valuable "Other" category items to keep
        self.valuable_other_keywords = {
            'hub', 'privacy filter', 'surge', 'display', 'organizer', 'organiser',
            'cleaning spray', 'screen cleaner', 'multiport', 'adapter',
            'power bank', 'airtag', 'bag', 'dock'
        }
        
        # Define garbage "Other" items to remove
        self.garbage_other_keywords = {
            'airpods', 'ear tips', 'earpods', 'pencil', 'watch band', 'strap',
            'jewelry', 'jewellery', 'diamond', 'apple tv', 'tv 4k',
            'iphone case', 'ipad case', 'screen protector'
        }
    
    def analyze_other_category(self, file_path: Path) -> tuple:
        """Analyze what's in the Other category"""
        df = pd.read_csv(file_path)
        
        # Get all "Other" category items
        other_items = df[df['accessory_category'] == 'Other']['accessory_product'].tolist()
        
        keep_items = []
        remove_items = []
        uncertain_items = []
        
        for item in other_items:
            item_lower = item.lower()
            
            # Check if it's definitely garbage
            if any(garbage in item_lower for garbage in self.garbage_other_keywords):
                remove_items.append(item)
            # Check if it's definitely valuable
            elif any(valuable in item_lower for valuable in self.valuable_other_keywords):
                keep_items.append(item)
            else:
                uncertain_items.append(item)
        
        return keep_items, remove_items, uncertain_items
    
    def clean_mac_cohorts_step_by_step(self):
        """Clean Mac cohorts with step-by-step user input"""
        # Use backup file for analysis
        backup_file = self.data_path / "backup_original" / "mac_planogram_cohorts.csv"
        current_file = self.data_path / "mac_planogram_cohorts.csv"
        
        if not backup_file.exists():
            print("❌ Backup file not found. Please run the main cleaner first.")
            return
        
        print("🔍 Analyzing Mac cohort data...")
        df = pd.read_csv(backup_file)
        
        print(f"Original Mac cohort entries: {len(df)}")
        print(f"Categories found: {df['accessory_category'].unique()}")
        
        # Step 1: Keep only specified categories + Other
        print(f"\n📋 Step 1: Keeping categories: {', '.join(self.valid_categories)} + Other")
        valid_df = df[df['accessory_category'].isin(self.valid_categories | {'Other'})]
        print(f"After category filtering: {len(valid_df)} entries")
        
        # Step 2: Analyze Other category
        print(f"\n🔍 Step 2: Analyzing 'Other' category items...")
        keep_items, remove_items, uncertain_items = self.analyze_other_category(backup_file)
        
        print(f"\n✅ Items to KEEP ({len(keep_items)}):")
        for item in keep_items[:10]:  # Show first 10
            print(f"  ✓ {item}")
        if len(keep_items) > 10:
            print(f"  ... and {len(keep_items) - 10} more")
        
        print(f"\n❌ Items to REMOVE ({len(remove_items)}):")
        for item in remove_items[:10]:  # Show first 10
            print(f"  ✗ {item}")
        if len(remove_items) > 10:
            print(f"  ... and {len(remove_items) - 10} more")
        
        print(f"\n❓ UNCERTAIN items ({len(uncertain_items)}):")
        for item in uncertain_items[:15]:  # Show first 15
            print(f"  ? {item}")
        if len(uncertain_items) > 15:
            print(f"  ... and {len(uncertain_items) - 15} more")
        
        # Step 3: User decision on uncertain items
        final_keep_items = set(keep_items)
        
        if uncertain_items:
            print(f"\n🤔 Please review uncertain items:")
            print("Type 'k' to keep, 'r' to remove, 'a' to keep all, 'd' to remove all:")
            
            for item in uncertain_items:
                while True:
                    choice = input(f"\n'{item[:80]}...' -> ").lower().strip()
                    if choice in ['k', 'keep']:
                        final_keep_items.add(item)
                        print("  ✓ Keeping")
                        break
                    elif choice in ['r', 'remove']:
                        print("  ✗ Removing")
                        break
                    elif choice in ['a', 'all']:
                        final_keep_items.update(uncertain_items)
                        print("  ✓ Keeping all remaining uncertain items")
                        break
                    elif choice in ['d', 'delete']:
                        print("  ✗ Removing all remaining uncertain items")
                        break
                    else:
                        print("  Please enter 'k', 'r', 'a', or 'd'")
                
                if choice in ['a', 'all', 'd', 'delete']:
                    break
        
        # Step 4: Apply filtering
        print(f"\n🧹 Step 4: Applying final filtering...")
        
        # Keep non-Other categories as-is
        non_other_df = valid_df[valid_df['accessory_category'] != 'Other']
        
        # Filter Other category based on decisions
        other_df = valid_df[valid_df['accessory_category'] == 'Other']
        kept_other_df = other_df[other_df['accessory_product'].isin(final_keep_items)]
        
        # Combine
        final_df = pd.concat([non_other_df, kept_other_df], ignore_index=True)
        
        # Sort by attach_rate descending
        final_df = final_df.sort_values('attach_rate', ascending=False)
        
        print(f"\n📊 Final Results:")
        print(f"  Original entries: {len(df)}")
        print(f"  Final entries: {len(final_df)}")
        print(f"  Removed: {len(df) - len(final_df)}")
        
        # Show category breakdown
        print(f"\n📈 Category breakdown:")
        for category, count in final_df['accessory_category'].value_counts().items():
            print(f"  {category}: {count}")
        
        # Save cleaned data
        final_df.to_csv(current_file, index=False)
        print(f"\n✅ Cleaned Mac cohort data saved to: {current_file}")
        
        # Show top items
        print(f"\n🏆 Top 10 Mac accessories by attach rate:")
        for _, row in final_df.head(10).iterrows():
            print(f"  {row['attach_rate']:.3f} - {row['accessory_category']}: {row['accessory_product'][:60]}...")

def main():
    """Main function"""
    cleaner = RefinedMacCohortCleaner()
    cleaner.clean_mac_cohorts_step_by_step()

if __name__ == "__main__":
    main()
