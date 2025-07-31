"""
Test script for Mac Accessories Planogram System
Tests the complete Mac accessories and bags/sleeves generation system.
"""

import sys
import os
from pathlib import Path

# Add the web-ui backend to the path
sys.path.append(str(Path(__file__).parent / "web-ui" / "backend"))

def test_mac_accessories_generator():
    """Test the Mac accessories generator"""
    print("🧪 Testing Mac Accessories Generator...")
    
    try:
        from planogram_services.mac_accessories_generator import MacAccessoriesGenerator
        
        # Initialize generator
        generator = MacAccessoriesGenerator()
        print("✅ Mac accessories generator initialized successfully")
        
        # Test data loading
        products, cohorts_df = generator.load_mac_data()
        print(f"✅ Loaded {len(products)} Mac products and {len(cohorts_df)} cohort entries")
        
        # Test TPA brand filtering
        filtered_products = generator.filter_tpa_brands(products)
        print(f"✅ Filtered to {len(filtered_products)} TPA brand products")
        
        # Test dimensional categorization
        dim_categories = generator.categorize_by_dimensions(filtered_products)
        for category, items in dim_categories.items():
            print(f"   - {category}: {len(items)} products")
        
        # Test single wall generation
        test_store = "Test_Store_Mac"
        results = generator.generate_store_planograms(test_store, 1)
        print(f"✅ Generated {len(results)} single-wall planograms")
        
        # Test multi-wall generation
        results_multi = generator.generate_store_planograms(test_store, 3)
        print(f"✅ Generated {len(results_multi)} three-wall planograms")
        
        return True
        
    except Exception as e:
        print(f"❌ Mac accessories generator test failed: {e}")
        return False

def test_bags_sleeves_generator():
    """Test the bags & sleeves generator"""
    print("\n🧪 Testing Bags & Sleeves Generator...")
    
    try:
        from planogram_services.bags_sleeves_generator import BagsSleevesGenerator
        
        # Initialize generator
        generator = BagsSleevesGenerator()
        print("✅ Bags & sleeves generator initialized successfully")
        
        # Test data loading
        products = generator.load_bags_sleeves_data()
        print(f"✅ Loaded {len(products)} bags & sleeves products")
        
        # Test brand filtering
        filtered_products = generator.filter_approved_brands(products)
        print(f"✅ Filtered to {len(filtered_products)} approved brand products")
        
        # Test planogram generation
        test_store = "Test_Store_Bags"
        result_path = generator.generate_enhanced_bags_sleeves_planogram(test_store)
        print(f"✅ Generated bags & sleeves planogram: {result_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bags & sleeves generator test failed: {e}")
        return False

def test_mac_integration():
    """Test the Mac integration layer"""
    print("\n🧪 Testing Mac Integration Layer...")
    
    try:
        from planogram_services.mac_integration import MacIntegration
        
        # Initialize integration
        integration = MacIntegration()
        print("✅ Mac integration initialized successfully")
        
        # Test wall recommendations
        recommendations = integration.get_mac_wall_recommendations('standard')
        print(f"✅ Wall recommendations: {recommendations}")
        
        # Test category info
        category_info = integration.get_mac_category_info()
        print(f"✅ Category info for {len(category_info)} categories")
        
        # Test product statistics
        stats = integration.get_mac_product_stats()
        print(f"✅ Product statistics: {stats}")
        
        # Test planogram generation
        test_store = "Test_Store_Integration"
        wall_config = {'Mac Accessories': 2}
        results = integration.generate_mac_planograms(
            store_name=test_store,
            wall_config=wall_config,
            selected_categories=['mac_accessories', 'bags_sleeves']
        )
        print(f"✅ Generated {len(results)} integrated planograms")
        
        return True
        
    except Exception as e:
        print(f"❌ Mac integration test failed: {e}")
        return False

def test_planogram_manager_integration():
    """Test Mac integration with planogram manager"""
    print("\n🧪 Testing Planogram Manager Integration...")
    
    try:
        from planogram_services.planogram_manager import PlanogramManager
        
        # Initialize manager with project root
        project_root = Path(__file__).parent
        manager = PlanogramManager(project_root)
        print("✅ Planogram manager initialized successfully")
        
        # Check if Mac generator is available
        generators = manager._init_generators()
        if 'Mac Accessories' in generators and generators['Mac Accessories'] is not None:
            print("✅ Mac Accessories generator is registered in planogram manager")
        else:
            print("❌ Mac Accessories generator not found in planogram manager")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Planogram manager integration test failed: {e}")
        return False

def test_data_files():
    """Test that all required data files exist"""
    print("\n🧪 Testing Data File Availability...")
    
    required_files = [
        "data/raw/accessories/mac-accessories-transformed.csv",
        "data/raw/cohorts/mac_planogram_cohorts.csv",
        "data/processed/planogram_sleeves_bags.csv"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🚀 Starting Mac Accessories Planogram System Tests\n")
    
    # Test data files first
    data_ok = test_data_files()
    if not data_ok:
        print("\n❌ Data files missing - some tests may fail")
    
    # Run component tests
    tests = [
        test_mac_accessories_generator,
        test_bags_sleeves_generator,
        test_mac_integration,
        test_planogram_manager_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print(f"   - Data Files: {'✅' if data_ok else '❌'}")
    print(f"   - Mac Accessories Generator: {'✅' if results[0] else '❌'}")
    print(f"   - Bags & Sleeves Generator: {'✅' if results[1] else '❌'}")
    print(f"   - Mac Integration Layer: {'✅' if results[2] else '❌'}")
    print(f"   - Planogram Manager Integration: {'✅' if results[3] else '❌'}")
    
    total_passed = sum([data_ok] + results)
    total_tests = 5
    
    print(f"\n🎯 Overall Result: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All tests passed! Mac accessories system is ready.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
