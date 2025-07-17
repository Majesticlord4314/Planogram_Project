#!/usr/bin/env python3
"""
Test script to verify the entire planogram pipeline works end-to-end
"""

import sys
import os
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.absolute()))
sys.path.insert(0, str(Path(__file__).parent / "web-ui" / "backend"))

def test_cohort_planogram_system():
    """Test the cohort planogram system"""
    print("Testing cohort planogram system...")
    
    try:
        from src.cohort_planogram.runner import CohortPlanogramRunner
        from src.cohort_planogram.data_loader import CohortDataLoader
        
        # Test data loader
        data_loader = CohortDataLoader()
        iphone_data = data_loader.get_lob_data('iPhone')
        print(f"SUCCESS: Loaded {len(iphone_data)} iPhone cohort records")
        
        # Test runner
        runner = CohortPlanogramRunner()
        print("SUCCESS: CohortPlanogramRunner initialized")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Cohort planogram system test failed: {e}")
        return False

def test_backend_integration():
    """Test the backend integration system"""
    print("Testing backend integration...")
    
    try:
        from integration import planogram_system, JobStatus
        from app import app
        
        # Test job creation
        job_id = planogram_system.create_job('cohort', {
            'lob': 'iPhone',
            'store_type': 'flagship'
        })
        
        print(f"SUCCESS: Created test job: {job_id}")
        
        # Test job retrieval
        job = planogram_system.get_job(job_id)
        if job and job.status == JobStatus.PENDING:
            print("SUCCESS: Job creation and retrieval works")
            return True
        else:
            print("ERROR: Job status incorrect")
            return False
            
    except Exception as e:
        print(f"ERROR: Backend integration test failed: {e}")
        return False

def test_file_manager():
    """Test the file manager system"""
    print("Testing file manager...")
    
    try:
        from file_manager import FileManager
        
        project_root = Path(__file__).parent.absolute()
        file_manager = FileManager(project_root)
        
        system_info = file_manager.get_system_info()
        print(f"SUCCESS: File manager works, project root: {system_info.get('project_root', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: File manager test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("PLANOGRAM PIPELINE END-TO-END TEST")
    print("=" * 60)
    
    tests = [
        ("Cohort Planogram System", test_cohort_planogram_system),
        ("Backend Integration", test_backend_integration),
        ("File Manager", test_file_manager)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"CRITICAL ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All pipeline components are working!")
        return 0
    else:
        print("ERROR: Some pipeline components have issues")
        return 1

if __name__ == "__main__":
    exit(main())