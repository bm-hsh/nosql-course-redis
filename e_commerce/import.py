"""
E-Commerce Use Case – Data Import into Redis
--------------------------------------------

This script imports the Olist Brazilian E-Commerce dataset into Redis
using a well-defined data model based on HASH, LIST, SET, and SORTED SET structures.

Data Model implemented here:
• customer:<customer_id>              -> HASH (zip, city, state)
• customer:<customer_id>:orders       -> LIST of order IDs
• order:<order_id>                    -> HASH (customer_id, status, timestamps, freight)
• order:<order_id>:items              -> LIST of product IDs
• order:<order_id>:payments           -> LIST of payment info (JSON)
• order:<order_id>:review             -> HASH (score, comment)
• product:<product_id>                -> HASH (category, weight, price)
• seller:<seller_id>                  -> HASH (city, state)
• product:sales                       -> ZSET (ranking by sales count)
• product:revenue                     -> ZSET (ranking by total revenue)
• category:revenue                    -> ZSET (ranking categories by revenue)
• order:status:<status>               -> SET of order IDs per status
• state:<state>:customers             -> SET of customer IDs per state
• review:scores                       -> ZSET (order_id by review score)

Uses Redis pipelines for fast bulk imports.
"""

import csv
import redis
import os
import json

r = redis.Redis(host="localhost", port=6379, db=0)
DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
BATCH_SIZE = 5000


#############################################################
# 1. Import Customers
#############################################################

def import_customers():
    path = os.path.join(DATA_PATH, "olist_customers_dataset.csv")
    if not os.path.exists(path):
        print("  -> Customers file not found, skipping...")
        return

    count = 0
    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            customer_id = row["customer_id"]
            state = row["customer_state"]

            pipe.hset(f"customer:{customer_id}", mapping={
                "zip": row["customer_zip_code_prefix"],
                "city": row["customer_city"],
                "state": state
            })
            pipe.sadd(f"state:{state}:customers", customer_id)
            pipe.sadd("customer:all", customer_id)
            pipe_count += 3
            count += 1

            if pipe_count >= BATCH_SIZE:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0

    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} customers imported.")


#############################################################
# 2. Import Orders
#############################################################

def import_orders():
    path = os.path.join(DATA_PATH, "olist_orders_dataset.csv")
    if not os.path.exists(path):
        print("  -> Orders file not found, skipping...")
        return

    count = 0
    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            order_id = row["order_id"]
            customer_id = row["customer_id"]
            status = row["order_status"]

            pipe.hset(f"order:{order_id}", mapping={
                "customer_id": customer_id,
                "status": status,
                "purchase_ts": row["order_purchase_timestamp"],
                "approved_ts": row.get("order_approved_at", ""),
                "delivered_carrier_ts": row.get("order_delivered_carrier_date", ""),
                "delivered_customer_ts": row.get("order_delivered_customer_date", ""),
                "estimated_delivery_ts": row.get("order_estimated_delivery_date", "")
            })
            pipe.lpush(f"customer:{customer_id}:orders", order_id)
            pipe.sadd(f"order:status:{status}", order_id)
            pipe.sadd("order:all", order_id)
            pipe_count += 4
            count += 1

            if pipe_count >= BATCH_SIZE:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0

    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} orders imported.")


#############################################################
# 3. Import Products
#############################################################

def import_products():
    path = os.path.join(DATA_PATH, "olist_products_dataset.csv")
    if not os.path.exists(path):
        print("  -> Products file not found, skipping...")
        return

    count = 0
    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_id = row["product_id"]
            category = row.get("product_category_name", "unknown")

            pipe.hset(f"product:{product_id}", mapping={
                "category": category,
                "weight": row.get("product_weight_g", "0"),
                "length": row.get("product_length_cm", "0"),
                "height": row.get("product_height_cm", "0"),
                "width": row.get("product_width_cm", "0")
            })
            pipe.sadd(f"category:{category}:products", product_id)
            pipe.sadd("product:all", product_id)
            pipe_count += 3
            count += 1

            if pipe_count >= BATCH_SIZE:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0

    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} products imported.")


#############################################################
# 4. Import Order Items (with freight)
#############################################################

def import_order_items():
    path = os.path.join(DATA_PATH, "olist_order_items_dataset.csv")
    if not os.path.exists(path):
        print("  -> Order items file not found, skipping...")
        return

    count = 0
    pipe = r.pipeline()
    pipe_count = 0

    # Track sales and revenue in memory, update at end
    product_sales = {}
    product_revenue = {}
    category_revenue = {}

    # First pass: get product categories
    product_categories = {}
    products_path = os.path.join(DATA_PATH, "olist_products_dataset.csv")
    if os.path.exists(products_path):
        with open(products_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                product_categories[row["product_id"]] = row.get("product_category_name", "unknown")

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            order_id = row["order_id"]
            product_id = row["product_id"]
            seller_id = row["seller_id"]
            price = float(row["price"])
            freight = float(row["freight_value"])

            pipe.lpush(f"order:{order_id}:items", product_id)
            pipe.hset(f"product:{product_id}", "price", price)
            pipe.hset(f"order:{order_id}", mapping={
                "freight_value": freight,
                "seller_id": seller_id
            })
            pipe_count += 3

            # Track in memory
            product_sales[product_id] = product_sales.get(product_id, 0) + 1
            product_revenue[product_id] = product_revenue.get(product_id, 0) + price

            category = product_categories.get(product_id, "unknown")
            category_revenue[category] = category_revenue.get(category, 0) + price

            count += 1

            if pipe_count >= BATCH_SIZE:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0

    if pipe_count > 0:
        pipe.execute()

    # Update rankings
    pipe = r.pipeline()
    for product_id, sales in product_sales.items():
        pipe.zadd("product:sales", {product_id: sales})
    for product_id, revenue in product_revenue.items():
        pipe.zadd("product:revenue", {product_id: revenue})
    for category, revenue in category_revenue.items():
        pipe.zadd("category:revenue", {category: revenue})
    pipe.execute()

    print(f"  -> {count} order items imported.")


#############################################################
# 5. Import Payments
#############################################################

def import_payments():
    path = os.path.join(DATA_PATH, "olist_order_payments_dataset.csv")
    if not os.path.exists(path):
        print("  -> Payments file not found, skipping...")
        return

    count = 0
    pipe = r.pipeline()
    pipe_count = 0
    payment_types = {}

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            order_id = row["order_id"]
            payment_type = row["payment_type"]

            payment = json.dumps({
                "type": payment_type,
                "installments": row["payment_installments"],
                "value": row["payment_value"]
            })

            pipe.lpush(f"order:{order_id}:payments", payment)
            pipe_count += 1

            # Track payment types
            if payment_type not in payment_types:
                payment_types[payment_type] = {}
            payment_types[payment_type][order_id] = payment_types[payment_type].get(order_id, 0) + 1

            count += 1

            if pipe_count >= BATCH_SIZE:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0

    if pipe_count > 0:
        pipe.execute()

    # Update payment type rankings
    pipe = r.pipeline()
    for ptype, orders in payment_types.items():
        for order_id, cnt in orders.items():
            pipe.zadd(f"payment:type:{ptype}", {order_id: cnt})
    pipe.execute()

    print(f"  -> {count} payments imported.")


#############################################################
# 6. Import Reviews
#############################################################

def import_reviews():
    path = os.path.join(DATA_PATH, "olist_order_reviews_dataset.csv")
    if not os.path.exists(path):
        print("  -> Reviews file not found, skipping...")
        return

    count = 0
    pipe = r.pipeline()
    pipe_count = 0
    score_distribution = {}

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            order_id = row["order_id"]
            try:
                score = int(row["review_score"])
            except:
                continue

            pipe.hset(f"order:{order_id}:review", mapping={
                "score": score,
                "comment_title": row.get("review_comment_title", ""),
                "comment": row.get("review_comment_message", "")[:500],
                "creation_date": row.get("review_creation_date", "")
            })
            pipe.zadd("review:scores", {order_id: score})
            pipe_count += 2

            score_distribution[score] = score_distribution.get(score, 0) + 1
            count += 1

            if pipe_count >= BATCH_SIZE:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0

    if pipe_count > 0:
        pipe.execute()

    # Update score distribution
    pipe = r.pipeline()
    for score, cnt in score_distribution.items():
        pipe.zadd("review:score:distribution", {str(score): cnt})
    pipe.execute()

    print(f"  -> {count} reviews imported.")


#############################################################
# 7. Import Sellers
#############################################################

def import_sellers():
    path = os.path.join(DATA_PATH, "olist_sellers_dataset.csv")
    if not os.path.exists(path):
        print("  -> Sellers file not found, skipping...")
        return

    count = 0
    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            seller_id = row["seller_id"]
            state = row["seller_state"]

            pipe.hset(f"seller:{seller_id}", mapping={
                "zip": row["seller_zip_code_prefix"],
                "city": row["seller_city"],
                "state": state
            })
            pipe.sadd(f"state:{state}:sellers", seller_id)
            pipe.sadd("seller:all", seller_id)
            pipe_count += 3
            count += 1

            if pipe_count >= BATCH_SIZE:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0

    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} sellers imported.")


#############################################################
# 8. Import Geolocation
#############################################################

def import_geolocation():
    path = os.path.join(DATA_PATH, "olist_geolocation_dataset.csv")
    if not os.path.exists(path):
        print("  -> Geolocation file not found, skipping...")
        return

    count = 0
    pipe = r.pipeline()
    pipe_count = 0
    seen_zips = set()

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            zip_code = row["geolocation_zip_code_prefix"]

            if zip_code in seen_zips:
                continue
            seen_zips.add(zip_code)

            pipe.hset(f"geo:{zip_code}", mapping={
                "lat": row["geolocation_lat"],
                "lng": row["geolocation_lng"],
                "city": row["geolocation_city"],
                "state": row["geolocation_state"]
            })
            pipe_count += 1
            count += 1

            if pipe_count >= BATCH_SIZE:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0

    if pipe_count > 0:
        pipe.execute()

    print(f"  -> {count} geolocations imported.")


#############################################################

if __name__ == "__main__":
    print("=" * 50)
    print("E-Commerce Use Case - Data Import")
    print("=" * 50)

    print("\nStep 1: Importing customers...")
    import_customers()

    print("\nStep 2: Importing orders...")
    import_orders()

    print("\nStep 3: Importing products...")
    import_products()

    print("\nStep 4: Importing order items...")
    import_order_items()

    print("\nStep 5: Importing payments...")
    import_payments()

    print("\nStep 6: Importing reviews...")
    import_reviews()

    print("\nStep 7: Importing sellers...")
    import_sellers()

    print("\nStep 8: Importing geolocation...")
    import_geolocation()

    print("\n" + "=" * 50)
    print("Import finished successfully!")
    print("=" * 50)
