"""
E-Commerce Use Case – CRUD Operations & Queries in Redis
---------------------------------------------------------

This script demonstrates:
• CRUD operations (Create, Read, Update, Delete)
• Analytical queries on Redis structures
• Use of HASH, LIST, and SORTED SET structures.

Implemented on data created by import.py
"""

import redis
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
    print(f"Order {order_id} created.")


#############################################################
# R = READ
#############################################################

def get_order(order_id):
    """Retrieve a single order."""
    data = r.hgetall(f"order:{order_id}")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_customer_orders(customer_id, limit=10):
    """List all orders of a customer."""
    order_ids = r.lrange(f"customer:{customer_id}:orders", 0, limit-1)
    print(f"Orders for customer {customer_id}:")
    for oid in order_ids:
        print(" -", oid.decode())


#############################################################
# U = UPDATE
#############################################################

def update_order_status(order_id, new_status):
    """Change the status of an order."""
    r.hset(f"order:{order_id}", "status", new_status)
    print(f"Order {order_id} updated to status '{new_status}'.")


#############################################################
# D = DELETE
#############################################################

def delete_order(order_id):
    """Delete an order and remove it from customer's order list."""
    customer_id = r.hget(f"order:{order_id}", "customer_id")
    if customer_id:
        r.lrem(f"customer:{customer_id.decode()}:orders", 0, order_id)

    r.delete(f"order:{order_id}")
    print(f"Order {order_id} deleted.")


#############################################################
# ANALYTICAL QUERIES
#############################################################

def top_products(n=10):
    print("\nTop selling products:")
    for pid, score in r.zrevrange("product:sales", 0, n-1, withscores=True):
        print(pid.decode(), int(score))


#############################################################

if __name__ == "__main__":
    # Example usage (you can comment/uncomment as needed)
    top_products()
    get_customer_orders("00005e8ea7c7dc6b1e5fd57f5f9f7c6d")

    # CRUD demo:
    create_order("test123", "00005e8ea7c7dc6b1e5fd57f5f9f7c6d")
    print(get_order("test123"))
    update_order_status("test123", "shipped")
    delete_order("test123")
