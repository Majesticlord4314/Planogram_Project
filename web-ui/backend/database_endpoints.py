#!/usr/bin/env python3
"""
Database-powered API endpoints for the planogram system
"""

import sys
import logging
import re
from pathlib import Path
from flask import jsonify, request
from functools import wraps
import time
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.database.store_database import StoreDatabase

logger = logging.getLogger(__name__)

# Initialize database
db_path = project_root / "data" / "store_data.db"
store_db = StoreDatabase(str(db_path))

# Simple in-memory cache
cache = {}
CACHE_TIMEOUT = 300  # 5 minutes

def cached(timeout=CACHE_TIMEOUT):
    """Simple caching decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check if cached result exists and is not expired
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < timeout:
                    logger.debug(f"Cache hit for {cache_key}")
                    return result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            logger.debug(f"Cache miss for {cache_key}")
            return result
        return decorated_function
    return decorator

def categorize_product_enhanced(product_str, product_type=''):
    """Enhanced product categorization based on business logic and frequency analysis"""
    if pd.isna(product_str):
        return 'Miscellaneous'
        
    product_lower = str(product_str).lower()
    
    # Check Watch Accessories FIRST (to avoid conflicts with other patterns)
    if any(re.search(pattern, product_lower) for pattern in [
        r'watch.*band', r'watch.*strap', r'apple.*watch.*band', 
        r'apple.*watch.*strap', r'watch.*accessories', r'watch.*glass',
        r'watch.*case', r'watch.*bumper', r'watch.*tg', r'watch.*protector',
        r'watch.*charger', r'\bband(?!.*phone)', r'\bstrap', r'bands',
        # Watch-specific screen protectors and accessories
        r'watch.*screen', r'pulse.*watch', r'gripp.*watch'
    ]):
        return 'Watch Accessories'
    
    # 1. iPhone Accessories (47.9% - Most common) - includes cases, covers, screen protectors, TG
    elif any(re.search(pattern, product_lower) for pattern in [
        r'iphone.*case', r'phone.*case', r'case.*iphone', r'back.*case',
        r'iphone.*cover', r'cover.*iphone', r'phone.*cover',
        r'iphone.*tg', r'phone.*tg', r'iphone.*glass', r'phone.*glass',
        r'iphone.*protector', r'phone.*protector', r'lens.*protector',
        r'silicon.*case', r'leather.*case', r'clear.*case', r'matt.*case',
        r'^case(?!.*ipad|.*mac)', r'^cover(?!.*ipad)', r'^tg(?!.*ipad)',
        r'tempered.*glass(?!.*ipad)', r'screen.*protector(?!.*ipad)',
        r'camera.*lens', r'phone.*accessories',
        # Screen protectors and TG for iPhone
        r'iphone.*screen', r'phone.*screen', r'mobile.*screen'
    ]):
        return 'iPhone Accessories'
    
    # 2. Power & Cables (21.5% - Second most common)
    elif any(re.search(pattern, product_lower) for pattern in [
        r'adapter', r'adaptors', r'cable', r'cables', r'charger', r'charging',
        r'power.*bank', r'powerbank', r'wireless.*charger', r'car.*charger', 
        r'wall.*charger', r'power.*adapter', r'apple.*power', r'magsafe',
        r'lightning.*cable', r'usb.*cable', r'type.*c.*cable', r'hub(?!.*mac)',
        r'converter', r'surge.*protector', r'tsf', r'car.*mount.*charger'
    ]):
        return 'Power & Cables'
    
    # 3. Audio Accessories (19.0%)
    elif any(re.search(pattern, product_lower) for pattern in [
        r'airpod.*case', r'airpods.*case', r'speaker', r'speakers', 
        r'headphone', r'headphones', r'earphone', r'earphones', r'earpods',
        r'audio', r'marshall', r'beats', r'earbuds', r'headset', 
        r'bluetooth.*speaker', r'bt.*speaker', r'gravastar', r'jbl', r'bose'
    ]):
        return 'Audio Accessories'
    
    # 4. iPad Accessories (17.8%) - includes cases, covers, screen protectors, TG, keyboards
    elif any(re.search(pattern, product_lower) for pattern in [
        r'ipad.*case', r'case.*ipad', r'ipad.*cover', r'cover.*ipad',
        r'ipad.*tg', r'ipad.*glass', r'ipad.*protector', r'ipad.*folio',
        r'ipad.*accessories', r'ipad.*keyboard', r'keyboard.*folio',
        # Screen protectors and TG specifically for iPad
        r'ipad.*screen', r'ipad.*tempered'
    ]):
        return 'iPad Accessories'
    
    # 5. Mac Accessories (17.6%)
    elif any(re.search(pattern, product_lower) for pattern in [
        r'mac.*sleeve', r'macbook.*sleeve', r'laptop.*sleeve', r'sleeve',
        r'mac.*bag', r'macbook.*bag', r'laptop.*bag', r'bagpack', r'backpack',
        r'magic.*keyboard', r'magic.*mouse', r'apple.*pencil', r'pencil.*tip',
        r'mac.*hub', r'mac.*adapter', r'mac.*stand', r'privacy.*filter',
        r'organizer', r'organiser', r'essential.*kit', r'gadget.*organizer',
        r'mac.*acc', r'apple.*acc(?!.*phone|.*iphone)', r'trackpad',
        r'hard.*shell', r'hardshell'
    ]):
        return 'Mac Accessories'
    

    
    # 7. Apple Core Products (for HomePod, Apple TV, etc.)
    elif any(re.search(pattern, product_lower) for pattern in [
        r'\bhomepod\b', r'apple\s+tv', r'apple.*tv', r'airtag', r'airtags'
    ]):
        return 'Apple Core Products'
    
    # Everything else goes to Miscellaneous
    return 'Miscellaneous'

def register_database_endpoints(app):
    """Register database-powered endpoints with Flask app"""
    
    @app.route('/api/database/status', methods=['GET'])
    def get_database_status():
        """Get database status and statistics"""
        try:
            stats = store_db.get_store_statistics()
            return jsonify({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"Database status error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/database/refresh', methods=['POST'])
    def refresh_database():
        """Refresh database from CSV file"""
        try:
            csv_path = project_root / "data" / "raw" / "store_templates" / "Plannogram compiled_16052025.backup.csv"
            
            if not csv_path.exists():
                return jsonify({
                    'success': False, 
                    'error': f'CSV file not found: {csv_path}'
                }), 404
            
            # Clear cache
            cache.clear()
            
            # Refresh database
            store_db.refresh_data(str(csv_path))
            
            # Get updated statistics
            stats = store_db.get_store_statistics()
            
            return jsonify({
                'success': True,
                'message': 'Database refreshed successfully',
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Database refresh error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/stores', methods=['GET'])
    @cached(timeout=600)  # Cache for 10 minutes
    def get_all_stores():
        """Get all stores from database"""
        try:
            stores = store_db.get_all_stores()
            
            # Format for frontend
            formatted_stores = []
            for store in stores:
                formatted_stores.append({
                    'store_name': store['store_name'],
                    'location': store['location'],
                    'city': store['city'],
                    'cm': store['cm'],
                    'total_walls': store['total_walls']
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'stores': formatted_stores,
                    'total_stores': len(formatted_stores)
                }
            })
            
        except Exception as e:
            logger.error(f"Get stores error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/stores/<store_name>/walls', methods=['GET'])
    @cached(timeout=300)
    def get_store_walls(store_name):
        """Get wall information for specific store"""
        try:
            # Decode URL-encoded store name
            from urllib.parse import unquote
            store_name = unquote(store_name)
            
            # Get store info
            store_info = store_db.get_store_by_name(store_name)
            if not store_info:
                return jsonify({
                    'success': False,
                    'error': f'Store not found: {store_name}'
                }), 404
            
            # Get wall counts
            wall_counts = store_db.get_wall_counts_by_store(store_name)
            
            return jsonify({
                'success': True,
                'data': {
                    'store_info': store_info,
                    'wall_counts': wall_counts
                }
            })
            
        except Exception as e:
            logger.error(f"Get store walls error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/stores/<store_name>/analysis', methods=['GET'])
    @cached(timeout=300)
    def get_store_analysis_db(store_name):
        """Get wall analysis from database"""
        try:
            from urllib.parse import unquote
            store_name = unquote(store_name)
            
            # Get store info
            store_info = store_db.get_store_by_name(store_name)
            if not store_info:
                return jsonify({
                    'success': False,
                    'error': f'Store not found: {store_name}'
                }), 404
            
            # Get wall counts by category
            wall_counts = store_db.get_wall_counts_by_store(store_name)
            
            # Format response similar to original endpoint
            response_data = {
                'store_name': store_name,
                'location': store_info.get('location', ''),
                'city': store_info.get('city', ''),
                'cm': store_info.get('cm', ''),
                'total_walls': wall_counts.get('total', 0),
                'wall_details': {}
            }
            
            # Add wall category details
            for category, count in wall_counts.items():
                if category != 'total':
                    response_data['wall_details'][category] = {
                        'wall_count': count,
                        'walls': [],  # Could be populated with actual wall identifiers
                        'total_capacity': 0,  # Could be calculated from products
                        'products': [],
                        'product_details': []
                    }
            
            return jsonify({
                'success': True,
                'data': response_data
            })
            
        except Exception as e:
            logger.error(f"Get store analysis error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/stores/<store_name>/categories', methods=['GET'])
    @cached(timeout=300)
    def get_store_categories(store_name):
        """Get wall categories for store"""
        try:
            from urllib.parse import unquote
            store_name = unquote(store_name)
            
            wall_counts = store_db.get_wall_counts_by_store(store_name)
            
            if not wall_counts:
                return jsonify({
                    'success': False,
                    'error': f'Store not found: {store_name}'
                }), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'store_name': store_name,
                    'categories': wall_counts
                }
            })
            
        except Exception as e:
            logger.error(f"Get store categories error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/stores/search', methods=['GET'])
    @cached(timeout=300)
    def search_stores():
        """Search stores by name or location"""
        try:
            query = request.args.get('q', '').lower()
            if not query:
                return jsonify({
                    'success': False,
                    'error': 'Search query required'
                }), 400
            
            all_stores = store_db.get_all_stores()
            
            # Filter stores based on query
            matching_stores = []
            for store in all_stores:
                if (query in store['store_name'].lower() or 
                    query in store.get('location', '').lower() or 
                    query in store.get('city', '').lower()):
                    matching_stores.append({
                        'store_name': store['store_name'],
                        'location': store['location'],
                        'city': store['city'],
                        'cm': store['cm'],
                        'total_walls': store['total_walls']
                    })
            
            return jsonify({
                'success': True,
                'data': {
                    'stores': matching_stores,
                    'total_results': len(matching_stores),
                    'query': query
                }
            })
            
        except Exception as e:
            logger.error(f"Search stores error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Override the original stores analysis endpoint to use database
    @app.route('/api/stores/analysis', methods=['GET'])
    @cached(timeout=600)
    def get_stores_analysis_db():
        """Return store names and metadata from database"""
        try:
            stores = store_db.get_all_stores()
            
            # Format in the same structure as the original endpoint
            store_selector = {}
            for store in stores:
                store_name = store['store_name']
                if store_name and store_name.strip():  # Skip empty store names
                    store_selector[store_name] = {
                        'store_name': store_name,
                        'city': store['city'] or '',
                        'location': store['location'] or '',
                        'cm': store['cm'] or '',
                        'total_walls': store['total_walls']
                    }
            
            return jsonify({
                'success': True,
                'data': {
                    'store_selector': store_selector
                }
            })
            
        except Exception as e:
            logger.error(f"Get stores analysis error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/stores/<store_name>/lob-details', methods=['GET'])
    @cached(timeout=300)
    def get_store_lob_details_db(store_name):
        """Get store LOB details from database"""
        try:
            from urllib.parse import unquote
            store_name = unquote(store_name)
            
            # Get store info
            store_info = store_db.get_store_by_name(store_name)
            if not store_info:
                return jsonify({
                    'success': False,
                    'error': f'Store not found: {store_name}'
                }), 404
            
            # Get wall counts by category
            wall_counts = store_db.get_wall_counts_by_store(store_name)
            
            # Format response similar to original endpoint
            wall_details = {}
            
            # Get detailed wall and product information
            with store_db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get walls with products for this store
                cursor.execute("""
                    SELECT w.wall_identifier, w.panel_name, w.panel_type,
                           p.brand, p.product, p.product_type,
                           p.shelf_count, p.per_shelf, p.shelf_capacity,
                           p.peg_count, p.per_peg, p.peg_capacity
                    FROM walls w
                    LEFT JOIN products p ON w.id = p.wall_id
                    WHERE w.store_id = ?
                    ORDER BY w.wall_identifier, p.id
                """, (store_info['id'],))
                
                results = cursor.fetchall()
                
                # Group by product category (not panel type)
                for row in results:
                    if row['product']:
                        # Use proper product categorization
                        category = categorize_product_enhanced(row['product'], row['product_type'] or '')
                        
                        if category and category != 'Miscellaneous':
                            if category not in wall_details:
                                wall_details[category] = {
                                    'wall_count': 0,
                                    'walls': [],
                                    'total_capacity': 0,
                                    'products': [],
                                    'product_details': []
                                }
                            
                            # Add wall if not already added
                            if row['wall_identifier'] not in wall_details[category]['walls']:
                                wall_details[category]['walls'].append(row['wall_identifier'])
                                wall_details[category]['wall_count'] = len(wall_details[category]['walls'])
                            
                            # Add product
                            product_info = {
                                'name': row['product'],
                                'brand': row['brand'] or '',
                                'type': row['product_type'] or '',
                                'capacity': (row['shelf_capacity'] or 0) + (row['peg_capacity'] or 0)
                            }
                            
                            wall_details[category]['products'].append(row['product'])
                            wall_details[category]['product_details'].append(product_info)
                            wall_details[category]['total_capacity'] += product_info['capacity']
            
            response_data = {
                'store_name': store_name,
                'location': store_info.get('location', ''),
                'city': store_info.get('city', ''),
                'cm': store_info.get('cm', ''),
                'total_walls': wall_counts.get('total', 0),
                'wall_details': wall_details
            }
            
            return jsonify({
                'success': True,
                'data': response_data
            })
            
        except Exception as e:
            logger.error(f"Get store LOB details error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/stores/<store_name>/recommendations', methods=['GET'])
    @cached(timeout=300)
    def get_store_recommendations_db(store_name):
        """Get store recommendations from database"""
        try:
            from urllib.parse import unquote
            store_name = unquote(store_name)
            
            # Get store info
            store_info = store_db.get_store_by_name(store_name)
            if not store_info:
                return jsonify({
                    'success': False,
                    'error': f'Store not found: {store_name}'
                }), 404
            
            # Get wall counts
            wall_counts = store_db.get_wall_counts_by_store(store_name)
            
            # Get actual product categories from the store
            with store_db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all products for this store and categorize them
                cursor.execute("""
                    SELECT p.product, p.product_type, w.wall_identifier
                    FROM products p
                    JOIN walls w ON p.wall_id = w.id
                    WHERE w.store_id = ?
                """, (store_info['id'],))
                
                results = cursor.fetchall()
                
                # Count walls by product category
                category_walls = {}
                wall_to_category = {}
                
                for row in results:
                    if row['product']:
                        category = categorize_product_enhanced(row['product'], row['product_type'] or '')
                        if category and category != 'Miscellaneous':
                            wall_id = row['wall_identifier']
                            
                            # Track which category each wall belongs to
                            if wall_id not in wall_to_category:
                                wall_to_category[wall_id] = category
                                if category not in category_walls:
                                    category_walls[category] = 0
                                category_walls[category] += 1
            
            total_walls = sum(category_walls.values())
            
            if total_walls == 0:
                return jsonify({
                    'success': True,
                    'data': {
                        'summary': 'No categorized walls found for this store.',
                        'optimization': {
                            'current_distribution': {},
                            'changes_needed': {}
                        }
                    }
                })
            
            # Current distribution
            current_distribution = category_walls
            
            # Balanced recommendation logic that sums to zero
            changes_needed = {}
            
            # Ideal distribution based on actual product analysis
            ideal_ratios = {
                'iPhone Accessories': 0.35,  # 35% - Most popular category (47.9% in analysis)
                'Power & Cables': 0.20,      # 20% - Essential items (21.5% in analysis)
                'Mac Accessories': 0.15,     # 15% - High-value accessories (17.6% in analysis)
                'Audio Accessories': 0.15,   # 15% - Popular items (19.0% in analysis)
                'iPad Accessories': 0.10,    # 10% - Growing category (17.8% in analysis)
                'Watch Accessories': 0.05    # 5% - Specialized (10.5% in analysis)
            }
            
            # Calculate changes needed (ensuring they sum to zero)
            total_changes = 0
            temp_changes = {}
            
            for category, ideal_ratio in ideal_ratios.items():
                current_count = current_distribution.get(category, 0)
                ideal_count = round(total_walls * ideal_ratio)
                difference = ideal_count - current_count
                
                if abs(difference) > 0:
                    temp_changes[category] = difference
                    total_changes += difference
            
            # Adjust to ensure sum equals zero
            if total_changes != 0 and temp_changes:
                # Find the category with the largest absolute change to adjust
                largest_category = max(temp_changes.keys(), key=lambda k: abs(temp_changes[k]))
                temp_changes[largest_category] -= total_changes
            
            # Convert to final format
            for category, difference in temp_changes.items():
                if difference != 0:
                    changes_needed[category] = {
                        'action': 'ADD' if difference > 0 else 'REMOVE',
                        'walls_affected': abs(difference),
                        'reason': f'Optimize {category} wall allocation for better product mix'
                    }
            
            # Generate summary
            if changes_needed:
                summary = f"Store has {total_walls} walls across {len(current_distribution)} categories. Optimization recommendations available."
            else:
                summary = f"Store has {total_walls} walls with optimal category distribution."
            
            return jsonify({
                'success': True,
                'data': {
                    'summary': summary,
                    'optimization': {
                        'current_distribution': current_distribution,
                        'changes_needed': changes_needed
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Get store recommendations error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

def clear_cache():
    """Clear the endpoint cache"""
    cache.clear()
    logger.info("API cache cleared")