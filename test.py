import subprocess
import time
import os
import signal

def start_process(name, args):
    print(f"Starting {name}...")
    return subprocess.Popen(args)

def stop_process(proc, name):
    print(f"Stopping {name}...")
    try:
        proc.terminate()
    except:
        pass

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)

    # Start Central Server
    server_proc = start_process("Central Server", ["python", "gui/server_gui.py"])
    time.sleep(1)

    # Start Drone
    drone_proc = start_process("Drone", ["python", "gui/drone_gui.py"])
    time.sleep(2)

    # Start Sensor 1 (normal)
    sensor1_proc = start_process("Sensor 1", ["python", "sensor/sensor.py", "--sensor_id", "sensor1"])
    time.sleep(1)

    # Start Sensor 2 (anomaly mode if implemented)
    print("Injecting anomaly...")
    sensor2_proc = start_process("Sensor 2", ["python", "sensor/sensor.py", "--sensor_id", "sensor2"])
    time.sleep(1)

    # Wait for sensors to run
    print("🟢 Test running... observing normal + anomaly + logs")
    time.sleep(10)

    # Simulate sensor disconnection (Sensor 1)
    print("Simulating sensor disconnection...")
    stop_process(sensor1_proc, "Sensor 1")
    time.sleep(5)

    # Wait for battery to drain below 20% (5s per % → 80s)
    print("⏳ Waiting for battery to drop below 20%...")
    time.sleep(85)

    print("Waiting for battery to recover above 90%...")
    time.sleep(80)

    print("✅ Test complete. You can now review GUI screens and log files.")

    # Clean up processes
    stop_process(sensor2_proc, "Sensor 2")
    stop_process(drone_proc, "Drone")
    stop_process(server_proc, "Central Server")
