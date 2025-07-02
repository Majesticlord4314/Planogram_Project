"""System-wide constants"""

# Planogram settings
DEFAULT_GAP_SIZE = 4.0  # cm between products
MIN_PRODUCT_WIDTH = 5.0
MAX_PRODUCT_WIDTH = 50.0

# Optimization weights
DEMAND_WEIGHT = 0.4
MARGIN_WEIGHT = 0.3
PLACEMENT_WEIGHT = 0.3

# Store types
STORE_TYPES = {
    'flagship': {
        'min_skus': 150,
        'max_skus': 500,
        'premium_required': True
    },
    'standard': {
        'min_skus': 50,
        'max_skus': 150,
        'premium_required': False
    },
    'express': {
        'min_skus': 20,
        'max_skus': 50,
        'premium_required': False
    }
}

# Category priorities
CATEGORY_PRIORITY = {
    'case': 1,
    'screen_protector': 2,
    'cable': 3,
    'charger': 4,
    'adapter': 5,
    'mount': 6,
    'audio': 7,
    'other': 8
}