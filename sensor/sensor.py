import socket
import json
import time
import argparse
import logging
from datetime import datetime
import os

# Log ayarları
os.makedirs("logs", exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument("--drone_ip", type=str, default="127.0.0.1")
parser.add_argument("--drone_port", type=int, default=5000)
parser.add_argument("--interval", type=int, default=2)
parser.add_argument("--sensor_id", type=str, default="sensor1")
args, unknown = parser.parse_known_args()

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

def get_sensor_data(sensor_id):
    return {
        "sensor_id": sensor_id,
        "temperature": round(20 + 5 * (0.5 - time.time() % 1), 2),
        "humidity": round(50 + 10 * (0.5 - time.time() % 1), 2),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def main():
    while True:
        try:
            with socket.create_connection((args.drone_ip, args.drone_port)) as sock:
                logging.info(f"Connected to Drone at {args.drone_ip}:{args.drone_port}")
                while True:
                    data = get_sensor_data(args.sensor_id)
                    sock.sendall(json.dumps(data).encode() + b"\n")
                    logging.info(f"Sent: {data}")
                    time.sleep(args.interval)
        except Exception as e:
            logging.error(f"Connection failed: {e}, retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
