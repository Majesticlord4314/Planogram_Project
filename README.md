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
9. [iPad Accessories System](#ipad-accessories-system)
10. [TPA Brand Management](#tpa-brand-management)
11. [Wall Configuration System](#wall-configuration-system)
12. [Latest Features & Updates](#latest-features--updates)

---

## 🏗️ PROJECT OVERVIEW

### Core Purpose
Generate optimized planograms for Apple Store accessory layouts using real product data with enhanced visual presentation across multiple product categories.

### Key Features
- **Multi-Category Support**: Cases & Covers, iPad Accessories, Mac Accessories, Audio, Watch, Adapters & Cables
- **Advanced iPad System**: 5-row grid with Apple/TPA brand allocation and no blank facings
- **TPA Brand Filtering**: Gripp, Pulse, and Tekne brands only for planograms
- **Series-based allocation**: Products allocated by iPhone series (Base, Plus, Pro, Pro Max)
- **Phone-like rectangles**: Visual products rendered as phone-shaped rectangles instead of squares
- **Brand grouping**: Apple products get 50% placement in top rows, organized by brand
- **Realistic retail layout**: Proper spacing, labeling, and aesthetic presentation
- **Fast store lookup**: Optimized JSON-based store reference system
- **Wall Configuration Management**: Dynamic wall allocation per store and LOB
- **Real-time Generation**: Async job processing with status tracking

---

## 🏛️ SYSTEM ARCHITECTURE

```
Frontend (React/TypeScript) ←→ Flask Backend ←→ Multi-Category Generators
     ↓                              ↓                       ↓
  Web UI                     Job Management           Data Processing
  Store Selector                     ↓                       ↓
  Wall Configuration            File Serving            Visual Output
                                     ↓                       ↓
                              Cases & Covers          iPad Accessories
                              iPad Generator          Mac Accessories
                              TPA Filtering           Audio/Watch/Cables
```

### Technology Stack
- **Backend**: Flask (Python) with async job processing
- **Frontend**: React/TypeScript + HTML/JavaScript
- **Data Processing**: Pandas, DataLoader, Multi-category processors
- **Visualization**: Matplotlib, Enhanced Planogram Generators
- **Storage**: JSON (optimized), CSV (raw data), Wall configurations
- **File Serving**: Dynamic output serving with path resolution

---

## 📁 FILE STRUCTURE & CONNECTIONS

### Backend Core Files
```
web-ui/backend/
├── app.py                     # Main Flask application with multi-LOB support
├── requirements.txt           # Python dependencies
├── planogram_services/        # NEW: Modular planogram generators
│   ├── planogram_manager.py   # Central job management
│   ├── cases_covers_generator.py    # Cases & Covers planograms
│   ├── ipad_accessories_generator.py # iPad planograms (5-row system)
│   └── ipad_integration.py    # iPad integration layer
├── output/                    # Generated planogram files
└── static/                    # Static assets

Key Connections in app.py:
- Line 219: build_store_master() → Uses store_reference.json
- Line 712: generate_planograms() → Multi-LOB job management
- Line 947: create_intelligent_cases_planogram() → Enhanced generator
- NEW: iPad integration with TPA brand filtering
```

### Data Processing
```
src/
├── data_processing/
│   └── data_loader.py         # Loads 1,125+ products from 4 CSV files
├── visualization/
│   ├── enhanced_retail_planogram.py  # Enhanced visual generator
│   └── streamlined_planogram_generator.py # Alternative generator
└── models/
    └── product.py             # Product data models

Data Flow:
data_loader.py → product.py → multi-category generators → PNG output
```

### Store Reference System
```
data/
├── processed/
│   ├── store_reference.json   # Fast lookup (45+ stores)
│   ├── final_wall_configs.json # Wall configurations per store
│   └── cases_reference.json   # Cases & covers product reference
└── raw/
    ├── accessories/           # 4 CSV files with product data
    └── store_templates/       # Original CSV template

Generation:
create_store_reference.py → store_reference.json (one-time setup)
Wall configurations → final_wall_configs.json (dynamic)
```

### Multi-Category Planogram Generators
```
web-ui/backend/planogram_services/
├── planogram_manager.py       # Central coordination
├── cases_covers_generator.py  # Cases & Covers (enhanced retail style)
├── ipad_accessories_generator.py # iPad (5-row Apple/TPA system)
└── ipad_integration.py        # iPad integration layer

src/visualization/
├── enhanced_retail_planogram.py    # Enhanced visual generator
└── streamlined_planogram_generator.py # Alternative approach
```

---

## 🔌 API ENDPOINTS

### Store Management
```
GET  /api/stores                           # List all available stores
GET  /api/stores/{store_name}/lob-details  # Get store LOB configuration
POST /api/stores/{store_name}/save-wall-config  # Save wall configuration
GET  /api/stores/{store_name}/recommendations   # Get optimization recommendations
GET  /api/stores/{store_name}/final-config # Get finalized wall configuration
```

### Planogram Generation (Multi-LOB Support)
```
POST /api/stores/{store_name}/generate-planograms
Request: {
  "selected_accessories": ["cases_covers", "ipad_accessories", "mac_accessories"]
}
Response: {"success": true, "job_id": "uuid", "message": "started"}

GET  /api/jobs/{job_id}                    # Check generation status
GET  /output/{filename}                    # Serve generated planogram files (auto-path resolution)
```

### System Information
```
GET  /api/system/info                      # System health and available stores
GET  /api/stores/analysis                  # Store metadata for UI dropdowns
GET  /api/wall-configs                     # Get all wall configurations
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

### Multi-Category Planogram Generator Functions

#### Cases & Covers Generator
```python
EnhancedPlanogramGenerator.create_intelligent_cases_planogram()
# Main entry point - generates all walls with series allocation

allocate_walls_by_series(products, num_walls)
# Distributes products across walls by iPhone series

create_retail_style_layout(products, wall_num, store_type)
# Creates realistic retail-style visual layout
```

#### iPad Accessories Generator (NEW)
```python
IPadAccessoriesGenerator.generate_store_planograms(store_name, num_walls)
# Main entry point for iPad planogram generation

create_ipad_grid_generation_system(products)
# Creates 5-row grid with Apple/TPA allocation

_generate_single_wall_mixed(products, store_name)
# Single wall strategy: Half Apple, 2 rows Gripp, 1 row other TPA

_generate_two_wall_apple_tpa_split(products, store_name)
# Two wall strategy: Wall 1 Apple/TPA split, Wall 2 TPA-focused

_generate_multi_wall_apple_tpa_strategy(products, store_name, num_walls)
# Multi-wall strategy: 2 Apple/TPA walls + TPA-only walls

filter_tpa_brands(products)
# Filters to approved TPA brands: Gripp, Pulse, Tekne only
```

#### Visual Enhancement
```python
draw_phone_rectangle(ax, x, y, width, height, product, color)
# Draws phone-shaped rectangles instead of squares

categorize_by_series(products)
# Groups products by iPhone series (Base, Plus, Pro, Pro Max)

apply_brand_priority(products)
# Ensures Apple gets 50% placement in top rows

generate_ipad_planogram_visual(grid, store_name, wall_number, output_path)
# Creates visual iPad planogram with 5-row layout
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

# Generate planogram for a store (Multi-LOB)
curl -X POST http://localhost:5000/api/stores/imagine-ub-city-bengaluru/generate-planograms \
  -H "Content-Type: application/json" \
  -d '{"selected_accessories": ["cases_covers", "ipad_accessories", "mac_accessories"]}'

# Generate iPad-only planogram
curl -X POST http://localhost:5000/api/stores/imagine-ub-city-bengaluru/generate-planograms \
  -H "Content-Type: application/json" \
  -d '{"selected_accessories": ["ipad_accessories"]}'

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

### Test iPad Accessories Generator (NEW)
```bash
# Test iPad planogram generation
python -c "
from web-ui.backend.planogram_services.ipad_accessories_generator import IPadAccessoriesGenerator
from src.data_processing.data_loader import DataLoader

loader = DataLoader()
products = loader.load_ipad_accessories()
print(f'Loaded {len(products)} iPad products')

# Filter to TPA brands only
tpa_products = [p for p in products if p.brand in ['Gripp', 'Pulse', 'Tekne']]
print(f'TPA products: {len(tpa_products)}')

generator = IPadAccessoriesGenerator()
result = generator.generate_store_planograms('test_store', 2)
print('iPad Result:', result)
"
```

### Test TPA Brand Filtering
```bash
# Verify TPA brand filtering
python -c "
from src.data_processing.data_loader import DataLoader

loader = DataLoader()
products = loader.load_all_accessories()

# Check all brands
all_brands = set(p.brand for p in products)
print('All brands:', sorted(all_brands))

# Check TPA filtering
approved_tpa = {'Gripp', 'Pulse', 'Tekne'}
tpa_products = [p for p in products if p.brand in approved_tpa]
print(f'Approved TPA products: {len(tpa_products)}')

excluded_brands = all_brands - approved_tpa - {'Apple'}
print('Excluded brands:', sorted(excluded_brands))
"
```

---

## 🌊 DATA FLOW

### Complete Multi-LOB Generation Process
```
1. Frontend Request → Flask API endpoint (Store + LOB Selection)
2. Flask → Multi-LOB Job Management (async)
3. Job Manager → Category-Specific Generators:
   ├── Cases & Covers Generator
   ├── iPad Accessories Generator (5-row system)
   ├── Mac Accessories Generator
   └── Audio/Watch/Cables Generators
4. Each Generator → DataLoader → 4+ CSV files → 1,125+ products
5. Products → TPA Brand Filtering (Gripp, Pulse, Tekne only)
6. Filtered Products → Category-Specific Processing
7. Processing → Visual Generation (category-optimized)
8. Visual Generation → PNG files (per wall, per LOB)
9. Flask → Automatic File Serving (path resolution)
10. Frontend → Real-time Display with job status
```

### iPad Accessories Flow (NEW)
```
1. iPad CSV Data → DataLoader.load_ipad_accessories()
2. Raw Products → TPA Brand Filtering
3. Filtered Products → Apple/TPA Categorization
4. Categories → 5-Row Grid Allocation:
   - Row 1: Apple iPad Cases (premium placement)
   - Row 2: Apple iPad Accessories
   - Row 3: TPA iPad Cases (Gripp priority)
   - Row 4: TPA iPad Accessories (Pulse, Tekne)
   - Row 5: Mixed TPA overflow
5. Grid → Visual Generation (no blank facings)
6. Visual → PNG Output (per wall)
```

### Store Lookup Flow
```
1. API Request with store_name
2. normalize_store_name() → Clean store name
3. load_store_reference() → Fast JSON lookup
4. store_reference.json → Store configuration
5. final_wall_configs.json → Wall allocation per LOB
6. Wall details → Multi-category planogram generation
```

### Visual Enhancement Flow
```
1. Raw products → categorize_by_series() / categorize_by_brand()
2. Categories → allocate_walls_by_series() / 5-row allocation
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

## � IPAD ACCESSORIES SYSTEM

### 5-Row Grid System (NEW)
```
Row 1: Apple iPad Cases (Premium placement)
Row 2: Apple iPad Accessories
Row 3: TPA iPad Cases (Gripp priority)
Row 4: TPA iPad Accessories (Pulse, Tekne)
Row 5: Mixed TPA brands and overflow
```

### Apple/TPA Allocation Strategy
- **1 Wall**: Half Apple, 2 rows Gripp, 1 row other TPA brands
- **2 Walls**: Wall 1 Apple/TPA split, Wall 2 TPA-focused
- **3+ Walls**: 2 walls Apple/TPA split, rest TPA-focused

### Key Features
- **No Blank Facings**: 100% grid utilization with intelligent product distribution
- **Brand Priority**: Apple products in top rows, TPA brands strategically placed
- **Series Integration**: Compatible with iPhone series allocation logic
- **Visual Consistency**: Same phone-rectangle styling as Cases & Covers

---

## 🏷️ TPA BRAND MANAGEMENT

### Approved TPA Brands (CRITICAL)
```
✅ Gripp    - Primary TPA brand (highest priority)
✅ Pulse    - Secondary TPA brand
✅ Tekne    - Tertiary TPA brand
❌ Hyphen   - EXCLUDED from planograms
❌ AT Minimal - EXCLUDED from planograms
❌ PG       - EXCLUDED from planograms
❌ UAG      - EXCLUDED from planograms
❌ Roskilde - EXCLUDED from planograms
```

### Brand Filtering Implementation
- **Automatic Filtering**: All generators filter to approved brands only
- **Priority Order**: Gripp → Pulse → Tekne for placement decisions
- **Memory Integration**: Brand preferences stored in system memory
- **Consistent Application**: Applied across all LOBs (Cases, iPad, etc.)

---

## ⚙️ WALL CONFIGURATION SYSTEM

### Dynamic Wall Allocation
```json
{
  "store_name": {
    "wall_counts": {
      "Cases & Covers": 3,
      "iPad Accessories": 2,
      "Mac Accessories": 1,
      "Audio Accessories": 2,
      "Watch Accessories": 1,
      "Adapters & Cables": 1
    },
    "total_walls": 10,
    "status": "finalized"
  }
}
```

### Configuration Management
- **Per-Store Customization**: Each store can have unique wall allocations
- **LOB-Specific Counts**: Independent wall counts per Line of Business
- **Real-time Updates**: Configuration changes reflected immediately
- **Validation**: Ensures total walls match store capacity

---

## 🆕 LATEST FEATURES & UPDATES

### Recent Additions (July 2025)
- ✅ **iPad Accessories Generator**: Complete 5-row system with Apple/TPA allocation
- ✅ **TPA Brand Filtering**: Gripp, Pulse, Tekne only across all categories
- ✅ **Multi-LOB Support**: Cases, iPad, Mac, Audio, Watch, Cables
- ✅ **Wall Configuration Management**: Dynamic per-store allocation
- ✅ **File Serving Fix**: Automatic path resolution for generated files
- ✅ **Project Cleanup**: Removed 100+ unnecessary files for better performance
- ✅ **Local Indexing**: Created searchable local codebase index
- ✅ **Memory System**: TPA brand preferences and planogram logic stored

### System Optimizations
- **Async Job Processing**: Non-blocking planogram generation
- **Modular Architecture**: Separate generators per LOB category
- **Enhanced Error Handling**: Better debugging and status reporting
- **Performance Improvements**: Faster generation and file serving

### Frontend Enhancements
- **React/TypeScript**: Modern frontend with type safety
- **Store Selector**: Interactive store selection with wall configuration
- **Real-time Status**: Live job progress tracking
- **Multi-LOB Selection**: Choose multiple categories for generation

---

## 📈 STATUS & HEALTH CHECK

### Current System Status
- ✅ **DataLoader**: Working (1,125+ products loaded)
- ✅ **Multi-Category Generators**: Cases, iPad, Mac, Audio, Watch, Cables
- ✅ **Store Reference**: Optimized JSON system (45+ stores)
- ✅ **Backend API**: Flask server with async job processing
- ✅ **Visual Enhancements**: Phone rectangles, series allocation, brand grouping
- ✅ **TPA Brand Filtering**: Gripp, Pulse, Tekne only
- ✅ **iPad 5-Row System**: No blank facings, Apple/TPA allocation
- ✅ **Wall Configuration**: Dynamic per-store management
- ✅ **Frontend**: React/TypeScript with modern UI

### Latest Improvements
- **iPad Accessories**: Complete 5-row system with strategic brand placement
- **TPA Brand Management**: Strict filtering to approved brands only
- **Multi-LOB Architecture**: Modular generators for all product categories
- **File Serving**: Automatic path resolution and serving optimization
- **Project Structure**: Cleaned and optimized codebase

---

*Last Updated: July 31, 2025*
*Version: 3.0 - Multi-LOB System with iPad Integration*
