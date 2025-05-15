import socket
import json
import time
import argparse
import logging
from datetime import datetime, timezone, timedelta
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Command-line arguments to configure sensor behavior
parser = argparse.ArgumentParser()
parser.add_argument("--drone_ip", type=str, default="127.0.0.1")  # IP of the drone
parser.add_argument("--drone_port", type=int, default=5000)       # Port the drone listens on
parser.add_argument("--interval", type=int, default=2)            # Time interval between messages
parser.add_argument("--sensor_id", type=str, default="sensor1")   # Unique ID of this sensor
args, unknown = parser.parse_known_args()

# Configure logging for this specific sensor
logging.basicConfig(
    filename=f"logs/{args.sensor_id}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# --- SENSOR DATA GENERATION FUNCTIONS ---

# ❗ For anomaly testing (comment this in for testing anomalies)
def get_sensor_data(sensor_id):
    turkey_tz = timezone(timedelta(hours=3))  # Use UTC+3 timezone (Turkey time)
    return {
        "sensor_id": sensor_id,
        "temperature": 100.0,      # Anomalous high temperature
        "humidity": 85.0,          # Still within normal humidity
        "timestamp": datetime.now(turkey_tz).isoformat()
    }

"""
# ✅ For normal operation (use this instead of above for non-anomaly test)
def get_sensor_data(sensor_id):
    turkey_tz = timezone(timedelta(hours=3))  # Use UTC+3 timezone (Turkey time)
    return {
        "sensor_id": sensor_id,
        "temperature": round(20 + 5 * (0.5 - time.time() % 1), 2),  # Simulate small variation
        "humidity": round(50 + 10 * (0.5 - time.time() % 1), 2),
        "timestamp": datetime.now(turkey_tz).isoformat()
    }
"""

# --- MAIN FUNCTION ---

def main():
    while True:
        try:
            # Try to connect to the drone
            with socket.create_connection((args.drone_ip, args.drone_port)) as sock:
                logging.info(f"Connected to Drone at {args.drone_ip}:{args.drone_port}")
                while True:
                    # Generate and send sensor data
                    data = get_sensor_data(args.sensor_id)
                    sock.sendall(json.dumps(data).encode() + b"\n")
                    logging.info(f"Sent: {data}")
                    time.sleep(args.interval)
        except Exception as e:
            logging.error(f"Connection failed: {e}, retrying in 5 seconds...")
            time.sleep(5)

# Entry point
if __name__ == "__main__":
    main()
