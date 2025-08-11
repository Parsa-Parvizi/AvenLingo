#!/usr/bin/env python3
"""
Simple Performance Test Script for Django Application
"""

import time
import requests
import statistics

def test_performance(url, iterations=5):
    """Test performance of a URL"""
    print(f"\n🔍 Testing performance for: {url}")
    print("=" * 50)
    
    response_times = []
    status_codes = []
    
    for i in range(iterations):
        start_time = time.time()
        try:
            response = requests.get(url, timeout=30)
            end_time = time.time()
            
            duration = end_time - start_time
            response_times.append(duration)
            status_codes.append(response.status_code)
            
            print(f"Request {i+1}: {duration:.3f}s - Status: {response.status_code}")
            
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
    
    if response_times:
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"\n📊 Performance Summary:")
        print(f"   Average: {avg_time:.3f}s")
        print(f"   Minimum: {min_time:.3f}s")
        print(f"   Maximum: {max_time:.3f}s")
        
        if avg_time < 0.5:
            print("   ✅ Excellent performance!")
        elif avg_time < 1.0:
            print("   ⚠️  Good performance")
        elif avg_time < 2.0:
            print("   ⚠️  Moderate performance")
        else:
            print("   ❌ Poor performance - needs optimization")
    
    return response_times

def main():
    """Main performance test function"""
    print("🚀 Django Performance Test Suite")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test different pages
    test_urls = [
        f"{base_url}/",
        f"{base_url}/course/",
        f"{base_url}/contact/",
    ]
    
    all_results = {}
    
    for url in test_urls:
        results = test_performance(url)
        all_results[url] = results
    
    # Overall summary
    print(f"\n🎯 Overall Performance Summary:")
    print("=" * 50)
    
    for url, results in all_results.items():
        if results:
            avg_time = statistics.mean(results)
            page_name = url.split('/')[-2] if url.split('/')[-2] else 'home'
            print(f"   {page_name:12}: {avg_time:.3f}s average")
    
    print(f"\n💡 Performance Tips:")
    print("   • Use Django Debug Toolbar to analyze queries")
    print("   • Enable caching for expensive operations")
    print("   • Optimize database queries with select_related/prefetch_related")
    print("   • Use database indexes for frequently queried fields")

if __name__ == "__main__":
    main() 