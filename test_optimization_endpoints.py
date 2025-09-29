#!/usr/bin/env python3
"""
Test script for the new optimization endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🧪 Testing {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', False)}")
            if result.get('success'):
                print(f"✅ {endpoint} working correctly")
                return result
            else:
                print(f"❌ {endpoint} returned success=False: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ {endpoint} failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing {endpoint}: {e}")
    
    return None

def main():
    print("🚀 Testing Mac Accessories Optimization Endpoints")
    
    # Test valid parameters endpoint
    params = test_endpoint("/api/validate/parameters")
    if params and params.get('success'):
        lobs = params['data']['lobs']
        print(f"Available LOBs: {lobs}")
        if 'Mac' in lobs:
            print("✅ Mac is available in LOBs")
        else:
            print("❌ Mac not found in LOBs")
    
    # Test Mac cohort optimization
    cohort_data = {
        "lob": "Mac",
        "store_type": "standard"
    }
    cohort_result = test_endpoint("/api/optimize/cohort", "POST", cohort_data)
    
    # Test Mac LOB optimization
    lob_data = {
        "lob": "Mac", 
        "store_type": "flagship",
        "strategy": "balanced"
    }
    lob_result = test_endpoint("/api/optimize/lob", "POST", lob_data)
    
    # Test full store optimization
    full_store_data = {
        "store_type": "standard",
        "strategy": "balanced"
    }
    full_store_result = test_endpoint("/api/optimize/full-store", "POST", full_store_data)
    
    # Test jobs endpoint
    jobs_result = test_endpoint("/api/jobs")
    if jobs_result and jobs_result.get('success'):
        jobs = jobs_result['data']['jobs']
        print(f"\n📋 Found {len(jobs)} jobs:")
        for job in jobs:
            print(f"  - {job['job_id']}: {job['job_type']} ({job['status']})")
    
    print("\n🎉 Mac Accessories optimization endpoints are ready!")

if __name__ == "__main__":
    main()