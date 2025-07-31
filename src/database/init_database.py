#!/usr/bin/env python3
"""
Database Initialization Script
Sets up the store database and populates it with initial data.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.database.store_database import StoreDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Initialize database and populate with CSV data"""
    try:
        # Initialize database
        db_path = project_root / "data" / "store_data.db"
        csv_path = project_root / "data" / "raw" / "store_templates" / "Plannogram compiled_16052025.backup.csv"
        
        logger.info("Initializing store database...")
        db = StoreDatabase(str(db_path))
        
        # Check if CSV file exists
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return False
        
        # Populate database from CSV
        logger.info(f"Populating database from {csv_path}")
        db.populate_from_csv(str(csv_path))
        
        # Print statistics
        stats = db.get_store_statistics()
        logger.info("Database initialization completed!")
        logger.info(f"Statistics: {stats}")
        
        # Test with a sample query
        stores = db.get_all_stores()
        logger.info(f"Total stores loaded: {len(stores)}")
        
        if stores:
            sample_store = stores[0]
            wall_counts = db.get_wall_counts_by_store(sample_store['store_name'])
            logger.info(f"Sample store '{sample_store['store_name']}' wall counts: {wall_counts}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)