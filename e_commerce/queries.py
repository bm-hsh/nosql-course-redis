"""
E-Commerce Use Case – CRUD Operations & Queries in Redis
---------------------------------------------------------

This script demonstrates:
• CRUD operations (Create, Read, Update, Delete)
• Analytical queries on Redis structures
• Use of HASH, LIST, SET, and SORTED SET structures.

Implemented on data created by import.py
"""

import redis
import json

r = redis.Redis(host="localhost", port=6379, db=0)


#############################################################
# C = CREATE
#############################################################

def create_order(order_id, customer_id, status="created"):
    """Create a new order and link it to a customer."""
    r.hset(f"order:{order_id}", mapping={
        "customer_id": customer_id,
        "status": status
    })
    r.lpush(f"customer:{customer_id}:orders", order_id)
    r.sadd(f"order:status:{status}", order_id)
    r.sadd("order:all", order_id)
    print(f"Order {order_id} created.")


def add_review(order_id, score, comment=""):
    """Add a review to an order."""
    r.hset(f"order:{order_id}:review", mapping={
        "score": score,
        "comment": comment[:500]
    })
    r.zadd("review:scores", {order_id: score})
    print(f"Review added for order {order_id}: {score} stars.")


#############################################################
# R = READ
#############################################################

def get_order(order_id):
    """Retrieve a single order."""
    data = r.hgetall(f"order:{order_id}")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_customer(customer_id):
    """Retrieve customer info."""
    data = r.hgetall(f"customer:{customer_id}")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_product(product_id):
    """Retrieve product info."""
    data = r.hgetall(f"product:{product_id}")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_customer_orders(customer_id, limit=10):
    """List orders of a customer."""
    order_ids = r.lrange(f"customer:{customer_id}:orders", 0, limit-1)
    return [oid.decode() for oid in order_ids]


def get_order_review(order_id):
    """Get review for an order."""
    data = r.hgetall(f"order:{order_id}:review")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_order_payments(order_id):
    """Get payments for an order."""
    payments = r.lrange(f"order:{order_id}:payments", 0, -1)
    return [json.loads(p.decode()) for p in payments]


def get_geolocation(zip_code):
    """Get coordinates for a zip code."""
    data = r.hgetall(f"geo:{zip_code}")
    return {k.decode(): v.decode() for k, v in data.items()}


#############################################################
# U = UPDATE
#############################################################

def update_order_status(order_id, new_status):
    """Change the status of an order."""
    old_status = r.hget(f"order:{order_id}", "status")
    if old_status:
        r.srem(f"order:status:{old_status.decode()}", order_id)

    r.hset(f"order:{order_id}", "status", new_status)
    r.sadd(f"order:status:{new_status}", order_id)
    print(f"Order {order_id} updated to status '{new_status}'.")


#############################################################
# D = DELETE
#############################################################

def delete_order(order_id):
    """Delete an order and all associated data."""
    order = get_order(order_id)
    customer_id = order.get("customer_id")
    status = order.get("status")

    if customer_id:
        r.lrem(f"customer:{customer_id}:orders", 0, order_id)
    if status:
        r.srem(f"order:status:{status}", order_id)

    r.srem("order:all", order_id)
    r.zrem("review:scores", order_id)
    r.delete(f"order:{order_id}")
    r.delete(f"order:{order_id}:items")
    r.delete(f"order:{order_id}:payments")
    r.delete(f"order:{order_id}:review")

    print(f"Order {order_id} deleted.")


#############################################################
# ANALYTICAL QUERIES - Products
#############################################################

def top_selling_products(n=10):
    """Get top selling products by quantity."""
    print(f"\nTop {n} selling products (by quantity):")
    results = r.zrevrange("product:sales", 0, n-1, withscores=True)
    for pid, count in results:
        product = get_product(pid.decode())
        category = product.get("category", "N/A")
        print(f"  {pid.decode()[:20]}...  {int(count):>5} sold  [{category}]")
    return results


def top_revenue_products(n=10):
    """Get top products by revenue."""
    print(f"\nTop {n} products by revenue:")
    results = r.zrevrange("product:revenue", 0, n-1, withscores=True)
    for pid, revenue in results:
        product = get_product(pid.decode())
        category = product.get("category", "N/A")
        print(f"  {pid.decode()[:20]}...  R${revenue:>10.2f}  [{category}]")
    return results


def top_categories(n=10):
    """Get top categories by revenue."""
    print(f"\nTop {n} categories by revenue:")
    results = r.zrevrange("category:revenue", 0, n-1, withscores=True)
    for category, revenue in results:
        print(f"  {category.decode():<30}  R${revenue:>12.2f}")
    return results


#############################################################
# ANALYTICAL QUERIES - Orders
#############################################################

def orders_by_status():
    """Get order count per status."""
    print("\nOrders by status:")
    statuses = ["delivered", "shipped", "processing", "canceled", "unavailable", "invoiced", "created", "approved"]
    results = {}
    for status in statuses:
        count = r.scard(f"order:status:{status}")
        if count > 0:
            results[status] = count
            print(f"  {status:<15} {count:>8} orders")
    return results


def get_order_count():
    """Get total number of orders."""
    return r.scard("order:all")


def get_customer_count():
    """Get total number of customers."""
    return r.scard("customer:all")


def get_product_count():
    """Get total number of products."""
    return r.scard("product:all")


def get_seller_count():
    """Get total number of sellers."""
    return r.scard("seller:all")


#############################################################
# ANALYTICAL QUERIES - Reviews
#############################################################

def review_score_distribution():
    """Get distribution of review scores."""
    print("\nReview score distribution:")
    results = r.zrange("review:score:distribution", 0, -1, withscores=True)
    total = sum(count for _, count in results)
    for score, count in sorted(results, key=lambda x: int(x[0].decode())):
        pct = (count / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {score.decode()} stars: {int(count):>6} ({pct:>5.1f}%) {bar}")
    return results


def average_review_score():
    """Calculate average review score."""
    results = r.zrange("review:score:distribution", 0, -1, withscores=True)
    total_score = sum(int(score.decode()) * count for score, count in results)
    total_count = sum(count for _, count in results)
    avg = total_score / total_count if total_count > 0 else 0
    print(f"\nAverage review score: {avg:.2f} / 5.0")
    return avg


def best_reviewed_orders(n=10):
    """Get orders with best reviews."""
    print(f"\nTop {n} best reviewed orders:")
    results = r.zrevrange("review:scores", 0, n-1, withscores=True)
    for order_id, score in results:
        print(f"  Order {order_id.decode()}: {int(score)} stars")
    return results


def worst_reviewed_orders(n=10):
    """Get orders with worst reviews."""
    print(f"\nTop {n} worst reviewed orders:")
    results = r.zrange("review:scores", 0, n-1, withscores=True)
    for order_id, score in results:
        review = get_order_review(order_id.decode())
        comment = review.get("comment", "")[:50]
        print(f"  Order {order_id.decode()}: {int(score)} star - {comment}...")
    return results


#############################################################
# ANALYTICAL QUERIES - Geographic
#############################################################

def customers_by_state(n=10):
    """Get customer count per state."""
    print(f"\nTop {n} states by customer count:")
    states = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF", "GO", "ES", "PE", "CE", "PA", "MT", "MA", "MS", "PB", "RN", "PI", "AL", "SE", "RO", "TO", "AC", "AP", "AM", "RR"]
    results = []
    for state in states:
        count = r.scard(f"state:{state}:customers")
        if count > 0:
            results.append((state, count))

    results.sort(key=lambda x: -x[1])
    for state, count in results[:n]:
        print(f"  {state}: {count:>8} customers")

    return results[:n]


def sellers_by_state(n=10):
    """Get seller count per state."""
    print(f"\nTop {n} states by seller count:")
    states = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF", "GO", "ES", "PE", "CE", "PA", "MT", "MA", "MS", "PB", "RN", "PI", "AL", "SE", "RO", "TO", "AC", "AP", "AM", "RR"]
    results = []
    for state in states:
        count = r.scard(f"state:{state}:sellers")
        if count > 0:
            results.append((state, count))

    results.sort(key=lambda x: -x[1])
    for state, count in results[:n]:
        print(f"  {state}: {count:>8} sellers")

    return results[:n]


#############################################################
# ANALYTICAL QUERIES - Freight
#############################################################

def analyze_freight_by_state(sample_size=1000):
    """Analyze average freight cost by customer state."""
    print("\nAverage freight by customer state (sample):")

    order_ids = list(r.srandmember("order:all", sample_size))
    state_freight = {}

    for order_id in order_ids:
        order = get_order(order_id.decode())
        freight = float(order.get("freight_value", 0))
        customer_id = order.get("customer_id", "")

        if customer_id:
            customer = get_customer(customer_id)
            state = customer.get("state", "")
            if state:
                if state not in state_freight:
                    state_freight[state] = []
                state_freight[state].append(freight)

    results = []
    for state, freights in state_freight.items():
        avg = sum(freights) / len(freights)
        results.append((state, avg, len(freights)))

    results.sort(key=lambda x: -x[1])
    for state, avg, count in results[:10]:
        print(f"  {state}: R${avg:>8.2f} avg freight ({count} orders)")

    return results


#############################################################

if __name__ == "__main__":
    print("=" * 50)
    print("E-Commerce Use Case - Queries Demo")
    print("=" * 50)

    # Statistics
    print(f"\nTotal orders: {get_order_count()}")
    print(f"Total customers: {get_customer_count()}")
    print(f"Total products: {get_product_count()}")
    print(f"Total sellers: {get_seller_count()}")

    # Order analysis
    orders_by_status()

    # Product analysis
    top_selling_products(5)
    top_revenue_products(5)
    top_categories(5)

    # Review analysis
    review_score_distribution()
    average_review_score()

    # Geographic analysis
    customers_by_state(5)
    sellers_by_state(5)

    # Freight analysis
    analyze_freight_by_state(500)

    # CRUD Demo
    print("\n" + "-" * 50)
    print("CRUD Demo")
    print("-" * 50)

    create_order("test123", "test_customer")
    print(f"Order: {get_order('test123')}")

    add_review("test123", 5, "Great product!")
    print(f"Review: {get_order_review('test123')}")

    update_order_status("test123", "shipped")
    print(f"After update: {get_order('test123')}")

    delete_order("test123")
    print(f"After delete: {get_order('test123')}")
