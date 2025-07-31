# 🎯 PLANOGRAM PROJECT - MASTER DOCUMENTATION

**Complete reference for all connections, APIs, functions, and testing procedures.**  
*Use this as context for all future conversations.*

---

## 📋 TABLE OF CONTENTS

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture) 
3. [File Structure & Connections](#file-structure--connections)
4. [API Endpoints](#api-endpoints)
5. [Functions Reference](#functions-reference)
6. [Testing & Development](#testing--development)
7. [Data Flow](#data-flow)
8. [Visual Enhancement Details](#visual-enhancement-details)

---

## 🏗️ PROJECT OVERVIEW

### Core Purpose
Generate optimized planograms for Apple Store accessory layouts using real product data with enhanced visual presentation.

### Key Features
- **Series-based allocation**: Products allocated by iPhone series (Base, Plus, Pro, Pro Max)
- **Phone-like rectangles**: Visual products rendered as phone-shaped rectangles instead of squares
- **Brand grouping**: Apple products get 50% placement in top rows, organized by brand
- **Realistic retail layout**: Proper spacing, labeling, and aesthetic presentation
- **Fast store lookup**: Optimized JSON-based store reference system

---

## 🏛️ SYSTEM ARCHITECTURE

```
Frontend (React/HTML) ←→ Flask Backend ←→ Enhanced Planogram Generator
     ↓                        ↓                       ↓
  Web UI                 Job Management           Data Processing
                              ↓                       ↓
                         File Serving            Visual Output
```

### Technology Stack
- **Backend**: Flask (Python)
- **Frontend**: React/HTML + JavaScript
- **Data Processing**: Pandas, DataLoader
- **Visualization**: Matplotlib, Enhanced Planogram Generator
- **Storage**: JSON (optimized), CSV (raw data)

---

## 📁 FILE STRUCTURE & CONNECTIONS

### Backend Core Files
```
web-ui/backend/
├── app.py                     # Main Flask application
├── requirements.txt           # Python dependencies
└── static/                    # Static assets

Key Connections in app.py:
- Line 219: build_store_master() → Uses store_reference.json
- Line 712: generate_planograms() → Triggers job management
- Line 947: create_intelligent_cases_planogram() → Enhanced generator
```

### Data Processing
```
create_cases_reference.py         # One-time: Processes 493 cases from CSV into JSON
data/processed/cases_reference.json  # Fast lookup for 493 case products
src/visualization/streamlined_planogram_generator.py  # Streamlined visual generator
└── models/
    └── product.py             # Product data models (legacy)

Data Flow:
cases_reference.json → streamlined_planogram_generator.py → PNG output (100% utilization)
```

### Store Reference System
```
data/
├── processed/
│   ├── store_reference.json   # Fast lookup (45 stores)
│   └── cases_reference.json   # Fast cases lookup (493 products)
└── raw/
    ├── accessories/           # 4 CSV files with product data (legacy)
    └── store_templates/       # Original CSV template

Generation:
create_store_reference.py → store_reference.json (one-time setup)
create_cases_reference.py → cases_reference.json (one-time setup)
```

### Enhanced Planogram Generator
```
src/visualization/streamlined_planogram_generator.py
├── StreamlinedPlanogramGenerator class
├── generate_store_planograms()
├── _organize_for_wall() (100% utilization enforced)
├── _draw_phone_rectangle()
└── Fast loading from processed cases_reference.json
```

---

## 🔌 API ENDPOINTS

### Store Management
```
GET  /api/stores                           # List all available stores
GET  /api/stores/{store_name}/lob-details  # Get store LOB configuration
POST /api/stores/{store_name}/save-wall-config  # Save wall configuration
GET  /api/stores/{store_name}/recommendations   # Get optimization recommendations
```

### Planogram Generation
```
POST /api/stores/{store_name}/generate-planograms
Request: {"selected_accessories": ["cases_covers"]}
Response: {"success": true, "job_id": "uuid", "message": "started"}

GET  /api/jobs/{job_id}                    # Check generation status
GET  /output/{filename}                    # Serve generated planogram files
```

### System Information
```
GET  /api/system/info                      # System health and available stores
GET  /api/stores/analysis                  # Store metadata for UI dropdowns
```

---

## ⚙️ FUNCTIONS REFERENCE

### Backend Core Functions (app.py)

#### Store Management
```python
normalize_store_name(name)                 # Line 88  - Normalize store names
load_store_reference()                     # Line 224 - Load optimized store data
build_store_master(csv_path)               # Line 243 - Build store master (optimized)
```

#### Job Management  
```python
run_job_async(job_id)                      # Line 734 - Async job execution
generate_planogram_for_store(parameters)   # Line 754 - Core planogram generation
create_intelligent_cases_planogram(...)    # Line 947 - Enhanced generator interface
```

#### Data Loading
```python
load_products(data_dir)                    # Line 985 - Load products via DataLoader
```

### Enhanced Planogram Generator Functions

#### Core Generation
```python
EnhancedPlanogramGenerator.create_intelligent_cases_planogram()
# Main entry point - generates all walls with series allocation

allocate_walls_by_series(products, num_walls)
# Distributes products across walls by iPhone series

create_retail_style_layout(products, wall_num, store_type)
# Creates realistic retail-style visual layout
```

#### Visual Enhancement
```python
draw_phone_rectangle(ax, x, y, width, height, product, color)
# Draws phone-shaped rectangles instead of squares

categorize_by_series(products)
# Groups products by iPhone series (Base, Plus, Pro, Pro Max)

apply_brand_priority(products)
# Ensures Apple gets 50% placement in top rows
```

### Data Processing Functions

#### DataLoader (src/data_processing/data_loader.py)
```python
load_all_products()                        # Loads from 4 CSV files
load_cases_sales()                         # 399 products
load_combined_watch()                      # 314 products  
load_ipad_cases()                          # 158 products
load_mac_accessories()                     # 254 products
```

---

## 🧪 TESTING & DEVELOPMENT

### Start Backend Server
```bash
cd web-ui/backend
python app.py
# Server runs on http://localhost:5000
```

### Test API Endpoints
```bash
# Check system health
curl http://localhost:5000/api/system/info

# List stores
curl http://localhost:5000/api/stores

# Generate planogram for a store
curl -X POST http://localhost:5000/api/stores/imagine-ub-city-bengaluru/generate-planograms \
  -H "Content-Type: application/json" \
  -d '{"selected_accessories": ["cases_covers"]}'

# Check job status  
curl http://localhost:5000/api/jobs/{job_id}
```

### Test Store Reference System
```bash
# Generate optimized store reference (run once)
python create_store_reference.py

# Verify store data
python -c "
import json
with open('data/processed/store_reference.json') as f:
    stores = json.load(f)
print(f'Loaded {len(stores)} stores')
print('Sample:', list(stores.keys())[:3])
"
```

### Test Enhanced Planogram Generator
```bash
# Direct test of enhanced generator
python -c "
from src.visualization.enhanced_retail_planogram import EnhancedPlanogramGenerator
from src.data_processing.data_loader import DataLoader

loader = DataLoader('data/raw')
products = loader.load_all_products()
print(f'Loaded {len(products)} products')

generator = EnhancedPlanogramGenerator()
result = generator.create_intelligent_cases_planogram(
    products=products[:100], 
    store_type='flagship', 
    store_name='test_store', 
    num_walls=3
)
print('Result:', result.get('status'))
"
```

---

## 🌊 DATA FLOW

### Complete Generation Process
```
1. Frontend Request → Flask API endpoint
2. Flask → Job Management (async)
3. Job → load_products() → DataLoader
4. DataLoader → 4 CSV files → 1,125 products
5. Products → Enhanced Planogram Generator
6. Generator → Series allocation + Visual enhancement
7. Enhanced Generator → PNG files + product details
8. Flask → Serve files via /output/ endpoint
9. Frontend → Display generated planograms
```

### Store Lookup Flow
```
1. API Request with store_name
2. normalize_store_name() → Clean store name
3. load_store_reference() → Fast JSON lookup
4. store_reference.json → Store configuration
5. Wall details → Enhanced planogram generation
```

### Visual Enhancement Flow
```
1. Raw products → categorize_by_series()
2. Series groups → allocate_walls_by_series()
3. Wall allocation → create_retail_style_layout()
4. Layout → draw_phone_rectangle() for each product
5. Phone rectangles → Brand grouping + labeling
6. Final layout → PNG output with retail aesthetics
```

---

## 🎨 VISUAL ENHANCEMENT DETAILS

### Phone-like Rectangle Implementation
- **Shape**: Rounded rectangles mimicking phone proportions
- **Dimensions**: Width:Height ratio of 9:16 (phone aspect ratio)
- **Colors**: Brand-specific color coding (Apple blue, third-party varied)
- **Labels**: Product name, price, series information

### Series-based Allocation Logic
```
Wall 1: Pro Max products (premium placement)
Wall 2: Pro products (high-value placement)  
Wall 3: Plus products (mid-tier placement)
Wall 4: Base products (entry-level placement)
Wall 5+: Screen protectors, accessories, overflow
```

### Brand Grouping Strategy
- **Top rows (50%)**: Apple products prioritized
- **Bottom rows (50%)**: Third-party brand mix
- **Column organization**: Brands grouped vertically when possible
- **Diversity**: Ensures representation across all major brands

### Retail Layout Features
- **Proper spacing**: Realistic gaps between products
- **Grid alignment**: Professional retail-style arrangement
- **Visual hierarchy**: Important products prominently placed
- **Aesthetic labels**: Clean typography with product information

---

## 🔧 DEVELOPMENT COMMANDS

### Quick Start
```bash
# 1. Start backend
cd web-ui/backend && python app.py

# 2. Generate store reference (first time only)
python create_store_reference.py

# 3. Test planogram generation
curl -X POST http://localhost:5000/api/stores/imagine-ub-city-bengaluru/generate-planograms \
  -H "Content-Type: application/json" \
  -d '{"selected_accessories": ["cases_covers"]}'
```

### File Locations for Quick Access
- **Main backend**: `web-ui/backend/app.py`
- **Enhanced generator**: `src/visualization/enhanced_retail_planogram.py`
- **Data loader**: `src/data_processing/data_loader.py`
- **Store reference**: `data/processed/store_reference.json`
- **Output files**: `output/` directory

---

## 📈 STATUS & HEALTH CHECK

### Current System Status
- ✅ **Professional Planogram Generator**: Series split logic with accessory rows
- ✅ **Product Categorization**: MagSafe, Armor, Silicone, Clear categories
- ✅ **TPA Diversity**: Round-robin brand mixing for proper representation  
- ✅ **Store Reference**: Optimized JSON system (45 real stores)
- ✅ **Backend API**: Flask server operational with real store integration
- ✅ **Series Allocation**: Dynamic based on wall count (1-4 walls supported)
- ✅ **Visual Excellence**: Phone rectangles, category colors, accessory sections
- ⚠️ **Frontend**: Basic UI available, may need updates

### Latest Improvements
- **Series Split Logic**: Wall allocation based on number of walls (1: Mixed, 2: Premium/Standard, 3: Pro Max/Pro/Plus+Base)
- **Dedicated Accessory Rows**: Bottom row reserved for screen protectors/TG/lens protectors
- **Product Categorization**: MagSafe, Armor, Silicone, Clear, Leather, Wallet categories
- **TPA Diversity**: Proper brand mixing with round-robin distribution
- **Professional Rectangles**: Phone-like dimensions with category-based colors
- **Real Store Integration**: Using actual store names like "Imagine UB City Bengaluru"
- **Enhanced Details**: Series, brand, and category breakdowns in output files

---

*Last Updated: July 28, 2025*  
*Version: 2.0 - Enhanced Retail System*
