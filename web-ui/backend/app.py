#!/usr/bin/env python3
"""
Apple Store Planogram Optimization System
A streamlined Flask-based web service for optimizing Apple Store wall layouts.
"""

import os
import sys
import json
import logging
import re
import uuid
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import unquote
from enum import Enum

import pandas as pd
import numpy as np

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ---------------------------------------------------------------------------- #
#                                  Setup                                       #
# ---------------------------------------------------------------------------- #

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / "logs" / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'planogram-optimization-key'
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Import planogram services
from planogram_services.planogram_manager import get_planogram_manager

# Global storage for user wall configurations
user_wall_configs = {}

# Job management
class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Job:
    def __init__(self, job_id, job_type, parameters):
        self.job_id = job_id
        self.job_type = job_type
        self.parameters = parameters
        self.status = JobStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.completed_at = None
        
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

# Global job storage
jobs = {}

# ---------------------------------------------------------------------------- #
#                              Helper Functions                                #
# ---------------------------------------------------------------------------- #

def normalize_store_name(name):
    """Normalize store name for consistent matching - matches store reference format"""
    if pd.isna(name) or str(name).strip() == 'nan':
        return ''
    
    name = str(name).strip()
    # Remove extra spaces and normalize
    name = re.sub(r'\s+', ' ', name)
    # Convert to lowercase for matching (same as store reference)
    return name.lower()

def categorize_product(product_str):
    """Categorize a product based on its description"""
    if pd.isna(product_str):
        return 'Miscellaneous'
        
    product_lower = str(product_str).lower()
    
    # Skip actual devices (not accessories) - be more specific to avoid false positives
    device_patterns = [
        r'\biphones?\s*$',  # iPhones standalone
        r'\bairpods?\s*$',  # AirPods standalone  
        r'\bwatch\s*$',     # Watch standalone
        r'\bipad\s*$',      # iPad standalone
        r'\bmac\s*$',       # Mac standalone
        r'\bhomepod\b(?!\s*(case|cover|accessory))',  # HomePod (not accessories)
        r'\bapple\s+tv\b(?!\s*(case|cover|accessory))'  # Apple TV (not accessories)
    ]
    
    # Check for device patterns, but be more lenient
    for pattern in device_patterns:
        if re.search(pattern, product_lower):
            # Additional check: if it also mentions accessories, don't skip
            if not re.search(r'(case|cover|accessory|accessories|tg|glass|protector|keyboard|sleeve|bag|adapter|cable|charger)', product_lower):
                return None
    
    # iPhone Accessories (Cases & Covers)
    if any(re.search(pattern, product_lower) for pattern in [
        r'iphone.*case', r'phone.*case', r'case.*iphone', 
        r'iphone.*cover', r'cover.*iphone', r'phone.*cover',
        r'iphone.*tg', r'iphone.*glass', r'iphone.*protector',
        r'phone.*tg', r'phone.*glass', r'phone.*protector',
        r'silicon.*case', r'leather.*case', r'clear.*case', r'back.*case',
        r'^(case|cover|tg|tempered.*glass|screen.*protector)$',
        r'phone.*accessories', r'lens.*protector', r'camera.*lens'
    ]):
        return 'Cases & Covers'
    
    # iPad Accessories (including keyboards)
    elif any(re.search(pattern, product_lower) for pattern in [
        r'ipad.*case', r'case.*ipad', r'ipad.*cover', r'cover.*ipad',
        r'ipad.*tg', r'ipad.*glass', r'ipad.*protector', r'ipad.*folio',
        r'ipad.*accessories', r'ipad.*keyboard', r'ipad.*and.*keyboard',
        r'tekne.*ipad'
    ]):
        return 'iPad Accessories'
    
    # Watch Accessories
    elif any(re.search(pattern, product_lower) for pattern in [
        r'watch.*band', r'watch.*strap', r'apple.*watch.*band', 
        r'apple.*watch.*strap', r'watch.*accessories', r'watch.*glass',
        r'watch.*case', r'watch.*bumper', r'watch.*tg', r'watch.*protector',
        r'\bbands\b', r'\bstrap\b', r'bands.*case', r'ultrahuman.*ring',
        r'imoo.*watch', r'pulse.*watch'
    ]):
        return 'Watch Accessories'
    
    # Adapters & Cables (check this before Mac Accessories to catch adapter/charger kits)
    elif any(re.search(pattern, product_lower) for pattern in [
        r'adapter.*powerbank', r'powerbank.*adapter', r'adapter.*charger', r'charger.*adapter',
        r'adapter', r'cable', r'charger', r'power.*bank', 
        r'wireless.*charger', r'car.*charger', r'wall.*charger', 
        r'hub', r'converter', r'magsafe', r'lightning.*cable', 
        r'usb.*cable', r'type.*c.*cable', r'surge.*protector', r'power.*adapter',
        r'powerbank'
    ]):
        return 'Adapters & Cables'
    
    # Mac Accessories (including organizational items)
    elif any(re.search(pattern, product_lower) for pattern in [
        r'mac.*sleeve', r'macbook.*sleeve', r'mac.*bag', r'macbook.*bag',
        r'magic.*keyboard', r'magic.*mouse', r'apple.*pencil', r'pencil.*tip',
        r'mac.*hub', r'mac.*adapter', r'mac.*stand', r'privacy.*filter',
        r'laptop.*sleeve', r'laptop.*bag', r'organizer', r'organiser',
        r'essential.*kit', r'apple.*acc', r'bags.*and.*sleeve', r'sleeve.*and.*bag',
        r'tekne.*mac.*acc', r'tekne.*organiser', r'macbook.*sleeve.*and.*bags'
    ]):
        return 'Mac Accessories'
    
    # Audio Accessories (including Gripp AirPods cases)
    elif any(re.search(pattern, product_lower) for pattern in [
        r'airpod.*case', r'airpods.*case', r'speaker', r'headphone', 
        r'earphone', r'audio', r'marshall', r'beats', r'earbuds',
        r'headset', r'bluetooth.*speaker', r'gripp.*airpods'
    ]):
        return 'Audio Accessories'
    
    # Storage & Organization
    elif any(re.search(pattern, product_lower) for pattern in [
        r'popsocket', r'card.*holder', r'mobile.*holder', r'ring.*holder',
        r'car.*mount', r'phone.*mount', r'stand', r'mount',
        r'holder', r'storage', r'ssd.*drive', r'gaming.*mouse', r'grip',
        r'bagpack', r'bag', r'sandisk.*ssd'
    ]):
        return 'Storage & Organization'
    
    # Screen Protectors
    elif any(re.search(pattern, product_lower) for pattern in [
        r'privacy.*screen'
    ]):
        return 'Screen Protectors'
    
    return 'Miscellaneous'

def extract_wall_number(wall_str):
    """Extract wall number from wall string"""
    if pd.isna(wall_str):
        return None
    
    wall_str = str(wall_str).strip().upper()
    patterns = [
        r'W(\d+)',           # W1, W2, etc.
        r'WALL\s*(\d+)',     # WALL 1, WALL1, etc.
        r'^(\d+)$',          # Just numbers like 1, 2, etc.
    ]
    
    for pattern in patterns:
        match = re.search(pattern, wall_str)
        if match:
            return int(match.group(1))
    
    if 'GONDOLA' in wall_str:
        gondola_match = re.search(r'GONDOLA\s*(\d+)', wall_str)
        if gondola_match:
            return 100 + int(gondola_match.group(1))
    
    return None

# Global store reference cache
_store_reference_cache = None

def load_store_reference():
    """Load optimized store reference from JSON file"""
    global _store_reference_cache
    
    if _store_reference_cache is not None:
        return _store_reference_cache
    
    reference_path = project_root / 'data' / 'processed' / 'store_reference.json'
    
    if not reference_path.exists():
        logger.warning(f"Store reference not found at {reference_path}. Run create_store_reference.py first.")
        return {}
    
    try:
        with open(reference_path, 'r', encoding='utf-8') as f:
            _store_reference_cache = json.load(f)
        
        logger.info(f"Loaded store reference with {len(_store_reference_cache)} stores")
        return _store_reference_cache
        
    except Exception as e:
        logger.error(f"Error loading store reference: {e}")
        return {}

def build_store_master(csv_path):
    """Build store master data structure - now uses optimized JSON reference"""
    return load_store_reference()
    if not csv_path.exists():
        logger.error(f"Store template file not found: {csv_path}")
        return {}
    
    try:
        df = pd.read_csv(csv_path)
        df['Store name clean'] = df['Store name'].astype(str).apply(normalize_store_name)
        store_master = {}
        
        for store_clean in df['Store name clean'].unique():
            df_store = df[df['Store name clean'] == store_clean]
            if df_store.empty:
                continue
                
            store_name = df_store['Store name'].iloc[0]
            location = df_store['LOCATION'].iloc[0] if 'LOCATION' in df_store else ''
            city = df_store['CITY'].iloc[0] if 'CITY' in df_store else ''
            
            logger.info(f"Processing store: {store_name} (clean: {store_clean}) with {len(df_store)} rows")
            
            # Calculate total walls using wall number extraction
            if 'Wall' not in df_store.columns:
                logger.warning(f"No 'Wall' column found for store {store_name}")
                total_walls = 0
                unique_walls = []
            else:
                # Filter out empty/null wall values and extract numbers
                wall_values = df_store['Wall'].dropna()
                wall_values = wall_values[wall_values.str.strip() != '']
                wall_values_unique = wall_values.unique()
                
                # Extract wall numbers from non-empty wall values
                wall_numbers = []
                for wall_val in wall_values_unique:
                    wall_num = extract_wall_number(wall_val)
                    if wall_num is not None:
                        wall_numbers.append(wall_num)
                
                if wall_numbers:
                    unique_walls = sorted(list(set(wall_numbers)))
                    total_walls = len(unique_walls)
                else:
                    total_walls = 0
                    unique_walls = []
            
            wall_details = {}
            
            # Categorize products automatically and group by category
            products = df_store['Product'].dropna().unique()
            
            categories = {
                'Cases & Covers': [],
                'iPad Accessories': [],
                'Watch Accessories': [],
                'Audio Accessories': [],
                'Mac Accessories': [],
                'Adapters & Cables': [],
                'Storage & Organization': [],
                'Screen Protectors': [],
                'Miscellaneous': []
            }
            
            for product in products:
                category = categorize_product(product)
                if category and category in categories:
                    categories[category].append(product)
            
            # Only include product types that have actual products
            product_types = [cat for cat, prods in categories.items() if prods]
            
            if not product_types:
                product_types = ['Miscellaneous']
            
            # Process each product type
            for lob in product_types:
                if not lob:
                    continue
                
                # Get all rows that belong to this category (handle None returns properly)
                def belongs_to_lob(product):
                    category = categorize_product(product)
                    return category == lob
                
                lob_rows = df_store[df_store['Product'].apply(belongs_to_lob)]
                
                if lob_rows.empty:
                    continue
                
                # Get wall information
                walls = lob_rows['Wall'].dropna().unique().tolist() if 'Wall' in lob_rows.columns else []
                wall_count = len(walls)
                
                # Calculate total capacity from both shelf and peg capacity columns
                total_capacity = 0
                capacity_cols = ['Capacity', 'capacity', 'Capacity.1', 'capacity.1', 'Facings', 'facings', 'Total Qty', 'total_qty', 'Qty', 'qty', 'Quantity', 'quantity']
                
                # Debug capacity calculation
                logger.info(f"LOB: {lob}, Available columns: {list(lob_rows.columns)}")
                
                for col in capacity_cols:
                    if col in lob_rows.columns:
                        # Convert to numeric and handle strings/errors safely
                        numeric_values = pd.to_numeric(lob_rows[col], errors='coerce').fillna(0)
                        col_sum = float(numeric_values.sum())
                        if col_sum > 0:  # Only log if there's actual capacity
                            logger.info(f"LOB: {lob}, Column: {col}, Sum: {col_sum}")
                        total_capacity += col_sum
                
                # If no capacity found from standard columns, try to estimate from product count
                if total_capacity == 0:
                    # Estimate capacity as number of products * 2 (conservative estimate)
                    product_count = len(lob_rows)
                    total_capacity = max(1, product_count * 2)  # Minimum 1, usually 2 per product
                    logger.info(f"LOB: {lob}, No capacity data found, estimated from {product_count} products: {total_capacity}")
                else:
                    logger.info(f"LOB: {lob}, Total calculated capacity: {total_capacity}")
                
                # Ensure total_capacity is a valid number
                if pd.isna(total_capacity) or total_capacity != total_capacity:  # Check for NaN
                    total_capacity = 0
                
                # List all products with their facings/qty from both capacity columns
                product_list = []
                for _, prow in lob_rows.iterrows():
                    pname = prow['Product'] if pd.notnull(prow['Product']) else ''
                    pqty = 0
                    for col in capacity_cols:
                        if col in prow.index and pd.notnull(prow[col]):
                            # Convert to numeric safely
                            try:
                                numeric_val = pd.to_numeric(prow[col], errors='coerce')
                                if pd.notna(numeric_val):
                                    pqty += float(numeric_val)
                            except:
                                pass
                    if pname:
                        # Ensure pqty is a valid number and convert to int
                        if pd.isna(pqty) or pqty != pqty:  # Check for NaN
                            pqty = 0
                        pqty = int(max(0, pqty))  # Ensure non-negative integer
                        product_list.append({'name': pname, 'qty': pqty})
                
                if product_list or total_capacity > 0 or wall_count > 0:
                    wall_details[lob] = {
                        'walls': walls,
                        'wall_count': wall_count,
                        'total_capacity': total_capacity,
                        'products': [p['name'] for p in product_list],
                        'product_details': product_list
                    }
            
            store_master[store_clean] = {
                'store_name': store_name,
                'location': location,
                'city': city,
                'total_walls': total_walls,
                'wall_details': wall_details
            }
        
        return store_master
    except Exception as e:
        logger.error(f"Error building store master: {e}", exc_info=True)
        return {}

# ---------------------------------------------------------------------------- #
#                                  API Endpoints                               #
# ---------------------------------------------------------------------------- #

@app.route('/api/stores/<store_name>/lob-details', methods=['GET'])
def get_store_lob_details(store_name):
    """Return wall details for the selected store"""
    csv_path = project_root / 'data' / 'raw' / 'store_templates' / 'Plannogram compiled_16052025.backup.csv'
    if not csv_path.exists():
        logger.error(f"Store template file not found: {csv_path}")
        return jsonify({'success': False, 'error': 'Store template file not found'})
        
    try:
        store_master = build_store_master(csv_path)
        decoded_name = normalize_store_name(unquote(store_name))
        logger.info(f"Decoded name: {decoded_name}")
        
        if decoded_name not in store_master:
            logger.warning(f"No matching store '{store_name}' (decoded: {decoded_name}) in master data.")
            return jsonify({'success': True, 'data': {
                'location': '',
                'city': '',
                'total_walls': 0,
                'lob_breakdown': {},
                'capacity_summary': {},
                'wall_details': {},
                'diagnostics': f"No matching store '{store_name}' (decoded: {decoded_name}) in master data."
            }})
            
        store_data = store_master[decoded_name]
        wall_details = store_data['wall_details']
        total_walls = store_data.get('total_walls', 0)
        
        # Check if user has saved a custom wall configuration
        global user_wall_configs
        if decoded_name in user_wall_configs:
            user_config = user_wall_configs[decoded_name]
            logger.info(f"Using saved user configuration for {decoded_name}: {user_config}")
            
            # Update wall_details with user's configuration
            updated_wall_details = {}
            for lob, details in wall_details.items():
                updated_wall_details[lob] = {
                    **details,
                    'wall_count': user_config.get(lob, details['wall_count'])
                }
            wall_details = updated_wall_details
            total_walls = sum(details['wall_count'] for details in wall_details.values())
        
        # Handle capacity data - only use real values, no fallbacks
        capacity_summary = {}
        for lob in wall_details:
            capacity = wall_details[lob].get('total_capacity', 0)
            # Only use real capacity data, no fallback estimation
            capacity_summary[lob] = capacity if capacity > 0 else 0
            
        lob_breakdown = {}
        for lob in wall_details:
            products = wall_details[lob].get('products', [])
            if isinstance(products, list) and products:
                # Handle list of product objects
                if isinstance(products[0], dict):
                    product_names = [p.get('product', '') for p in products]
                else:
                    product_names = products
                display_products = product_names[:5]
                if len(product_names) > 5:
                    display_products.append('...')
                lob_breakdown[lob] = ', '.join(display_products)
            else:
                lob_breakdown[lob] = str(products) if products else 'No products'
        
        # Store default configuration if no user config exists
        try:
            planogram_mgr = get_planogram_manager(project_root)
            existing_config = planogram_mgr.get_final_wall_config(decoded_name)
            
            if not existing_config:
                # Store the default wall counts as the initial final configuration
                default_wall_counts = {lob: details['wall_count'] for lob, details in wall_details.items()}
                planogram_mgr.store_final_wall_config(decoded_name, default_wall_counts)
                logger.info(f"Stored default wall configuration for {decoded_name}")
        except Exception as e:
            logger.warning(f"Could not store default configuration: {e}")
            
        return jsonify({'success': True, 'data': {
            'location': store_data['location'],
            'city': store_data['city'],
            'total_walls': total_walls,
            'lob_breakdown': lob_breakdown,
            'capacity_summary': capacity_summary,
            'wall_details': wall_details,
            'diagnostics': None
        }})
            
    except Exception as e:
        logger.error(f"Error in get_store_lob_details: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stores/<store_name>/save-wall-config', methods=['POST'])
def save_wall_config(store_name):
    """Save user-edited wall counts for a store"""
    try:
        decoded_name = normalize_store_name(unquote(store_name))
        wall_config = request.get_json().get('wall_counts', {})
        logger.info(f"Received wall config for {store_name}: {wall_config}")
        
        # Store the configuration in the global dictionary (for API compatibility)
        global user_wall_configs
        user_wall_configs[decoded_name] = wall_config
        logger.info(f"Stored wall configuration for {decoded_name}: {wall_config}")
        
        # Also store as final configuration for planogram generation
        planogram_mgr = get_planogram_manager(project_root)
        final_stored = planogram_mgr.store_final_wall_config(decoded_name, wall_config)
        
        if final_stored:
            logger.info(f"Final wall configuration stored for planogram generation: {decoded_name}")
        
        return jsonify({
            'success': True, 
            'message': 'Wall configuration saved successfully.',
            'saved_config': wall_config,
            'final_config_stored': final_stored
        })
        
    except Exception as e:
        logger.error(f"Error saving wall config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stores/<store_name>/reset-wall-config', methods=['POST'])
def reset_wall_config(store_name):
    """Reset wall configuration to original store data"""
    try:
        decoded_name = normalize_store_name(unquote(store_name))
        logger.info(f"Resetting wall configuration for {store_name} to original data")

        # Clear from global dictionary
        global user_wall_configs
        if decoded_name in user_wall_configs:
            del user_wall_configs[decoded_name]
            logger.info(f"Cleared user wall config for {decoded_name}")

        # Clear from PlanogramManager storage
        planogram_mgr = get_planogram_manager(project_root)
        configs = planogram_mgr._load_wall_configs()
        if decoded_name in configs:
            del configs[decoded_name]
            # Save the updated configs back to file
            with open(planogram_mgr.storage_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(configs, f, indent=2, ensure_ascii=False)
            logger.info(f"Cleared final wall config for {decoded_name}")

        return jsonify({
            'success': True,
            'message': 'Wall configuration reset to original data successfully.'
        })

    except Exception as e:
        logger.error(f"Error resetting wall config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})



@app.route('/api/stores/<store_name>/recommendations', methods=['GET'])
def get_store_recommendations(store_name):
    """Return optimized wall recommendations for the selected store"""
    logger.info(f"=== Optimization request for store: {store_name} ===")
    
    csv_path = project_root / 'data' / 'raw' / 'store_templates' / 'Plannogram compiled_16052025.backup.csv'
    if not csv_path.exists():
        return jsonify({'success': False, 'error': 'Store template file not found'})
        
    try:
        store_master = build_store_master(csv_path)
        decoded_name = normalize_store_name(unquote(store_name))
        
        if decoded_name not in store_master:
            return jsonify({'success': True, 'data': {
                'optimization': {},
                'lob_priorities': {},
                'summary': 'No matching store in master data.',
                'diagnostics': f"No matching store '{store_name}' (decoded: {decoded_name}) in master data."
            }})
            
        wall_details = store_master[decoded_name]['wall_details']
        wall_counts = {lob: wd['wall_count'] for lob, wd in wall_details.items()}
        
        # Handle capacity data - only use real values, no fallbacks
        capacities = {}
        for lob, wd in wall_details.items():
            capacity = wd.get('total_capacity', 0)
            # Only use real capacity data, no fallback estimation
            capacities[lob] = capacity if capacity > 0 else 0
        
        # Check if user has saved a custom wall configuration
        user_config = None
        global user_wall_configs
        if decoded_name in user_wall_configs:
            user_config = user_wall_configs[decoded_name]
            logger.info(f"Using saved user configuration for optimization: {user_config}")
            
            # Update wall_counts with user's configuration
            for lob in wall_counts.keys():
                wall_counts[lob] = user_config.get(lob, wall_counts[lob])
        
        total_walls = sum(wall_counts.values())
        
        logger.info(f"Store: {decoded_name}, Total walls: {total_walls}")
        logger.info(f"Current distribution: {wall_counts}")
        logger.info(f"Capacity summary: {capacities}")
        
        # Apple Store Business Priority (iPhone > Mac > iPad > Others have equal priority)
        business_priority = {
            'Cases & Covers': 1,           # iPhone accessories (highest priority)
            'Mac Accessories': 2,          # Mac accessories (second priority)  
            'iPad Accessories': 3,         # iPad accessories (third priority)
            'Watch Accessories': 4,        # Watch accessories (fourth priority)
            'Adapters & Cables': 4,        # Power & Cables (same as watch/audio)
            'Audio Accessories': 4,        # Audio accessories (same as watch/adapters)
            'Screen Protectors': 4,        # Screen protectors (same as others)
            'Storage & Organization': 4,   # Storage (same as others)
            'Miscellaneous': 4             # Miscellaneous (same as others)
        }
        
        # Calculate normalized capacity scores for balanced optimization
        total_capacity = sum(capacities.values())
        capacity_scores = {}
        for lob, capacity in capacities.items():
            if total_capacity > 0:
                capacity_scores[lob] = capacity / total_capacity
            else:
                capacity_scores[lob] = 0
        
        logger.info(f"Capacity scores: {capacity_scores}")
        
        # OPTIMIZATION ALGORITHM: Conservative approach - only recommend changes for significant imbalances
        optimal_distribution = {}
        
        if total_walls > 0:
            # Only work with categories that actually exist in this store
            existing_categories = [lob for lob in wall_counts.keys() if wall_counts[lob] > 0 or capacities.get(lob, 0) > 0]
            
            if not existing_categories:
                optimal_distribution = wall_counts.copy()
            else:
                # Start with current distribution - conservative approach
                optimal_distribution = wall_counts.copy()
                
                # Check for significant imbalances that need correction
                imbalances = []
                
                for lob in existing_categories:
                    current_walls = wall_counts[lob]
                    priority = business_priority.get(lob, 10)
                    
                    # Define what constitutes a significant imbalance
                    if priority == 1:  # iPhone accessories (highest priority)
                        # Should have at least 25% of walls or minimum 3 walls for stores with 10+ walls
                        expected_min = max(3 if total_walls >= 10 else 2, int(total_walls * 0.25))
                        if current_walls < expected_min:
                            imbalances.append({
                                'lob': lob,
                                'current': current_walls,
                                'needed': expected_min - current_walls,
                                'reason': f"iPhone accessories underrepresented (priority 1)"
                            })
                    
                    elif priority <= 3:  # Mac and iPad accessories
                        # Should have reasonable representation, not crowded out
                        expected_min = max(1, int(total_walls * 0.15))
                        if current_walls < expected_min and total_walls >= 8:
                            imbalances.append({
                                'lob': lob,
                                'current': current_walls,
                                'needed': expected_min - current_walls,
                                'reason': f"High priority category underrepresented (priority {priority})"
                            })
                    
                    elif priority >= 4:  # Lower priority categories
                        # Should not dominate - check if taking too much space
                        max_reasonable = max(1, int(total_walls * 0.35))  # No more than 35%
                        if current_walls > max_reasonable and total_walls >= 6:
                            imbalances.append({
                                'lob': lob,
                                'current': current_walls,
                                'needed': -(current_walls - max_reasonable),
                                'reason': f"Lower priority category overrepresented (priority {priority})"
                            })
                
                # Only make changes if there are significant imbalances
                if imbalances:
                    logger.info(f"Detected imbalances: {imbalances}")
                    
                    # Apply conservative corrections
                    for imbalance in imbalances:
                        lob = imbalance['lob']
                        needed_change = imbalance['needed']
                        
                        # Cap changes to be conservative (max 2 walls change per category)
                        if needed_change > 0:
                            change = min(needed_change, 2)
                            optimal_distribution[lob] += change
                        else:
                            change = max(needed_change, -2)
                            optimal_distribution[lob] = max(1, optimal_distribution[lob] + change)
                    
                    # Ensure total walls remain constant by redistributing
                    current_total = sum(optimal_distribution.values())
                    if current_total != total_walls:
                        diff = total_walls - current_total
                        
                        if diff > 0:  # Need to add walls
                            # Add to highest priority categories that can accommodate
                            for priority in [1, 2, 3, 4]:
                                if diff <= 0:
                                    break
                                candidates = [lob for lob in existing_categories 
                                            if business_priority.get(lob, 10) == priority 
                                            and optimal_distribution[lob] < int(total_walls * 0.4)]
                                for lob in candidates:
                                    if diff > 0:
                                        optimal_distribution[lob] += 1
                                        diff -= 1
                        
                        elif diff < 0:  # Need to remove walls
                            # Remove from lowest priority categories
                            for priority in [4, 3, 2, 1]:
                                if diff >= 0:
                                    break
                                candidates = [lob for lob in existing_categories 
                                            if business_priority.get(lob, 10) == priority 
                                            and optimal_distribution[lob] > 1]
                                for lob in candidates:
                                    if diff < 0:
                                        optimal_distribution[lob] -= 1
                                        diff += 1
                else:
                    logger.info("No significant imbalances detected - current distribution is reasonable")
        
        # Calculate changes needed (with zero-sum constraint)
        changes_needed = {}
        existing_categories = [lob for lob in wall_counts.keys() if wall_counts[lob] > 0 or capacities.get(lob, 0) > 0]
        
        for lob in existing_categories:
            current = wall_counts[lob]
            optimal = optimal_distribution.get(lob, 0)
            change = optimal - current
            
            if change != 0:
                changes_needed[lob] = {
                    'current': current,
                    'optimal': optimal,
                    'walls_affected': change,
                    'action': 'ADD' if change > 0 else 'REMOVE',
                    'change_type': 'increase' if change > 0 else 'decrease',
                    'reason': f"Business priority optimization for {lob}"
                }
        
        # Verify zero-sum constraint
        total_changes = sum(data['walls_affected'] for data in changes_needed.values())
        if abs(total_changes) > 0.01:
            logger.warning(f"Zero-sum constraint violated: total changes = {total_changes}")
        
        # Generate summary
        if changes_needed:
            summary = f"Optimization detected {len(changes_needed)} significant imbalances that require correction to better align with business priorities."
        else:
            summary = "Current wall allocation is well-balanced and aligned with business priorities. No changes needed."
        
        logger.info(f"Optimal distribution: {optimal_distribution}")
        logger.info(f"Changes needed: {changes_needed}")
        
        return jsonify({'success': True, 'data': {
            'optimization': {
                'current_distribution': wall_counts,
                'optimal_distribution': optimal_distribution,
                'changes_needed': changes_needed
            },
            'lob_priorities': business_priority,
            'summary': summary,
            'diagnostics': None
        }})
        
    except Exception as e:
        logger.error(f"Error in recommendations: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stores/analysis', methods=['GET'])
def get_store_analysis():
    """Return unique store names and metadata for dropdown selection"""
    csv_path = project_root / 'data' / 'raw' / 'store_templates' / 'Plannogram compiled_16052025.backup.csv'
    if not csv_path.exists():
        return jsonify({'success': False, 'error': 'Store template file not found'})
        
    try:
        df = pd.read_csv(csv_path)
        store_selector = {}
        for _, row in df.iterrows():
            store_name = str(row['Store name']).strip()
            city = str(row['CITY']).strip()
            location = str(row['LOCATION']).strip()
            if store_name not in store_selector:
                store_selector[store_name] = {'city': city, 'location': location}

        return jsonify({'success': True, 'data': {'store_selector': store_selector}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stores/<store_name>/generate-planograms', methods=['POST'])
def generate_planograms(store_name):
    """Generate planograms for a store based on current wall configuration"""
    try:
        data = request.get_json()
        job_id = str(uuid.uuid4())
        
        # Create job record
        job = Job(job_id, 'generate_planogram', {
            "store_name": store_name,
            "selected_accessories": data.get("selected_accessories", ["cases_covers", "ipad_accessories"])
        })
        
        jobs[job_id] = job
        job.status = JobStatus.RUNNING
        
        # Run synchronously to avoid Flask context issues
        try:
            result = generate_planogram_for_store(job.parameters)
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
            return jsonify({
                "success": True,
                "job_id": job_id,
                "message": "Planogram generation completed successfully",
                "result": result
            })
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
            
            return jsonify({
                "success": False,
                "job_id": job_id,
                "error": str(e)
            })
        
    except Exception as e:
        logger.error(f"Error starting planogram generation: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        })

# Job runner function removed - now using synchronous processing

def generate_planogram_for_store(parameters):
    """Generate planograms for a specific store"""
    store_name = parameters['store_name']
    selected_accessories = parameters.get('selected_accessories', ['cases_covers', 'ipad_accessories'])
    
    logger.info(f"Generating planograms for store: {store_name}")
    logger.info(f"Selected accessories: {selected_accessories}")
    
    decoded_name = normalize_store_name(unquote(store_name))
    
    # Get current wall configuration using optimized store reference
    store_master = build_store_master(None)  # No CSV needed anymore
    if decoded_name not in store_master:
        logger.error(f"Store '{store_name}' not found in master data. Available stores: {list(store_master.keys())[:10]}...")
        return {
            'error': f"Store '{store_name}' not found",
            'available_stores': list(store_master.keys())[:20]
        }
    
    store_data = store_master[decoded_name]
    wall_details = store_data['wall_details']
    
    # Apply final wall configuration (includes user edits and optimization recommendations)
    try:
        planogram_mgr = get_planogram_manager(project_root)
        final_config = planogram_mgr.get_final_wall_config(decoded_name)

        if final_config and final_config.get('wall_counts'):
            final_wall_counts = final_config['wall_counts']
            logger.info(f"Using final optimized wall configuration: {final_wall_counts}")

            # Update wall_details with final configuration
            updated_wall_details = {}
            for lob, details in wall_details.items():
                updated_wall_details[lob] = {
                    **details,
                    'wall_count': final_wall_counts.get(lob, details['wall_count'])
                }
            wall_details = updated_wall_details
        else:
            # Fallback to user configuration if no final config exists
            global user_wall_configs
            if decoded_name in user_wall_configs:
                user_config = user_wall_configs[decoded_name]
                logger.info(f"Using user wall configuration: {user_config}")

                # Update wall_details with user's configuration
                updated_wall_details = {}
                for lob, details in wall_details.items():
                    updated_wall_details[lob] = {
                        **details,
                        'wall_count': user_config.get(lob, details['wall_count'])
                    }
                wall_details = updated_wall_details
            else:
                logger.info(f"Using default wall configuration from store master")
    except Exception as e:
        logger.warning(f"Error loading final wall configuration: {e}, using default")
    
    # Handle multiple accessory types
    generated_files = []
    generation_results = []
    
    # Generate Cases & Covers planograms
    if ('cases_covers' in selected_accessories or 'cases' in selected_accessories) and 'Cases & Covers' in wall_details:
        cases_details = wall_details['Cases & Covers']
        num_walls = cases_details['wall_count']
        
        if num_walls > 0:
            logger.info(f"Generating planograms for {num_walls} Cases & Covers walls")
            cases_result = generate_cases_planograms(store_name, num_walls, decoded_name)
            if cases_result['success']:
                generated_files.extend(cases_result['generated_files'])
                generation_results.append(f"Cases & Covers: {num_walls} walls")
            else:
                generation_results.append(f"Cases & Covers: Failed - {cases_result['message']}")
    
    # Generate iPad Accessories planograms
    if 'ipad_accessories' in selected_accessories and 'iPad Accessories' in wall_details:
        ipad_details = wall_details['iPad Accessories']
        num_walls = ipad_details['wall_count']

        if num_walls > 0:
            logger.info(f"Generating planograms for {num_walls} iPad Accessories walls")
            ipad_result = generate_ipad_planograms(store_name, num_walls, decoded_name)
            if ipad_result['success']:
                generated_files.extend(ipad_result['generated_files'])
                generation_results.append(f"iPad Accessories: {num_walls} walls")
            else:
                generation_results.append(f"iPad Accessories: Failed - {ipad_result['message']}")

    # Generate Mac Accessories planograms
    if 'mac_accessories' in selected_accessories and 'Mac Accessories' in wall_details:
        mac_details = wall_details['Mac Accessories']
        num_walls = mac_details['wall_count']

        if num_walls > 0:
            logger.info(f"Generating planograms for {num_walls} Mac Accessories walls")
            mac_result = generate_mac_planograms(store_name, num_walls, decoded_name)
            if mac_result['success']:
                generated_files.extend(mac_result['generated_files'])
                generation_results.append(f"Mac Accessories: {num_walls} walls")
            else:
                generation_results.append(f"Mac Accessories: Failed - {mac_result['message']}")

    # Check if any planograms were generated
    if not generated_files:
        return {
            'success': False,
            'message': 'No planograms were generated. Check selected accessories and wall allocations.',
            'generated_files': [],
            'details': generation_results
        }
    
    return {
        'success': True,
        'message': f'Successfully generated planograms for {store_name}',
        'generated_files': generated_files,
        'store_name': store_name,
        'details': generation_results
    }

def generate_cases_planograms(store_name: str, num_walls: int, decoded_name: str) -> dict:
    """Generate Cases & Covers planograms using the proper Cases & Covers generator"""
    try:
        from planogram_services.cases_covers_generator import CasesCoversGenerator
        
        logger.info(f"Generating {num_walls} Cases & Covers planograms using CasesCoversGenerator")
        
        # Initialize Cases & Covers generator
        cases_generator = CasesCoversGenerator(str(project_root))
        
        # Generate planograms for all walls
        results = cases_generator.generate_store_planograms(store_name, num_walls)
        
        if not results or not isinstance(results, dict):
            return {
                'success': False,
                'message': 'Cases & Covers generation returned invalid results',
                'generated_files': []
            }
        
        # Convert to expected format
        generated_files = []
        
        for wall_key, success in results.items():
            if success:
                wall_number = int(wall_key.split('_')[1])
                
                # Determine file paths (Cases generator creates its own naming)
                store_slug = store_name.lower()  # Match generator's naming exactly
                planogram_path = f"{store_slug}_wall{wall_number}_cases_covers_planogram.png"
                report_path = f"{store_slug}_wall{wall_number}_cases_covers_details.txt"
                
                # Add planogram image
                generated_files.append({
                    "type": "planogram_image",
                    "accessory": "cases",
                    "filename": planogram_path,
                    "description": f"Cases & Covers Planogram - Wall {wall_number}",
                    "wall": str(wall_number)
                })
                
                # Add report file
                generated_files.append({
                    "type": "planogram_report",
                    "accessory": "cases",
                    "filename": report_path,
                    "description": f"Cases & Covers Report - Wall {wall_number}",
                    "wall": str(wall_number)
                })
        
        return {
            'success': True,
            'generated_files': generated_files,
            'message': f'Generated {len(generated_files)} Cases & Covers files'
        }
            
    except Exception as e:
        logger.error(f"Error in Cases & Covers generation: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'Error generating Cases & Covers: {str(e)}',
            'generated_files': []
        }

# REMOVED: create_intelligent_cases_planogram() - Now using StreamlinedPlanogramGenerator directly

def load_products(data_dir):
    """REMOVED - Use StreamlinedPlanogramGenerator which loads from processed cases_reference.json"""
    # This function is no longer needed as the streamlined generator
    # loads cases data directly from the processed reference file
    return []

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'})
    return jsonify({'success': True, 'data': job.to_dict()})

@app.route('/api/results/<job_id>/files', methods=['GET'])
def get_job_files(job_id):
    """Get files generated by a job"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'})
    
    if job.status != JobStatus.COMPLETED or not job.result:
        return jsonify({'success': True, 'data': {'files': [], 'planograms': []}})
    
    result = job.result
    generated_files = result.get('generated_files', [])
    
    # Transform generated files into the format expected by frontend
    files = []
    planograms = []
    
    for file_info in generated_files:
        if isinstance(file_info, dict):
            filename = file_info.get('filename', '')
            file_type = file_info.get('type', 'unknown')
            
            # Create file entry
            file_entry = {
                'filename': filename,
                'type': file_type,
                'url': f'/output/{filename}' if filename else ''
            }
            files.append(file_entry)
            
            # If it's a planogram image, also add to planograms list
            if file_type == 'planogram_image' and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                planogram_entry = {
                    'name': filename,
                    'url': f'/output/{filename}',
                    'type': 'image'
                }
                planograms.append(planogram_entry)
    
    return jsonify({
        'success': True,
        'data': {
            'files': files,
            'planograms': planograms
        }
    })

@app.route('/api/stores', methods=['GET'])
def get_stores():
    """Get list of available stores"""
    try:
        store_master = build_store_master(None)  # Use optimized reference
        
        stores = []
        for store_name, store_data in store_master.items():
            stores.append({
                "name": store_name,
                "original_name": store_data.get('original_name', store_name),
                "location": store_data.get('location', ''),
                "city": store_data.get('city', ''),
                "wall_count": len(store_data.get('wall_details', {}))
            })
        
        return jsonify({
            "success": True,
            "data": stores[:20]  # Return first 20 stores
        })
    except Exception as e:
        logger.error(f"Error loading stores: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    try:
        # Load and check stores from optimized reference
        store_master = build_store_master(None)
        available_stores = list(store_master.keys())[:5]  # First 5 stores
        
        return jsonify({
            "success": True,
            "data": {
                "data_files": {"cases": True, "cables": True, "screen_protectors": True, "others": True},
                "store_templates": ["flagship", "standard", "express"],
                "lob_status": {"iPhone": True, "iPad": True, "Mac": True, "Watch": True, "AirPods": True},
                "system_health": "healthy",
                "available_stores": available_stores,
                "total_stores": len(store_master)
            }
        })
    except Exception as e:
        return jsonify({
            "success": True,
            "data": {
                "data_files": {"cases": True, "cables": True, "screen_protectors": True, "others": True},
                "store_templates": ["flagship", "standard", "express"],
                "lob_status": {"iPhone": True, "iPad": True, "Mac": True, "Watch": True, "AirPods": True},
                "system_health": "healthy",
                "error": str(e)
            }
        })

@app.route('/output/<path:filename>')
def serve_output_file(filename):
    """Serve generated output files"""
    return send_from_directory(project_root / 'output', filename)

# ---------------------------------------------------------------------------- #
#                                  Main                                        #
# ---------------------------------------------------------------------------- #

@app.route('/api/clear-cache', methods=['POST'])
def generate_ipad_planograms(store_name: str, num_walls: int, decoded_name: str) -> dict:
    """Generate iPad Accessories planograms using the new 5-row system"""
    try:
        from planogram_services.ipad_integration import OptimizedIPadIntegration
        
        logger.info(f"Generating {num_walls} iPad planograms using NEW 5-row system")
        
        # Initialize iPad integration
        ipad_integration = OptimizedIPadIntegration(str(project_root))
        
        # Generate planograms
        results = ipad_integration.generate_optimized_planograms(store_name, num_walls)
        
        if not results['success']:
            return {
                'success': False,
                'message': f"iPad generation failed: {results.get('error', 'Unknown error')}",
                'generated_files': []
            }
        
        # Convert to expected format
        generated_files = []
        
        for wall in results['generated_walls']:
            if wall['success']:
                wall_num = wall['wall_number']
                
                # Add planogram image
                generated_files.append({
                    "type": "planogram_image",
                    "accessory": "ipad",
                    "filename": wall['planogram_path'],
                    "description": f"iPad Accessories Planogram - Wall {wall_num} ({wall['wall_type']})",
                    "wall": str(wall_num)
                })
                
                # Add report file
                generated_files.append({
                    "type": "planogram_report",
                    "accessory": "ipad",
                    "filename": wall['report_path'],
                    "description": f"iPad Accessories Report - Wall {wall_num}",
                    "wall": str(wall_num)
                })
        
        return {
            'success': True,
            'generated_files': generated_files,
            'message': f'Generated {len(generated_files)} iPad Accessories files (5-row system, no blanks)'
        }
        
    except Exception as e:
        logger.error(f"Error in iPad Accessories generation: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'Error generating iPad Accessories: {str(e)}',
            'generated_files': []
        }

def generate_mac_planograms(store_name: str, num_walls: int, decoded_name: str) -> dict:
    """Generate Mac Accessories planograms using the enhanced Mac system"""
    try:
        from planogram_services.mac_integration import MacIntegration

        logger.info(f"Generating {num_walls} Mac planograms using enhanced Mac system")

        # Initialize Mac integration
        mac_integration = MacIntegration()

        # Generate Mac planograms
        wall_config = {'Mac Accessories': num_walls}
        mac_results = mac_integration.generate_mac_planograms(
            store_name=store_name,
            wall_config=wall_config,
            selected_categories=['mac_accessories', 'bags_sleeves']
        )

        if not mac_results:
            return {
                'success': False,
                'message': 'Mac generation returned no results',
                'generated_files': []
            }

        # Convert to expected format
        generated_files = []
        for wall_id, file_path in mac_results.items():
            if file_path and Path(file_path).exists():
                # Extract wall number from wall_id (e.g., "wall_1" -> 1)
                if wall_id.startswith('wall_'):
                    wall_number = wall_id.split('_')[1]
                elif wall_id == 'bags_sleeves':
                    wall_number = 'bags'
                else:
                    wall_number = '1'

                # Add planogram image
                generated_files.append({
                    "type": "planogram_image",
                    "accessory": "mac",
                    "filename": Path(file_path).name,
                    "description": f"Mac Accessories Planogram - {wall_id.replace('_', ' ').title()}",
                    "wall": str(wall_number)
                })

        return {
            'success': True,
            'generated_files': generated_files,
            'message': f'Generated {len(generated_files)} Mac Accessories files (dimensional optimization)'
        }

    except Exception as e:
        logger.error(f"Error in Mac Accessories generation: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'Error generating Mac Accessories: {str(e)}',
            'generated_files': []
        }

def clear_cache():
    """Clear the store reference cache to force reload of data"""
    global _store_reference_cache
    _store_reference_cache = None
    logger.info("Store reference cache cleared")
    return jsonify({'success': True, 'message': 'Cache cleared successfully'})

@app.route('/api/stores/<store_name>/generate-all-planograms', methods=['POST'])
def generate_store_planograms(store_name):
    """Generate planograms for all walls based on final wall configuration"""
    try:
        decoded_name = normalize_store_name(unquote(store_name))
        logger.info(f"Generating planograms for store: {decoded_name}")
        
        # Get store data
        store_master = build_store_master(project_root / 'data' / 'raw' / 'store_templates' / 'Plannogram compiled_16052025.backup.csv')
        if decoded_name not in store_master:
            return jsonify({
                'success': False, 
                'error': f'Store not found: {store_name}'
            })
        
        store_data = store_master[decoded_name]
        
        # Generate planograms
        planogram_mgr = get_planogram_manager(project_root)
        results = planogram_mgr.generate_planograms(decoded_name, store_data)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error generating planograms: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stores/<store_name>/final-wall-config', methods=['GET'])
def get_final_wall_config(store_name):
    """Get the final wall configuration for a store"""
    try:
        decoded_name = normalize_store_name(unquote(store_name))
        
        planogram_mgr = get_planogram_manager(project_root)
        final_config = planogram_mgr.get_final_wall_config(decoded_name)
        
        if final_config:
            return jsonify({
                'success': True,
                'data': final_config
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No final wall configuration found'
            })
            
    except Exception as e:
        logger.error(f"Error getting final wall config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------- #

if __name__ == '__main__':
    try:
        logger.info("Starting Apple Store Planogram Optimization System...")
        logger.info(f"Project root: {project_root}")
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
