"""
E-Commerce Use Case – Data Import into Redis
--------------------------------------------

This script imports the Olist Brazilian E-Commerce dataset into Redis
using a well-defined data model based on HASH, LIST, and SORTED SET structures.

Data Model implemented here:
• customer:<customer_id>              -> HASH containing basic customer info
• customer:<customer_id>:orders       -> LIST of order IDs
• order:<order_id>                    -> HASH with order details
• order:<order_id>:items              -> LIST of product IDs
• product:<product_id>                -> HASH describing the product
• product:sales                       -> ZSET (ranking products by sales count)

This script demonstrates:
• CREATE operations (HSET, LPUSH, ZINCRBY)
• Example of modeling relational data in Redis
"""

import csv
import redis
import os

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, db=0)

# Path to CSV data
DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

#############################################################
# 1. Import Customers
#############################################################

def import_customers():
    path = os.path.join(DATA_PATH, "olist_customers_dataset.csv")
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            customer_id = row["customer_id"]

            # HASH representing a customer
            r.hset(f"customer:{customer_id}", mapping={
                "zip": row["customer_zip_code_prefix"],
                "city": row["customer_city"],
                "state": row["customer_state"]
            })


#############################################################
# 2. Import Orders
#############################################################

def import_orders():
    path = os.path.join(DATA_PATH, "olist_orders_dataset.csv")
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            order_id = row["order_id"]
            cid = row["customer_id"]

            # Order HASH
            r.hset(f"order:{order_id}", mapping={
                "customer_id": cid,
                "status": row["order_status"],
                "purchase_ts": row["order_purchase_timestamp"]
            })

            # LINK: order belongs to customer -> LIST
            r.lpush(f"customer:{cid}:orders", order_id)


#############################################################
# 3. Import Products
#############################################################

def import_products():
    path = os.path.join(DATA_PATH, "olist_products_dataset.csv")
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_id = row["product_id"]

            # Product HASH
            r.hset(f"product:{product_id}", mapping={
                "category": row["product_category_name"],
                "weight": row["product_weight_g"]
            })


#############################################################
# 4. Import Order Items
#############################################################

def import_order_items():
    path = os.path.join(DATA_PATH, "olist_order_items_dataset.csv")
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            order_id = row["order_id"]
            product_id = row["product_id"]

            # Add product to order item list
            r.lpush(f"order:{order_id}:items", product_id)

            # Record price in product hash
            r.hset(f"product:{product_id}", "price", row["price"])

            # Update sales ranking (ZSET)
            r.zincrby("product:sales", 1, product_id)


#############################################################

if __name__ == "__main__":
    print("Importing Customers...")
    import_customers()
    print("Importing Orders...")
    import_orders()
    print("Importing Products...")
    import_products()
    print("Importing Order Items...")
    import_order_items()
    print("Import finished successfully!")
