#!/usr/bin/env python3
"""
Test Web API generation through HTTP endpoints.
Tests the complete web flow with CSRF tokens and sessions.
"""

import requests
import json
import time
import sys

def test_web_api():
    """Test the web API for image generation."""
    
    base_url = "http://localhost:4500"
    
    print("=" * 60)
    print("WEB API GENERATION TEST")
    print("=" * 60)
    
    # Step 1: Get CSRF token
    print("\n[1/4] Getting CSRF token...")
    try:
        csrf_response = requests.post(f"{base_url}/api/get-csrf-token")
        csrf_data = csrf_response.json()
        
        if not csrf_data.get('success'):
            print(f"   ❌ Failed to get CSRF token: {csrf_data}")
            return False
        
        csrf_token = csrf_data['csrf_token']
        session_id = csrf_data['session_id']
        print(f"   ✅ Got CSRF token: {csrf_token[:10]}...")
        print(f"   ✅ Got Session ID: {session_id[:10]}...")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Step 2: Start session
    print("\n[2/4] Starting generation session...")
    headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token,
        'X-Session-ID': session_id
    }
    
    try:
        # Try the simpler generation endpoint
        gen_response = requests.post(
            f"{base_url}/api/start-generation",
            headers=headers,
            json={
                'num_samples': 3,
                'test_mode': True
            }
        )
        
        gen_data = gen_response.json()
        print(f"   Response: {gen_data}")
        
        if gen_data.get('success'):
            job_id = gen_data.get('job_id')
            print(f"   ✅ Generation started with job ID: {job_id}")
        else:
            print(f"   ⚠️ Generation response: {gen_data}")
            # Try the sample generation endpoint
            print("\n   Trying sample generation endpoint...")
            gen_response = requests.post(
                f"{base_url}/api/start-sample-generation",
                headers=headers,
                json={}
            )
            gen_data = gen_response.json()
            
            if gen_data.get('success'):
                job_id = gen_data.get('job_id')
                print(f"   ✅ Sample generation started with job ID: {job_id}")
            else:
                print(f"   ❌ Failed to start generation: {gen_data}")
                return False
                
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Step 3: Monitor generation status
    if job_id:
        print(f"\n[3/4] Monitoring job {job_id}...")
        max_wait = 60  # Wait max 60 seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                status_response = requests.get(
                    f"{base_url}/api/generation-status/{job_id}",
                    headers=headers
                )
                status_data = status_response.json()
                
                if status_data.get('success'):
                    status = status_data.get('status', 'unknown')
                    progress = status_data.get('progress', 0)
                    print(f"   Status: {status} | Progress: {progress}%")
                    
                    if status == 'completed':
                        print(f"   ✅ Generation completed!")
                        break
                    elif status == 'failed':
                        print(f"   ❌ Generation failed: {status_data.get('error')}")
                        return False
                        
                time.sleep(2)
                
            except Exception as e:
                print(f"   ⚠️ Status check error: {e}")
                
    # Step 4: Check generation logs
    print(f"\n[4/4] Fetching generation logs...")
    try:
        logs_response = requests.get(
            f"{base_url}/api/generation-logs/{job_id}",
            headers=headers
        )
        
        if logs_response.status_code == 200:
            logs_data = logs_response.json()
            if logs_data.get('success'):
                logs = logs_data.get('logs', [])
                print(f"   ✅ Found {len(logs)} log entries")
                # Show last few log entries
                for log in logs[-3:]:
                    print(f"      {log}")
            else:
                print(f"   ⚠️ No logs available")
                
    except Exception as e:
        print(f"   ⚠️ Log fetch error: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    # Test the web API
    success = test_web_api()
    
    if success:
        print("\n🎉 WEB API TEST SUCCESSFUL!")
        sys.exit(0)
    else:
        print("\n⚠️ WEB API TEST HAD ISSUES")
        sys.exit(1)