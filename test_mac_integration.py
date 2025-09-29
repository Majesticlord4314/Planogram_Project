#!/usr/bin/env python3
"""
Test script for Mac accessories integration in the website
"""

import sys
import os
from pathlib import Path

# Add the web-ui backend to Python path
sys.path.append(str(Path(__file__).parent / "web-ui" / "backend"))

try:
    from planogram_services.mac_integration import MacIntegration
    from planogram_services.mac_accessories_generator import MacAccessoriesGenerator
    
    print("✅ Successfully imported Mac integration modules")
    
    # Test Mac integration
    mac_integration = MacIntegration()
    print("✅ Mac integration initialized")
    
    # Test Mac accessories generator
    mac_generator = MacAccessoriesGenerator()
    print("✅ Mac accessories generator initialized")
    
    # Test planogram generation
    print("\n🎨 Testing planogram generation...")
    
    store_name = "IMAGINE KORAMANGALA BENGALURU (BANGALORE)"
    wall_config = {"Mac Accessories": 1}
    
    # Generate planogram
    results = mac_integration.generate_mac_planograms(
        store_name=store_name,
        wall_config=wall_config,
        selected_categories=['mac_accessories']
    )
    
    print(f"✅ Generated {len(results)} planogram(s)")
    for key, path in results.items():
        print(f"   - {key}: {path}")
    
    # Test category info
    category_info = mac_integration.get_mac_category_info()
    print(f"\n📊 Available categories: {len(category_info)}")
    for cat, info in category_info.items():
        print(f"   - {info['name']}: {info['description']}")
    
    # Test wall recommendations
    recommendations = mac_integration.get_mac_wall_recommendations('standard')
    print(f"\n🏪 Wall recommendations for standard store: {recommendations}")
    
    print("\n🎉 All tests passed! Mac integration is ready for the website.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available")
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()