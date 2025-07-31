#!/usr/bin/env python3
"""
Test script for store database functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.database.store_database import StoreDatabase

def test_database():
    """Test database functionality"""
    db_path = project_root / "data" / "store_data.db"
    db = StoreDatabase(str(db_path))
    
    print("=== Database Statistics ===")
    stats = db.get_store_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== All Stores ===")
    stores = db.get_all_stores()
    for i, store in enumerate(stores[:5]):  # Show first 5 stores
        print(f"{i+1}. {store['store_name']} - {store['city']} ({store['total_walls']} walls)")
    
    print(f"\n... and {len(stores) - 5} more stores")
    
    print("\n=== Sample Store Wall Analysis ===")
    if stores:
        sample_store = stores[0]
        wall_counts = db.get_wall_counts_by_store(sample_store['store_name'])
        print(f"Store: {sample_store['store_name']}")
        print(f"Wall counts: {wall_counts}")
    
    print("\n=== Test Specific Store ===")
    # Test with a known store name
    test_store_name = "IMAGINE- UB CITY BENGALURU"
    store_info = db.get_store_by_name(test_store_name)
    if store_info:
        print(f"Found store: {store_info}")
        wall_counts = db.get_wall_counts_by_store(test_store_name)
        print(f"Wall counts: {wall_counts}")
    else:
        print(f"Store '{test_store_name}' not found")

if __name__ == "__main__":
    test_database()