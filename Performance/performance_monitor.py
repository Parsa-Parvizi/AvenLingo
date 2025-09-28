 #!/usr/bin/env python
"""
Performance monitoring script for English Teacher platform
"""
import os
import sys
import django
import time
import requests
from statistics import mean, median
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EnglishTeacher.settings')
django.setup()

from django.core.cache import cache
from django.db import connection
from django.test import Client
from django.urls import reverse
from django.core.management import execute_from_command_line


class PerformanceMonitor:
    """Performance monitoring and reporting"""
    
    def __init__(self, base_url='http://127.0.0.1:8000'):
        self.base_url = base_url
        self.client = Client()
        self.results = {}
    
    def measure_response_time(self, url, iterations=5):
        """Measure response time for a URL"""
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{url}", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    times.append(end_time - start_time)
                else:
                    print(f"❌ Error {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                print(f"❌ Request failed for {url}: {e}")
                continue
        
        if times:
            return {
                'mean': mean(times),
                'median': median(times),
                'min': min(times),
                'max': max(times),
                'samples': len(times)
            }
        return None
    
    def test_database_queries(self):
        """Test database query performance"""
        from course.models import Course
        from account.models import Teacher
        from account.models import User
        
        query_tests = {
            'course_filter': lambda: list(Course.objects.filter(is_active=True)[:10]),
            'teacher_with_user': lambda: list(Teacher.objects.select_related('user')[:10]),
            'user_lookup': lambda: User.objects.filter(email='test@example.com').first(),
        }
        
        results = {}
        for test_name, query_func in query_tests.items():
            connection.queries_log.clear()
            
            start_time = time.time()
            query_func()
            end_time = time.time()
            
            results[test_name] = {
                'time': end_time - start_time,
                'queries': len(connection.queries)
            }
        
        return results
    
    def test_cache_performance(self):
        """Test cache performance"""
        cache_tests = {
            'set_operation': lambda: cache.set('test_key', 'test_value', 300),
            'get_operation': lambda: cache.get('test_key'),
            'delete_operation': lambda: cache.delete('test_key'),
        }
        
        results = {}
        for test_name, cache_func in cache_tests.items():
            times = []
            for _ in range(100):  # Test 100 operations
                start_time = time.time()
                cache_func()
                end_time = time.time()
                times.append(end_time - start_time)
            
            results[test_name] = {
                'mean': mean(times),
                'median': median(times),
                'min': min(times),
                'max': max(times)
            }
        
        return results
    
    def test_memory_usage(self):
        """Test memory usage"""
        try:
            import psutil
            process = psutil.Process()
            
            return {
                'memory_percent': process.memory_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent()
            }
        except ImportError:
            print("⚠️  psutil not installed. Install with: pip install psutil")
            return None
    
    def run_full_performance_test(self):
        """Run complete performance test suite"""
        print("🔍 Starting Performance Analysis...")
        print("=" * 50)
        
        # Test response times
        print("\n📊 Testing Response Times...")
        urls_to_test = [
            '/',
            '/courses/',
            '/auth/login/',
            '/auth/register/student/',
        ]
        
        response_results = {}
        for url in urls_to_test:
            print(f"Testing {url}...")
            result = self.measure_response_time(url)
            if result:
                response_results[url] = result
                print(f"  ✅ Mean: {result['mean']:.3f}s, Median: {result['median']:.3f}s")
            else:
                print(f"  ❌ Failed to test {url}")
        
        self.results['response_times'] = response_results
        
        # Test database performance
        print("\n🗄️  Testing Database Performance...")
        db_results = self.test_database_queries()
        for test_name, result in db_results.items():
            print(f"  {test_name}: {result['time']:.3f}s ({result['queries']} queries)")
        self.results['database'] = db_results
        
        # Test cache performance
        print("\n⚡ Testing Cache Performance...")
        cache_results = self.test_cache_performance()
        for test_name, result in cache_results.items():
            print(f"  {test_name}: {result['mean']:.6f}s avg")
        self.results['cache'] = cache_results
        
        # Test memory usage
        print("\n💾 Testing Memory Usage...")
        memory_results = self.test_memory_usage()
        if memory_results:
            print(f"  Memory: {memory_results['memory_mb']:.1f}MB ({memory_results['memory_percent']:.1f}%)")
            print(f"  CPU: {memory_results['cpu_percent']:.1f}%")
            self.results['memory'] = memory_results
        
        return self.results
    
    def generate_report(self):
        """Generate performance report"""
        print("\n" + "=" * 50)
        print("📈 PERFORMANCE REPORT")
        print("=" * 50)
        
        # Response time analysis
        if 'response_times' in self.results:
            print("\n🌐 Response Time Analysis:")
            for url, stats in self.results['response_times'].items():
                status = "✅ GOOD" if stats['mean'] < 1.0 else "⚠️  SLOW" if stats['mean'] < 2.0 else "❌ CRITICAL"
                print(f"  {url}: {stats['mean']:.3f}s {status}")
        
        # Database performance analysis
        if 'database' in self.results:
            print("\n🗄️  Database Performance:")
            for test_name, stats in self.results['database'].items():
                status = "✅ GOOD" if stats['time'] < 0.1 else "⚠️  SLOW" if stats['time'] < 0.5 else "❌ CRITICAL"
                print(f"  {test_name}: {stats['time']:.3f}s ({stats['queries']} queries) {status}")
        
        # Cache performance analysis
        if 'cache' in self.results:
            print("\n⚡ Cache Performance:")
            for test_name, stats in self.results['cache'].items():
                status = "✅ GOOD" if stats['mean'] < 0.001 else "⚠️  SLOW"
                print(f"  {test_name}: {stats['mean']:.6f}s {status}")
        
        # Memory usage analysis
        if 'memory' in self.results:
            print("\n💾 Memory Usage:")
            memory = self.results['memory']
            mem_status = "✅ GOOD" if memory['memory_mb'] < 512 else "⚠️  HIGH" if memory['memory_mb'] < 1024 else "❌ CRITICAL"
            cpu_status = "✅ GOOD" if memory['cpu_percent'] < 50 else "⚠️  HIGH" if memory['cpu_percent'] < 80 else "❌ CRITICAL"
            print(f"  Memory: {memory['memory_mb']:.1f}MB {mem_status}")
            print(f"  CPU: {memory['cpu_percent']:.1f}% {cpu_status}")
        
        # Recommendations
        print("\n💡 Recommendations:")
        self._generate_recommendations()
        
        print("\n" + "=" * 50)
        print(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _generate_recommendations(self):
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Response time recommendations
        if 'response_times' in self.results:
            slow_pages = [url for url, stats in self.results['response_times'].items() if stats['mean'] > 1.0]
            if slow_pages:
                recommendations.append(f"🐌 Slow pages detected: {', '.join(slow_pages)}")
                recommendations.append("   Consider: caching, query optimization, or CDN")
        
        # Database recommendations
        if 'database' in self.results:
            slow_queries = [test for test, stats in self.results['database'].items() if stats['time'] > 0.1]
            if slow_queries:
                recommendations.append(f"🗄️  Slow database operations: {', '.join(slow_queries)}")
                recommendations.append("   Consider: adding indexes, query optimization, or connection pooling")
            
            high_query_count = [test for test, stats in self.results['database'].items() if stats['queries'] > 5]
            if high_query_count:
                recommendations.append(f"📊 High query count detected: {', '.join(high_query_count)}")
                recommendations.append("   Consider: select_related(), prefetch_related(), or query optimization")
        
        # Memory recommendations
        if 'memory' in self.results:
            if self.results['memory']['memory_mb'] > 512:
                recommendations.append("💾 High memory usage detected")
                recommendations.append("   Consider: memory profiling, data pagination, or caching strategy")
        
        if not recommendations:
            recommendations.append("✅ All systems performing within acceptable ranges!")
        
        for rec in recommendations:
            print(f"  {rec}")
    
    def save_results_to_file(self, filename=None):
        """Save results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'performance_report_{timestamp}.json'
        
        import json
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': self.results
            }, f, indent=2)
        
        print(f"📄 Results saved to: {filename}")


def main():
    """Main function to run performance monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance monitoring for English Teacher platform')
    parser.add_argument('--url', default='http://127.0.0.1:8000', help='Base URL to test')
    parser.add_argument('--iterations', type=int, default=5, help='Number of iterations for each test')
    parser.add_argument('--save', action='store_true', help='Save results to JSON file')
    parser.add_argument('--quick', action='store_true', help='Run quick test (fewer iterations)')
    
    args = parser.parse_args()
    
    if args.quick:
        args.iterations = 2
    
    monitor = PerformanceMonitor(base_url=args.url)
    
    try:
        results = monitor.run_full_performance_test()
        monitor.generate_report()
        
        if args.save:
            monitor.save_results_to_file()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Performance monitoring interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during performance monitoring: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()