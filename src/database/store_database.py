#!/usr/bin/env python3
"""
Store Database Manager
Handles SQLite database operations for store, wall, and product data.
"""

import sqlite3
import pandas as pd
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class StoreDatabase:
    """Database manager for store planogram data"""
    
    def __init__(self, db_path: str = "store_data.db"):
        """Initialize database connection"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.create_tables()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def create_tables(self) -> None:
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create stores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_name TEXT NOT NULL UNIQUE,
                    location TEXT,
                    city TEXT,
                    cm TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create walls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS walls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id INTEGER NOT NULL,
                    wall_identifier TEXT NOT NULL,
                    panel_name TEXT,
                    panel_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE CASCADE
                )
            """)
            
            # Create products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wall_id INTEGER NOT NULL,
                    brand TEXT,
                    brand_type TEXT,
                    product TEXT,
                    product_type TEXT,
                    shelf_count INTEGER DEFAULT 0,
                    per_shelf INTEGER DEFAULT 0,
                    shelf_capacity INTEGER DEFAULT 0,
                    peg_count INTEGER DEFAULT 0,
                    per_peg INTEGER DEFAULT 0,
                    peg_capacity INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (wall_id) REFERENCES walls (id) ON DELETE CASCADE
                )
            """)
            
            # Create wall categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wall_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    wall_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (store_id) REFERENCES stores (id) ON DELETE CASCADE,
                    UNIQUE(store_id, category)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stores_name ON stores (store_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_walls_store ON walls (store_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_walls_type ON walls (panel_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_wall ON products (wall_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_store ON wall_categories (store_id)")
            
            conn.commit()
            logger.info("Database tables created successfully")
    
    def normalize_store_name(self, name: str) -> str:
        """Normalize store name for consistent matching"""
        if pd.isna(name) or not name:
            return ""
        return re.sub(r'[^a-zA-Z0-9\s]', '', str(name)).strip()
    
    def extract_wall_number(self, wall_str: str) -> Optional[str]:
        """Extract wall identifier from wall string"""
        if pd.isna(wall_str) or not wall_str:
            return None
        
        wall_str = str(wall_str).strip().upper()
        
        # Handle various wall formats
        patterns = [
            r'(W\d+)',           # W1, W2, etc.
            r'(WALL\s*\d+)',     # WALL 1, WALL1, etc.
            r'^(\d+)$',          # Just numbers like 1, 2, etc.
            r'(GONDOLA\s*\d+)',  # GONDOLA 1, etc.
        ]
        
        for pattern in patterns:
            match = re.search(pattern, wall_str)
            if match:
                return match.group(1)
        
        return wall_str  # Return original if no pattern matches
    
    def determine_panel_type(self, panel_name: str) -> str:
        """Determine panel type from panel name"""
        if pd.isna(panel_name) or not panel_name:
            return "Unknown"
        
        panel_name = str(panel_name).upper()
        
        if any(keyword in panel_name for keyword in ['APPLE PANEL', 'PA']):
            return 'PA'
        elif any(keyword in panel_name for keyword in ['MIXED PANEL', 'PM']):
            return 'PM'
        elif any(keyword in panel_name for keyword in ['TPA PANEL', 'PT']):
            return 'PT'
        else:
            return 'Other'
    
    def populate_from_csv(self, csv_path: str) -> None:
        """Populate database from CSV file"""
        logger.info(f"Starting CSV import from {csv_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} rows from CSV")
            
            # Clear existing data
            self.clear_all_data()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Process each unique store
                stores_processed = set()
                
                for _, row in df.iterrows():
                    store_name = row.get('Store name', '')
                    if pd.isna(store_name) or not store_name or store_name in stores_processed:
                        continue
                    
                    # Insert store
                    store_id = self._insert_store(cursor, row)
                    if store_id:
                        stores_processed.add(store_name)
                        logger.debug(f"Processed store: {store_name}")
                
                # Process walls and products for each store
                for store_name in stores_processed:
                    store_rows = df[df['Store name'] == store_name]
                    store_id = self._get_store_id(cursor, store_name)
                    
                    if store_id:
                        self._process_store_walls(cursor, store_id, store_rows)
                        self._update_wall_categories(cursor, store_id)
                
                conn.commit()
                logger.info("CSV import completed successfully")
                
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            raise
    
    def _insert_store(self, cursor, row) -> Optional[int]:
        """Insert a store record"""
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO stores (store_name, location, city, cm, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                row.get('Store name', ''),
                row.get('LOCATION', ''),
                row.get('CITY', ''),
                row.get('CM', '')
            ))
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting store: {e}")
            return None
    
    def _get_store_id(self, cursor, store_name: str) -> Optional[int]:
        """Get store ID by name"""
        cursor.execute("SELECT id FROM stores WHERE store_name = ?", (store_name,))
        result = cursor.fetchone()
        return result['id'] if result else None
    
    def _process_store_walls(self, cursor, store_id: int, store_rows: pd.DataFrame) -> None:
        """Process walls and products for a store"""
        walls_processed = set()
        
        for _, row in store_rows.iterrows():
            wall_identifier = self.extract_wall_number(row.get('Wall', ''))
            if not wall_identifier or wall_identifier in walls_processed:
                continue
            
            # Insert wall
            panel_name = row.get('Panel Name', '')
            panel_type = self.determine_panel_type(panel_name)
            
            cursor.execute("""
                INSERT INTO walls (store_id, wall_identifier, panel_name, panel_type)
                VALUES (?, ?, ?, ?)
            """, (store_id, wall_identifier, panel_name, panel_type))
            
            wall_id = cursor.lastrowid
            walls_processed.add(wall_identifier)
            
            # Insert product for this wall
            self._insert_product(cursor, wall_id, row)
    
    def _insert_product(self, cursor, wall_id: int, row) -> None:
        """Insert a product record"""
        try:
            # Parse numeric values safely
            def safe_int(value, default=0):
                try:
                    if pd.isna(value) or value == '-':
                        return default
                    return int(float(value))
                except (ValueError, TypeError):
                    return default
            
            cursor.execute("""
                INSERT INTO products (
                    wall_id, brand, brand_type, product, product_type,
                    shelf_count, per_shelf, shelf_capacity,
                    peg_count, per_peg, peg_capacity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wall_id,
                row.get('BRAND', ''),
                row.get('BRAND Type', ''),
                row.get('Product', ''),
                row.get('Product Type', ''),
                safe_int(row.get('SHELF')),
                safe_int(row.get('Per shelf')),
                safe_int(row.get('Capacity')),
                safe_int(row.get('PEGS')),
                safe_int(row.get('Per peg')),
                safe_int(row.get('Capacity.1'))
            ))
        except Exception as e:
            logger.error(f"Error inserting product: {e}")
    
    def _update_wall_categories(self, cursor, store_id: int) -> None:
        """Update wall category counts for a store"""
        cursor.execute("""
            SELECT panel_type, COUNT(*) as count
            FROM walls
            WHERE store_id = ?
            GROUP BY panel_type
        """, (store_id,))
        
        categories = cursor.fetchall()
        
        for category in categories:
            cursor.execute("""
                INSERT OR REPLACE INTO wall_categories (store_id, category, wall_count, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (store_id, category['panel_type'], category['count']))
    
    def clear_all_data(self) -> None:
        """Clear all data from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM walls")
            cursor.execute("DELETE FROM wall_categories")
            cursor.execute("DELETE FROM stores")
            conn.commit()
            logger.info("All data cleared from database")
    
    def get_store_by_name(self, store_name: str) -> Optional[Dict]:
        """Get store information by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM stores WHERE store_name = ?
            """, (store_name,))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
    
    def get_wall_counts_by_store(self, store_name: str) -> Dict[str, int]:
        """Get wall counts by category for a store"""
        store = self.get_store_by_name(store_name)
        if not store:
            return {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, wall_count
                FROM wall_categories
                WHERE store_id = ?
            """, (store['id'],))
            
            results = cursor.fetchall()
            wall_counts = {row['category']: row['wall_count'] for row in results}
            
            # Add total count
            wall_counts['total'] = sum(wall_counts.values())
            
            return wall_counts
    
    def get_all_stores(self) -> List[Dict]:
        """Get all stores with their wall counts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, 
                       COALESCE(SUM(wc.wall_count), 0) as total_walls
                FROM stores s
                LEFT JOIN wall_categories wc ON s.id = wc.store_id
                GROUP BY s.id, s.store_name, s.location, s.city, s.cm
                ORDER BY s.store_name
            """)
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
    
    def get_store_statistics(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get counts
            cursor.execute("SELECT COUNT(*) as count FROM stores")
            store_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM walls")
            wall_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM products")
            product_count = cursor.fetchone()['count']
            
            # Get last update time
            cursor.execute("SELECT MAX(updated_at) as last_update FROM stores")
            last_update = cursor.fetchone()['last_update']
            
            return {
                'stores': store_count,
                'walls': wall_count,
                'products': product_count,
                'last_update': last_update,
                'database_path': str(self.db_path)
            }
    
    def refresh_data(self, csv_path: str) -> None:
        """Refresh database data from CSV file"""
        logger.info("Refreshing database data")
        self.populate_from_csv(csv_path)
        logger.info("Database refresh completed")