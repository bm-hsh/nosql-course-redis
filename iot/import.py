"""
IoT Use Case – Data Import into Redis
--------------------------------------

This script imports the Intel Berkeley Lab Sensor dataset into Redis
using a well-defined data model based on HASH, LIST, SORTED SET, and STRING structures.

Data Model implemented here:
• sensor:<mote_id>                   -> HASH containing sensor metadata (location, status)
• sensor:<mote_id>:readings          -> SORTED SET with timestamp as score (time series data)
• sensor:<mote_id>:latest            -> HASH with most recent reading values
• sensor:all                         -> SET of all sensor IDs
• sensor:avg:temperature             -> SORTED SET ranking sensors by avg temperature
• sensor:alerts                      -> LIST of alert messages (low battery, anomalies)

This script demonstrates:
• CREATE operations (HSET, ZADD, LPUSH, SADD)
• Time series modeling in Redis using Sorted Sets
• Real-time data patterns for IoT scenarios
"""

import csv
import redis
import os
import json
from datetime import datetime

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, db=0)

# Path to CSV data
DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

# Battery voltage threshold for alerts
LOW_BATTERY_THRESHOLD = 2.0

#############################################################
# 1. Import Sensor Metadata
#############################################################

def load_sensor_positions():
    """Load sensor positions from mote_locs.txt file."""
    positions = {}
    path = os.path.join(DATA_PATH, "mote_locs.txt")

    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        mote_id = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        positions[mote_id] = (x, y)
                    except ValueError:
                        continue
    return positions


def import_sensors():
    """Initialize sensor metadata in Redis."""
    print("Initializing sensor metadata...")

    # Load positions from file
    positions = load_sensor_positions()
    if positions:
        print(f"  -> Loaded {len(positions)} sensor positions from mote_locs.txt")

    for mote_id in range(1, 55):  # 54 sensors
        pos = positions.get(mote_id, (0.0, 0.0))

        # HASH representing a sensor
        r.hset(f"sensor:{mote_id}", mapping={
            "mote_id": mote_id,
            "pos_x": pos[0],
            "pos_y": pos[1],
            "status": "active",
            "type": "Mica2"
        })

        # Add to sensor index SET
        r.sadd("sensor:all", mote_id)

    print(f"  -> {54} sensors initialized.")


#############################################################
# 2. Import Sensor Readings (Time Series Data)
#############################################################

def import_readings(limit=None, batch_size=5000):
    """
    Import sensor readings from the dataset.

    Args:
        limit: Optional limit on number of records to import (for testing)
        batch_size: Number of operations to batch before executing (default 5000)
    """
    path = os.path.join(DATA_PATH, "data.txt")

    if not os.path.exists(path):
        print(f"Error: {path} not found. Please download the Intel Berkeley Lab dataset.")
        return

    print("Importing sensor readings...")
    count = 0
    skipped = 0
    temp_sums = {}
    temp_counts = {}
    alerts = []
    latest_readings = {}

    # Use pipeline for batch operations
    pipe = r.pipeline()
    pipe_count = 0

    with open(path, encoding="utf-8") as f:
        for line in f:
            if limit and count >= limit:
                break

            parts = line.strip().split()
            if len(parts) < 8:
                continue

            try:
                date_str = parts[0]
                time_str = parts[1]
                mote_id = int(parts[3])
                temperature = float(parts[4])
                humidity = float(parts[5])
                light = float(parts[6])
                voltage = float(parts[7])

                datetime_str = f"{date_str} {time_str.split('.')[0]}"
                dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                epoch = dt.timestamp()

            except (ValueError, IndexError):
                skipped += 1
                continue

            # Filter invalid readings
            if temperature < -40 or temperature > 60:
                skipped += 1
                continue
            if humidity < 0 or humidity > 100:
                skipped += 1
                continue
            if voltage < 0 or voltage > 3.5:
                skipped += 1
                continue

            reading = json.dumps({
                "temp": round(temperature, 2),
                "humidity": round(humidity, 2),
                "light": round(light, 2),
                "voltage": round(voltage, 3),
                "date": date_str,
                "time": time_str
            })

            # Add to pipeline instead of executing immediately
            pipe.zadd(f"sensor:{mote_id}:readings", {reading: epoch})
            pipe_count += 1

            # Track latest reading per sensor (will update at end)
            latest_readings[mote_id] = {
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2),
                "light": round(light, 2),
                "voltage": round(voltage, 3),
                "timestamp": epoch,
                "date": date_str,
                "time": time_str
            }

            # Track for average calculation
            if mote_id not in temp_sums:
                temp_sums[mote_id] = 0.0
                temp_counts[mote_id] = 0
            temp_sums[mote_id] += temperature
            temp_counts[mote_id] += 1

            # Collect alerts
            if voltage < LOW_BATTERY_THRESHOLD:
                alerts.append(f"Low battery on sensor {mote_id}: {voltage}V at {date_str} {time_str}")

            count += 1

            # Execute pipeline in batches
            if pipe_count >= batch_size:
                pipe.execute()
                pipe = r.pipeline()
                pipe_count = 0
                print(f"  -> {count} readings imported...")

    # Execute remaining items in pipeline
    if pipe_count > 0:
        pipe.execute()

    # Update latest readings and averages (smaller dataset, single pipeline)
    pipe = r.pipeline()
    for mote_id, data in latest_readings.items():
        pipe.hset(f"sensor:{mote_id}:latest", mapping=data)
    for mote_id, total in temp_sums.items():
        avg_temp = total / temp_counts[mote_id]
        pipe.zadd("sensor:avg:temperature", {mote_id: avg_temp})
    for alert in alerts[:1000]:  # Limit alerts to prevent memory issues
        pipe.lpush("sensor:alerts", alert)
    pipe.execute()

    print(f"  -> {count} readings imported ({skipped} skipped due to invalid data).")


#############################################################
# 3. Import Connectivity Data (Network Graph)
#############################################################

def import_connectivity():
    """
    Import sensor connectivity/network data.
    Stores transmission success probability between sensor pairs.
    """
    path = os.path.join(DATA_PATH, "connectivity.txt")

    if not os.path.exists(path):
        print("Connectivity data not found, skipping...")
        return

    print("Importing connectivity data...")
    count = 0

    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 3:
                continue

            try:
                from_sensor = int(parts[0])
                to_sensor = int(parts[1])
                probability = float(parts[2])
            except ValueError:
                continue

            # Store as HASH: connectivity from sensor A to sensor B
            r.hset(f"sensor:{from_sensor}:connectivity", str(to_sensor), probability)
            count += 1

    print(f"  -> {count} connectivity records imported.")


#############################################################

if __name__ == "__main__":
    print("=" * 50)
    print("IoT Use Case - Data Import")
    print("=" * 50)

    print("\nStep 1: Initializing sensors...")
    import_sensors()

    print("\nStep 2: Importing readings...")
    import_readings()

    print("\nStep 3: Importing connectivity...")
    import_connectivity()

    print("\n" + "=" * 50)
    print("Import finished successfully!")
    print("=" * 50)
