"""
NoSQL Course - Redis Use Cases
==============================

Interactive terminal menu to run and compare all 4 use cases.
"""

import redis
import subprocess
import sys
import os
import time

r = redis.Redis(host="localhost", port=6379, db=0)

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_menu_item(num, text, indent=2):
    print(f"{' '*indent}{Colors.YELLOW}[{num}]{Colors.END} {text}")


def wait_for_enter():
    input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")


#############################################################
# Statistics Functions
#############################################################

def get_ecommerce_stats():
    """Get E-Commerce statistics from Redis."""
    return {
        "name": "E-Commerce",
        "orders": r.scard("order:all"),
        "customers": r.scard("customer:all"),
        "products": r.scard("product:all"),
        "sellers": r.scard("seller:all")
    }


def get_iot_stats():
    """Get IoT statistics from Redis."""
    return {
        "name": "IoT",
        "sensors": r.scard("sensor:all"),
        "alerts": r.llen("sensor:alerts"),
        "readings": sum(r.zcard(f"sensor:{i}:readings") for i in range(1, 55))
    }


def get_movies_stats():
    """Get Movies statistics from Redis."""
    return {
        "name": "Movies",
        "movies": r.scard("movie:all"),
        "users": r.scard("user:all"),
        "top_rated": r.zcard("movie:top_rated"),
        "popular": r.zcard("movie:popular")
    }


def get_social_stats():
    """Get Social Media statistics from Redis."""
    return {
        "name": "Social Media",
        "posts": r.scard("post:all"),
        "users": r.scard("social:user:all"),
        "hashtags": r.zcard("hashtag:trending"),
        "trending_posts": r.zcard("post:trending")
    }


#############################################################
# Comparison View
#############################################################

def show_comparison():
    """Show comparison of all 4 use cases."""
    clear_screen()
    print_header("USE CASE COMPARISON")

    print(f"{Colors.BOLD}Fetching statistics from Redis...{Colors.END}\n")

    stats = []
    try:
        stats.append(get_ecommerce_stats())
    except:
        stats.append({"name": "E-Commerce", "error": True})

    try:
        stats.append(get_iot_stats())
    except:
        stats.append({"name": "IoT", "error": True})

    try:
        stats.append(get_social_stats())
    except:
        stats.append({"name": "Social Media", "error": True})

    try:
        stats.append(get_movies_stats())
    except:
        stats.append({"name": "Movies", "error": True})

    # Print comparison table
    print(f"{Colors.BOLD}{'Use Case':<15} {'Primary Entity':<18} {'Count':<12} {'Secondary':<15} {'Count':<10}{Colors.END}")
    print("-" * 70)

    # E-Commerce
    ec = stats[0]
    if "error" not in ec:
        print(f"{'E-Commerce':<15} {'Orders':<18} {ec['orders']:<12} {'Customers':<15} {ec['customers']:<10}")
        print(f"{'':<15} {'Products':<18} {ec['products']:<12} {'Sellers':<15} {ec['sellers']:<10}")
    else:
        print(f"{'E-Commerce':<15} {Colors.RED}No data imported{Colors.END}")

    # IoT
    iot = stats[1]
    if "error" not in iot:
        print(f"{'IoT':<15} {'Sensors':<18} {iot['sensors']:<12} {'Readings':<15} {iot['readings']:<10}")
        print(f"{'':<15} {'Alerts':<18} {iot['alerts']:<12}")
    else:
        print(f"{'IoT':<15} {Colors.RED}No data imported{Colors.END}")

    # Social Media
    sm = stats[2]
    if "error" not in sm:
        print(f"{'Social Media':<15} {'Posts':<18} {sm['posts']:<12} {'Users':<15} {sm['users']:<10}")
        print(f"{'':<15} {'Hashtags':<18} {sm['hashtags']:<12} {'Trending':<15} {sm['trending_posts']:<10}")
    else:
        print(f"{'Social Media':<15} {Colors.RED}No data imported{Colors.END}")

    # Movies
    mov = stats[3]
    if "error" not in mov:
        print(f"{'Movies':<15} {'Movies':<18} {mov['movies']:<12} {'Users':<15} {mov['users']:<10}")
        print(f"{'':<15} {'Top Rated':<18} {mov['top_rated']:<12} {'Popular':<15} {mov['popular']:<10}")
    else:
        print(f"{'Movies':<15} {Colors.RED}No data imported{Colors.END}")

    wait_for_enter()


#############################################################
# Import Functions
#############################################################

def is_use_case_imported(use_case):
    """Check if a use case already has data in Redis."""
    if use_case == "e_commerce":
        return r.scard("order:all") > 0
    elif use_case == "iot":
        return r.scard("sensor:all") > 0
    elif use_case == "social_media":
        return r.scard("post:all") > 0
    elif use_case == "movies":
        return r.scard("movie:all") > 0
    return False


def get_use_case_count(use_case):
    """Get primary entity count for a use case."""
    if use_case == "e_commerce":
        return r.scard("order:all"), "orders"
    elif use_case == "iot":
        return r.scard("sensor:all"), "sensors"
    elif use_case == "social_media":
        return r.scard("post:all"), "posts"
    elif use_case == "movies":
        return r.scard("movie:all"), "movies"
    return 0, "items"


def run_import(use_case):
    """Run import script for a use case."""
    clear_screen()
    print_header(f"IMPORTING {use_case.upper()} DATA")

    script_path = os.path.join(os.path.dirname(__file__), use_case, "import.py")

    if not os.path.exists(script_path):
        print(f"{Colors.RED}Error: {script_path} not found{Colors.END}")
        wait_for_enter()
        return

    # Check if already imported
    if is_use_case_imported(use_case):
        count, entity = get_use_case_count(use_case)
        print(f"{Colors.YELLOW}Already imported: {count} {entity} found in Redis.{Colors.END}\n")
        confirm = input(f"Re-import anyway? (y/N): ")
        if confirm.lower() != 'y':
            print(f"\n{Colors.CYAN}Import skipped.{Colors.END}")
            wait_for_enter()
            return

    print(f"Running: python {script_path}\n")

    # Run with timing
    start = time.perf_counter()
    subprocess.run([sys.executable, script_path])
    elapsed = time.perf_counter() - start

    # Show result
    count, entity = get_use_case_count(use_case)
    print(f"\n{Colors.GREEN}Import completed in {elapsed:.2f}s{Colors.END}")
    print(f"{Colors.GREEN}Total {entity} in Redis: {count}{Colors.END}")

    wait_for_enter()


def run_queries(use_case):
    """Run queries script for a use case."""
    clear_screen()
    print_header(f"RUNNING {use_case.upper()} QUERIES")

    script_path = os.path.join(os.path.dirname(__file__), use_case, "queries.py")

    if not os.path.exists(script_path):
        print(f"{Colors.RED}Error: {script_path} not found{Colors.END}")
        wait_for_enter()
        return

    print(f"Running: python {script_path}\n")
    subprocess.run([sys.executable, script_path])
    wait_for_enter()


def run_all_imports():
    """Run all import scripts with timing."""
    clear_screen()
    print_header("IMPORTING ALL USE CASES")

    use_cases = [
        ("e_commerce", "E-Commerce"),
        ("iot", "IoT"),
        ("social_media", "Social Media"),
        ("movies", "Movies")
    ]

    # Check what's already imported
    already_imported = []
    for folder, name in use_cases:
        if is_use_case_imported(folder):
            count, entity = get_use_case_count(folder)
            already_imported.append((name, count, entity))

    if already_imported:
        print(f"{Colors.YELLOW}Already imported:{Colors.END}")
        for name, count, entity in already_imported:
            print(f"  - {name}: {count} {entity}")
        print()
        confirm = input(f"Re-import all anyway? (y/N): ")
        if confirm.lower() != 'y':
            print(f"\n{Colors.CYAN}Import cancelled.{Colors.END}")
            wait_for_enter()
            return
        print()

    import_times = []
    total_start = time.perf_counter()

    for folder, name in use_cases:
        print(f"\n{Colors.BOLD}{Colors.CYAN}>>> {name.upper()}{Colors.END}\n")
        script_path = os.path.join(os.path.dirname(__file__), folder, "import.py")
        if os.path.exists(script_path):
            start = time.perf_counter()
            subprocess.run([sys.executable, script_path])
            elapsed = time.perf_counter() - start
            count, entity = get_use_case_count(folder)
            import_times.append((name, elapsed, count, entity))
            print(f"\n{Colors.GREEN}  -> {name} imported in {elapsed:.2f}s ({count} {entity}){Colors.END}")
        else:
            print(f"{Colors.RED}Script not found: {script_path}{Colors.END}")

    total_elapsed = time.perf_counter() - total_start

    # Show timing summary
    print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
    print(f"{Colors.BOLD}IMPORT TIME SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{'='*50}{Colors.END}")
    for name, elapsed, count, entity in import_times:
        print(f"  {name:<15} {elapsed:>8.2f}s  ({count} {entity})")
    print(f"  {'-'*40}")
    print(f"  {'TOTAL':<15} {total_elapsed:>8.2f}s")

    wait_for_enter()


def flush_redis():
    """Flush all Redis data."""
    clear_screen()
    print_header("FLUSH REDIS DATABASE")

    print(f"{Colors.RED}{Colors.BOLD}WARNING: This will delete ALL data in Redis!{Colors.END}\n")
    confirm = input("Type 'YES' to confirm: ")

    if confirm == "YES":
        r.flushdb()
        print(f"\n{Colors.GREEN}Redis database flushed successfully.{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}Operation cancelled.{Colors.END}")

    wait_for_enter()


def run_benchmark():
    """Run performance benchmark."""
    clear_screen()
    print_header("PERFORMANCE BENCHMARK")

    script_path = os.path.join(os.path.dirname(__file__), "benchmark.py")

    if not os.path.exists(script_path):
        print(f"{Colors.RED}Error: benchmark.py not found{Colors.END}")
        wait_for_enter()
        return

    print(f"Running: python benchmark.py\n")
    subprocess.run([sys.executable, script_path])
    wait_for_enter()


#############################################################
# Use Case Submenus
#############################################################

def use_case_menu(name, folder):
    """Show submenu for a specific use case."""
    while True:
        clear_screen()
        print_header(f"{name.upper()} USE CASE")

        print_menu_item(1, "Run Import (load data into Redis)")
        print_menu_item(2, "Run Queries (CRUD + Analytics)")
        print_menu_item(3, "Show Statistics")
        print_menu_item(0, "Back to Main Menu")

        choice = input(f"\n{Colors.CYAN}Select option: {Colors.END}")

        if choice == "1":
            run_import(folder)
        elif choice == "2":
            run_queries(folder)
        elif choice == "3":
            clear_screen()
            print_header(f"{name.upper()} STATISTICS")
            if folder == "e_commerce":
                stats = get_ecommerce_stats()
                print(f"Orders:    {stats['orders']}")
                print(f"Customers: {stats['customers']}")
                print(f"Products:  {stats['products']}")
                print(f"Sellers:   {stats['sellers']}")
            elif folder == "iot":
                stats = get_iot_stats()
                print(f"Sensors:  {stats['sensors']}")
                print(f"Readings: {stats['readings']}")
                print(f"Alerts:   {stats['alerts']}")
            elif folder == "movies":
                stats = get_movies_stats()
                print(f"Movies:    {stats['movies']}")
                print(f"Users:     {stats['users']}")
                print(f"Top Rated: {stats['top_rated']}")
            elif folder == "social_media":
                stats = get_social_stats()
                print(f"Posts:    {stats['posts']}")
                print(f"Users:    {stats['users']}")
                print(f"Hashtags: {stats['hashtags']}")
            wait_for_enter()
        elif choice == "0":
            break


#############################################################
# Main Menu
#############################################################

def main_menu():
    """Show main menu."""
    while True:
        clear_screen()
        print_header("NoSQL Course - Redis Use Cases")

        print(f"{Colors.BOLD}Select a Use Case:{Colors.END}\n")
        print_menu_item(1, "E-Commerce  (Olist Brazilian Dataset)")
        print_menu_item(2, "IoT         (Intel Berkeley Lab Sensors)")
        print_menu_item(3, "Social Media (Sentiment Analysis)")
        print_menu_item(4, "Movies      (MovieLens + TMDB)")

        print(f"\n{Colors.BOLD}Actions:{Colors.END}\n")
        print_menu_item(5, "Compare All Use Cases")
        print_menu_item(6, "Import All Use Cases (with timing)")
        print_menu_item(7, "Run Performance Benchmark")
        print_menu_item(8, "Flush Redis (delete all data)")
        print_menu_item(0, "Exit")

        choice = input(f"\n{Colors.CYAN}Select option: {Colors.END}")

        if choice == "1":
            use_case_menu("E-Commerce", "e_commerce")
        elif choice == "2":
            use_case_menu("IoT", "iot")
        elif choice == "3":
            use_case_menu("Social Media", "social_media")
        elif choice == "4":
            use_case_menu("Movies", "movies")
        elif choice == "5":
            show_comparison()
        elif choice == "6":
            run_all_imports()
        elif choice == "7":
            run_benchmark()
        elif choice == "8":
            flush_redis()
        elif choice == "0":
            clear_screen()
            print(f"{Colors.GREEN}Goodbye!{Colors.END}\n")
            break


#############################################################

if __name__ == "__main__":
    try:
        # Test Redis connection
        r.ping()
        main_menu()
    except redis.ConnectionError:
        print(f"{Colors.RED}Error: Cannot connect to Redis.{Colors.END}")
        print(f"Make sure Redis is running: docker compose up -d")
        sys.exit(1)
