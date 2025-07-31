#!/usr/bin/env python3
"""
Professional Planogram Service - Standalone API for generating professional planograms
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.planogram_v2.cases_data_processor import CasesDataProcessor
from src.planogram_v2.advanced_cases_plotter import AdvancedCasesPlanogramPlotter

# Create Flask application
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/professional-planograms/generate/<store_name>', methods=['POST'])
def generate_professional_planograms(store_name):
    """Generate professional retail-quality planograms for a store"""
    try:
        data = request.get_json() or {}
        accessories = data.get("selected_accessories", ["cases"])
        
        # Only process if Cases & Covers is selected
        if 'cases' not in [acc.lower() for acc in accessories]:
            return jsonify({
                "success": False, 
                "error": "Cases & Covers must be selected for professional planogram generation"
            })
        
        # Initialize components
        data_processor = CasesDataProcessor(str(project_root))
        advanced_plotter = AdvancedCasesPlanogramPlotter(str(project_root))
        
        # Load and process data
        print(f"Loading data for store: {store_name}")
        data_processor.load_cases_data()
        
        # Determine store size based on wall config
        config_file = project_root / 'store_wall_config.json'
        total_walls = 3  # Default
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                store_config = json.load(f)
            if store_name in store_config['stores']:
                cases_walls = store_config['stores'][store_name]['wall_allocation'].get('Cases & Covers', 3)
                total_walls = cases_walls
        
        print(f"Generating {total_walls} walls for {store_name}")
        
        # Generate wall layouts
        wall_layouts = data_processor.generate_wall_layouts(store_name, total_walls)
        
        # Create professional planograms
        generated_files = []
        planogram_files = []
        text_files = []
        
        for wall_name, wall_data in wall_layouts.items():
            if wall_data['total_products'] > 0:
                print(f"Creating planogram for {wall_name}")
                planogram_file, text_file = advanced_plotter.create_professional_planogram(
                    wall_data, wall_name, store_name, total_walls
                )
                planogram_files.append(planogram_file)
                text_files.append(text_file)
                generated_files.extend([planogram_file, text_file])
        
        # Generate summary
        summary = {
            "store_name": store_name,
            "generation_date": datetime.now().isoformat(),
            "total_walls": total_walls,
            "total_products": sum(layout['total_products'] for layout in wall_layouts.values()),
            "total_sales_capacity": sum(layout['total_capacity'] for layout in wall_layouts.values()),
            "planogram_files": [Path(f).name for f in planogram_files],
            "text_files": [Path(f).name for f in text_files],
            "wall_breakdown": {
                wall_name: {
                    "products": layout['total_products'],
                    "sales_capacity": layout['total_capacity'],
                    "series_distribution": layout['series_distribution'],
                    "category_distribution": layout['category_distribution']
                }
                for wall_name, layout in wall_layouts.items()
            }
        }
        
        return jsonify({
            "success": True,
            "generated_files": [Path(f).name for f in generated_files],
            "planogram_files": [Path(f).name for f in planogram_files],
            "text_files": [Path(f).name for f in text_files],
            "summary": summary,
            "message": f"Generated {len(planogram_files)} professional planograms for {store_name}"
        })
        
    except Exception as e:
        print(f"Error generating professional planograms: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": str(e),
            "message": "Failed to generate professional planograms"
        })

@app.route('/api/professional-planograms/files/<filename>')
def serve_planogram_file(filename):
    """Serve generated planogram files"""
    try:
        planogram_dir = project_root / 'output' / 'planograms_v2'
        return send_from_directory(planogram_dir, filename)
    except Exception as e:
        print(f"Error serving planogram file: {e}")
        return jsonify({"error": "File not found"}), 404

@app.route('/api/professional-planograms/stores')
def list_available_stores():
    """List available stores for planogram generation"""
    try:
        config_file = project_root / 'store_wall_config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                store_config = json.load(f)
            
            stores = []
            for store_name, data in store_config['stores'].items():
                stores.append({
                    "name": store_name,
                    "total_walls": data['total_walls'],
                    "cases_walls": data['wall_allocation'].get('Cases & Covers', 0),
                    "store_type": "large" if data['total_walls'] >= 4 else "medium" if data['total_walls'] == 3 else "small"
                })
            
            return jsonify({
                "success": True,
                "stores": stores
            })
        else:
            return jsonify({
                "success": False,
                "error": "Store configuration not found"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/professional-planograms/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Professional Planogram Service",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🎨 Professional Planogram Service Starting...")
    print(f"📁 Project root: {project_root}")
    print(f"🌐 Service will be available at: http://localhost:5001")
    print("📋 Available endpoints:")
    print("   POST /api/professional-planograms/generate/<store_name>")
    print("   GET  /api/professional-planograms/files/<filename>")
    print("   GET  /api/professional-planograms/stores")
    print("   GET  /api/professional-planograms/health")
    
    app.run(host='0.0.0.0', port=5001, debug=True)