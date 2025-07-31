#!/usr/bin/env python3
"""
Enhanced data migration script with validation
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.database.store_database import StoreDatabase
from src.database.data_validator import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_with_validation(csv_path: str, db_path: str, force: bool = False) -> bool:
    """Migrate data with validation"""
    try:
        # Validate CSV data first
        logger.info("Validating CSV data...")
        validator = DataValidator()
        report = validator.generate_validation_report(csv_path)
        
        # Print validation report
        print("=== Data Validation Report ===")
        print(f"Status: {report['validation_summary']['status']}")
        print(f"Total rows: {report['total_rows']}")
        print(f"Unique stores: {report['unique_stores']}")
        print(f"Errors: {report['validation_summary']['error_count']}")
        print(f"Warnings: {report['validation_summary']['warning_count']}")
        
        if report['errors']:
            print("\nErrors found:")
            for error in report['errors']:
                print(f"  - {error}")
        
        if report['warnings']:
            print("\nWarnings:")
            for warning in report['warnings'][:5]:  # Show first 5 warnings
                print(f"  - {warning}")
            if len(report['warnings']) > 5:
                print(f"  ... and {len(report['warnings']) - 5} more warnings")
        
        # Check if we should proceed
        if not report['is_valid'] and not force:
            logger.error("Validation failed. Use --force to proceed anyway.")
            return False
        
        if report['warnings'] and not force:
            response = input("\nWarnings found. Continue with migration? (y/N): ")
            if response.lower() != 'y':
                logger.info("Migration cancelled by user")
                return False
        
        # Proceed with migration
        logger.info("Starting database migration...")
        db = StoreDatabase(db_path)
        db.populate_from_csv(csv_path)
        
        # Verify migration
        stats = db.get_store_statistics()
        logger.info("Migration completed successfully!")
        logger.info(f"Final statistics: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate CSV data to store database")
    parser.add_argument("--csv", default=None, help="Path to CSV file")
    parser.add_argument("--db", default=None, help="Path to database file")
    parser.add_argument("--force", action="store_true", help="Force migration even with validation errors")
    
    args = parser.parse_args()
    
    # Set default paths
    csv_path = args.csv or str(project_root / "data" / "raw" / "store_templates" / "Plannogram compiled_16052025.backup.csv")
    db_path = args.db or str(project_root / "data" / "store_data.db")
    
    success = migrate_with_validation(csv_path, db_path, args.force)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()