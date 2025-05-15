import tkinter as tk
from tkinter import ttk
import threading
import socket
import json
import logging
import os

# TCP port for incoming drone data
CENTRAL_PORT = 6000

# Logging configuration: file + console output
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Central Server Dashboard")

        # Create a Treeview widget to display incoming sensor data
        self.tree = ttk.Treeview(root, columns=("Sensor ID", "Temperature", "Humidity", "Timestamp"), show="headings")
        for col in ("Sensor ID", "Temperature", "Humidity", "Timestamp"):
            self.tree.heading(col, text=col)

        # Tag to highlight anomalous rows in red
        self.tree.tag_configure("anomaly", background="lightcoral")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Label and Listbox to display detected anomalies separately
        self.anomaly_label = tk.Label(root, text="Anomalies", fg="darkred")
        self.anomaly_label.pack(pady=(10, 0))  # spacing above the label

        self.anomaly_listbox = tk.Listbox(root, height=6)
        self.anomaly_listbox.pack(fill=tk.BOTH, expand=True)

        # Start the TCP server thread to listen for Drone connections
        threading.Thread(target=self.start_server, daemon=True).start()

    # TCP server to listen for connections from the drone
    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(("", CENTRAL_PORT))
            server_socket.listen()
            logging.info(f"Central Server listening on port {CENTRAL_PORT}")
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_drone, args=(conn, addr), daemon=True).start()

    # Handle data from a connected drone client
    def handle_drone(self, conn, addr):
        with conn:
            logging.info(f"Drone connected from {addr}")
            buffer = b""
            while True:
                try:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break  # connection closed
                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        data = json.loads(line.decode())

                        # GUI update must be done in the main thread
                        self.root.after(0, self.update_gui, data)
                        logging.info(f"Received data from Drone: {data}")
                except Exception as e:
                    logging.error(f"Connection error with Drone: {e}")
                    break

    # Update GUI with new data and mark anomalies
    def update_gui(self, data):
        tag = "anomaly" if "anomaly" in data else ""

        # Insert sensor data into the main table
        self.tree.insert("", tk.END, values=(
            data.get("sensor_id", ""),
            data.get("temperature", ""),
            data.get("humidity", ""),
            data.get("timestamp", "")
        ), tags=(tag,))

        # If anomaly detected, log and display it in the anomaly listbox
        if "anomaly" in data:
            for a in data["anomaly"]:
                msg = f"[ANOMALY] {data['sensor_id']} - {a}"
                self.anomaly_listbox.insert(tk.END, msg)
                logging.warning(msg)

# Start the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()
