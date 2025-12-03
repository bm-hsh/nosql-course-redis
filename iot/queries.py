"""
IoT Use Case – CRUD Operations & Queries in Redis
--------------------------------------------------

This script demonstrates:
• CRUD operations (Create, Read, Update, Delete)
• Time series queries (range queries, aggregations)
• Analytical queries on IoT sensor data
• Use of HASH, LIST, SORTED SET, and SET structures.

Implemented on data created by import.py
"""

import redis
import json
from datetime import datetime

r = redis.Redis(host="localhost", port=6379, db=0)


#############################################################
# C = CREATE
#############################################################

def create_sensor(mote_id, pos_x=0.0, pos_y=0.0, sensor_type="Mica2"):
    """Register a new sensor in the system."""
    r.hset(f"sensor:{mote_id}", mapping={
        "mote_id": mote_id,
        "pos_x": pos_x,
        "pos_y": pos_y,
        "status": "active",
        "type": sensor_type
    })
    r.sadd("sensor:all", mote_id)
    print(f"Sensor {mote_id} created at position ({pos_x}, {pos_y}).")


def add_reading(mote_id, temperature, humidity, light, voltage, timestamp=None):
    """Add a new sensor reading."""
    if timestamp is None:
        timestamp = datetime.now()
        epoch = timestamp.timestamp()
    else:
        epoch = timestamp

    date_str = datetime.fromtimestamp(epoch).strftime("%Y-%m-%d")
    time_str = datetime.fromtimestamp(epoch).strftime("%H:%M:%S")

    reading = json.dumps({
        "temp": temperature,
        "humidity": humidity,
        "light": light,
        "voltage": voltage,
        "date": date_str,
        "time": time_str
    })

    # Add to time series
    r.zadd(f"sensor:{mote_id}:readings", {reading: epoch})

    # Update latest reading
    r.hset(f"sensor:{mote_id}:latest", mapping={
        "temperature": temperature,
        "humidity": humidity,
        "light": light,
        "voltage": voltage,
        "timestamp": epoch,
        "date": date_str,
        "time": time_str
    })

    print(f"Reading added for sensor {mote_id}: {temperature}°C, {humidity}% humidity")


#############################################################
# R = READ
#############################################################

def get_sensor(mote_id):
    """Retrieve sensor metadata."""
    data = r.hgetall(f"sensor:{mote_id}")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_latest_reading(mote_id):
    """Get the most recent reading from a sensor."""
    data = r.hgetall(f"sensor:{mote_id}:latest")
    return {k.decode(): v.decode() for k, v in data.items()}


def get_readings_in_range(mote_id, start_epoch, end_epoch, limit=100):
    """
    Get sensor readings within a time range.
    Uses SORTED SET range query by score (timestamp).
    """
    readings = r.zrangebyscore(
        f"sensor:{mote_id}:readings",
        start_epoch,
        end_epoch,
        start=0,
        num=limit
    )
    return [json.loads(r.decode()) for r in readings]


def get_all_sensors():
    """List all registered sensor IDs."""
    return [int(s.decode()) for s in r.smembers("sensor:all")]


def get_sensor_count():
    """Get total number of sensors."""
    return r.scard("sensor:all")


#############################################################
# U = UPDATE
#############################################################

def update_sensor_status(mote_id, new_status):
    """Update the status of a sensor (active, inactive, maintenance)."""
    r.hset(f"sensor:{mote_id}", "status", new_status)
    print(f"Sensor {mote_id} status updated to '{new_status}'.")


def update_sensor_position(mote_id, pos_x, pos_y):
    """Update the position of a sensor."""
    r.hset(f"sensor:{mote_id}", mapping={
        "pos_x": pos_x,
        "pos_y": pos_y
    })
    print(f"Sensor {mote_id} position updated to ({pos_x}, {pos_y}).")


#############################################################
# D = DELETE
#############################################################

def delete_sensor(mote_id):
    """Delete a sensor and all its associated data."""
    # Remove from sensor index
    r.srem("sensor:all", mote_id)

    # Remove from temperature ranking
    r.zrem("sensor:avg:temperature", mote_id)

    # Delete all associated keys
    r.delete(f"sensor:{mote_id}")
    r.delete(f"sensor:{mote_id}:readings")
    r.delete(f"sensor:{mote_id}:latest")
    r.delete(f"sensor:{mote_id}:connectivity")

    print(f"Sensor {mote_id} and all associated data deleted.")


def delete_old_readings(mote_id, before_epoch):
    """Delete readings older than a specified timestamp."""
    removed = r.zremrangebyscore(f"sensor:{mote_id}:readings", "-inf", before_epoch)
    print(f"Removed {removed} old readings from sensor {mote_id}.")
    return removed


#############################################################
# ANALYTICAL QUERIES
#############################################################

def top_hottest_sensors(n=10):
    """Get sensors ranked by average temperature (highest first)."""
    print(f"\nTop {n} hottest sensors (by avg temperature):")
    results = r.zrevrange("sensor:avg:temperature", 0, n-1, withscores=True)
    for mote_id, avg_temp in results:
        print(f"  Sensor {mote_id.decode()}: {avg_temp:.2f}°C")
    return results


def top_coldest_sensors(n=10):
    """Get sensors ranked by average temperature (lowest first)."""
    print(f"\nTop {n} coldest sensors (by avg temperature):")
    results = r.zrange("sensor:avg:temperature", 0, n-1, withscores=True)
    for mote_id, avg_temp in results:
        print(f"  Sensor {mote_id.decode()}: {avg_temp:.2f}°C")
    return results


def get_recent_alerts(n=10):
    """Get the most recent sensor alerts."""
    print(f"\nRecent {n} alerts:")
    alerts = r.lrange("sensor:alerts", 0, n-1)
    for alert in alerts:
        print(f"  - {alert.decode()}")
    return alerts


def get_alert_count():
    """Get total number of alerts."""
    return r.llen("sensor:alerts")


def sensors_in_temperature_range(min_temp, max_temp):
    """Find sensors with average temperature in a specific range."""
    print(f"\nSensors with avg temperature between {min_temp}°C and {max_temp}°C:")
    results = r.zrangebyscore("sensor:avg:temperature", min_temp, max_temp, withscores=True)
    for mote_id, avg_temp in results:
        print(f"  Sensor {mote_id.decode()}: {avg_temp:.2f}°C")
    return results


def get_reading_count(mote_id):
    """Get total number of readings for a sensor."""
    return r.zcard(f"sensor:{mote_id}:readings")


def get_connectivity(mote_id):
    """Get connectivity data for a sensor (transmission probabilities)."""
    data = r.hgetall(f"sensor:{mote_id}:connectivity")
    return {k.decode(): float(v.decode()) for k, v in data.items()}


def find_best_connected_sensors(mote_id, threshold=0.8):
    """Find sensors with high transmission probability from a given sensor."""
    connectivity = get_connectivity(mote_id)
    good_connections = {k: v for k, v in connectivity.items() if v >= threshold}
    print(f"\nSensors well-connected to sensor {mote_id} (>{threshold*100}% success):")
    for target, prob in sorted(good_connections.items(), key=lambda x: -x[1]):
        print(f"  -> Sensor {target}: {prob*100:.1f}%")
    return good_connections


#############################################################
# TEMPORAL ANALYSIS (Daily Patterns)
#############################################################

def get_hourly_temperature_pattern(mote_id, limit=10000):
    """Analyze temperature patterns by hour of day for a sensor."""
    readings = r.zrange(f"sensor:{mote_id}:readings", 0, limit-1)

    hourly_temps = {h: [] for h in range(24)}

    for reading in readings:
        data = json.loads(reading.decode())
        time_str = data.get("time", "00:00:00")
        hour = int(time_str.split(":")[0])
        temp = data.get("temp", 0)
        hourly_temps[hour].append(temp)

    print(f"\nHourly temperature pattern for Sensor {mote_id}:")
    result = {}
    for hour in range(24):
        if hourly_temps[hour]:
            avg = sum(hourly_temps[hour]) / len(hourly_temps[hour])
            result[hour] = round(avg, 2)
            bar = "█" * int(avg - 15)  # Visual bar (assuming ~15-25°C range)
            print(f"  {hour:02d}:00  {avg:5.2f}°C  {bar}")

    return result


def get_daily_temperature_cycle(mote_id):
    """Show temperature variation throughout the day (min, max, avg per hour)."""
    readings = r.zrange(f"sensor:{mote_id}:readings", 0, -1)

    hourly_data = {h: [] for h in range(24)}

    for reading in readings:
        data = json.loads(reading.decode())
        time_str = data.get("time", "00:00:00")
        hour = int(time_str.split(":")[0])
        temp = data.get("temp", 0)
        hourly_data[hour].append(temp)

    print(f"\nDaily temperature cycle for Sensor {mote_id}:")
    print(f"  {'Hour':<6} {'Min':>8} {'Avg':>8} {'Max':>8}")
    print("  " + "-" * 32)

    result = {}
    for hour in range(24):
        if hourly_data[hour]:
            temps = hourly_data[hour]
            result[hour] = {
                "min": round(min(temps), 2),
                "avg": round(sum(temps) / len(temps), 2),
                "max": round(max(temps), 2)
            }
            print(f"  {hour:02d}:00  {result[hour]['min']:8.2f} {result[hour]['avg']:8.2f} {result[hour]['max']:8.2f}")

    return result


def compare_day_night_temperatures():
    """Compare average temperatures between day (8-20h) and night (20-8h)."""
    sensor_ids = get_all_sensors()

    print("\nDay vs. Night temperature comparison:")
    print(f"  {'Sensor':<10} {'Day (8-20h)':>12} {'Night':>12} {'Difference':>12}")
    print("  " + "-" * 48)

    results = []
    for mote_id in sorted(sensor_ids)[:10]:
        readings = r.zrange(f"sensor:{mote_id}:readings", 0, 5000)

        day_temps = []
        night_temps = []

        for reading in readings:
            data = json.loads(reading.decode())
            time_str = data.get("time", "00:00:00")
            hour = int(time_str.split(":")[0])
            temp = data.get("temp", 0)

            if 8 <= hour < 20:
                day_temps.append(temp)
            else:
                night_temps.append(temp)

        if day_temps and night_temps:
            day_avg = sum(day_temps) / len(day_temps)
            night_avg = sum(night_temps) / len(night_temps)
            diff = day_avg - night_avg
            results.append((mote_id, day_avg, night_avg, diff))
            print(f"  {mote_id:<10} {day_avg:>12.2f} {night_avg:>12.2f} {diff:>+12.2f}")

    return results


#############################################################
# SPATIAL ANALYSIS (Location-based Patterns)
#############################################################

def get_sensors_by_zone(x_threshold=20):
    """Group sensors by zone (left/right of x threshold)."""
    sensor_ids = get_all_sensors()

    left_zone = []
    right_zone = []

    for mote_id in sensor_ids:
        sensor = get_sensor(mote_id)
        x = float(sensor.get("pos_x", 0))
        if x < x_threshold:
            left_zone.append(mote_id)
        else:
            right_zone.append(mote_id)

    print(f"\nSensors by zone (threshold x={x_threshold}):")
    print(f"  Left zone:  {len(left_zone)} sensors")
    print(f"  Right zone: {len(right_zone)} sensors")

    return {"left": left_zone, "right": right_zone}


def compare_zones_temperature(x_threshold=20):
    """Compare average temperatures between left and right zones."""
    zones = get_sensors_by_zone(x_threshold)

    def zone_avg_temp(sensor_ids):
        temps = []
        for mote_id in sensor_ids:
            score = r.zscore("sensor:avg:temperature", mote_id)
            if score:
                temps.append(score)
        return sum(temps) / len(temps) if temps else 0

    left_avg = zone_avg_temp(zones["left"])
    right_avg = zone_avg_temp(zones["right"])

    print(f"\nZone temperature comparison:")
    print(f"  Left zone (x < {x_threshold}):  {left_avg:.2f}°C")
    print(f"  Right zone (x >= {x_threshold}): {right_avg:.2f}°C")
    print(f"  Difference: {abs(left_avg - right_avg):.2f}°C")

    return {"left": left_avg, "right": right_avg}


def find_hotspots(n=5):
    """Find spatial hotspots (warmest areas in the lab)."""
    print(f"\nTop {n} temperature hotspots:")

    results = r.zrevrange("sensor:avg:temperature", 0, n-1, withscores=True)

    hotspots = []
    for mote_id, temp in results:
        mid = mote_id.decode()
        sensor = get_sensor(int(mid))
        x = sensor.get("pos_x", "?")
        y = sensor.get("pos_y", "?")
        hotspots.append({"sensor": mid, "temp": temp, "x": x, "y": y})
        print(f"  Sensor {mid}: {temp:.2f}°C at position ({x}, {y})")

    return hotspots


def find_coldspots(n=5):
    """Find spatial coldspots (coldest areas in the lab)."""
    print(f"\nTop {n} temperature coldspots:")

    results = r.zrange("sensor:avg:temperature", 0, n-1, withscores=True)

    coldspots = []
    for mote_id, temp in results:
        mid = mote_id.decode()
        sensor = get_sensor(int(mid))
        x = sensor.get("pos_x", "?")
        y = sensor.get("pos_y", "?")
        coldspots.append({"sensor": mid, "temp": temp, "x": x, "y": y})
        print(f"  Sensor {mid}: {temp:.2f}°C at position ({x}, {y})")

    return coldspots


def spatial_temperature_map():
    """Create a spatial temperature overview of all sensors."""
    sensor_ids = get_all_sensors()

    print("\nSpatial temperature map:")
    print(f"  {'Sensor':<8} {'X':>6} {'Y':>6} {'Avg Temp':>10}")
    print("  " + "-" * 32)

    data = []
    for mote_id in sorted(sensor_ids):
        sensor = get_sensor(mote_id)
        x = float(sensor.get("pos_x", 0))
        y = float(sensor.get("pos_y", 0))
        temp = r.zscore("sensor:avg:temperature", mote_id)

        if temp:
            data.append({"sensor": mote_id, "x": x, "y": y, "temp": temp})
            print(f"  {mote_id:<8} {x:>6.1f} {y:>6.1f} {temp:>10.2f}°C")

    return data


#############################################################

if __name__ == "__main__":
    print("=" * 50)
    print("IoT Use Case - Queries Demo")
    print("=" * 50)

    # Statistics
    sensor_count = get_sensor_count()
    print(f"\nTotal sensors: {sensor_count}")

    top_hottest_sensors(5)
    top_coldest_sensors(5)

    alert_count = get_alert_count()
    print(f"\nTotal alerts: {alert_count}")
    get_recent_alerts(5)

    sensors_in_temperature_range(18.0, 22.0)

    # Sensor Details
    print("\n" + "-" * 50)
    print("Sensor 1 Details")
    print("-" * 50)
    print(f"Metadata: {get_sensor(1)}")
    print(f"Latest reading: {get_latest_reading(1)}")
    print(f"Total readings: {get_reading_count(1)}")

    # Temporal Analysis
    print("\n" + "=" * 50)
    print("TEMPORAL ANALYSIS")
    print("=" * 50)
    get_hourly_temperature_pattern(1, limit=5000)
    get_daily_temperature_cycle(1)
    compare_day_night_temperatures()

    # Spatial Analysis
    print("\n" + "=" * 50)
    print("SPATIAL ANALYSIS")
    print("=" * 50)
    find_hotspots(5)
    find_coldspots(5)
    compare_zones_temperature(20)

    # Connectivity
    print("\n" + "-" * 50)
    print("Network Connectivity")
    print("-" * 50)
    find_best_connected_sensors(1, threshold=0.5)

    # CRUD Demo
    print("\n" + "-" * 50)
    print("CRUD Demo")
    print("-" * 50)
    create_sensor(99, pos_x=5.0, pos_y=5.0, sensor_type="Test")
    print(f"Sensor 99: {get_sensor(99)}")
    add_reading(99, temperature=22.5, humidity=45.0, light=300, voltage=2.7)
    print(f"Latest reading: {get_latest_reading(99)}")
    update_sensor_status(99, "maintenance")
    print(f"After update: {get_sensor(99)}")
    delete_sensor(99)
    print(f"After delete: {get_sensor(99)}")
