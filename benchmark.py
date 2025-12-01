"""
Redis Performance Benchmark
============================

Measures and compares performance across all 4 use cases.
Run this AFTER importing data into Redis.
"""

import redis
import time
import json
import os

r = redis.Redis(host="localhost", port=6379, db=0)


def measure(name, func, iterations=1000):
    """Measure execution time of a function."""
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    elapsed = time.perf_counter() - start
    ops_per_sec = iterations / elapsed
    avg_ms = (elapsed / iterations) * 1000
    print(f"  {name:<40} {avg_ms:>8.3f} ms   {ops_per_sec:>10,.0f} ops/sec")
    return {"name": name, "avg_ms": avg_ms, "ops_per_sec": ops_per_sec}


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    print(f"  {'Operation':<40} {'Avg Time':>12} {'Throughput':>14}")
    print(f"  {'-'*40} {'-'*12} {'-'*14}")


#############################################################
# 1. Basic Redis Operations
#############################################################

def benchmark_basic_operations():
    """Benchmark basic Redis data structure operations."""
    print_header("BASIC REDIS OPERATIONS")

    # Prepare test data
    r.hset("bench:hash", mapping={"field1": "value1", "field2": "value2"})
    r.sadd("bench:set", *[f"member{i}" for i in range(100)])
    r.zadd("bench:zset", {f"member{i}": i for i in range(100)})
    r.lpush("bench:list", *[f"item{i}" for i in range(100)])
    r.set("bench:string", "test_value")

    results = []

    # STRING
    results.append(measure("GET (String)", lambda: r.get("bench:string")))
    results.append(measure("SET (String)", lambda: r.set("bench:string", "new_value")))

    # HASH
    results.append(measure("HGET (single field)", lambda: r.hget("bench:hash", "field1")))
    results.append(measure("HGETALL (all fields)", lambda: r.hgetall("bench:hash")))
    results.append(measure("HSET (single field)", lambda: r.hset("bench:hash", "field1", "x")))

    # SET
    results.append(measure("SISMEMBER (membership check)", lambda: r.sismember("bench:set", "member50")))
    results.append(measure("SMEMBERS (get all)", lambda: r.smembers("bench:set")))
    results.append(measure("SCARD (count)", lambda: r.scard("bench:set")))

    # SORTED SET
    results.append(measure("ZSCORE (get score)", lambda: r.zscore("bench:zset", "member50")))
    results.append(measure("ZRANGE (top 10)", lambda: r.zrange("bench:zset", 0, 9)))
    results.append(measure("ZREVRANGE (top 10 desc)", lambda: r.zrevrange("bench:zset", 0, 9)))
    results.append(measure("ZRANGEBYSCORE (range query)", lambda: r.zrangebyscore("bench:zset", 20, 50)))

    # LIST
    results.append(measure("LRANGE (first 10)", lambda: r.lrange("bench:list", 0, 9)))
    results.append(measure("LLEN (length)", lambda: r.llen("bench:list")))

    # Cleanup
    r.delete("bench:hash", "bench:set", "bench:zset", "bench:list", "bench:string")

    return results


#############################################################
# 2. Use Case Specific Benchmarks
#############################################################

def benchmark_ecommerce():
    """Benchmark E-Commerce use case operations."""
    print_header("E-COMMERCE USE CASE")

    results = []

    # Check if data exists
    if r.scard("order:all") == 0:
        print("  [!] No E-Commerce data found. Run import first.")
        return results

    # Get a sample order ID
    order_ids = list(r.srandmember("order:all", 10))
    if not order_ids:
        return results
    order_id = order_ids[0].decode()

    # Get a sample customer ID
    customer_ids = list(r.srandmember("customer:all", 10))
    customer_id = customer_ids[0].decode() if customer_ids else "1"

    results.append(measure("Get order details (HGETALL)",
        lambda: r.hgetall(f"order:{order_id}")))

    results.append(measure("Get customer info (HGETALL)",
        lambda: r.hgetall(f"customer:{customer_id}")))

    results.append(measure("Get customer orders (LRANGE)",
        lambda: r.lrange(f"customer:{customer_id}:orders", 0, -1)))

    results.append(measure("Check product exists (SISMEMBER)",
        lambda: r.sismember("product:all", "1")))

    results.append(measure("Count all orders (SCARD)",
        lambda: r.scard("order:all")))

    return results


def benchmark_iot():
    """Benchmark IoT use case operations."""
    print_header("IoT USE CASE")

    results = []

    if r.scard("sensor:all") == 0:
        print("  [!] No IoT data found. Run import first.")
        return results

    results.append(measure("Get sensor metadata (HGETALL)",
        lambda: r.hgetall("sensor:1")))

    results.append(measure("Get latest reading (ZREVRANGE 1)",
        lambda: r.zrevrange("sensor:1:readings", 0, 0)))

    results.append(measure("Get last 100 readings (ZREVRANGE)",
        lambda: r.zrevrange("sensor:1:readings", 0, 99)))

    results.append(measure("Get readings in time range (ZRANGEBYSCORE)",
        lambda: r.zrangebyscore("sensor:1:readings", 0, 1000000000)))

    results.append(measure("Get hottest sensors (ZREVRANGE)",
        lambda: r.zrevrange("sensor:avg:temperature", 0, 4, withscores=True)))

    results.append(measure("Get recent alerts (LRANGE)",
        lambda: r.lrange("sensor:alerts", 0, 9)))

    results.append(measure("Count all sensors (SCARD)",
        lambda: r.scard("sensor:all")))

    return results


def benchmark_movies():
    """Benchmark Movies use case operations."""
    print_header("MOVIES USE CASE")

    results = []

    if r.scard("movie:all") == 0:
        print("  [!] No Movies data found. Run import first.")
        return results

    results.append(measure("Get movie details (HGETALL)",
        lambda: r.hgetall("movie:1")))

    results.append(measure("Get movie genres (SMEMBERS)",
        lambda: r.smembers("movie:1:genres")))

    results.append(measure("Get movie cast (LRANGE)",
        lambda: r.lrange("movie:1:cast", 0, 9)))

    results.append(measure("Get top rated movies (ZREVRANGE)",
        lambda: r.zrevrange("movie:top_rated", 0, 9, withscores=True)))

    results.append(measure("Get movies by genre (SMEMBERS)",
        lambda: r.smembers("genre:drama:movies")))

    results.append(measure("Get user ratings (ZRANGE)",
        lambda: r.zrange("user:1:ratings", 0, -1, withscores=True)))

    results.append(measure("IMDB lookup (GET)",
        lambda: r.get("imdb:tt0114709")))

    results.append(measure("Count all movies (SCARD)",
        lambda: r.scard("movie:all")))

    return results


def benchmark_social_media():
    """Benchmark Social Media use case operations."""
    print_header("SOCIAL MEDIA USE CASE")

    results = []

    if r.scard("post:all") == 0:
        print("  [!] No Social Media data found. Run import first.")
        return results

    results.append(measure("Get post details (HGETALL)",
        lambda: r.hgetall("post:1")))

    results.append(measure("Get post hashtags (SMEMBERS)",
        lambda: r.smembers("post:1:hashtags")))

    results.append(measure("Get trending posts (ZREVRANGE)",
        lambda: r.zrevrange("post:trending", 0, 9, withscores=True)))

    results.append(measure("Get trending hashtags (ZREVRANGE)",
        lambda: r.zrevrange("hashtag:trending", 0, 9, withscores=True)))

    results.append(measure("Get posts by hashtag (SMEMBERS)",
        lambda: r.smembers("hashtag:tech:posts")))

    results.append(measure("Get posts by platform (SMEMBERS)",
        lambda: r.smembers("platform:twitter:posts")))

    results.append(measure("Get user posts (LRANGE)",
        lambda: r.lrange("social:user:user_1:posts", 0, 9)))

    results.append(measure("Count all posts (SCARD)",
        lambda: r.scard("post:all")))

    return results


#############################################################
# 3. Scalability Test
#############################################################

def benchmark_scalability():
    """Test how performance scales with data size."""
    print_header("SCALABILITY TEST (Write Performance)")

    sizes = [100, 1000, 10000]

    print(f"\n  Testing bulk insert performance...")
    print(f"  {'Records':<12} {'Total Time':>12} {'Records/sec':>14}")
    print(f"  {'-'*12} {'-'*12} {'-'*14}")

    for size in sizes:
        # Clean up
        for i in range(size):
            r.delete(f"bench:scale:{i}")

        # Measure insert time
        start = time.perf_counter()
        pipe = r.pipeline()
        for i in range(size):
            pipe.hset(f"bench:scale:{i}", mapping={
                "field1": f"value{i}",
                "field2": i,
                "field3": f"data{i}"
            })
        pipe.execute()
        elapsed = time.perf_counter() - start

        print(f"  {size:<12} {elapsed:>12.3f}s {size/elapsed:>14,.0f}")

        # Clean up
        for i in range(size):
            r.delete(f"bench:scale:{i}")


#############################################################
# 4. Memory Usage
#############################################################

def show_memory_usage():
    """Show Redis memory usage statistics."""
    print_header("MEMORY USAGE")

    info = r.info("memory")

    used_memory = info.get("used_memory_human", "N/A")
    used_memory_peak = info.get("used_memory_peak_human", "N/A")
    used_memory_dataset = info.get("used_memory_dataset", 0)

    print(f"  Current memory usage:     {used_memory}")
    print(f"  Peak memory usage:        {used_memory_peak}")
    print(f"  Dataset memory:           {used_memory_dataset / 1024 / 1024:.2f} MB")

    # Key count per use case
    print(f"\n  Keys per use case:")

    patterns = [
        ("E-Commerce", ["order:*", "customer:*", "product:*", "seller:*"]),
        ("IoT", ["sensor:*"]),
        ("Social Media", ["post:*", "hashtag:*", "platform:*", "sentiment:*"]),
        ("Movies", ["movie:*", "user:*", "genre:*", "actor:*", "director:*"]),
    ]

    for name, keys in patterns:
        total = 0
        for pattern in keys:
            count = len(list(r.scan_iter(pattern, count=10000)))
            total += count
        print(f"    {name:<15} {total:>10,} keys")

    print(f"\n  Total keys in database:   {r.dbsize():,}")


#############################################################
# 5. Latency Test
#############################################################

def benchmark_latency():
    """Measure operation latency percentiles."""
    print_header("LATENCY DISTRIBUTION (1000 HGETALL operations)")

    # Use a real key if available
    test_key = "movie:1" if r.exists("movie:1") else "sensor:1"
    if not r.exists(test_key):
        r.hset(test_key, mapping={"test": "data"})

    latencies = []
    for _ in range(1000):
        start = time.perf_counter()
        r.hgetall(test_key)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        latencies.append(elapsed)

    latencies.sort()

    print(f"  Min:        {latencies[0]:.3f} ms")
    print(f"  p50:        {latencies[500]:.3f} ms")
    print(f"  p90:        {latencies[900]:.3f} ms")
    print(f"  p99:        {latencies[990]:.3f} ms")
    print(f"  Max:        {latencies[-1]:.3f} ms")
    print(f"  Avg:        {sum(latencies)/len(latencies):.3f} ms")


#############################################################
# 6. Import Time Measurement
#############################################################

def benchmark_import_time():
    """Measure import times for each use case (requires fresh Redis)."""
    import subprocess
    import sys

    print_header("IMPORT TIME MEASUREMENT")
    print("  Note: Run this with empty Redis for accurate results.\n")

    use_cases = [
        ("E-Commerce", "e_commerce"),
        ("IoT", "iot"),
        ("Social Media", "social_media"),
        ("Movies", "movies"),
    ]

    results = []
    for name, folder in use_cases:
        script_path = os.path.join(os.path.dirname(__file__), folder, "import.py")
        if not os.path.exists(script_path):
            print(f"  {name:<15} Script not found")
            continue

        # Check if data exists
        data_path = os.path.join(os.path.dirname(__file__), folder, "data")
        if not os.path.exists(data_path):
            print(f"  {name:<15} No data folder")
            continue

        print(f"  {name:<15} Measuring...", end="", flush=True)
        start = time.perf_counter()
        try:
            subprocess.run([sys.executable, script_path],
                          capture_output=True, timeout=600)
            elapsed = time.perf_counter() - start
            print(f"\r  {name:<15} {elapsed:>10.2f}s")
            results.append((name, elapsed))
        except subprocess.TimeoutExpired:
            print(f"\r  {name:<15} Timeout (>10min)")
        except Exception as e:
            print(f"\r  {name:<15} Error: {e}")

    return results


#############################################################
# Main
#############################################################

if __name__ == "__main__":
    import sys
    import os

    print("\n" + "="*70)
    print("  REDIS PERFORMANCE BENCHMARK")
    print("  " + "="*66)

    try:
        r.ping()
    except redis.ConnectionError:
        print("\n  [ERROR] Cannot connect to Redis. Is it running?")
        print("  Start with: docker compose up -d")
        exit(1)

    # Check command line args
    if len(sys.argv) > 1 and sys.argv[1] == "--import":
        # Only run import benchmark
        benchmark_import_time()
    else:
        # Run all benchmarks
        benchmark_basic_operations()
        benchmark_ecommerce()
        benchmark_iot()
        benchmark_social_media()
        benchmark_movies()
        benchmark_scalability()
        show_memory_usage()
        benchmark_latency()

    print("\n" + "="*70)
    print("  BENCHMARK COMPLETE")
    print("="*70 + "\n")
