import tkinter as tk
from tkinter import ttk
import threading
import socket
import json
import time
import logging
import os

# Drone listens on this port for incoming sensor connections
DRONE_PORT = 5000

# Central server connection details
CENTRAL_SERVER_IP = "127.0.0.1"
CENTRAL_SERVER_PORT = 6000

# Buffer to hold incoming sensor data temporarily
sensor_data_buffer = []

# Setup logging: both to file and console
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/drone.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

class DroneGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Drone Dashboard")

        # GUI component to display live sensor data
        self.tree = ttk.Treeview(root, columns=("Sensor ID", "Temperature", "Humidity", "Timestamp"), show="headings")
        for col in ("Sensor ID", "Temperature", "Humidity", "Timestamp"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Status label to indicate operational state
        self.status_label = tk.Label(root, text="Status: Normal", fg="green")
        self.status_label.pack()

        # Battery simulation parameters
        self.battery_level = 100.0
        self.returning_to_base = False
        self.queued_data = []

        # Battery level indicator
        self.battery_label = tk.Label(root, text=f"Battery: {self.battery_level:.1f}%", fg="blue")
        self.battery_label.pack()

        # Anomaly list label and component
        self.anomaly_list_label = tk.Label(root, text="Anomalies", fg="darkred")
        self.anomaly_list_label.pack()

        self.anomaly_listbox = tk.Listbox(root, height=6)
        self.anomaly_listbox.pack(fill=tk.BOTH, expand=True)

        # Start threads for TCP server, data forwarding, and battery drain
        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.forward_to_central, daemon=True).start()
        threading.Thread(target=self.battery_drain_loop, daemon=True).start()

    # Detect anomalies based on predefined thresholds
    def is_anomaly(self, data):
        temp = data.get("temperature")
        hum = data.get("humidity")
        anomalies = []

        if temp is not None:
            if temp > 60.0 or temp < -10.0:
                anomalies.append(f"Temperature anomaly: {temp}°C")
        if hum is not None:
            if hum > 90.0 or hum < 10.0:
                anomalies.append(f"Humidity anomaly: {hum}%")

        return anomalies

    # Simulate battery consumption over time
    def battery_drain_loop(self):
        while True:
            time.sleep(5)
            self.battery_level -= 1.0
            if self.battery_level < 0:
                self.battery_level = 0
            self.root.after(0, self.update_battery_label)

            # Enter low battery mode
            if self.battery_level < 20.0 and not self.returning_to_base:
                self.returning_to_base = True
                logging.warning("Battery low! Returning to base.")
                self.root.after(0, lambda: self.status_label.config(text="Status: Returning to Base", fg="red"))

            # Restore to normal if battery recharges
            elif self.battery_level >= 90.0 and self.returning_to_base:
                self.returning_to_base = False
                logging.info("Battery restored! Resuming normal operation.")
                self.root.after(0, lambda: self.status_label.config(text="Status: Normal", fg="green"))
                self.flush_queued_data()

    # Send queued data to server after battery recovers
    def flush_queued_data(self):
        try:
            with socket.create_connection((CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT)) as central_sock:
                for data in self.queued_data:
                    central_sock.sendall(json.dumps(data).encode() + b"\n")
                    logging.info(f"[QUEUE-FLUSH] Sent: {data}")
                self.queued_data.clear()
        except Exception as e:
            logging.error(f"Flush failed: {e}")

    # Update battery level on the GUI
    def update_battery_label(self):
        self.battery_label.config(text=f"Battery: {self.battery_level:.1f}%")

    # Start TCP server to accept sensor connections
    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(("", DRONE_PORT))
            server_socket.listen()
            logging.info(f"Drone listening for sensors on port {DRONE_PORT}")
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_sensor, args=(conn, addr), daemon=True).start()

    # Handle incoming data from each connected sensor
    def handle_sensor(self, conn, addr):
        with conn:
            logging.info(f"Sensor connected from {addr}")
            buffer = b""
            while True:
                try:
                    chunk = conn.recv(1024)
                    if not chunk:
                        raise ConnectionResetError("Sensor disconnected cleanly.")
                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)

                        # If battery is dead, drop incoming data
                        if self.battery_level <= 0:
                            logging.warning("Battery depleted. Dropping incoming data.")
                            continue

                        data = json.loads(line.decode())
                        self.root.after(0, self.update_gui, data)

                        # Check for anomalies
                        anomalies = self.is_anomaly(data)
                        if anomalies:
                            for a in anomalies:
                                msg = f"[ANOMALY] {data['sensor_id']} - {a}"
                                self.root.after(0, self.anomaly_listbox.insert, tk.END, msg)
                                logging.warning(msg)
                            data["anomaly"] = anomalies

                        sensor_data_buffer.append(data)
                        logging.info(f"Received data: {data}")
                except Exception as e:
                    msg = f"[DISCONNECT] Sensor at {addr} disconnected: {e}"
                    self.root.after(0, self.anomaly_listbox.insert, tk.END, msg)
                    logging.warning(msg)
                    break

    # Add new row to GUI table
    def update_gui(self, data):
        self.tree.insert("", tk.END, values=(data["sensor_id"], data["temperature"], data["humidity"], data["timestamp"]))

    # Periodically forward buffered sensor data to the central server
    def forward_to_central(self):
        while True:
            if sensor_data_buffer:
                if self.returning_to_base:
                    # Queue data while returning to base
                    self.queued_data.extend(sensor_data_buffer)
                    logging.warning(f"[QUEUE] Queued {len(sensor_data_buffer)} items during low battery.")
                    sensor_data_buffer.clear()
                else:
                    try:
                        with socket.create_connection((CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT)) as central_sock:
                            for data in sensor_data_buffer:
                                central_sock.sendall(json.dumps(data).encode() + b"\n")
                                logging.info(f"Forwarded to Central Server: {data}")
                            sensor_data_buffer.clear()
                    except Exception as e:
                        logging.error(f"Could not connect to Central Server: {e}")
            time.sleep(5)

# Entry point to launch the Drone GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = DroneGUI(root)
    root.mainloop()
