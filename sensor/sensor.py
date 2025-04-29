import socket
import json
import time
import argparse
from datetime import datetime

def get_sensor_data(sensor_id):
    return {
        "sensor_id": sensor_id,
        "temperature": round(20 + 5 * (0.5 - time.time() % 1), 2),
        "humidity": round(50 + 10 * (0.5 - time.time() % 1), 2),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drone_ip", type=str, default="127.0.0.1")
    parser.add_argument("--drone_port", type=int, default=5000)
    parser.add_argument("--interval", type=int, default=2)
    parser.add_argument("--sensor_id", type=str, default="sensor1")
    args = parser.parse_args()

    while True:
        try:
            with socket.create_connection((args.drone_ip, args.drone_port)) as sock:
                print(f"[{args.sensor_id}] Connected to Drone at {args.drone_ip}:{args.drone_port}")
                while True:
                    data = get_sensor_data(args.sensor_id)
                    sock.sendall(json.dumps(data).encode() + b"\n")
                    print(f"[{args.sensor_id}] Sent: {data}")
                    time.sleep(args.interval)
        except Exception as e:
            print(f"[{args.sensor_id}] Connection failed: {e}, retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
