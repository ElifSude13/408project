import tkinter as tk
from tkinter import ttk
import threading
import socket
import json
import time
import logging
import os

DRONE_PORT = 5000
CENTRAL_SERVER_IP = "127.0.0.1"
CENTRAL_SERVER_PORT = 6000

sensor_data_buffer = []

# Log ayarları
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
    
        self.tree = ttk.Treeview(root, columns=("Sensor ID", "Temperature", "Humidity", "Timestamp"), show="headings")
        for col in ("Sensor ID", "Temperature", "Humidity", "Timestamp"):
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)
    
        self.status_label = tk.Label(root, text="Status: Normal", fg="green")
        self.status_label.pack()
    
        # Batarya ile ilgili değişkenler ve label
        self.battery_level = 100.0
        self.returning_to_base = False
        self.queued_data = []
    
        self.battery_label = tk.Label(root, text=f"Battery: {self.battery_level:.1f}%", fg="blue")
        self.battery_label.pack()
    
        # Sunucu ve forward threadleri
        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.forward_to_central, daemon=True).start()
    
        # Batarya tüketim döngüsü thread'i
        threading.Thread(target=self.battery_drain_loop, daemon=True).start

     def battery_drain_loop(self):
        while True:
            time.sleep(5)
            self.battery_level -= 1.0
            if self.battery_level < 0:
                self.battery_level = 0
            self.root.after(0, self.update_battery_label)

            if self.battery_level < 20.0 and not self.returning_to_base:
                self.returning_to_base = True
                logging.warning("Battery low! Returning to base.")
                self.root.after(0, lambda: self.status_label.config(text="Status: Returning to Base", fg="red"))

            elif self.battery_level >= 90.0 and self.returning_to_base:
                self.returning_to_base = False
                logging.info("Battery restored! Resuming normal operation.")
                self.root.after(0, lambda: self.status_label.config(text="Status: Normal", fg="green"))
                # Flush queued data
                self.flush_queued_data

    def flush_queued_data(self):
        try:
            with socket.create_connection((CENTRAL_SERVER_IP, CENTRAL_SERVER_PORT)) as central_sock:
                for data in self.queued_data:
                    central_sock.sendall(json.dumps(data).encode() + b"\n")
                    logging.info(f"[QUEUE-FLUSH] Sent: {data}")
                self.queued_data.clear()
        except Exception as e:
            logging.error(f"Flush failed: {e}")


    
    def update_battery_label(self):
        self.battery_label.config(text=f"Battery: {self.battery_level:.1f}%")


    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(("", DRONE_PORT))
            server_socket.listen()
            logging.info(f"Drone listening for sensors on port {DRONE_PORT}")
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_sensor, args=(conn, addr), daemon=True).start()

    def handle_sensor(self, conn, addr):
        with conn:
            logging.info(f"Sensor connected from {addr}")
            buffer = b""
            while True:
                try:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        data = json.loads(line.decode())
                        self.root.after(0, self.update_gui, data)
                        sensor_data_buffer.append(data)
                        logging.info(f"Received data: {data}")
                except Exception as e:
                    logging.error(f"Connection error with sensor {addr}: {e}")
                    break

    def update_gui(self, data):
        self.tree.insert("", tk.END, values=(data["sensor_id"], data["temperature"], data["humidity"], data["timestamp"]))

    def forward_to_central(self):
        while True:
            if sensor_data_buffer:
                if self.returning_to_base:
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DroneGUI(root)
    root.mainloop()
