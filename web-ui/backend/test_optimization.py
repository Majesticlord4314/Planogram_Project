#!/usr/bin/env python3
"""
Test script to verify optimization jobs are working
"""

import time
import requests
import json

def test_backend():
    """Test the backend API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Backend API...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False
    
    # Test system info endpoint
    try:
        response = requests.get(f"{base_url}/api/system/info")
        if response.status_code == 200:
            data = response.json()
            print("✅ System info endpoint working")
            print(f"   Data files: {data['data']['data_files']}")
            print(f"   LOB status: {data['data']['lob_status']}")
            print(f"   System health: {data['data']['system_health']}")
        else:
            print(f"❌ System info endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ System info endpoint error: {e}")
    
    # Test starting a cohort optimization
    try:
        print("\n🚀 Testing cohort optimization...")
        response = requests.post(f"{base_url}/api/optimize/cohort", 
                               json={"lob": "iPhone", "store_type": "flagship"})
        if response.status_code == 200:
            data = response.json()
            job_id = data['data']['job_id']
            print(f"✅ Cohort optimization started: {job_id}")
            
            # Monitor job progress
            for i in range(10):  # Check for 20 seconds
                time.sleep(2)
                job_response = requests.get(f"{base_url}/api/jobs/{job_id}")
                if job_response.status_code == 200:
                    job_data = job_response.json()['data']
                    status = job_data['status']
                    progress = job_data['progress']
                    print(f"   Job {job_id[:8]}: {status} ({progress}%)")
                    
                    if status in ['completed', 'failed']:
                        break
                else:
                    print(f"   Error checking job status: {job_response.status_code}")
                    break
        else:
            print(f"❌ Cohort optimization failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Cohort optimization error: {e}")
    
    return True

if __name__ == "__main__":
    test_backend()